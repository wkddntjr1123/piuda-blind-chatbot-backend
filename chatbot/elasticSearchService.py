import json
from elasticsearch import Elasticsearch, helpers
from django.conf import settings

host = getattr(settings, "ELK_BASE_URL")
es = Elasticsearch(host)

### ElasticSearch Bulk Insert ###
#   @param
#       index : String  #인덱스이름
#       data : List => [item1, item2, ...]  #데이터 객체 배열
#       item : Dictionary => {"title":"","content":"",...}  #데이터 아이템dict
#   @param
def bulkInsert(index, data):
    processedArray = []
    for item in data:
        processedArray.append({"_index": index, "_type": "_doc", "_source": item})
    helpers.bulk(es, processedArray)
    return True


"""
### bulkInsert 예시 ###
    bokjiros = Bokjiro.objects.all()
    data = []
    for item in bokjiros:
        data.append(
            {
                "id": item.id,
                "address": item.address,
                "age": item.age,
                "classification": item.classification,
                "contents": item.contents,
                "department": item.department,
                "family": item.family,
                "inserted_date": item.db_inserted_date,
                "interest": item.interest,
                "lifecycle": item.lifecycle,
                "phone": item.phone,
                "title": item.title,
            }
        )
    bulkInsert("bokjiro", data)
"""

### ElasticSearch 복지로 Search By Age, Area, Interest ###
#   가중치 : age(6), area(1), interest(1)
#
#   @param
#       index : String  #검색할 인덱스 이름
#       keyword : String or List  #검색할 문장 or 키워드
#   @return
#       results : Dictionary  #검색결과는 results["hits"]["hits"]에 List형태로 리턴
#   '추천'에서 사용
def searchBokjiroByParams(age, area, interest):
    ageNum = 0
    if int(age) in range(0, 6):
        ageNum = "0"
    elif int(age) in range(6, 13):
        ageNum = "1"
    elif int(age) in range(13, 19):
        ageNum = "2"
    elif int(age) in range(19, 40):
        ageNum = "3"
    elif int(age) in range(40, 65):
        ageNum = "4"
    else:
        ageNum = "5"

    # age, interest, address 모두 완전 일치하는 쿼리 (DB의 Where Like문과 결과 일치)
    body = json.dumps(
        {
            "query": {
                "bool": {
                    "must": [
                        {"wildcard": {"age": {"value": f"*{ageNum}*"}}},
                        {"wildcard": {"interest": {"value": f"*{interest}*"}}},
                        {"wildcard": {"address": {"value": f"*{area}*"}}},
                    ]
                },
            }
        }
    )
    """
    # age, interest, address 가중치 쿼리 (사용자의 입력과 일치하지 않는 경우, 예상치 못한 결과 리턴되는 문제)
    body = json.dumps(
        {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"age": {"query": ageNum, "boost": 2.5}}},
                        {"match": {"address": {"query": area, "boost": 1}}},
                        {"match": {"interest": {"query": interest, "boost": 1}}},
                    ]
                }
            }
        }
    )
    그 외 쿼리
    {
        "query": {
            "bool": {
                "must": [
                    {
                        "wildcard": {
                            "age": {
                                "value": "*2*"
                            }
                        }
                    },
                    {
                        "wildcard": {
                            "address": {
                                "value": "*전라북도*"
                            }
                        }
                    }
                ],
                "should": [
                    {
                        "wildcard": {
                            "interest": {
                                "value": "*일자리*",
                                "boost": 2
                            }
                        }
                    }
                ]
            }
        }
    }
    """
    results = es.search(index="bokjiro", body=body)
    return results["hits"]["hits"]


