import json, requests, time
from chatbot.elasticSearchService import documentInsert
from chatbot.models import Bokjiro
from elasticsearch import Elasticsearch


def run():
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

        items = []
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
            items.append(dto)
            # Bokjiro.objects.create(**dto)
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
            items.append(dto)
        # DB에 데이터가 존재하는지 비교 : 만약 없다면 객체 저장
        for item in items:
            if not Bokjiro.objects.filter(id=item["id"]).exists():
                insertedObject = Bokjiro.objects.create(item)
                dtoForElasticsearch = {
                    "id": insertedObject.id,
                    "title": insertedObject.title,
                    "contents": insertedObject.contents,
                    "interest": insertedObject.interest,
                    "family": insertedObject.family,
                    "lifecycle": insertedObject.lifecycle,
                    "age": insertedObject.age,
                    "address": insertedObject.address,
                    "phone": insertedObject.phone,
                    "department": insertedObject.department,
                    "classification": insertedObject.classification,
                    "inserted_date": item.db_inserted_date,
                }
                documentInsert("bokjiro", dtoForElasticsearch)
        i = i + 1
        time.sleep(0.25)
