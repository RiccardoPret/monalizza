import ast
from pyxdameraulevenshtein import damerau_levenshtein_distance


def read_fuzzies(path_file):
    dic = dict()
    lines = open(path_file, "r").read().splitlines()
    for l in lines:
        apk_path, fuzzies_list = ast.literal_eval(l)
        dic[apk_path] = fuzzies_list

    return dic


def compute_distances(file_path):
    hashes_dic = read_fuzzies("ris_androdump_safe/hashes.txt")
    hashes_dic_db = read_fuzzies("ris_androdump_safe/hashes_database.txt")

    with open(file_path, "w") as h_file:
        for apk_path, fuzzies_list in hashes_dic.items():
            for apk_path2, fuzzies_list2 in hashes_dic_db.items():
                sim_list = list()
                fam = apk_path.split("/")[-2]
                fam2 = apk_path2.split("/")[-2]
                if fam != fam2:
                    for fuzzy in fuzzies_list:
                        for fuzzy2 in fuzzies_list2:
                            #  Compute edit distance between two sub-fuzzies
                            dist = damerau_levenshtein_distance(fuzzy, fuzzy2)
                            if 0 < dist < 5:
                                sim_list.append((dist, (fuzzy, fuzzy2)))
                    # write down couple with delimiter
                    couple_str = fam + "/" + apk_path.split("/")[-1] + "@" + fam2 + "/" + apk_path2.split("/")[-1]
                    h_file.write(str((couple_str, sim_list))+"\n")


def read_false_negatives():
    fn = list()
    lines = open("ris_androdump/classifications.txt", "r").read().splitlines()
    for l in lines:
        mlw, status = ast.literal_eval(l)
        if status == "safe":
            fn.append(mlw.split("/")[-2]+"/"+mlw.split("/")[-1])
    return fn


def read_dist(distance_file):
    list_distances = list()
    lines = open(distance_file, "r").read().splitlines()
    for l in lines:
        bb = ast.literal_eval(l)
        list_distances.append(bb)
    return list_distances


def count_missed(couple_dist_list):
    similar_couples = list()

    for dist, similar_fuzzies_tuple in couple_dist_list:
        if len(similar_fuzzies_tuple[0]) > len(similar_fuzzies_tuple[1]):
            str_s = similar_fuzzies_tuple[1]
            str_l = similar_fuzzies_tuple[0]
        elif len(similar_fuzzies_tuple[0]) < len(similar_fuzzies_tuple[1]):
            str_s = similar_fuzzies_tuple[0]
            str_l = similar_fuzzies_tuple[1]
        else:
            continue  # strings have same len so the distance is due to characters transformations. Not a split problem

        if str_l[:-dist] == str_s or str_l[dist:] == str_s:
            similar_couples.append(similar_fuzzies_tuple)

    return similar_couples


def main():
    fn = read_false_negatives()
    list_dist = read_dist("distances_mlw.txt")
    testset = "/media/pret/Maxtor1/AndroDumpsys/AndroDumpsys_test_mlw/"
    fuzzies = read_fuzzies("ris_androdump/hashes.txt")

    for couple, couple_dist_list in list_dist:
        test_sample = couple.split("@")[0]
        if test_sample in fn and len(couple_dist_list) > 0:
            missed = count_missed(couple_dist_list)

            fuzzies_set_cardinality = len(fuzzies[testset+test_sample])
            print(test_sample+", "+str(len(missed))+"/"+str(fuzzies_set_cardinality)+", "+str(missed))


if __name__ == '__main__':
    #compute_distances("distances_safe.txt")
    main()
