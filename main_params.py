import ast
import glob
import os
from collections import defaultdict

from detection import detection_mlw
from stats import mlw_stats


def read_jaccards(file_path):
    detections = defaultdict(dict)
    lines = list()

    for f in glob.glob(file_path + "/*", recursive=True):
        if os.path.isdir(f):
            lines.extend(open(f+"/jaccard_scores.txt", "r").read().splitlines())

    for line in lines:
        apk, apk_neighbors_with_jaccard = ast.literal_eval(line)
        detections[apk] = apk_neighbors_with_jaccard

    return detections


def generate_families_freq(db_folder):
    db_freq = dict()

    for f in glob.glob(db_folder + "/*", recursive=True):
        if os.path.isdir(f):
            db_freq[f.split("/")[-1]] = len(os.listdir(f))

    open("families_frequency.txt", "w").write(str(db_freq))


def detect():
    #db_samples = "/media/pret/Maxtor1/Andrubis/Andrubis_db20"
    #db_samples = "/media/pret/Maxtor1/AndroDumpsys/AndroDumpsys_db"
    #db_samples = "/media/pret/Maxtor1/AndroTracker/AndroTracker_db"
    db_samples = "/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Database"

    results_folder = "personal"

    generate_families_freq(db_samples)
    detections = read_jaccards(results_folder)

    detection_mlw(detections, ".")
    mlw_stats("." + "/classifications.txt")


def longest_common_substring(string1, string2):
    from difflib import SequenceMatcher

    match = SequenceMatcher(None, string1, string2).find_longest_match(0, len(string1), 0, len(string2))

    print(match)  # -> Match(a=0, b=15, size=9)
    print(string1[match.a: match.a + match.size])  # -> apple pie
    print(string2[match.b: match.b + match.size])  # -> apple pie

if __name__ == '__main__':
    #detect()
    longest_common_substring("apple pie available", "come have some apple pies")
