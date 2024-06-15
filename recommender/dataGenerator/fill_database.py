import json
import os
import psycopg2
import pandas as pd
from RecommenderSystemsFinalProject.settings import DATABASES

movie_files_path = "./extracted_content_ml-latest"
cosine_path = "./cosine_jaccard.csv"
# cosine_path = "./cosine_full.csv"
cosine_reduced_path = "./cosine_full.csv"
jaccard_path = "./jaccard_similarity.csv"
jaccard_tags_path = "./tags_jaccard_similarity_final_no_duplicates.csv"
movies_path = "./movies.csv"


def filter_recommendations(movie, data):
    translation = {"G": 1, "M": 2, "R": 3, "X": 4}
    recommendations_new = []
    for element in data:
        element_file_name = (str(element)+".json")
        if "movielens" in element_file_name and translation[movie["movielens"]["mpaa"]] <= translation[element_file_name["movielens"]["mpaa"]]:
            recommendations_new.append(element)
    
    return recommendations_new


if __name__ == "__main__":
    print("Generating database")
    directory = os.fsencode(movie_files_path)
    cosine_data = pd.read_csv(cosine_path, index_col=0, header=None)
    cosine_reduced_data = pd.read_csv(cosine_reduced_path, index_col=0, header=None)
    jaccard_data = pd.read_csv(jaccard_path, index_col=0, header=None)
    jaccard_tags_data = pd.read_csv(jaccard_tags_path, index_col=0, header=None)

    conn = psycopg2.connect(user=DATABASES["default"]["USER"],
                     password=DATABASES["default"]["PASSWORD"],
                     host=DATABASES["default"]["HOST"],
                     port="5432",
                     database="movies_recommender")
    cur = conn.cursor()
    for file in sorted(os.listdir(directory)):
        filename = os.fsdecode(file)
        if filename.endswith(".json"):
            # print(os.path.join(directory, filename))
            movie = {}
            with open(movie_files_path + "/" + filename) as f:
                movie = json.load(f)
            movielens_id = filename.split(".")[0]
            print("Analysing id: {}".format(movielens_id))
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
                try:
                    data = list(cosine_data.loc[int(movielens_id)])
                    data = filter_recommendations(movie, data)
                    to_store["recommendations"]["cosine"] = data
                except KeyError:
                    print("No cosine similarities for movie: {}".format(movielens_id))
                    to_store["recommendations"]["cosine"] = []
                try:
                    data = list(cosine_reduced_data.loc[int(movielens_id)])
                    data = filter_recommendations(movie, data)
                    to_store["recommendations"]["cosine_reduced"] = data
                except KeyError:
                    print("No reduced cosine similarities for movie: {}".format(movielens_id))
                    to_store["recommendations"]["cosine_reduced"] = []
                # Jaccard
                try:
                    data = list(jaccard_data.loc[int(movielens_id)])
                    data = filter_recommendations(movie, data)
                    to_store["recommendations"]["jaccard"] = data
                except KeyError:
                    print("No jaccard similarities for movie: {}".format(movielens_id))
                    to_store["recommendations"]["jaccard"] = []
                try:
                    data = list(jaccard_tags_data.loc[int(movielens_id)])
                    data = filter_recommendations(movie, data)
                    to_store["recommendations"]["jaccard_tag"] = data
                except KeyError:
                    print("No jaccard_tag similarities for movie: {}".format(movielens_id))
                    to_store["recommendations"]["jaccard_tag"] = []
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

            sql_template = '''
                            INSERT INTO data.movie_infos (id, tmdb_id,  title, description, release_date, recommendations, actors, trailer_url, duration, mpaa, ratings) 
                            VALUES ({}, {}, '{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', '{}')
                            '''.format(to_store["id"],
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
                                       )

            cur.execute(sql_template)
        else:
            continue
        conn.commit()