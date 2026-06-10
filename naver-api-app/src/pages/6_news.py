import streamlit as st
import pandas as pd
import re
import html
from urllib.parse import urlparse
import plotly.express as px
from utils import search_naver, init_naver_credentials

# API 인증키 및 공통 세션 초기화
init_naver_credentials()

st.set_page_config(page_title="뉴스 검색 분석", layout="wide")

st.markdown("<h2 style='color: #00C73C;'>📰 네이버 뉴스 검색 분석</h2>", unsafe_allow_html=True)
st.markdown("네이버 뉴스 검색 API를 통해 입력된 키워드와 관련된 언론 기사를 수집하고 뉴스 보도 추이 및 주요 채널을 분석합니다.")
st.markdown("---")

# API 인증 키 및 검색 조건 확인
client_id = st.session_state.get("client_id", "")
client_secret = st.session_state.get("client_secret", "")
keywords_list = st.session_state.get("keywords_list", [])

if not client_id or not client_secret:
    st.warning("⚠️ naver-api-app/.env 파일에 네이버 API Client ID와 Client Secret을 먼저 입력해 주세요.")
    st.stop()

if not keywords_list:
    st.warning("⚠️ 왼쪽 사이드바 메뉴에서 최소 하나 이상의 검색어를 입력해 주세요.")
    st.stop()

# 정렬 방식 선택
sort_option = st.selectbox(
    "정렬 방식 선택",
    options=["sim", "date"],
    format_func=lambda x: "유사도순" if x == "sim" else "최신순"
)

# HTML 태그 및 엔티티 제거 함수
def clean_text(text):
    text = re.sub('<.*?>', '', text)  # HTML 태그 제거
    text = html.unescape(text)       # HTML 엔티티(예: &quot;) 변환
    return text

# 도메인 추출 함수 (언론사 대용)
def extract_domain(url):
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except:
        return "알수없음"

all_news = []
with st.spinner("네이버 뉴스 데이터를 수집하는 중..."):
    for kw in keywords_list:
        data, error = search_naver(
            client_id=client_id,
            client_secret=client_secret,
            api_type="news",
            query=kw,
            display=50,
            sort=sort_option
        )
        if error:
            st.error(f"'{kw}' 뉴스 검색 실패: {error}")
        else:
            items = data.get("items", [])
            for item in items:
                all_news.append({
                    "검색키워드": kw,
                    "제목": clean_text(item.get("title", "")),
                    "요약": clean_text(item.get("description", "")),
                    "보도시간": item.get("pubDate", ""),
                    "원본링크": item.get("originallink", ""),
                    "네이버뉴스링크": item.get("link", ""),
                    "출처도메인": extract_domain(item.get("originallink", ""))
                })

if not all_news:
    st.info("수집된 뉴스 정보가 없습니다.")
else:
    df_news = pd.DataFrame(all_news)
    
    # 1. 요약 메트릭
    st.markdown("### 📋 수집 요약")
    sum_col1, sum_col2 = st.columns(2)
    sum_col1.metric("총 수집 뉴스 기사 수", f"{len(df_news)} 개")
    sum_col2.metric("고유 출처(도메인) 수", f"{df_news['출처도메인'].nunique()} 개")
    
    st.markdown("---")
    
    # 2. 분석 탭
    tab1, tab2, tab3 = st.tabs(["📅 보도 시간대별 분석", "📰 주요 언론 채널(도메인) 분석", "📋 뉴스 기사 목록"])
    
    with tab1:
        st.markdown("#### 뉴스 보도 일자/시간대별 추이")
        # 날짜 타입 변환
        df_news['보도일시'] = pd.to_datetime(df_news['보도시간'], errors='coerce')
        df_date = df_news.groupby([df_news['보도일시'].dt.date, "검색키워드"]).size().reset_index(name="기사수")
        df_date.columns = ["보도일", "검색키워드", "기사수"]
        
        # 유효한 날짜만 필터링
        df_date = df_date.dropna(subset=['보도일']).sort_values('보도일')
        
        if df_date.empty:
            st.info("보도시간 데이터 파싱 결과가 없어 추이 차트를 생성할 수 없습니다.")
        else:
            fig_line = px.line(
                df_date,
                x="보도일",
                y="기사수",
                color="검색키워드",
                title="일자별 뉴스 기사 보도량 추이 (수집 데이터 기준)",
                labels={"기사수": "보도된 기사 수", "보도일": "보도 날짜"},
                template="plotly_white"
            )
            fig_line.update_layout(hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
            
    with tab2:
        st.markdown("#### 주요 뉴스 출처 Top 10 (도메인 기준)")
        df_source = df_news["출처도메인"].value_counts().reset_index()
        df_source.columns = ["출처도메인", "기사수"]
        
        # 'naver.com'은 포털이므로 제외하고 원문 언론사 중심 도메인만 노출하기 위한 필터링 (필요시)
        # 여기서는 전체 포함하되 상위 10개
        fig_bar = px.bar(
            df_source.head(10),
            x="기사수",
            y="출처도메인",
            orientation='h',
            title="기사를 많이 보도한 상위 도메인 Top 10",
            labels={"기사수": "보도된 기사 수", "출처도메인": "도메인"},
            color="기사수",
            color_continuous_scale="Purples",
            template="plotly_white"
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab3:
        selected_kw = st.selectbox("조회할 검색 키워드 선택", options=["전체"] + keywords_list)
        df_filtered = df_news if selected_kw == "전체" else df_news[df_news["검색키워드"] == selected_kw]
        
        st.markdown("#### 📝 뉴스 검색 기사 리스트")
        
        # 목록 출력
        for index, row in df_filtered.iterrows():
            with st.container():
                st.markdown(f"##### [{row['검색키워드']}] [{row['제목']}]({row['원본링크']})")
                st.markdown(f"**출처**: {row['출처도메인']} | **보도일시**: {row['보도시간']}")
                st.write(row['요약'])
                if row['네이버뉴스링크']:
                    st.markdown(f"[네이버 뉴스에서 보기]({row['네이버뉴스링크']})")
                st.markdown("---")
