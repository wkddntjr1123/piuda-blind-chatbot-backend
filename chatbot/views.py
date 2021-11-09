import json
from rest_framework import viewsets

from config.settings import BASE_DIR
from .serializers import WelfareSerializer
from .models import Classification, Welfare
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# viewset으로 CRUD 자동 구현
class WelfareViewSet(viewsets.ModelViewSet):
    queryset = Welfare.objects.all()
    serializer_class = WelfareSerializer


# beautifulsoup 테스트
def beautifulsoupTest(request):
    import requests
    from bs4 import BeautifulSoup as bs

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
def detect_intent_texts(project_id, location_id, session_id, texts, language_code):
    from google.cloud import dialogflow

    # 동일한 세션ID로 통신을 하면 지속적인 대화가 가능하다. (약 20분 유지)
    # 따라서 동일한 세션ID를 여러 사용자가 사용X
    session_client = dialogflow.SessionsClient(
        client_options={"api_endpoint": f"{location_id}-dialogflow.googleapis.com"}
    )
    session = f"projects/{project_id}/locations/{location_id}/agent/sessions/{session_id}"
    print(f"Session path: {session}")

    results = []
    for text in texts:
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        print("=" * 100 + "\n")
        print(f"=> Query text: {response.query_result.query_text}")
        print(
            f"=> Detected intent: {response.query_result.intent.display_name} (confidence: {response.query_result.intent_detection_confidence})"
        )
        print(f"=> Fulfillment text: {response.query_result.fulfillment_text} \n")
        print("=" * 100)
        results.append(response.query_result.fulfillment_text)
    return results


# dialogflow 테스트
# 환경변수 GOOGLE_APPLICATION_CREDENTIALS 등록하면 Cloud SDK가 알아서 사용자 계정으로 인증처리 하는 거 같음
@csrf_exempt
def dialogflowTest(request):
    import json, os, uuid

    credentials = os.path.join(BASE_DIR, "credentials.json")
    # GOOGLE_APPLICATION_CREDENTIALS 환경변수 등록
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials

    # 쿠키에 세션 정보 있으면 해당 세션값 사용
    if request.COOKIES.get("session"):
        SESSION_ID = request.COOKIES.get("session")
    # 쿠키에 세션 정보 없으면 새로운 세션갑 설정
    else:
        SESSION_ID = uuid.uuid4()
    # 예시
    """
    texts필드에 []형태로 넘겨야함
    {
        "texts" : ["I know french", "I know English"]
    }
    """
    # body에 실려온 json
    inputRawText = request.body
    # json to dict
    inputText = json.loads(inputRawText)["texts"]

    PROJECT_ID = "welfare-chat-gm9e"
    LANGUAGE_CODE = "ko"
    LOCATION_ID = "asia-northeast1"
    import datetime

    now = datetime.datetime.now()
    resultTexts = detect_intent_texts(PROJECT_ID, LOCATION_ID, SESSION_ID, inputText, LANGUAGE_CODE)
    print(datetime.datetime.now() - now)

    response = JsonResponse({"input texts": inputText, "result texts": resultTexts})
    # 쿠키 설정 : {"session":SESSION_ID값}, 유지시간 20분

    response.set_cookie(key="session", value=SESSION_ID, max_age=1200)

    return response


def testing(request):
    import os

    data = json.load(
        open(
            os.path.join(
                BASE_DIR,
                "data.json",
            ),
            encoding="utf8",
        )
    )
    data2 = data.get("__collections__").get("member")
    for item in data2:
        rawData = data2[item]
        print(rawData["WLFARE_INFO_NM"])
    return JsonResponse({"...": "ㅠㅠ"})
