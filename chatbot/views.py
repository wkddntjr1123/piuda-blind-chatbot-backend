import json, os
from config.settings import BASE_DIR
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.cloud import dialogflow
from proto import Message
from chatbot.elasticSearchService import *
from .models import *
from django.core.paginator import Paginator
from django.db.models import Q

# dialogFlow서버에서 결과 받아오기
# return : 리턴된 응답 메시지, 응답한 인텐트 이름, 입력된 파라미터들 Object
def getDialogflowResult(project_id, location_id, session_id, text, language_code):
    # 동일한 세션ID로 통신을 하면 지속적인 대화가 가능 (약 20분 유지)
    session_client = dialogflow.SessionsClient(
        client_options={"api_endpoint": f"{location_id}-dialogflow.googleapis.com"}
    )
    session = f"projects/{project_id}/locations/{location_id}/agent/sessions/{session_id}"

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    # dialogflow의 결과를 dict로 변환
    dict_response = Message.to_dict(response)
    fulfillment_text = dict_response.get("query_result").get("fulfillment_text")
    recent_intent = dict_response.get("query_result").get("intent").get("display_name")
    params = dict_response.get("query_result").get("parameters")

    return fulfillment_text, recent_intent, params


# Client(안드로이드)의 dialogFlow 통신용 엔드 포인트
# input : {"texts":"내용", "sessionId":"세션ID"}
# output : {"input texts":"입력내용", "result texts":"결과내용", "sessionId":"세션ID", "resultData":{최종결과오브젝트})
@csrf_exempt
def chatWithServer(request):

    SESSION_ID = json.loads(request.body)["sessionId"]
    inputText = json.loads(request.body)["texts"]

    # 환경변수 GOOGLE_APPLICATION_CREDENTIALS 등록하면 Google Cloud SDK가 알아서 사용자 계정으로 인증처리
    credentials = os.path.join(BASE_DIR, "credentials.json")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials

    PROJECT_ID = "welfare-chat-gm9e"
    LANGUAGE_CODE = "ko"
    LOCATION_ID = "asia-northeast1"
    # dialogflow에서 문장 받아오기 : (응답텍스트, 응답한 인텐트이름, 파라미터객체)
    result_texts, intent_name, params = getDialogflowResult(
        PROJECT_ID, LOCATION_ID, SESSION_ID, inputText, LANGUAGE_CODE
    )
    # 클라이언트에 응답할 데이터
    response = {"input texts": inputText, "result texts": result_texts, "sessionId": SESSION_ID}

    # From 추천 : 최종결과 리턴 트리거 => 인텐트 이름 : "Recommend_F - custom - custom - yes"

    resultData = None
    if intent_name == "Recommend_F - custom2 - custom - yes":
        resultData = searchBokjiroByParams(params["age"], params["area"], params["interest"])
        if not len(resultData):
            response["result texts"] = "일치하는 복지 결과가 없습니다. 010-5105-6656으로 연결할까요?"
            resultData = None
    # From 검색 : 최종결과 리턴 트리거 => 인텐트 이름 : "Search - custom"
    if intent_name == "Search - custom":
        if len(params["any"]):
            keyword = " ".join(params["any"])
        if len(params["Others"]):
            keyword = " ".join(params["Others"])
        resultData = searchBykeyword("bokjiro", keyword)

    # 최종적으로 반환되는 결과 오브젝트가 존재하면 추가해서 반환
    if resultData:
        response.update({"resultData": resultData})
    return JsonResponse(response, safe=False)


# 인자로 page, central, local, keyword를 받아서 elasticsearch에서 페이지네이션 된 data 반환
@csrf_exempt
def pagedBokjiroList(request):
    page = int(request.GET.get("page", 1))
    central = request.GET.get("central", None)
    local = request.GET.get("local", None)
    keyword = request.GET.get("keyword", None)
    results = getPagedList(page, central, local, keyword)

    return JsonResponse(results, safe=False)


@csrf_exempt
# 복지정보 detail 정보 return
def bokjoroDetail(request, id):
    result = searchById("bokjiro", id)
    return JsonResponse(result, safe=False)
