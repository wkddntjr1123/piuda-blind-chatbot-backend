from rest_framework import viewsets
from config.settings import BASE_DIR
from .serializers import WelfareSerializer
from .models import Classification, Welfare
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
from bs4 import BeautifulSoup as bs
from google.cloud import dialogflow
from google.protobuf.json_format import MessageToDict
import json, os
from time import sleep, time

# viewset으로 CRUD 자동 구현
class WelfareViewSet(viewsets.ModelViewSet):
    queryset = Welfare.objects.all()
    serializer_class = WelfareSerializer


# beautifulsoup 테스트
def beautifulsoupTest(request):
    # requirement : requests 패키지 (기본 내장인 urllib보다 깔끔한 듯), beautifulsoap4 패키지
    url = "https://tcrosa.ichaward.org/gunsan/"

    response = requests.get(url)

    if response.status_code == 200:
        html = response.text
        soup = bs(html, "html.parser")
    else:
        print(response.status_code)

    crollingData = soup.select_one(".grade-modal > div > .modal-content").text

    return JsonResponse({"crolling data": crollingData})


# dialogflow client 코드
# HTTP Body : JSON => {"texts":["text1","text2"]}
def detect_intent_texts(project_id, location_id, session_id, text, language_code):

    # 동일한 세션ID로 통신을 하면 지속적인 대화가 가능하다. (약 20분 유지)
    # 따라서 동일한 세션ID를 여러 사용자가 사용X
    session_client = dialogflow.SessionsClient(
        client_options={"api_endpoint": f"{location_id}-dialogflow.googleapis.com"}
    )
    session = f"projects/{project_id}/locations/{location_id}/agent/sessions/{session_id}"
    print(f"Session path: {session}")

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


# dialogflow 테스트
# 환경변수 GOOGLE_APPLICATION_CREDENTIALS 등록하면 Cloud SDK가 알아서 사용자 계정으로 인증처리 하는 거 같음
@csrf_exempt
def dialogflowTest(request):

    SESSION_ID = json.loads(request.body)["sessionId"]
    inputText = json.loads(request.body)["texts"]

    credentials = os.path.join(BASE_DIR, "credentials.json")
    # GOOGLE_APPLICATION_CREDENTIALS 환경변수 등록
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials

    PROJECT_ID = "welfare-chat-gm9e"
    LANGUAGE_CODE = "ko"
    LOCATION_ID = "asia-northeast1"

    resultTexts = detect_intent_texts(PROJECT_ID, LOCATION_ID, SESSION_ID, inputText, LANGUAGE_CODE)
    response = JsonResponse(
        {"input texts": inputText, "result texts": resultTexts, "sessionId": SESSION_ID}
    )

    return response


