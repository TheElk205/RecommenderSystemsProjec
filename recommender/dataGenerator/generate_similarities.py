from zipfile import ZipFile

import pandas as pd
import polars as pl
import numpy as np
import csv
import heapq
from scipy import spatial
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import manhattan_distances
from scipy import sparse

import os
import json


def create_tag_dict(tags_df):
    """
        Extracts the tag as a single dictionaries form all given movies
        :param tags_df: movie dataframe, as read from dataset
        :return: dictionary where key is TMDB movie Id and value are tags as an array of strings
        """
    movie_tags_dict = {}
    for index, row in tags_df.iterrows():
        movie_id = row['movieId']
        tag = row['tag']

        if movie_id in movie_tags_dict:
            movie_tags_dict[movie_id].append(tag)
        else:
            movie_tags_dict[movie_id] = [tag]
    return movie_tags_dict


def list_files_by_creation_time(directory):
    """
    Get all file names in a directory, sorted ascending after their creating timestamp
    :param directory: directory where to look for files in
    :return: list of file names, sorted by creation time ascending
    """
    entries = os.scandir(directory)
    files = [(entry.name, entry.stat().st_ctime) for entry in entries if entry.is_file()]
    sorted_files = sorted(files, key=lambda x: x[1])
    return [int(file[0].split(".")[0]) for file in sorted_files]


def get_tags_from_files(ids, folder):
    tags = {}
    for id in ids:
        with open("{}/{}.json".format(folder, id), 'r', encoding="cp437") as file:
            data = json.load(file)

            keywords = data.get('tmdb', {}).get('keywords', [])
            if len(keywords) == 0:
                continue
            tags[id] = []
            for keyword in keywords:
                tags[id].append(keyword["name"])
    return tags


def get_all_possible_tags(tags_df, folder):
    ids = list_movieids_by_creation_time(folder)
    tags_dict = create_tag_dict(tags_df)
    missing_tags = list(set(ids) - set(tags_dict.keys()))
    missed = get_tags_from_files(missing_tags, folder)
    return {**tags_dict, **missed}


def create_genre_dict(movies_df):
    """
    Extracts the genres as a single dictionaries form all given movies
    :param movies_df: movie dataframe, as read from dataset
    :return: dictionary where key is TMDB movie Id and value are genres as an array of strings
    """
    genre_dict = {}
    for _, row in movies_df.iterrows():
        movie_id = row['movieId']
        genres = row['genres'].split('|')
        genre_dict[movie_id] = genres
    return genre_dict


def get_genres_from_files(ids, folder):
    missing = {}
    for id in ids:
        with open("{}/{}.json".format(folder, id), 'r', encoding="cp437") as file:
            data = json.load(file)

            genres = data.get('tmdb', {}).get('genres', [])
            if genres and len(genres) > 0:
                missing[id] = []
                for genre in genres:
                    missing[id].append(genre["name"])
            else:
                genres = data.get('imdb', {}).get('genres', [])
                if genres and len(genres) > 0:
                    missing[id] = genres

    return missing


def list_movieids_by_creation_time(directory):
    """
    Get all movie ids in a directory, sorted ascending after their creating timestamp
    :param directory: directory where to look for files in
    :return: list of file names, sorted by creation time ascending
    """
    entries = os.scandir(directory)
    files = [(entry.name, entry.stat().st_ctime) for entry in entries if entry.is_file()]
    sorted_files = sorted(files, key=lambda x: x[1])
    return [int(file[0].split(".")[0]) for file in sorted_files]


def get_all_possible_genres(movies_df, folder):
    ids = list_movieids_by_creation_time(folder)
    genres_dict = create_genre_dict(movies_df)
    missing_genres = list(set(ids) - set(genres_dict.keys()))
    missed = get_genres_from_files(missing_genres, folder)
    return {**genres_dict, **missed}


def cosine_to_csv(movie_user_matrix, filename):
    for row in movie_user_matrix.iter_rows():
        row = list(row)
        first_cell = row[0]
        current_row = row[1:]

        similarities = {}
        for row_2 in movie_user_matrix.iter_rows():
            first_cell_compare = row_2[0]
            current_row_compare = row_2[1:]

            if first_cell == first_cell_compare:
                correlation = 1
            else:
                correlation = 1 - spatial.distance.cosine(current_row, current_row_compare)

            similarities[first_cell_compare] = correlation

        top_similariteis = heapq.nsmallest(10, similarities, key=similarities.get)

        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)

            row = [first_cell] + top_similariteis
            writer.writerow(row)


def jaccard_similarity_genres(movie_id, dict_to_evaluate):
    """
    Calculate Jaccard Similarity for one movie in combination with all others taking genres into account.
    :param movie_id: the tmdb movie ID we want to generate jaccard similarity for
    :param dict_to_evaluate: dictionary containing genres for all movies
    :return: similarity dict with all calculated similarities. Key is other movieId
    """
    # try:
    given_movie_genres = set(dict_to_evaluate[movie_id])
    similarities = {}
    for other_movie_id, other_genres in dict_to_evaluate.items():
        other_movie_genres = set(other_genres)
        # Calculate Jaccard similarity
        if len(given_movie_genres.intersection(other_movie_genres)) != 0:
            jaccard_sim = len(given_movie_genres.intersection(other_movie_genres)) / len(
                given_movie_genres.union(other_movie_genres))
            similarities[other_movie_id] = jaccard_sim
    return similarities


