from os import name
from django.db import models
from django.db.models.deletion import CASCADE


class Classification(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)


class Welfare(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=100, default="", blank=True, null=False)
    content = models.CharField(max_length=100, default="", blank=True, null=False)
    interest = models.CharField(max_length=50, default="", blank=True, null=False)
    family = models.CharField(max_length=50, default="", blank=True, null=False)
    lifecycle = models.CharField(max_length=50, default="", blank=True, null=False)
    age = models.CharField(max_length=20, default="", blank=True, null=False)
    address = models.CharField(max_length=100, default="", blank=True, null=False)
    phone = models.CharField(max_length=30, default="", blank=True, null=False)
    department = models.CharField(max_length=50, default="", blank=True, null=False)
    classification = models.ForeignKey("classification", on_delete=CASCADE)

    def __str__(self):
        return self.title


class MinistryHealthWelfare(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=20, default="", blank=True, null=False)
    title = models.CharField(max_length=100, default="", blank=True, null=False)
    contents = models.TextField(default="", blank=True, null=False)
    createdDate = models.CharField(max_length=15, default="", blank=True, null=False)
