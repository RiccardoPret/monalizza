import ast
import glob
import os
import zipfile
from collections import defaultdict

import pathlib
import ssdeep
import multiprocessing as mp
import numpy
import shutil

SLOPE = 0.05
MIN_LEN_FUZZY = 7
MIN_LEN_BLOCK_FUZZY = 3


def get_files(path):
    file_list = []

    for f in glob.glob(path + "/**/*", recursive=True):
        if not os.path.isdir(f):
            file_list.append(f)

    return file_list


def chunk_string(fuzzy, n):
    if len(fuzzy) == 0:
        print("Empty string")
        return ""  # return empty iterable
    n = min(n, len(fuzzy))
    k, m = divmod(len(fuzzy), n)
    return [fuzzy[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


def chunk_string2(fuzzy, n):
    """
    Test if it is faster than the other
    :param fuzzy:
    :param n:
    :return:
    """
    len_str = len(fuzzy)
    n = min(len_str, n)
    return [fuzzy[i*(len_str//n) + min(i, len_str % n):(i+1)*(len_str//n) + min(i+1, len_str % n)] for i in range(n)]


def get_family(apk):
    return apk.split("/")[-2]


def split_fuzzy_with_function(fuzzy_hash):
    n_pieces = int(round(SLOPE * len(fuzzy_hash), 0) + 1)
    sub_hashes = chunk_string(fuzzy_hash, n_pieces)
    return sub_hashes


def get_sub_fuzzies(fuzzy_hash):
    sub_fuzzies = list()
    sub_fz1, sub_fz2 = fuzzy_hash.split(":")[1:3]  # Get rid off the header
    if len(sub_fz1) >= MIN_LEN_BLOCK_FUZZY:
        sub_fuzzies.extend(split_fuzzy_with_function(sub_fz1))
    if len(sub_fz2) >= MIN_LEN_BLOCK_FUZZY:
        sub_fuzzies.extend(split_fuzzy_with_function(sub_fz2))

    return sub_fuzzies


def generate_apk_fuzzy_list(apk):
    apk_fuzzy_list = list()
    resources_dict = defaultdict(list)  # resource: [sub_fuzzies]

    try:
        with zipfile.ZipFile(apk, 'r') as zf:
            archive_elements = [(data.filename, data.file_size) for data in zf.filelist]
            for resource, res_size in archive_elements:
                if not resource.startswith("res/drawable"):
                    bfile = zf.read(resource)
                    fz_h = ssdeep.hash(bfile)
                    if len(fz_h) >= MIN_LEN_FUZZY:
                        sub_fuzzies = get_sub_fuzzies(fz_h)
                        apk_fuzzy_list.extend(sub_fuzzies)
                        resources_dict[resource] = sub_fuzzies
    except zipfile.BadZipfile as e:
        print(str(e.args) + "\t" + apk)

    return apk_fuzzy_list, resources_dict


def print_hashes_file(hashes_file_name, ssdeep_hashes):
    with open(hashes_file_name, "a") as fuzzy_hashes_file:
        for apk, sub_fuzzy_list in ssdeep_hashes.items():
            fuzzy_hashes_file.write("('"+apk+"', "+str(sub_fuzzy_list)+")\n")


def print_resources_file(res_file_name, hashes_resources):
    # Write auxiliary file in order to list shared resources at the end
    with open(res_file_name, "w") as res_hash_file:
        for apk, res_hash_defaultdict in hashes_resources.items():
            res_hash_file.write("('" + apk + "', {")
            res_hashes = ", ".join(["'" + str(res.replace("'", "")) + "': " + str(fuzzy_list)
                                    for res, fuzzy_list in res_hash_defaultdict.items()])
            res_hash_file.write(res_hashes + "})\n")


def families_freq_from_hashes_file(hashes_file):
    fams_dict = dict()
    lines = open(hashes_file, "r").read().splitlines()
    for l in lines:
        apk = ast.literal_eval(l)[0]
        try:
            fams_dict[get_family(apk)] += 1
        except:
            fams_dict[get_family(apk)] = 1

    return fams_dict

#@profile
def generate_fuzzy_hashes(folder, logs_folder):
    hashes_resources = defaultdict(defaultdict)  # apk: {res: [fuzzy]}
    ssdeep_hashes = defaultdict(list)  # apk: [fuzzy]
    apks = get_files(folder)

    for apk in apks:
        ssdeep_hashes[apk], hashes_resources[apk] = generate_apk_fuzzy_list(apk)

    # Store data
    print_hashes_file(logs_folder+"/hashes.txt", ssdeep_hashes)
    print_resources_file(logs_folder+"/res_hashes.txt", hashes_resources)

    return ssdeep_hashes

#@profile
def initialize_database(data_folder, logs_folder):
    ssdeep_hashes = defaultdict(list)  # apk: [fuzzy]
    apks = get_files(data_folder)
    fams_freq = dict()  # fam: |variants|

    for apk in apks:
        ssdeep_hashes[apk], nul = generate_apk_fuzzy_list(apk)
        try:
            fams_freq[get_family(apk)] += 1
        except KeyError:
            fams_freq[get_family(apk)] = 1

    # Store data (no print for res_hashes because they are not supposed to be available)
    pathlib.Path(logs_folder).mkdir(parents=True, exist_ok=True)
    print_hashes_file(mp.current_process().pid+"/hashes_database.txt", ssdeep_hashes)
    with open(logs_folder+"/families_frequency.txt", "w") as db_f:
        db_f.write(str(fams_freq))

    return ssdeep_hashes


def single_proc_compute_fuzzy(apk_list, output):
    hashes = defaultdict(list)  # apk: [fuzzy]
    fams_freq = dict()  # fam: |variants|

    for apk in apk_list:
        hashes[apk], nul = generate_apk_fuzzy_list(apk)
        try:
            fams_freq[get_family(apk)] += 1
        except KeyError:
            fams_freq[get_family(apk)] = 1
    pathlib.Path("hashes" + str(mp.current_process().pid)).mkdir(parents=True, exist_ok=True)
    print_hashes_file("hashes" + str(mp.current_process().pid) + "/hashes_database.txt", hashes)
    output.put(fams_freq)


def parallel_initialize_database(data_folder, logs_folder, n_proc):
    apks = get_files(data_folder)
    output = mp.Queue()
    fams_freq = dict()
    processes = [mp.Process(target=single_proc_compute_fuzzy, args=(apk_list, output)) for apk_list in numpy.array_split(apks, n_proc)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()
    unify_db_hashes()
    results = [output.get() for p in processes]
    pathlib.Path(logs_folder).mkdir(parents=True, exist_ok=True)

    for fam_freq in results:
        for fam, freq in fam_freq.items():
            try:
                fams_freq[fam] += freq
            except KeyError:
                fams_freq[fam] = freq
    with open("families_frequency.txt", "w") as db_f:
        db_f.write(str(fams_freq))


def unify_db_hashes():
    lines = list()
    for f in glob.glob("./**/*", recursive=True):
        if f.endswith("hashes_database.txt") and "hashes" in f.split("/")[-2]:
            lines.extend(open(f, "r").read().splitlines())
    with open("hashes_database.txt", "w") as cl:
        for l in lines:
            cl.write(l+"\n")
    # Delete temp folders
    for f in glob.glob("./**/*", recursive=True):
        if os.path.isdir(f) and "hashes" in f.split("/")[-1]:
            shutil.rmtree(f)


def parallel_generate_fuzzy_hashes(apks, logs_folder):
    hashes_resources = defaultdict(defaultdict)  # apk: {res: [fuzzy]}
    ssdeep_hashes = defaultdict(list)  # apk: [fuzzy]

    for apk in apks:
        ssdeep_hashes[apk], hashes_resources[apk] = generate_apk_fuzzy_list(apk)

    # Store data
    print_hashes_file(logs_folder + "/hashes.txt", ssdeep_hashes)
    print_resources_file(logs_folder + "/res_hashes.txt", hashes_resources)

    return ssdeep_hashes
