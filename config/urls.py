from django.conf.urls import include
from django.urls import path
from chatbot.views import *


urlpatterns = [
    path("dftest/", chatWithServer),  # 엔드포인트 : 안드로이드 <-> 백엔드 <-> dialogflow서버
    path("crolling-all-data-mohw/", crollingAllMohwFaq),  # 보건복지상담센터 FAQ 크롤링 => DB저장
    path("crolling-all-data-bokjiro/", crollingAllBokjiro),  # 복지로 데이터 크롤링 => DB저장
]
