import ast
import glob
import hashlib
import os

import matplotlib
import numpy as np
import matplotlib.pyplot as plt


def get_family(apk):
    return apk.split("/")[-2]


def mlw_stats(file_path):
    mlw_right_c = 0
    mlw_wrong_c = 0
    no_mlw = 0

    lines = open(file_path, "r").read().splitlines()
    for l in lines:
        apk, family = ast.literal_eval(l)
        if family == "safe":
            no_mlw += 1
        elif get_family(apk) == family:
            mlw_right_c += 1
        else:
            mlw_wrong_c += 1

    print("Right: " + str(mlw_right_c))
    print("Wrong family: " + str(mlw_wrong_c))
    print("Safe: " + str(no_mlw))


def get_families_with_total_samples(db):
    fams_tup_dict = dict()
    for f in glob.glob(db + "/*", recursive=True):
        if os.path.isdir(f):
            fam = f.split("/")[-1]
            fams_tup_dict[fam] = (0, len(os.listdir(f)))

    return fams_tup_dict


def update_with_classified(fams_tups_dict, classification_file):
    lines = open(classification_file, "r").read().splitlines()
    for l in lines:
        apk, fam = ast.literal_eval(l)
        if get_family(apk) == fam:
            fams_tups_dict[fam] = (fams_tups_dict[fam][0]+1, fams_tups_dict[fam][1])

    return fams_tups_dict


def retrieve_families_rate(db, data_folder):
    fams = list()
    detected = list()
    undetected = list()

    fams_tups_dict = get_families_with_total_samples(db)
    fams_tups_dict = update_with_classified(fams_tups_dict, data_folder+"/classifications.txt")
    list_tup_tup = sorted(fams_tups_dict.items(), key=lambda x: x[0])
    for fam, tup in list_tup_tup:
        if tup[0] > 0:
            fams.append(fam)
            detected.append(tup[0])
            undetected.append(tup[1]-tup[0])

    return fams, detected, undetected


def get_families_with_one_sample(full_dataset):
    dic = get_families_with_total_samples(full_dataset)
    fams = list()
    for fam, tup in dic.items():
        if tup[1] == 1:
            fams.append(fam)
    return fams


def plot_family_classifications(testset, data_folder):
    labels, detected, undetected = retrieve_families_rate(testset, data_folder)

    print(len(detected))
    print(len(undetected))

    ind = np.arange(len(detected))  # the x locations for the groups
    width = 0.7  # the width of the bars: can also be len(x) sequence

    p1 = plt.bar(ind, detected, width, edgecolor='black', hatch="//")
    p2 = plt.bar(ind, undetected, width, bottom=detected, color='orange', edgecolor='black')

    #plt.title('Test set variants distribution with at least one detection')
    plt.ylabel('Number of variants in the testset')
    plt.xticks(ind, labels, rotation='vertical')
    plt.yticks(np.arange(0, 36, 2))
    plt.legend((p1[0], p2[0]), ('Detected', 'Undetected'), loc='upper left')
    #plt.subplots_adjust(bottom=0.2)
    #for i, v in enumerate(detected):
    #    plt.text(i - .30, v + 1, str(v), color='blue')
    plt.tight_layout()
    plt.show()


def plot_zero_detections_families(testset, data_folder):
    fams = list()
    undetected = list()

    fams_tups_dict = get_families_with_total_samples(testset)
    fams_tups_dict = update_with_classified(fams_tups_dict, data_folder+"/classifications.txt")
    list_tup_tup = sorted(fams_tups_dict.items(), key=lambda x: x[0])
    for fam, tup in list_tup_tup:
        if tup[0] == 0:
            fams.append(fam)
            undetected.append(tup[1])

    x = np.arange(len(undetected))
    #plt.title('Variants distribution with 0 detections in the testset')
    plt.ylabel('Number of variants in the testset')
    plt.bar(x, undetected, color='orange')
    plt.xticks(x, fams, rotation='vertical')
    plt.yticks(np.arange(0, 26, 1))
    red_patch = matplotlib.patches.Patch(color='orange', label='Undetected')
    plt.legend(handles=[red_patch], loc='upper left')
    plt.tight_layout()
    plt.show()


def plot_misleading_families():
    misleading_fams = dict()
    lines = open("data/playstore/classifications.txt", "r").read().splitlines()[:100]
    for l in lines:
        apk, fam = ast.literal_eval(l)
        if fam != "safe":
            try:
                misleading_fams[fam] += 1
            except:
                misleading_fams[fam] = 1
    fams = list(misleading_fams.keys())
    freq = list(misleading_fams.values())

    x = np.arange(len(fams))
    #plt.title('Misleading families')
    plt.ylabel('Number of wrong classifications')
    plt.bar(x, freq)
    plt.xticks(x, fams, rotation='vertical')
    plt.yticks(np.arange(0, 12, 1))
    plt.tight_layout()
    plt.show()


