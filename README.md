# 자연어 처리 기반의 시각장애인을 위한 챗봇 어플리케이션
## 2021 ICT이노베이션 피우다 공모전 - 장려상

### 백엔드 기술 스택 : AWS EC2, ElasticSearch, Django, DialogFlow

### 시스템 구성
![image](https://user-images.githubusercontent.com/64186072/169105532-9bd70abc-a546-4fd1-81aa-9e1b6538500e.png)

#### 시각장애인을 위한 복지정보 접근성 개선 프로젝트

1. 안드로이드에서 TTS/SST를 이용하여 시각장애인 사용자와 상호작용
2. 가능한 많은 정보를 제공하기위해 주요 복지 사이트를 하루마다 자동적으로 크롤링
3. 챗봇 기능을 위해 Google Dialogflow, Full text검색을 위해 Elastic Search를 사용  

> 개발 초기에는 자연어 처리를 Elastic Search가 아닌 mecab을 이용해서 직접 문장의 형태소를 분석하여 수행했했었으나, 역인덱싱 데이터를 효율적으로 저장하기 위해서 ElasticSearch를 사용하는 방향으로 변경
