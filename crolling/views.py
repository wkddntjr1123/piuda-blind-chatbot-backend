import json, time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup as bs
from chatbot.models import Mohw, Bokjiro
import requests

# 복지로 사이트의 모든 복지정보 크롤링 => DB 저장
@csrf_exempt
def crollingAllBokjiro(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "invalid HTTP method"})
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
            contents = item.get("WLFARE_INFO_OUTL_CN", "").replace("&middot;", ",")
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
            interest = complexDict.get("INTRS_THEMA_CD", "").replace(",", "/").replace("·", "")
            family = complexDict.get("FMLY_CIRC_CD", "").replace(",", "/").replace("·", "/")
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
            classification = "중앙부처"
            dto = {
                "id": id,
                "title": title,
                "contents": contents,
                "interest": interest,
                "family": family,
                "lifecycle": lifecycle,
                "age": age,
                "address": address,
                "phone": phone,
                "department": department,
                "classification": classification,
            }
            Bokjiro.objects.create(**dto)
        # 지자체 데이터 DB화
        for item in localData:
            id = item.get("WLFARE_INFO_ID", "")
            title = item.get("WLFARE_INFO_NM", "").replace(",", "/")
            contents = item.get("WLFARE_INFO_OUTL_CN", "").replace("&middot;", ",")
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
            interest = complexDict.get("INTRS_THEMA_CD", "").replace(",", "/").replace("·", "")
            family = complexDict.get("FMLY_CIRC_CD", "").replace(",", "/").replace("·", "/")
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
            classification = "지자체"
            dto = {
                "id": id,
                "title": title,
                "contents": contents,
                "interest": interest,
                "family": family,
                "lifecycle": lifecycle,
                "age": age,
                "address": address,
                "phone": phone,
                "department": department,
                "classification": classification,
            }
            Bokjiro.objects.create(**dto)
        i = i + 1
        time.sleep(0.3)
    return JsonResponse({"success": True})


# 보건지부-복건복지상담센터 사이트의 모든 복지정보 크롤링 => DB 저장
@csrf_exempt
def crollingAllMohw(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "invalid HTTP method"})
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
            detailPageURLs = soup.select(".subject > a")
            # 크롤링할 상세페이지가 없으면 탈출
            if not detailPageURLs:
                break
            # 크롤링할 상세페이지가 있으면
            for item in detailPageURLs:
                # 각 상세페이지 get
                requestDetailURL = serverName + item["href"]
                id = str(urlNum + 1) + "-" + str(requestDetailURL.split("?n=")[1])
                detailResponse = requests.get(requestDetailURL)
                detailHtml = detailResponse.text
                detailSoup = bs(detailHtml, "html.parser")
                try:
                    title = detailSoup.select_one(".px > td").text
                    createdDate = detailSoup.find("th", text="작성일").find_next("td").text
                    contents = (
                        detailSoup.select(".faq-tr")[1]
                        .select_one("td")
                        .text.strip()
                        .replace("\n", " ")
                    )
                    # db insert
                    Mohw.objects.create(
                        id=id,
                        title=title,
                        category=category,
                        contents=contents,
                        createdDate=createdDate,
                    )
                except Exception as e:
                    print(detailSoup)
            page += 1
            time.sleep(0.3)
    return JsonResponse({"success": True})
