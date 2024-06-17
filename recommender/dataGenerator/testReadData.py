import pandas as pd
cosine_path = "generated_similarities/no_longer_needed/cosine_simm_2.csv"


def read_data():
    data = pd.read_csv(cosine_path, index_col=0, header=None)
    print("First row")
    try:
        print(list(data.loc[100]))
    except IndexError:
        print("Movie not found")


def remove_duplicate_lines(infilename, outfilename):
    lines_seen = set()  # holds lines already seen
    outfile = open(outfilename, "w")
    for line in open(infilename, "r"):
        if line not in lines_seen:  # not a duplicate
            outfile.write(line)
            lines_seen.add(line)
    outfile.close()


if __name__ == "__main__":
    read_data()
