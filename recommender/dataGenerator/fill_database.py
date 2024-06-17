import json
import os
import psycopg2
import pandas as pd
from RecommenderSystemsFinalProject.settings import DATABASES

movie_files_path = "./movie_lense_data/extracted_content_ml-latest"
cosine_description_path = "generated_similarities/cosine_full_descriptions.csv"
cosine_jaccard_path = "generated_similarities/cosine_jaccard.csv"
jaccard_genres_path = "generated_similarities/jaccard_similarity_final_no_duplicates.csv"
jaccard_tags_path = "generated_similarities/tags_jaccard_similarity_final_no_duplicates.csv"
manhattan_path = "generated_similarities/manhattan2.csv"


def store_in_recommendations(recommendation, key, data, movielens_id, missing_metrics):
    try:
        data = list(data.loc[int(movielens_id)])
        recommendation[key] = data
    except KeyError:
        # print("No cosine similarities for movie: {}".format(movielens_id))
        missing_metrics[key].append(movielens_id)
        recommendation[key] = []


if __name__ == "__main__":
    print("Generating database")
    directory = os.fsencode(movie_files_path)
    cosine_description_data = pd.read_csv(cosine_description_path, index_col=0, header=None)
    cosine_jaccard_data = pd.read_csv(cosine_jaccard_path, index_col=0, header=None)
    jaccard_genres_data = pd.read_csv(jaccard_genres_path, index_col=0, header=None)
    jaccard_tags_data = pd.read_csv(jaccard_tags_path, index_col=0, header=None)
    manhattan_data = pd.read_csv(manhattan_path, index_col=0, header=None)
    conn = psycopg2.connect(user=DATABASES["default"]["USER"],
                     password=DATABASES["default"]["PASSWORD"],
                     host=DATABASES["default"]["HOST"],
                     port="5432",
                     database="movies_recommender")
    cur = conn.cursor()
    sql_values = []

    missing_metrics = {
        "manhattan": [],
        "jaccard_tags": [],
        "jaccard_genres": [],
        "cosine_jaccard": [],
        "cosine_descriptions": []
    }
    print("Analysing movies")
    analysed = 0
    for file in sorted(os.listdir(directory)):
        filename = os.fsdecode(file)
        if filename.endswith(".json"):
            analysed = analysed + 1
            # print(os.path.join(directory, filename))
            movie = {}
            with open(movie_files_path + "/" + filename) as f:
                movie = json.load(f)
            movielens_id = filename.split(".")[0]
            # print("Analysing id: {}".format(movielens_id))
            to_store = {
                'id': movielens_id,
                'tmdb_id': 'null',
                'title': None,
                'description': None,
                'date': "1970-01-01",
                'recommendations': {
                    'tmdb': []
                },
                'duration': 0,
                'mpaa': '-',
                'actors': [],
                'trailer_url': None,
                'ratings': {
                    "tmdb": 0,
                    "movielens": 0
                }
            }
            if "tmdb" in movie:
                to_store["title"] = movie["tmdb"]["original_title"].replace("'", "''")
                to_store["tmdb_id"] = movie["tmdb"]["id"]
                to_store["description"] = movie["tmdb"]["overview"]
                to_store["date"] = movie["tmdb"]["release_date"]
                to_store["recommendations"]["tmdb"] = movie["tmdb"]["recommendations"]
                to_store["ratings"]["tmdb"] = movie["tmdb"]["vote_average"]
                to_store["actors"] = json.dumps(movie["tmdb"]["credits"]["cast"]).replace("'", "''")
            if "movielens" in movie:
                to_store["title"] = movie["movielens"]["title"].replace("'", "''")
                to_store["description"] = movie["movielens"]["plotSummary"]
                to_store["date"] = movie["movielens"]["releaseDate"]
                to_store["recommendations"]["movielens"]: []
                to_store["actors"] = json.dumps(movie["movielens"]["actors"]).replace("'", "''")
                to_store["mpaa"] = movie["movielens"]["mpaa"]
                to_store["ratings"]["movielens"] = movie["movielens"]["avgRating"]
                to_store["duration"] = movie["movielens"]["runtime"]
                trailers = movie["movielens"]["youtubeTrailerIds"]
                if trailers is not None and len(trailers) > 0:
                    to_store["trailer_url"] = trailers[0]
                # Cosine
                store_in_recommendations(to_store["recommendations"], "manhattan", manhattan_data, movielens_id, missing_metrics)
                store_in_recommendations(to_store["recommendations"], "cosine_descriptions", cosine_description_data, movielens_id, missing_metrics)
                store_in_recommendations(to_store["recommendations"], "cosine_jaccard", cosine_jaccard_data, movielens_id, missing_metrics)
                store_in_recommendations(to_store["recommendations"], "jaccard_tags", jaccard_tags_data, movielens_id, missing_metrics)
                store_in_recommendations(to_store["recommendations"], "jaccard_genres", jaccard_genres_data, movielens_id, missing_metrics)
            else:
                print("not Adding movie: {}".format(id))
                continue
            # Clean up data, store to database
            if to_store["title"] is not None:
                to_store["title"] = to_store["title"].replace("'", "''")
            if to_store["description"] is not None:
                to_store["description"] = to_store["description"].replace("'", "''")
            if to_store["date"] == '' or to_store["date"] is None:
                to_store["date"] = '1970-01-01'
            if to_store["duration"] is None:
                to_store["duration"] = 0
            to_store["ratings"] = json.dumps(to_store["ratings"]).replace("'", "''")
            to_store["recommendations"] = json.dumps(to_store["recommendations"]).replace("'", "''")

            sql_values.append("""({}, {}, '{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', '{}')""".format(to_store["id"],
               to_store["tmdb_id"],
               to_store["title"],
               to_store["description"],
               to_store["date"],
               to_store["recommendations"],
               to_store["actors"],
               to_store["trailer_url"],
               to_store["duration"],
               to_store["mpaa"],
               to_store["ratings"],
               ))
        else:
            continue

    print("Movies analysed\n")
    print("Overall analysed: {}".format(analysed))
    print("Missing Metrics: \n")
    print("Cosine Description: {} ({}%)".format(len(missing_metrics["cosine_descriptions"]), len(missing_metrics["cosine_descriptions"])/analysed*100))
    print("Cosine Jaccard: {} ({}%)".format(len(missing_metrics["cosine_jaccard"]), len(missing_metrics["cosine_jaccard"])/analysed*100))
    print("Manhattan: {} ({}%)".format(len(missing_metrics["manhattan"]), len(missing_metrics["manhattan"])/analysed*100))
    print("Jaccard Tags: {} ({}%)".format(len(missing_metrics["jaccard_tags"]), len(missing_metrics["jaccard_tags"])/analysed*100))
    print("Jaccard Genres: {} ({}%)".format(len(missing_metrics["jaccard_genres"]), len(missing_metrics["jaccard_genres"])/analysed*100))

    print("\n Storing them to database now")
    sql_template = "INSERT INTO data.movie_infos (id, tmdb_id,  title, description, release_date, recommendations, actors, trailer_url, duration, mpaa, ratings) VALUES "
    sql_template += ", ".join(sql_values)

    cur.execute(sql_template)
    conn.commit()