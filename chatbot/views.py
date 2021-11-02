from rest_framework import viewsets
from .serializers import WelfareSerializer
from .models import Welfare
from django.http import JsonResponse

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
def detect_intent_texts(project_id, session_id, texts, language_code):
    from google.cloud import dialogflow

    # 동일한 세션ID로 통신을 하면 지속적인 대화가 가능하다. (약 20분 유지)
    # 따라서 동일한 세션ID를 여러 사용자가 사용X
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    print(f"Session path: {session}")

    results = []
    for text in texts:
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        print("=" * 20)
        print(f"Query text: {response.query_result.query_text}")
        print(
            f"Detected intent: {response.query_result.intent.display_name} (confidence: {response.query_result.intent_detection_confidence})\n"
        )
        print(f"Fulfillment text: {response.query_result.fulfillment_text}\n")
        results.append(response.query_result.fulfillment_text)
    return results


# dialogflow 테스트
# 환경변수 GOOGLE_APPLICATION_CREDENTIALS 등록하면 Cloud SDK가 알아서 사용자 계정으로 인증처리 하는 거 같음
def dialogflowTest(request):
    import random

    PROJECT_ID = "dialogflow-test-330305"
    SESSION_ID = f"session{str(random.randint(1, 1000000))}"
    inputTexts = ["I know french", "I know English"]
    LANGUAGE_CODE = "en-US"

    resultTexts = detect_intent_texts(PROJECT_ID, SESSION_ID, inputTexts, LANGUAGE_CODE)
    return JsonResponse({"input texts": inputTexts, "result texts": resultTexts})
