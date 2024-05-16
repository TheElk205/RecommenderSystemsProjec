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
    tmdb_recommendations = list(Movie.objects.filter(tmdb_id__in=movie.recommendations['tmdb'][:5]))
    context = {
        'movie': prepare_movie(movie),
        'recommendations': {
            "tmdb": [prepare_movie(recom) for recom in tmdb_recommendations]
        }
    }

    return HttpResponse(template.render(context, request))

def prepare_movie(movie):
    return {
        'data': movie,
        'poster': "posters/{}.jpg".format(movie.id)
    }