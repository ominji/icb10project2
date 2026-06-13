import streamlit as st
import pandas as pd
import re
import plotly.express as px
from utils import search_naver, init_naver_credentials, inject_custom_css

# API 인증키 및 공통 세션 초기화
init_naver_credentials()
inject_custom_css()

st.set_page_config(page_title="카페글 검색 분석", layout="wide")

st.markdown("<h2 style='color: #03C75A;'>☕ 네이버 카페글 검색 분석</h2>", unsafe_allow_html=True)
st.markdown("네이버 카페글 검색 API를 통해 입력된 키워드와 관련된 전체 공개 카페 게시글을 수집하고 커뮤니티 트렌드를 분석합니다.")
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

# HTML 태그 제거 함수
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

all_cafe_posts = []
with st.spinner("네이버 카페글 데이터를 수집하는 중..."):
    for kw in keywords_list:
        data, error = search_naver(
            client_id=client_id,
            client_secret=client_secret,
            api_type="cafe",
            query=kw,
            display=50,
            sort=sort_option
        )
        if error:
            st.error(f"'{kw}' 카페 검색 실패: {error}")
        else:
            items = data.get("items", [])
            for item in items:
                all_cafe_posts.append({
                    "검색키워드": kw,
                    "제목": remove_html_tags(item.get("title", "")),
                    "요약": remove_html_tags(item.get("description", "")),
                    "카페명": item.get("cafename", "알수없음"),
                    "포스트링크": item.get("link", ""),
                    "카페주소": item.get("cafeurl", "")
                })

if not all_cafe_posts:
    st.info("수집된 카페글 정보가 없습니다.")
else:
    df_cafe = pd.DataFrame(all_cafe_posts)
    
    # 1. 요약 메트릭
    st.markdown("### 📋 수집 요약")
    sum_col1, sum_col2 = st.columns(2)
    sum_col1.metric("총 수집 카페글 수", f"{len(df_cafe)} 개")
    sum_col2.metric("고유 카페 커뮤니티 수", f"{df_cafe['카페명'].nunique()} 개")
    
    st.markdown("---")
    
    # 2. 분석 탭
    tab1, tab2 = st.tabs(["☕ 주요 활성 카페", "📋 수집 데이터 목록"])
    
    with tab1:
        st.markdown("#### 상위 언급 카페 TOP 10 (커뮤니티별 언급 빈도)")
        df_community = df_cafe["카페명"].value_counts().reset_index()
        df_community.columns = ["카페명", "작성글수"]
        
        fig_bar = px.bar(
            df_community.head(10),
            x="작성글수",
            y="카페명",
            orientation='h',
            title="언급 빈도가 높은 카페 커뮤니티 Top 10",
            labels={"작성글수": "수집된 카페글 수", "카페명": "카페 이름"},
            color="작성글수",
            color_continuous_scale="Greens",
            template="plotly_white"
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # 키워드별 카페글 비율
        st.markdown("#### 키워드별 수집 게시글 비중")
        df_kw_ratio = df_cafe["검색키워드"].value_counts().reset_index()
        df_kw_ratio.columns = ["검색키워드", "게시글수"]
        fig_pie = px.pie(
            df_kw_ratio,
            values="게시글수",
            names="검색키워드",
            title="수집된 데이터 중 키워드별 게시글 비중",
            template="plotly_white",
            hole=0.4,
            color_discrete_sequence=["#03C75A", "#10B981", "#3B82F6", "#F59E0B", "#EF4444"]
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with tab2:
        selected_kw = st.selectbox("조회할 검색 키워드 선택", options=["전체"] + keywords_list)
        df_filtered = df_cafe if selected_kw == "전체" else df_cafe[df_cafe["검색키워드"] == selected_kw]
        
        st.markdown("#### 📝 카페글 검색 게시글 리스트")
        
        # 목록 출력
        for index, row in df_filtered.iterrows():
            with st.container():
                st.markdown(f"##### [{row['검색키워드']}] [{row['제목']}]({row['포스트링크']})")
                st.markdown(f"**카페명**: [{row['카페명']}]({row['카페주소']})")
                st.write(row['요약'])
                st.markdown("---")
