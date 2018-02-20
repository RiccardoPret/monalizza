from collections import defaultdict


def jaccard_similarity(x, y):
    set1 = set(x)
    set2 = set(y)

    intersection = len(set1.intersection(set2))
    return float(intersection) / (len(set1) + len(set2) - intersection)

#@profile
def compute_jaccard(database_fuzzy, test_fuzzy, file_name):
    detections = defaultdict(dict)  # apk: {db_mlw: jaccard}

    for apk_to_classify, apk_hash_list in test_fuzzy.items():
        apk_detections = dict()
        for malware, mlw_hash_list in database_fuzzy.items():
            j = jaccard_similarity(apk_hash_list, mlw_hash_list)
            if j > 0:
                apk_detections[malware] = j
        detections[apk_to_classify] = apk_detections

    with open(file_name, "w") as stats:
        for apk1, detection_dict in detections.items():
            tup = (apk1, detection_dict)
            stats.write(str(tup)+"\n")

    return detections