def createAllWelfareData(request):
    # DB classification 생성
    try:
        if Classification.objects.get(name="central"):
            pass
    except Exception as e:
        newClassification = Classification()
        newClassification.name = "central"
        newClassification.save()

    try:
        if Classification.objects.get(name="local"):
            pass
    except Exception as e:
        newClassification = Classification()
        newClassification.name = "local"
        newClassification.save()
    # Request
    URL = "https://www.bokjiro.go.kr/ssis-teu/TWAT52005M/twataa/wlfareInfo/selectWlfareInfo.do"
    body = {
        "dmSearchParam": {
            "page": "1",
            "onlineYn": "",
            "searchTerm": "",
            "tabId": "1",
            "orderBy": "date",
            "bkjrLftmCycCd": "",
            "daesang": "",
            "period": "",
            "age": "",
            "region": "",
            "jjim": "",
            "subject": "",
            "favoriteKeyword": "Y",
            "sido": "",
            "gungu": "",
        },
        "menuParam": {
            "mnuId": "",
            "pgmId": "",
            "wlfareInfoId": "",
            "scrnCmpntId": "",
            "curScrId": "",
        },
        "dmScr": {"curScrId": "teu/app/twat/twata/twataa/TWAT52005M"},
    }
    headers = {
        "Host": "www.bokjiro.go.kr",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    }
    responseData = json.loads(requests.post(URL, headers=headers, data=json.dumps(body)).text)

    i = 1
    while True:
        body["dmSearchParam"]["page"] = i
        responseData = json.loads(requests.post(URL, headers=headers, data=json.dumps(body)).text)

        # 중앙부처 데이터
        centralData = responseData["dsServiceList1"]
        # 지자체 데이터
        localData = responseData["dsServiceList2"]

        # 탈출 조건 : 지자체 데이터 개수 0
        if len(localData) == 0:
            break

        # 중앙부처 데이터 DB화
        for item in centralData:
            id = item.get("WLFARE_INFO_ID", "")
            title = item.get("WLFARE_INFO_NM", "").replace(",", "/")
            content = item.get("WLFARE_INFO_OUTL_CN", "")
            address = item.get("ADDR", "")
            if address == " ":
                address = ""
            phone = item.get("RPRS_CTADR", "")
            department = item.get("BIZ_CHR_INST_NM", "")

            # family, lifecycle, age
            complexData = item.get("RETURN_STR")
            complexList = complexData.split(";")
            complexDict = {}
            for listItem in complexList:
                complexDict.update({listItem.split(":")[0]: listItem.split(":")[1]})
            interest = complexDict.get("INTRS_THEMA_CD", "").replace(",", "/")
            family = complexDict.get("FMLY_CIRC_CD", "").replace(",", "/")
            lifecycle = complexDict.get("BKJR_LFTM_CYC_CD", "").replace(",", "/")
            ageText = complexDict.get("WLFARE_INFO_AGGRP_CD", "")
            age = ""
            if "0~5" in ageText:
                age += "0"
            if "6~12" in ageText:
                age += "1"
            if "13~18" in ageText:
                age += "2"
            if "19~39" in ageText:
                age += "3"
            if "40~64" in ageText:
                age += "4"
            if "65" in ageText:
                age += "5"
            classification = Classification.objects.get(name="central")
            dto = {
                "id": id,
                "title": title,
                "content": content,
                "interest": interest,
                "family": family,
                "lifecycle": lifecycle,
                "age": age,
                "address": address,
                "phone": phone,
                "department": department,
                "classification": classification,
            }
            Welfare.objects.create(**dto)
        # 지자체 데이터 DB화
        for item in localData:
            id = item.get("WLFARE_INFO_ID", "")
            title = item.get("WLFARE_INFO_NM", "").replace(",", "/")
            content = item.get("WLFARE_INFO_OUTL_CN", "")
            address = item.get("ADDR", "")
            if address == " ":
                address = ""
            phone = item.get("RPRS_CTADR", "")
            department = item.get("BIZ_CHR_INST_NM", "")

            # family, lifecycle, age
            complexData = item.get("RETURN_STR")
            complexList = complexData.split(";")
            complexDict = {}
            for listItem in complexList:
                complexDict.update({listItem.split(":")[0]: listItem.split(":")[1]})
            interest = complexDict.get("INTRS_THEMA_CD", "").replace(",", "/")
            family = complexDict.get("FMLY_CIRC_CD", "").replace(",", "/")
            lifecycle = complexDict.get("BKJR_LFTM_CYC_CD", "").replace(",", "/")
            ageText = complexDict.get("WLFARE_INFO_AGGRP_CD", "")
            age = ""
            if "0~5" in ageText:
                age += "0"
            if "6~12" in ageText:
                age += "1"
            if "13~18" in ageText:
                age += "2"
            if "19~39" in ageText:
                age += "3"
            if "40~64" in ageText:
                age += "4"
            if "65" in ageText:
                age += "5"
            classification = Classification.objects.get(name="local")
            dto = {
                "id": id,
                "title": title,
                "content": content,
                "interest": interest,
                "family": family,
                "lifecycle": lifecycle,
                "age": age,
                "address": address,
                "phone": phone,
                "department": department,
                "classification": classification,
            }
            Welfare.objects.create(**dto)
        i = i + 1
        sleep(1)
    return JsonResponse({"...": "ㅠㅠ"})
