import ast
import glob
import os
import zipfile

from collections import defaultdict

import ssdeep
import time

MIN_LEN_FUZZY = 7


def pass_test(resource):
    return not resource.startswith("res/drawable") and not resource.startswith("META-INF")


def get_files(path):
    file_list = []

    for f in glob.glob(path + "/**/*", recursive=True):
        if not os.path.isdir(f):
            file_list.append(f)

    return file_list


def full_ssdeep(dataset_path, fuzzy_hash_file):
    """
    Get the normal ssdeep hash removing only resources from drawable folder
    :return:
    """
    ssdeep_hashes = defaultdict(list)
    apks = get_files(dataset_path)
    with open(fuzzy_hash_file, "w") as fuzzy_hashes_file:
        for apk in apks:
            try:
                with zipfile.ZipFile(apk, 'r') as zf:
                    archive_elements = [(data.filename, data.file_size) for data in zf.filelist]
                    for resource, res_size in archive_elements:
                        if pass_test(resource):
                            bfile = zf.read(resource)
                            fz_h = ssdeep.hash(bfile)
                            if len(fz_h) > MIN_LEN_FUZZY:  # Get rid off only single characters
                                ssdeep_hashes[apk].append(fz_h)
                fuzzy_hashes_file.write(str((apk, ssdeep_hashes[apk])) + "\n")
            except Exception as e:
                print(apk)
                print(e)

    return ssdeep_hashes


def read_hashes_file(path):
    ssdeep_hashes = defaultdict(list)

    lines = open(path, "r").read().splitlines()
    for l in lines:
        tup = ast.literal_eval(l)
        ssdeep_hashes[tup[0]] = tup[1]

    return ssdeep_hashes


def get_scanned(file_path):
    names = list()
    lines = open(file_path, "r").read().splitlines()
    for l in lines:
        names.append(ast.literal_eval(l)[0])

    return names


if __name__ == '__main__':
    test = full_ssdeep("/media/pret/Maxtor1/AndroDumpsys/AndroDumpsys_db", "hashes_database.txt")
    data = full_ssdeep("/media/pret/Maxtor1/AndroDumpsys/AndroDumpsys_test_safe", "hashes.txt")
    #test = read_hashes_file("edit/hashes.txt")
    #data = read_hashes_file("edit/hashes_database.txt")
    #already_scanned = list() #get_scanned("results.txt")
    final_dict = defaultdict(dict)

    start = time.time()

    with open("nresults.txt", "a") as ff:
        for t_app, t_fuzzies in test.items():
            #  if t_app not in already_scanned:
            apk_scores_dict = dict()
            for db_app, db_fuzzies in data.items():
                somma = 0.0
                for t_fuz in t_fuzzies:
                    max_fuz_score = 0
                    for db_fuz in db_fuzzies:
                        temp = ssdeep.compare(t_fuz, db_fuz)
                        if temp > max_fuz_score:
                            max_fuz_score = temp
                    somma += max_fuz_score
                avg = somma / len(t_fuzzies)
                if avg > 20:
                    apk_scores_dict[db_app] = avg
            final_dict[t_app] = apk_scores_dict  # each apk contains a dict {neighbor: avg_sim}
            ff.write(str((t_app, apk_scores_dict))+"\n")

    print(time.time() - start)
    # Get top list neighbors and classify samples
    '''
    for tested_apk, neighbors_dict in final_dict.items():
        top_neighbors = sorted(neighbors_dict.items(), key=lambda x: -x[1])[:5]
        print(top_neighbors)
    '''
