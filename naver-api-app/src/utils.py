import requests
import json
import pandas as pd
import os
import streamlit as st
from dotenv import load_dotenv
import datetime

def init_naver_credentials():
    """
    .env 파일에서 네이버 API 정보를 가져와 세션 상태(st.session_state)에 저장하고
    공통 검색 조건을 초기화합니다.
    """
    # 1. st.secrets 우선 로드 (Streamlit Cloud 배포 환경 또는 로컬 secrets.toml)
    client_id = st.secrets.get("NAVER_CLIENT_ID") if "NAVER_CLIENT_ID" in st.secrets else None
    client_secret = st.secrets.get("NAVER_CLIENT_SECRET") if "NAVER_CLIENT_SECRET" in st.secrets else None
    
    # 2. st.secrets에 없으면 .env 로드 및 환경 변수 참조 (로컬 .env 개발 환경)
    if not client_id or not client_secret:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(os.path.dirname(current_dir), '.env')
        load_dotenv(dotenv_path)
        client_id = os.environ.get("NAVER_CLIENT_ID", "")
        client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
    
    # API 키 세션 저장
    if "client_id" not in st.session_state or not st.session_state["client_id"]:
        st.session_state["client_id"] = client_id
    if "client_secret" not in st.session_state or not st.session_state["client_secret"]:
        st.session_state["client_secret"] = client_secret
        
    # 공통 검색 조건 초기화 (하위 페이지 직진입 대응)
    if "keywords" not in st.session_state:
        st.session_state["keywords"] = "아이폰, 갤럭시, 픽셀"
    if "keywords_list" not in st.session_state:
        st.session_state["keywords_list"] = [k.strip() for k in st.session_state["keywords"].split(",") if k.strip()]
    if "start_date" not in st.session_state:
        st.session_state["start_date"] = datetime.date.today() - datetime.timedelta(days=90)
    if "end_date" not in st.session_state:
        st.session_state["end_date"] = datetime.date.today()
    if "time_unit" not in st.session_state:
        st.session_state["time_unit"] = "date"


def get_headers(client_id, client_secret):
    """
    네이버 API 호출을 위한 공통 헤더를 반환합니다.
    """
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }

def get_search_trend(client_id, client_secret, keywords, start_date, end_date, time_unit='date'):
    """
    네이버 통합 검색어 트렌드 API를 호출합니다.
    """
    url = "https://openapi.naver.com/v1/datalab/search"
    
    # 입력된 키워드 리스트를 개별 키워드 그룹으로 구성
    keyword_groups = [{"groupName": kw.strip(), "keywords": [kw.strip()]} for kw in keywords if kw.strip()]
    
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups
    }
    
    try:
        response = requests.post(url, headers=get_headers(client_id, client_secret), data=json.dumps(body))
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"오류 코드: {response.status_code}, 메시지: {response.text}"
    except Exception as e:
        return None, str(e)

def get_shopping_trend(client_id, client_secret, keywords, start_date, end_date, time_unit='date', category='50000000'):
    """
    네이버 쇼핑인사이트 키워드별 클릭 추이 API를 호출합니다.
    """
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
    
    # 쇼핑 키워드 파라미터 구성
    keyword_list = [{"name": kw.strip(), "param": [kw.strip()]} for kw in keywords if kw.strip()]
    
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "category": category,
        "keyword": keyword_list
    }
    
    try:
        response = requests.post(url, headers=get_headers(client_id, client_secret), data=json.dumps(body))
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"오류 코드: {response.status_code}, 메시지: {response.text}"
    except Exception as e:
        return None, str(e)

def search_naver(client_id, client_secret, api_type, query, display=50, start=1, sort='sim'):
    """
    네이버 검색 API(쇼핑, 블로그, 카페글, 뉴스)를 호출합니다.
    """
    endpoints = {
        "shop": "https://openapi.naver.com/v1/search/shop.json",
        "blog": "https://openapi.naver.com/v1/search/blog.json",
        "cafe": "https://openapi.naver.com/v1/search/cafearticle.json",
        "news": "https://openapi.naver.com/v1/search/news.json"
    }
    
    if api_type not in endpoints:
        return None, "지원하지 않는 API 타입입니다."
        
    url = endpoints[api_type]
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort
    }
    
    # GET 요청이므로 별도의 헤더 인증 사용
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"오류 코드: {response.status_code}, 메시지: {response.text}"
    except Exception as e:
        return None, str(e)
