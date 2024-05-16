from django.db import models

# Create your models here.
from django.db import models


class Movie(models.Model):
    id = models.IntegerField(primary_key=True)
    tmdb_id = models.IntegerField()
    duration = models.IntegerField()
    mpaa = models.TextField()
    title = models.TextField()
    description = models.TextField()
    release_date = models.DateField()
    trailer_url = models.TextField()
    recommendations = models.JSONField()
    ratings = models.JSONField()

    class Meta:
        db_table = 'movie_infos'

    def __str__(self):
        return "id: {}, title: {}".format(self.id, self.title)