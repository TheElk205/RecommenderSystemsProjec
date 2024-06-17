from django.db.models import Case, When
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

    jaccard_tags_movies = movie.recommendations['jaccard_tags'][:5]
    manhattan_movies = movie.recommendations['manhattan'][:5]
    jaccard_genres_movies = movie.recommendations['jaccard_genres'][:5]
    cosine_jaccard_movies = movie.recommendations['cosine_jaccard'][:5]
    cosine_descriptions_movies = movie.recommendations['cosine_descriptions'][:5]

    preserved_jaccard_tags = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(jaccard_tags_movies)])
    preserved_manhattan = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(manhattan_movies)])
    preserved_cosine_jaccard = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(cosine_jaccard_movies)])
    preserved_jaccard_genres = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(jaccard_genres_movies)])
    preserved_cosine_descriptions = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(cosine_descriptions_movies)])

    manhattan = list(Movie.objects.filter(id__in=manhattan_movies).order_by(preserved_manhattan))
    jaccard_tags = list(Movie.objects.filter(id__in=jaccard_tags_movies).order_by(preserved_jaccard_tags))
    jaccard_genres = list(Movie.objects.filter(id__in=jaccard_genres_movies).order_by(preserved_jaccard_genres))
    cosine_jaccard = list(Movie.objects.filter(id__in=cosine_jaccard_movies).order_by(preserved_cosine_jaccard))
    cosine_descriptions = list(Movie.objects.filter(id__in=cosine_descriptions_movies).order_by(preserved_cosine_descriptions))
    context = {
        'movie': prepare_movie(movie),
        'recommendations': {
            "manhattan": [prepare_movie(recom) for recom in manhattan],
            "jaccard_tags": [prepare_movie(recom) for recom in jaccard_tags],
            "jaccard_genres": [prepare_movie(recom) for recom in jaccard_genres],
            "cosine_jaccard": [prepare_movie(recom) for recom in cosine_jaccard],
            "cosine_descriptions": [prepare_movie(recom) for recom in cosine_descriptions],
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