def plot_database_families_with_detections():
    detected_fams, nul, nul = retrieve_families_rate("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Test", "data/2014-6_2")
    db_fams_totals = get_families_with_total_samples("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Data")

    variants_freq = list()
    for fam in detected_fams:
        variants_freq.append(db_fams_totals[fam][1])

    x = np.arange(len(variants_freq))
    #plt.title('Families distribution in the database with at least one detection')
    plt.ylabel('Number of variants in the database')
    plt.bar(x, variants_freq)
    plt.xticks(x, detected_fams, rotation='vertical')
    plt.yticks(np.arange(0, 51, 2))
    plt.tight_layout()
    plt.show()


def plot_database_families_without_detections():
    detected_fams, nul, nul = retrieve_families_rate("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Test", "data/2014-6_2")
    db_fams_totals = get_families_with_total_samples("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Data")
    one_sample_fams = get_families_with_one_sample("/home/pret/Uni/Tesi/Datasets/Mix/2014-6_2")
    test_fams = list(get_families_with_total_samples("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Test").keys())

    families = list()
    frequency = list()
    for family in sorted(db_fams_totals.keys(), key=lambda x: x):
        if family not in detected_fams \
                and family not in one_sample_fams\
                and family in test_fams:
            families.append(family)
            frequency.append(db_fams_totals[family][1])

    x = np.arange(len(families))
    #plt.title('Families distribution in the database without detections')
    plt.ylabel('Number of variants in the database')
    plt.bar(x, frequency)
    plt.xticks(x, families, rotation='vertical')
    plt.yticks(np.arange(0, 51, 2))
    plt.tight_layout()
    plt.show()


def get_years(groundtruth_file, misleading_hashes):
    good_samples = list()

    with open(groundtruth_file, "r") as r:
        lines = r.read().splitlines()
    for line in lines:
        line_parsed = ast.literal_eval(line)
        try:
            if line_parsed["sha256"] in misleading_hashes:
                date = line_parsed["first_seen"].split(" ")[0]
                print(date)
        except KeyError:
            print(line_parsed)

    return good_samples


def get_hashes(apks):
    def get_sha256(file_path):
        chunk_size = 8192
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if len(chunk):
                    h.update(chunk)
                else:
                    break

        return h.hexdigest()

    hashes = list()
    for f in apks:
        hashes.append(get_sha256(f))

    return hashes


def plot_year_misleading_malware():
    misleadings = dict()
    # Get misleading apks
    lines = open("data/playstore/classifications.txt", "r").read().splitlines()[:100]
    for l in lines:
        apk, fam = ast.literal_eval(l)
        if fam != "safe":
            misleadings[apk] = fam
    lines = open("data/playstore/samples_neighbors.txt", "r").read().splitlines()[:100]
    misleading_mlws = list()
    for l in lines:
        apk, neighbors = ast.literal_eval(l)
        for neighbor in neighbors:
            if get_family(neighbor) == misleadings[apk]:
                misleading_mlws.append(neighbor)
    # Get years
    misleading_hashes = get_hashes(misleading_mlws)
    print(len(misleading_hashes))
    get_years("/home/pret/Uni/Tesi/Scripts/groundtruth/2014-groundtruth_6_2.json", misleading_hashes)


def plot_function_detection_family(data_folder):
    fams_tups_dict = get_families_with_total_samples("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Test")
    fams_tups_dict = update_with_classified(fams_tups_dict, data_folder + "/classifications.txt")
    final_dict = dict()
    for f in glob.glob("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Data/*", recursive=True):
        if os.path.isdir(f):
            fam = f.split("/")[-1]
            if fam in fams_tups_dict.keys():  # Some families are not present in the testset
                det_rate = fams_tups_dict[fam][0]/fams_tups_dict[fam][1]
                final_dict[fam] = (det_rate, len(os.listdir(f)))

    sorted_by_dbtotal = sorted(final_dict.items(), key=lambda x: x[1][1])
    detected = list()
    db_total = list()
    for fam, tup in sorted_by_dbtotal:
        detected.append(tup[0])
        db_total.append(tup[1])

    plt.plot(db_total, detected, 'o')
    plt.yticks(np.arange(0, 1.01, 0.1))
    plt.xticks(np.arange(0, 51, 5))
    plt.xlabel('Number of variants in the database')
    plt.ylabel('Detection rate')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # plot_family_classifications("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Test", "data/2014-6_2")
    # plot_zero_detections_families("/home/pret/Uni/Tesi/Datasets/Dataset14-6_2/Test", "data/2014-6_2")
    plot_misleading_families()
