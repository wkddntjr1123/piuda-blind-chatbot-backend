from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from chatbot.views import *

# DRF는 url을 자동으로 매핑해주는 router를 제공
routers = routers.DefaultRouter()
routers.register("chatbot", WelfareViewSet)  # prefix = chatbot

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(routers.urls)),
    path("dftest/", dialogflowTest),  # dialogflow
    path("crolling/", crolling123GoKr),  # 보건복지상담센터 FAQ 크롤링 => DB저장
    path("allDataUpdate/", createAllWelfareData),  # 복지로 데이터 크롤링 => DB저장
    path("natural/", newNatural),  # 자연어 처리 벡터 => DB저장
    path("elastic/", elasticTest),
]
