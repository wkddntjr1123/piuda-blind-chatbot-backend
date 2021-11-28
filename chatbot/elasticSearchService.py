from elasticsearch import Elasticsearch, helpers
from django.conf import settings

host = getattr(settings, "ELK_BASE_URL")
es = Elasticsearch(host)

"""
param
    index : string => 인덱스이름
    data : array => [item1, item2, ...] => 데이터 객체 배열
    item : {"title":"","content":"",...} => 데이터 dict
    }
"""
# bulk insert
def bulkInsert(index, data):
    processedArray = []
    for item in data:
        processedArray.append({"_index": index, "_type": "_doc", "_source": item})
    helpers.bulk(es, processedArray)
    return True


"""
param
    index : string => 인덱스이름
    keyword : string or list => list를 받으면 리스트의 각 아이템을 공백으로 합쳐서 string으로 변환
    }
"""
# search and return a most relevant object (제목으로 검색) / 리스트의 가장 앞에 있는 객체가 유사도가 제일 높은 객체
def searchByTitle(index, keyword):
    if isinstance(keyword, list):
        keyword = " ".join(keyword)
    body = {"query": {"match": {"content": keyword}}}
    results = es.search(index=index, body=body)
    return results