### ElasticSearch Keyword Search => From 검색 ###
#   가중치 : title(1.2), contents(1)
#   @param
#       index : String  #검색할 인덱스 이름 => bokjiro 또는 mohw
#       keyword : String or List  #검색할 문장 or 키워드
#   @return
#       results : Dictionary  #검색결과는 results["hits"]["hits"]에 List형태로 리턴
#   '추천','검색' 모두 사용
def searchBykeyword(index, keyword):
    if isinstance(keyword, list):
        keyword = " ".join(keyword)
    body = json.dumps(
        {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"title": {"query": keyword, "boost": 3}}},
                        {
                            "match": {
                                "contents": {
                                    "query": keyword,
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


### ElasticSearch Pagination  ###
#   @param
#       page (any) => 페이지 넘버
#       central (any) =>  중앙부처
#       local (any) => 지자체
#       keyword (String) => 검색어 (title)
#   @return
#       results : Dictionary  #검색결과는 results["hits"]["hits"]에 List형태로 리턴
def getPagedList(page, central, local, keyword):
    if page == 1:
        start_index = 1
    else:
        start_index = (page - 1) * 10
    body = {
        "from": start_index,
        "size": 10,
        "query": {"bool": {"must": [{"bool": {"should": []}}]}},
    }

    if keyword is not None:
        body["query"]["bool"]["must"].append({"match": {"title": keyword}})

    if central is not None:
        body["query"]["bool"]["must"][0]["bool"]["should"].append(
            {"term": {"classification": "중앙부처"}}
        )
    if local is not None:
        body["query"]["bool"]["must"][0]["bool"]["should"].append(
            {"term": {"classification": "지자체"}}
        )

    results = es.search(index="bokjiro", body=body)
    return results["hits"]["hits"]


"""
mohw index 생성
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
						"index_poses": [
							"UNK",
							"EP",
							"I",
							"J",
							"M",
							"N",
							"SL",
							"SH",
							"SN",
							"VCP",
							"XP",
							"XS",
							"XR"
						],
						"type": "seunjeon_tokenizer"
					}
				}
			}
		}
	},
	"mappings": {
		"properties": {
			"id": {
				"type": "keyword"
			},
			"category": {
				"type": "keyword"
			},
			"title": {
				"type": "text",
				"analyzer": "korean"
			},
			"contents": {
				"type": "text",
				"analyzer": "korean"
			},
			"created_date":{
				"type" : "keyword"
			},
			"inserted_date": {
				"type": "date",
				"format": "yyyy-mm-dd"
			}
		}
	}
}
"""

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
					},
					"spliter": {
						"tokenizer": "split_tokenizer"
					},
					"ngram_one": {
						"tokenizer": "ngram_tokenizer"
					}
				},
				"tokenizer": {
					"seunjeon": {
						"index_poses": [
							"UNK",
							"EP",
							"I",
							"J",
							"M",
							"N",
							"SL",
							"SH",
							"SN",
							"VCP",
							"XP",
							"XS",
							"XR"
						],
						"type": "seunjeon_tokenizer"
					},
					"split_tokenizer": {
						"type": "simple_pattern_split",
						"pattern": "/"
					},
					"ngram_tokenizer": {
						"type": "ngram",
						"min_gram": "1",
						"max_gram": "1"
					}
				}
			}
		}
	},
	"mappings": {
		"properties": {
			"id": {
				"type": "keyword"
			},
			"classification": {
				"type": "keyword"
			},
			"title": {
				"type": "text",
				"analyzer": "korean"
			},
			"contents": {
				"type": "text",
				"analyzer": "korean"
			},
			"interest": {
				"type": "text",
				"analyzer": "spliter"
			},
			"family": {
				"type": "text",
				"analyzer": "spliter"
			},
			"lifecycle": {
				"type": "text",
				"analyzer": "spliter"
			},
			"age": {
				"type": "text",
				"analyzer": "ngram_one"
			},
			"address": {
				"type": "text",
				"analyzer": "korean"
			},
			"phone": {
				"type": "keyword"
			},
			"department": {
				"type": "keyword"
			},
			"inserted_date": {
				"type": "date",
				"format": "yyyy-mm-dd"
			}
		}
	}
}
"""
