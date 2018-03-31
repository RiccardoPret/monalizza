import ast
import glob
import os
import time
from collections import defaultdict

import pathlib
import numpy
import multiprocessing as mp

from compute_jaccard import compute_jaccard
from detection import detection_mlw
from fuzzy_hashes import initialize_database, generate_fuzzy_hashes, parallel_initialize_database, \
    parallel_generate_fuzzy_hashes, get_files
from stats import mlw_stats


def read_hashes_file(path):
    #return ast.literal_eval(open(path, "r").read().splitlines()[0])
    ssdeep_hashes = defaultdict(list)

    lines = open(path, "r").read().splitlines()
    for l in lines:
        tup = ast.literal_eval(l)
        ssdeep_hashes[tup[0]] = tup[1]

    return ssdeep_hashes


def run_detection(data_folder, test_samples=None):
    pathlib.Path(data_folder).mkdir(parents=True, exist_ok=True)
    test_hashes_file_avail = os.path.exists(data_folder + "/hashes.txt")

    if test_hashes_file_avail:
        db_hashes = read_hashes_file("hashes_database.txt")
        test_hashes = read_hashes_file(data_folder + "/hashes.txt")
        detections = compute_jaccard(db_hashes, test_hashes, data_folder + "/jaccard_scores.txt")
    else:
        db_hashes = read_hashes_file("hashes_database.txt")
        start = time.time()
        test_hashes = generate_fuzzy_hashes(test_samples, data_folder)
        print("Testset fuzzy generation: " + str(time.time() - start))
        start = time.time()
        detections = compute_jaccard(db_hashes, test_hashes, data_folder + "/jaccard_scores.txt")
        print("Jaccard comparison: " + str(time.time() - start))

    detection_mlw(detections, data_folder)
    mlw_stats(data_folder + "/classifications.txt")


def init_db():
    start = time.time()
    initialize_database(database, ".")
    print("Database fuzzy generation: " + str(time.time() - start))


def parallel_detection(db_hashes, apks_list):
    process_folder = data_folder+"/"+str(mp.current_process().pid)
    pathlib.Path(process_folder).mkdir(parents=True, exist_ok=True)
    test_hashes = parallel_generate_fuzzy_hashes(apks_list, process_folder)
    s = time.time()
    detections = compute_jaccard(db_hashes, test_hashes, process_folder + "/jaccard_scores.txt")
    print("Jaccard computation: " + str(time.time() - s))
    detection_mlw(detections, process_folder)


def unify_classifications():
    lines = list()

    for f in glob.glob(data_folder+"/**/*", recursive=True):
        if f.endswith("classifications.txt"):
            lines.extend(open(f, "r").read().splitlines())
    with open("classifications.txt", "w") as cl:
        for l in lines:
            cl.write(l+"\n")


def first_run(testset, n_proc):
    db_hashes = read_hashes_file("hashes_database.txt")
    apks = get_files(testset)
    processes = [mp.Process(target=parallel_detection, args=(db_hashes, apk_list)) for apk_list in
                 numpy.array_split(apks, n_proc)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()
    unify_classifications()
    mlw_stats("classifications.txt")

if __name__ == '__main__':
    data_folder = "ris_andrubis_safe"
    n_proc = 2  # parallelism
    database = "/media/pret/Maxtor1/Andrubis/Andrubis_db20"  # database path
    testset = "/media/pret/Maxtor1/Andrubis/Andrubis_test_safe"  # test set path

    pathlib.Path(data_folder).mkdir(parents=True, exist_ok=True)
    start = time.time()
    parallel_initialize_database(database, data_folder, n_proc)
    print("Database generation: " + str(time.time() - start))
    first_run(testset, n_proc)
    print("Total time: " + str(time.time() - start))
