from django.urls import path
from chatbot.views import *
from crolling.views import *

urlpatterns = [
    #### chatbot ####
    path("chatting/", chatWithServer),  # 엔드포인트 : 안드로이드 <-> 백엔드 <-> dialogflow서버
    path("paged-list/", pagedBokjiroList),  # paging된 복지로 리스트 반환
    path("bokjiro/<id>/", bokjoroDetail),  # 복지로 아이템 상세보기
    #### crolling ####
    path("crolling/mohw/all/", crollingAllMohw),  # 보건복지상담센터 FAQ 크롤링 => DB저장
    path("crolling/bokjiro/all/", crollingAllBokjiro),  # 복지로 데이터 크롤링 => DB저장
]
