from os import name
from django.db import models
from django.db.models.deletion import CASCADE


# 복지로 엔티티
class Bokjiro(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    classification = models.CharField(max_length=15, default="", blank=True, null=False)
    title = models.CharField(max_length=200, default="", blank=True, null=False)
    contents = models.TextField(default="", blank=True, null=False)
    interest = models.CharField(max_length=100, default="", blank=True, null=False)
    family = models.CharField(max_length=100, default="", blank=True, null=False)
    lifecycle = models.CharField(max_length=50, default="", blank=True, null=False)
    age = models.CharField(max_length=20, default="", blank=True, null=False)
    address = models.CharField(max_length=100, default="", blank=True, null=False)
    phone = models.CharField(max_length=30, default="", blank=True, null=False)
    department = models.CharField(max_length=50, default="", blank=True, null=False)
    db_inserted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "bokjiro"


# 보건복지부 FAQ 엔티티
class MohwFaq(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    category = models.CharField(max_length=20, default="", blank=True, null=False)
    title = models.CharField(max_length=100, default="", blank=True, null=False)
    contents = models.TextField(default="", blank=True, null=False)
    createdDate = models.CharField(max_length=15, default="", blank=True, null=False)
    db_inserted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "mohw_faq"
