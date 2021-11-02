from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from chatbot.views import WelfareViewSet, beautifulsoupTest, dialogflowTest

# DRF는 url을 자동으로 매핑해주는 router를 제공
routers = routers.DefaultRouter()
routers.register("chatbot", WelfareViewSet)  # prefix = chatbot

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(routers.urls)),
    path("bstest/", beautifulsoupTest),
    path("dftest/", dialogflowTest),
]
