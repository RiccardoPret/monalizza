import ast


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
