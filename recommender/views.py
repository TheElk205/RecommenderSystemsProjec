from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import loader

from recommender.models import Movie


def index(request):
    return HttpResponse("Please select a movie!")


def results(request, movie_id):
    template = loader.get_template('recommender/movie_info.html')

    movie = Movie.objects.get(id=movie_id)
    recommendations = list(Movie.objects.filter(tmdb_id__in=movie.recommendations['tmdb'][:5]))
    print(movie)
    print(movie.recommendations['tmdb'][:5])
    print(recommendations)
    context = {
        'movie': prepare_movie(movie),
        'recommendations': [prepare_movie(recom) for recom in recommendations]
    }

    return HttpResponse(template.render(context, request))

def prepare_movie(movie):
    return {
        'data': movie,
        'poster': "posters/{}.jpg".format(movie.id)
    }