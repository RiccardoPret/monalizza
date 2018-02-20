import ast
import os
import time
from collections import defaultdict

import pathlib

from compute_jaccard import compute_jaccard
from detection import detection_mlw
from fuzzy_hashes import initialize_database, generate_fuzzy_hashes
from stats import mlw_stats


def read_hashes_file(path):
    #return ast.literal_eval(open(path, "r").read().splitlines()[0])
    ssdeep_hashes = defaultdict(list)

    lines = open(path, "r").read().splitlines()
    for l in lines:
        tup = ast.literal_eval(l)
        ssdeep_hashes[tup[0]] = tup[1]

    return ssdeep_hashes


def read_jaccard_scores(file_path):
    detections = defaultdict(dict)

    lines = open(file_path, "r").read().splitlines()

    for line in lines:
        apk, apk_neighbors_with_jaccard = ast.literal_eval(line)
        detections[apk] = apk_neighbors_with_jaccard

    return detections


def run_detection(data_folder, test_samples=None):
    pathlib.Path(data_folder).mkdir(parents=True, exist_ok=True)
    jaccard_file_avail = os.path.exists(data_folder + "/jaccard_scores.txt")
    test_hashes_file_avail = os.path.exists(data_folder + "/hashes.txt")

    if test_hashes_file_avail:
        if jaccard_file_avail:
            detections = read_jaccard_scores(data_folder+"/jaccard_scores.txt")
        else:
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

if __name__ == '__main__':
    data_folder = "malgenome"
    database = "/home/pret/Uni/Tesi/Datasets/Others/Malgenome"
    testset = "/home/pret/Uni/Tesi/Datasets/Others/MalgenomeObf"

    # init_db()
    run_detection(data_folder, testset)
