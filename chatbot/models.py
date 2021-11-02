from django.db import models


class Welfare(models.Model):
    title = models.CharField(max_length=50)
    genre = models.CharField(max_length=50)
    year = models.IntegerField()

    def __str__(self):
        return self.title
