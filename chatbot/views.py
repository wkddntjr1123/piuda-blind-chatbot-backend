import json, os, time
from config.settings import BASE_DIR
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Classification, MinistryHealthWelfare, Welfare
from bs4 import BeautifulSoup as bs
import requests
from google.cloud import dialogflow
from proto import Message
from chatbot.elasticSearchService import searchByTitle


# 전체 DB 생성 함수
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
        time.sleep(1)
    return JsonResponse({"...": "ㅠㅠ"})


# 보건복지부 보건복지상담센터 : FAQ 크롤링
def crolling123GoKr(request):
    serverName = "http://129.go.kr"
    # 대분류 : http://129.go.kr/faq/faq01.jsp ~ http://129.go.kr/faq/faq05.jsp
    # 1:보건의료, 2:사회복지, 3:인구아동, 4:위기대응, 5:노인장애인
    for urlNum in range(0, 5):
        requestURL = serverName + f"/faq/faq0{urlNum+1}.jsp"
        categoryDomain = ["보건의료", "사회복지", "인구아동", "위기대응", "노인장애인"]
        category = categoryDomain[urlNum]
        page = 1
        while True:
            queryParam = f"?page={page}"
            response = requests.get(requestURL + queryParam)
            html = response.text
            soup = bs(html, "html.parser")
            detailPageURLs = soup.select(".subject>a")
            # 크롤링할 상세페이지가 없으면 탈출
            if not detailPageURLs:
                break
            # 크롤링할 상세페이지가 있으면
            for item in detailPageURLs:
                # 각 상세페이지 get
                requestDetailURL = serverName + item["href"]
                detailResponse = requests.get(requestDetailURL)
                detailHtml = detailResponse.text
                detailSoup = bs(detailHtml, "html.parser")
                title = detailSoup.select_one(".px>td").text
                createdDate = detailSoup.find("th", text="작성일").find_next("td").text
                contents = (
                    detailSoup.select(".faq-tr")[1].select_one("td").text.strip().replace("\n", " ")
                )
                # db insert
                MinistryHealthWelfare.objects.create(
                    title=title,
                    category=category,
                    contents=contents,
                    createdDate=createdDate,
                )
            page += 1
    return JsonResponse({"success": True})


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
    params = dict_response.get("query_result").get("output_contexts")

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

    # 최종적으로 데이터 반환이 필요하면 : 추천의 최종 인텐트 이름 => "Recommend_F - custom - custom - yes"
    resultData = None
    if intent_name == "Recommend_F - custom - custom - yes":
        print("최종결과리턴해야해!")
        # resultData = searchByTitle("welfare")

    # 최종적으로 반환되는 결과 오브젝트가 존재하면 추가해서 반환
    if resultData is not None:
        response.update({"resultData": resultData})
    return JsonResponse(response)


@csrf_exempt
def newNatural(request):
    result = searchByTitle("welfare", "임신 중인데 일자리가 필요해요. 취약 계층")
    return JsonResponse(result, safe=False)
