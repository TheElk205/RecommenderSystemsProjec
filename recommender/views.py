from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views import generic

from recommender import models, forms
from recommender.Serializers import MovieSerializer
from recommender.models import Movie
from rest_framework import viewsets, generics


def index(request):
    return HttpResponse("Please select a movie!")


def results(request, movie_id):
    template = loader.get_template('recommender/movie_info.html')

    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        context = {}
        return HttpResponse(template.render(context, request))

    tmdb_recommendations = list(Movie.objects.filter(tmdb_id__in=movie.recommendations['tmdb'][:5]))
    cosine_recommendations = list(Movie.objects.filter(id__in=movie.recommendations['cosine'][:5]))
    cosine_reduced_recommendations = list(Movie.objects.filter(id__in=movie.recommendations['cosine_reduced'][:5]))
    jaccard_recommendations = list(Movie.objects.filter(id__in=movie.recommendations['jaccard'][:5]))
    jaccard_tag_recommendations = list(Movie.objects.filter(id__in=movie.recommendations['jaccard_tag'][:5]))
    print(cosine_recommendations)
    context = {
        'movie': prepare_movie(movie),
        'recommendations': {
            "tmdb": [prepare_movie(recom) for recom in tmdb_recommendations],
            "cosine": [prepare_movie(recom) for recom in cosine_recommendations],
            "cosine_reduced": [prepare_movie(recom) for recom in cosine_reduced_recommendations],
            "jaccard": [prepare_movie(recom) for recom in jaccard_recommendations],
            "jaccard_tag": [prepare_movie(recom) for recom in jaccard_tag_recommendations],
        }
    }

    return HttpResponse(template.render(context, request))


def prepare_movie(movie):
    return {
        'data': movie,
        'poster': "posters/{}.jpg".format(movie.id)
    }


class MovieNamesViewSet(generics.ListAPIView):
    """
    API endpoint that allows to query movies
    """

    serializer_class = MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all().order_by('-title')
        title = self.request.query_params.get('title')
        if title is not None and queryset is not None:
            queryset = queryset.filter(title__icontains=title)
        return queryset


class MovieSelectView(generic.FormView):
    model = models.Movie
    form_class = forms.MovieSelectForm
    success_url = "/test"

    template_name = "recommender/movie_form.html"

    def form_valid(self, form):
        print("Got form: ")
        print(form.data["title"])
        url = "{}".format(form.data["title"])
        print("URL to return: {}".format(url))
        return HttpResponseRedirect(url)

    def get_success_url(self):
        print("Success URL")
        print(self.title)
        if 'id' in self.kwargs:
            return "/{}".format(self.kwargs['id'])
        return "/"

