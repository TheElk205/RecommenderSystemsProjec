from zipfile import ZipFile

import pandas as pd
import polars as pl
import numpy as np
import csv
import heapq
from scipy import spatial
import os
from natsort import os_sorted
import json
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse

# ratings = pd.read_csv("../../../../../Downloads/assigment_final/ml-20m/ratings.csv")
# movies = pd.read_csv("../../../../../Downloads/assigment_final/ml-20m/movies.csv")
# tags = pd.read_csv("../../../../../Downloads/assigment_final/ml-20m/tags.csv")


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


def jaccard_similarity_genres(movie_id, genre_dict):
    """
    Calculate Jaccard Similarity for one movie in combination with all others taking genres into account.
    :param movie_id: the tmdb movie ID we want to generate jaccard similarity for
    :param genre_dict: dictionary containing genres for all movies
    :return: similarity dict with all calculated similarities. Key is other movieId
    """
    # try:
    given_movie_genres = set(genre_dict[movie_id])
    similarities = {}
    for other_movie_id, other_genres in genre_dict.items():
        other_movie_genres = set(other_genres)
        # Calculate Jaccard similarity
        if (len(given_movie_genres.intersection(other_movie_genres)) == 0):
            jaccard_sim = 0
        else:
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
    correlations = {}
    for key in genre_dict:
        correlations[key] = jaccard_similarity_genres(key, genre_dict)
    correlations_df = pd.DataFrame.from_dict(correlations, orient='index')
    correlations_df.fillna(0, inplace=True)
    return correlations_df


def manhattan_distance(list1, list2):
    """
    Calculates the manhatten distance between to lists of ratings
    :param list1: ratings movie 1
    :param list2: ratings movie 2
    :return: manhatten distance between the two lists
    """
    distance = 0
    for i in range(len(list1)):
        distance = + abs(list1[i] - list2[i])
    return distance


def generate_manhattan_sim(movie_user_matrix):
    """
    Iterates over all ratings, generates a dataframe containing all similarities; symmetric
    :param movie_user_matrix: movie user matrix as read from file
    :return:
    """
    print("Generating manhattan similarities for all movies")
    all_similarities = {}
    for row in movie_user_matrix.iterrows():
        row = list(row)
        first_cell = row[0]
        current_row = row[1:]

        similarities = {}
        for row_2 in movie_user_matrix.iterrows():
            row_2 = list(row_2)
            first_cell_compare = row_2[0]
            current_row_compare = row_2[1:]

            if first_cell == first_cell_compare:
                correlation = 1
            else:
                correlation = manhattan_distance(current_row, current_row_compare)

            similarities[first_cell_compare] = correlation
        all_similarities[first_cell] = similarities
    correlations_df = pd.DataFrame.from_dict(all_similarities, orient='index')
    correlations_df.fillna(0, inplace=True)
    return correlations_df


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


def list_files_by_creation_time(directory):
    """
    Get all file names in a directory, sorted ascending after their creating timestamp
    :param directory: directory where to look for files in
    :return: list of file names, sorted by creation time ascending
    """
    entries = os.scandir(directory)
    files = [(entry.name, entry.stat().st_ctime) for entry in entries if entry.is_file()]
    sorted_files = sorted(files, key=lambda x: x[1])
    return [file[0] for file in sorted_files]


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
    return pd.DataFrame(similarities, columns=pivot_data.columns[1:], index=pivot_data.columns[1:])


def read_user_ratings_matrix():
    print("Reading user ratings matrix")
    user_ratings = pl.read_csv(
        ZipFile("./movie_lense_data/ratings_pivot_full.csv.zip").open("ratings_pivot_full.csv").read()
    )
    user_ratings_filled = user_ratings.cast(pl.Float64).fill_null(0)
    return user_ratings_filled.transpose().to_pandas()


# directory_path = 'C:/Users/mikol/OneDrive/Dokumenty/erasmus_uni/recomendation/assigment_final/jsons'
# file_list = list_files_by_creation_time(directory_path)
# sorted_files = os_sorted(file_list)
# movie_description_dict = movie_description_list(sorted_files)
# list_of_descriptions = list(movie_description_dict.values())
# cos_matrix = cosine_similarity_matrix_descriptions(list_of_descriptions)
# print(cos_matrix)

if __name__ == "__main__":
    user_rating_matrix = read_user_ratings_matrix()
    print("Finished reading user ratings matrix")
    manhattan = generate_manhattan_sim(user_rating_matrix)
    store_topn_to_file(manhattan, 10, "manhattan.csv")


