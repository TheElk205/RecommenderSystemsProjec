from django import forms
from django.template import loader
from django_select2 import forms as s2forms

from . import models


class MoviesWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "title__icontains",
    ]
    model = models.Movie


# class MovieSelectForm(forms.ModelForm):
class MovieSelectForm(forms.ModelForm):
    class Meta:
        model = models.Movie
        fields = ('title',)
        widgets = {
            'title': MoviesWidget,
        }
