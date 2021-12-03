import json
from elasticsearch import Elasticsearch, helpers
from django.conf import settings

host = getattr(settings, "ELK_BASE_URL")
es = Elasticsearch(host)

"""
bokjiro index 생성
{
    "settings": {
        "index": {
            "analysis": {
                "analyzer": {
                    "korean": {
                        "type": "custom",
                        "tokenizer": "seunjeon"
                    }
                },
                "tokenizer": {
                    "seunjeon": {
                        "user_words": ["캐구", "골구", "맥퀸"],
                        "index_eojeol": "true",
                        "index_poses": [
                            "UNK",
                            "EP",
                            "I",
                        ],
                        "decompound": "true",
                        "type": "seunjeon_tokenizer"
                    }
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "name": {
                "type": "text",
                "analyzer": "korean"
            },
            "id": {
              "type": "integer"
            }
        }
    }
}
"""

"""
### ElasticSearch Bulk Insert ###

@param
    index : String  #인덱스이름
    data : List => [item1, item2, ...]  #데이터 객체 배열
    item : Dictionary => {"title":"","content":"",...}  #데이터 아이템dict
@param

"""


def bulkInsert(index, data):
    processedArray = []
    for item in data:
        processedArray.append({"_index": index, "_type": "_doc", "_source": item})
    helpers.bulk(es, processedArray)
    return True


"""
### ElasticSearch Data Search ###
@param
    index : String  #검색할 인덱스 이름
    keyword : String or List  #검색할 문장 or 키워드
@return
    results : Dictionary  #검색결과는 results["hits"]["hits"]에 List형태로 리턴
"""

# From 추천
# age, area => 유사도 처리 필요X
# interest => 유사도 처리 필요
def searchFromRecommend(age, area, interest):
    body = json.dumps(
        {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "age": {
                                    "query": age,
                                    "boost": 1,
                                }
                            }
                        },
                        {
                            "match": {
                                "area": {
                                    "query": area,
                                    "boost": 1,
                                }
                            }
                        },
                        {
                            "match": {
                                "interest": {
                                    "query": interest,
                                    "boost": 1,
                                }
                            }
                        },
                    ]
                }
            }
        }
    )
    results = es.search(index="welfare", body=body)
    return


# From 검색
def searchFromSearch():
    return


# search and return a most relevant object (제목으로 검색) / 리스트의 가장 앞에 있는 객체가 유사도가 제일 높은 객체
# keyword로 list가 들어오면 공백이 있는 string으로 변환 후 검색
# title에 가중치 1.2
def searchByTitle(index, keyword):
    if isinstance(keyword, list):
        keyword = " ".join(keyword)
    body = json.dumps(
        {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"title": {"query": keyword, "boost": 1.2}}},
                        {
                            "match": {
                                "contents": {
                                    "query": keyword,
                                }
                            }
                        },
                        {
                            "match_phrase": {
                                "title": {
                                    "query": keyword,
                                    "boost": 2,
                                }
                            }
                        },
                    ]
                }
            }
        }
    )
    results = es.search(index=index, body=body)
    return results["hits"]["hits"]
