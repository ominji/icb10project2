import requests
import json
import pandas as pd
import os
import streamlit as st
from dotenv import load_dotenv
import datetime
from openai import OpenAI

def init_naver_credentials():
    """
    .env 파일에서 네이버 API 정보 및 OpenAI API 정보를 가져와 세션 상태(st.session_state)에 저장하고
    공통 검색 조건을 초기화합니다.
    """
    # 1. st.secrets 우선 로드 (Streamlit Cloud 배포 환경 또는 로컬 secrets.toml)
    client_id = st.secrets.get("NAVER_CLIENT_ID") if "NAVER_CLIENT_ID" in st.secrets else None
    client_secret = st.secrets.get("NAVER_CLIENT_SECRET") if "NAVER_CLIENT_SECRET" in st.secrets else None
    openai_api_key = st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else None
    
    # 2. st.secrets에 없으면 .env 로드 및 환경 변수 참조 (로컬 .env 개발 환경)
    if not client_id or not client_secret or not openai_api_key:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(os.path.dirname(current_dir), '.env')
        load_dotenv(dotenv_path)
        if not client_id:
            client_id = os.environ.get("NAVER_CLIENT_ID", "")
        if not client_secret:
            client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
        if not openai_api_key:
            openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    
    # API 키 세션 저장
    if "client_id" not in st.session_state or not st.session_state["client_id"]:
        st.session_state["client_id"] = client_id
    if "client_secret" not in st.session_state or not st.session_state["client_secret"]:
        st.session_state["client_secret"] = client_secret
    if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
        st.session_state["openai_api_key"] = openai_api_key
        
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


def analyze_sentiment_and_keywords(openai_api_key, documents):
    """
    OpenAI GPT-4o-mini 모델을 사용하여 텍스트 데이터의 감성과 핵심 키워드를 배치(Batch)로 분석합니다.
    documents: [{"title": "...", "description": "..."}, ...] 형식의 리스트
    """
    if not openai_api_key:
        return None, "OpenAI API 키가 설정되지 않았습니다."
        
    if not documents:
        return None, "분석할 문서 데이터가 없습니다."

    # 분석을 위한 텍스트 내용 가공
    input_data = []
    for idx, doc in enumerate(documents):
        input_data.append({
            "id": idx,
            "title": doc.get("title", ""),
            "description": doc.get("description", "")
        })
        
    prompt = f"""
    당신은 숙련된 한국어 텍스트 분석기입니다. 제공된 블로그/뉴스 문서 데이터(제목 및 요약 설명)를 분석하여 두 가지 결과(감성 분석, 형태소 키워드 분석)를 반환해 주세요.
    
    분석 대상 데이터:
    {json.dumps(input_data, ensure_ascii=False, indent=2)}
    
    요청 조건:
    1. 전체 문서들의 통합 감성 비율(긍정, 부정, 중립)의 백분율 합산이 100%가 되도록 계산하세요.
    2. 문서 전체에서 언급된 단어 중 워드클라우드를 그리기에 적합한 핵심 명사/단어 15~20개를 선정하고 빈도수(weight)를 가중치로 환산하세요. 무의미한 조사, 특수 기호, 검색 도메인명(네이버, 블로그 등)은 제외해야 합니다.
    3. 입력된 개별 문서(id 기준)마다 감성 라벨("positive", "negative", "neutral")을 매기고, 왜 그렇게 분류했는지 한국어로 아주 짧은 한 문장 요약(summary)을 작성하세요.
    
    반드시 아래 JSON 스키마 구조를 엄격하게 지켜 결과를 반환해 주세요. JSON 외의 설명이나 텍스트는 출력하지 마세요:
    {{
      "sentiment_ratio": {{
        "positive": 60,
        "negative": 20,
        "neutral": 20
      }},
      "keywords": [
        {{"word": "핵심단어1", "weight": 15}},
        {{"word": "핵심단어2", "weight": 10}}
      ],
      "document_analyses": [
        {{"id": 0, "sentiment": "positive", "summary": "기능과 디자인에 대해 긍정적인 사용 경험을 기술함."}},
        {{"id": 1, "sentiment": "neutral", "summary": "단순한 스펙 비교 및 출시 예정 정보를 제공함."}}
      ]
    }}
    """
    
    try:
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        return result_json, None
    except Exception as e:
        return None, f"OpenAI API 호출 또는 파싱 중 오류 발생: {str(e)}"


def inject_custom_css():
    """
    대시보드 전반에 네이버 시그니처 룩앤필(그린 포인트 컬러, 그림자 카드 레이아웃, Noto Sans KR 폰트)을 주입합니다.
    """
    css_code = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    /* 글로벌 폰트 설정 */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    /* 메인 타이틀 및 헤더 강조 */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Noto Sans KR', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* 네이버 그린 포인트 컬러 버튼 커스텀 */
    div.stButton > button {
        background-color: #03C75A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(3, 199, 90, 0.2) !important;
    }
    
    div.stButton > button:hover {
        background-color: #02a84b !important;
        box-shadow: 0 4px 12px rgba(3, 199, 90, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    
    div.stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* 사이드바 배경 및 테두리 */
    [data-testid="stSidebar"] {
        background-color: #f4f6f8 !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    /* 메트릭 및 컨테이너 카드화 디자인 */
    [data-testid="metric-container"], .stDataFrame, .stTable, div.stAlert {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02) !important;
    }
    
    /* 탭 스타일링 */
    button[data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #4b5563 !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #03C75A !important;
        border-bottom-color: #03C75A !important;
        font-weight: 700 !important;
    }
    
    /* 테이블 헤더 네이버 컬러 */
    thead tr th {
        background-color: #f9fafb !important;
        color: #111827 !important;
        font-weight: 600 !important;
    }
    </style>
    """
    st.markdown(css_code, unsafe_allow_html=True)

