import ast
import glob
import os
import zipfile
from collections import defaultdict

import pathlib
import ssdeep

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


def full_ssdeep(dataset_path, fuzzy_hash_file):
    """
    Get the normal ssdeep hash removing only resources from drawable folder
    :return:
    """
    ssdeed_hashes = defaultdict(list)
    apks = get_files(dataset_path)
    with open(fuzzy_hash_file, "w") as fuzzy_hashes_file:
        for apk in apks:
            try:
                with zipfile.ZipFile(apk, 'r') as zf:
                    archive_elements = [(data.filename, data.file_size) for data in zf.filelist]
                    for resource, res_size in archive_elements:
                        if not resource.startswith("res/drawable"):
                            bfile = zf.read(resource)
                            fz_h = ssdeep.hash(bfile)
                            if len(fz_h) > 1:  # Get rid off only single characters
                                ssdeed_hashes[apk].append(fz_h)
                fuzzy_hashes_file.write(str((apk, ssdeed_hashes[apk])) + "\n")
            except Exception as e:
                print(apk)
                print(e)


def split_from_full_ssdeep(file_path):
    """
    :param file_path:
    :return:
    """
    ssdeep_hashes = defaultdict(list)

    with open(file_path, "r") as fp:
        lines = fp.read().splitlines()

    with open("splitted.txt", "w") as cf:
        for l in lines:
            tup = ast.literal_eval(l)
            apk = tup[0]
            for fz_h in tup[1]:
                if len(fz_h) >= MIN_LEN_FUZZY:
                    sub_fuzzies = get_sub_fuzzies(fz_h)
                    ssdeep_hashes[apk].extend(sub_fuzzies)
            cf.write(str((apk, ssdeep_hashes[apk])) + "\n")


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
    with open(hashes_file_name, "w") as fuzzy_hashes_file:
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
    print_hashes_file(logs_folder+"/hashes_database.txt", ssdeep_hashes)
    with open(logs_folder+"/families_frequency.txt", "w") as db_f:
        db_f.write(str(fams_freq))

    return ssdeep_hashes