def generate_jaccard_sim(genre_dict):
    """
    Iterate over all movies and create one big dataframe containing all similarities; creates symmetric matrix
    :param genre_dict: The extracted genres as a dictionary
    :return: dataframe containing all similarities
    """

    manhattan_distances
    correlations = {}
    for key in genre_dict:
        correlations[key] = jaccard_similarity_genres(key, genre_dict)
    correlations_df = pd.DataFrame.from_dict(correlations, orient='index')
    correlations_df.fillna(0, inplace=True)
    return correlations_df


def generate_manhattan_sim(pivot_data):
    """
    Iterates over all ratings, generates a dataframe containing all similarities; symmetric
    :param movie_user_matrix: movie user matrix as read from file
    :return:
    """
    user_ratings_filled_sparse = sparse.csr_matrix(pivot_data.iloc[1:])
    similarities = manhattan_distances(user_ratings_filled_sparse)
    return pd.DataFrame(similarities, columns=pivot_data.index[1:], index=pivot_data.index[1:])


def store_topn_to_file(sim, n=10, file="cosine_full.csv"):
    """
    Takes in a dataframe and sorts the entries ascending. Then stores the columns of the top n together with the current row index.
    This way we have the top n matching movies for whatever similarity in a file
    :param sim: Data frame to sort and evaluate
    :param n: How many hits we want to save
    :param file: filename to store data in
    :return: None
    """
    data = []

    for i in sim.index.values:
        data.append(sim.loc[i].sort_values(ascending=False)[:(n + 1)].index.values)

    with open(file, "wb") as myfile:
        np.savetxt(myfile, data, fmt="%s", delimiter=',', newline='\n')


def get_summaries_from_json(file_path):
    """
    Get summary from movie under key tmdb
    :param file_path: file path of the movie data
    :return: tmdb summaries of the movie
    """
    with open(file_path, 'r', encoding="cp437") as file:
        data = json.load(file)

        summaries = data.get('tmdb', {}).get('overview', None)
        if summaries is None:
            return "None"
        else:
            return summaries


def movie_description_list(sorted_files):
    """
    Get all summaries fo all movies
    :param sorted_files: movie files to analyse
    :return:
    """
    movie_description_dict = {}
    for movie in sorted_files:
        summaries = get_summaries_from_json('jsons/' + movie)
        try:
            movie_id = int(movie[:-5])
            movie_description_dict[movie_id] = summaries
        except:
            pass
    return movie_description_dict


def cosine_similarity_matrix_descriptions(list_of_descriptions):
    """
    Take the list of descriptions and calculate their cosine similarities. We are takign common english words out of the calculation.

    :param list_of_descriptions:
    :return:
    """
    vectorizer = CountVectorizer(stop_words="english")
    X = vectorizer.fit_transform(list_of_descriptions)
    arr = X.toarray()
    cos_sim = cosine_similarity(arr)
    return cos_sim


def generate_cosine_sim(pivot_data):
    user_ratings_filled_sparse = sparse.csr_matrix(pivot_data.iloc[1:])
    similarities = cosine_similarity(user_ratings_filled_sparse)
    return pd.DataFrame(similarities, columns=pivot_data.index[1:], index=pivot_data.index[1:])


def read_user_ratings_matrix():
    print("Reading user ratings matrix")
    user_ratings = pl.read_csv(
        ZipFile("./movie_lense_data/ratings_pivot_full.csv.zip").open("ratings_pivot_full.csv").read()
    )
    user_ratings_filled = user_ratings.cast(pl.Float64).fill_null(0)
    return user_ratings_filled.transpose().to_pandas()


def generate_translation_dict_tmdb_movielens(folder_path):
    translation_dictionary = {}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                tmdb_id = data.get('tmdb', {}).get('id', None)
                movielensId = data.get('movielensId')
                translation_dictionary[tmdb_id] = movielensId
    return translation_dictionary


def get_tmdb_recomendations(file_path):
    try:
        with open(file_path, 'r', encoding="cp437") as file:
            data = json.load(file)

            summaries = data.get('tmdb', {}).get('recommendations', None)
            if summaries is None:
                return "None"
            else:
                return summaries
    except:
        return []


def create_tmbd_list(file_path):
    first20 = get_tmdb_recomendations(file_path)
    tmdb_hopped_recomendations = first20
    for i in first20:
        file_path = os.path.join('./content_ml-latest/extracted_content_ml-latest/', str(i) + '.json')
        if os.path.isfile(file_path):
            another20 = get_tmdb_recomendations('./content_ml-latest/extracted_content_ml-latest/' + str(i) + '.json')
            try:
                tmdb_hopped_recomendations = tmdb_hopped_recomendations + another20
            except:
                pass
    return tmdb_hopped_recomendations


def count_elements_in_list(list1, list2):
    set2 = set(list2)

    count = sum(1 for element in list1 if element in set2)

    return count


def evaluation(row_from_csv, dictionary):
    recomendations_tmdb_translated = [dictionary.get(item, item) for item in row_from_csv]

    result = count_elements_in_list(recomendations_tmdb_translated, row_from_csv)
    return result


if __name__ == "__main__":
    user_rating_matrix = read_user_ratings_matrix()
    print("Finished reading user ratings matrix")
    manhattan = generate_manhattan_sim(user_rating_matrix)
    store_topn_to_file(manhattan, 10, "manhattan.csv")


