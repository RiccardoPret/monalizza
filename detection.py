import ast
import os
from collections import defaultdict

THRESHOLD1 = 0.15
THRESHOLD2 = 0.5
FRACTION = 10  # If there are more than 1/FRACTION of the total variants, use thr1 for that family for that app


def get_family(apk):
    return apk.split("/")[-2]


def get_custom_fam_threshold(neighbors_fam_freq, db_fams_freq):
    fams_threshold = dict()
    for fam, freq in neighbors_fam_freq.items():
        if db_fams_freq[fam] >= 10:
            if freq >= db_fams_freq[fam]/FRACTION:
                fams_threshold[fam] = THRESHOLD1
            else:
                fams_threshold[fam] = THRESHOLD2
        else:
            fams_threshold[fam] = THRESHOLD2
    return fams_threshold


def read_db_fams_freq(file_path):
    with open(file_path, "r") as db_f:
        ff = ast.literal_eval(db_f.read().splitlines()[0])
    return ff


def get_fams_freq_neighbors(neighbors):
    neighbors_fam_freq = dict()
    for n in neighbors.keys():
        try:
            neighbors_fam_freq[get_family(n)] += 1
        except:
            neighbors_fam_freq[get_family(n)] = 1
    return neighbors_fam_freq


def filter_phase(stats_dict):
    filtered_detections = defaultdict(dict)
    db_fams_freq = read_db_fams_freq("families_frequency.txt")
    no_malware = list()

    for apk, neighbors in stats_dict.items():
        if len(neighbors) > 0:
            neighbors_fams_freq = get_fams_freq_neighbors(neighbors)
            fams_thr = get_custom_fam_threshold(neighbors_fams_freq, db_fams_freq)
            for neighbor, jaccard in neighbors.items():
                fam = get_family(neighbor)
                if jaccard > fams_thr[fam]:
                    filtered_detections[apk][neighbor] = jaccard

        if len(filtered_detections[apk]) == 0:
            no_malware.append(apk)

    return filtered_detections, no_malware


def print_neighbors(apk, neighbors, file_name):
    with open(file_name, "a") as nf:
        tup = (apk, list(neighbors))
        nf.write(str(tup)+"\n")


def compute_sample_family(apk, neighbors, neighbors_file_name):
    top_neighbors = sorted(neighbors.items(), key=lambda x: -x[1])[:5]
    print_neighbors(apk, [apk for apk, j in top_neighbors], neighbors_file_name)
    fams = dict()
    for n, jaccard in top_neighbors:
        try:
            fams[get_family(n)] += 1*jaccard
        except:
            fams[get_family(n)] = jaccard
    fams_tup = sorted(fams.items(), key=lambda x: -x[1])
    return fams_tup[0][0]


def detection_mlw(apk_neighbors_list, data_folder):
    classifications = dict()
    neighbors_file_name = data_folder+"/samples_neighbors.txt"
    if os.path.exists(neighbors_file_name):
        os.remove(neighbors_file_name)

    filtered_samples, no_malware = filter_phase(apk_neighbors_list)
    for apk, apk_neighbors in filtered_samples.items():
        if len(apk_neighbors) != 0:
            classifications[apk] = compute_sample_family(apk, apk_neighbors, neighbors_file_name)

    with open(data_folder+"/classifications.txt", "w") as class_file:
        for apk, family in classifications.items():
            tup = (apk, family)
            class_file.write(str(tup)+"\n")
        for apk in no_malware:
            tup = (apk, "safe")
            class_file.write(str(tup)+"\n")

    return classifications
