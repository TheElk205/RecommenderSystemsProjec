from django.urls import path, include
from rest_framework import routers

from . import views

# router = routers.DefaultRouter()
# router.register(r'movies', views.MovieNamesViewSet, basename='movies')

urlpatterns = [
    # path("", views.index, name="index"),
    path('<int:movie_id>/', views.results, name='results'),
    # path('', include(router.urls)),
    path('movies/', views.MovieNamesViewSet.as_view(), name='movies'),
    path("select2/", include("django_select2.urls")),
    path("", views.MovieSelectView.as_view(), name="movie_select"),
]