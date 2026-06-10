import streamlit as st
import pandas as pd
import re
import plotly.express as px
from utils import search_naver, init_naver_credentials

# API 인증키 및 공통 세션 초기화
init_naver_credentials()

st.set_page_config(page_title="블로그 검색 분석", layout="wide")

st.markdown("<h2 style='color: #00C73C;'>📝 네이버 블로그 검색 분석</h2>", unsafe_allow_html=True)
st.markdown("네이버 블로그 검색 API를 통해 입력된 키워드와 관련된 최신 블로그 게시글 정보를 수집하고 추이를 분석합니다.")
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

all_posts = []
with st.spinner("네이버 블로그 포스트 데이터를 수집하는 중..."):
    for kw in keywords_list:
        data, error = search_naver(
            client_id=client_id,
            client_secret=client_secret,
            api_type="blog",
            query=kw,
            display=50,
            sort=sort_option
        )
        if error:
            st.error(f"'{kw}' 블로그 검색 실패: {error}")
        else:
            items = data.get("items", [])
            for item in items:
                # postdate 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
                postdate = item.get("postdate", "")
                if len(postdate) == 8:
                    formatted_date = f"{postdate[:4]}-{postdate[4:6]}-{postdate[6:]}"
                else:
                    formatted_date = postdate
                    
                all_posts.append({
                    "검색키워드": kw,
                    "제목": remove_html_tags(item.get("title", "")),
                    "요약": remove_html_tags(item.get("description", "")),
                    "작성일": formatted_date,
                    "블로거명": item.get("bloggername", "알수없음"),
                    "포스트링크": item.get("link", ""),
                    "블로그링크": item.get("bloggerlink", "")
                })

if not all_posts:
    st.info("수집된 블로그 포스트 정보가 없습니다.")
else:
    df_blog = pd.DataFrame(all_posts)
    
    # 1. 요약 메트릭
    st.markdown("### 📋 수집 요약")
    sum_col1, sum_col2 = st.columns(2)
    sum_col1.metric("총 수집 블로그 포스트 수", f"{len(df_blog)} 개")
    sum_col2.metric("고유 블로거 수", f"{df_blog['블로거명'].nunique()} 명")
    
    st.markdown("---")
    
    # 2. 분석 탭
    tab1, tab2, tab3 = st.tabs(["📅 작성일별 트렌드", "👤 영향력 있는 블로거", "📋 수집 데이터 목록"])
    
    with tab1:
        st.markdown("#### 블로그 포스팅 일자별 추이")
        # 날짜별 포스팅 수 집계
        df_blog['작성일'] = pd.to_datetime(df_blog['작성일'], errors='coerce')
        df_date = df_blog.groupby(["작성일", "검색키워드"]).size().reset_index(name="포스팅수")
        
        # 유효한 날짜만 필터링
        df_date = df_date.dropna(subset=['작성일']).sort_values('작성일')
        
        if df_date.empty:
            st.info("작성일자 데이터가 불완전하여 추이 차트를 생성할 수 없습니다.")
        else:
            fig_line = px.line(
                df_date,
                x="작성일",
                y="포스팅수",
                color="검색키워드",
                title="일자별 블로그 작성량 비교 (수집 데이터 기준)",
                labels={"포스팅수": "작성 게시글 수"},
                template="plotly_white"
            )
            fig_line.update_layout(hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
            
    with tab2:
        st.markdown("#### 상위 활성 블로거 TOP 10 (포스트 언급 빈도)")
        df_blogger = df_blog["블로거명"].value_counts().reset_index()
        df_blogger.columns = ["블로거명", "작성글수"]
        
        fig_bar = px.bar(
            df_blogger.head(10),
            x="작성글수",
            y="블로거명",
            orientation='h',
            title="언급 빈도가 높은 블로거 Top 10",
            labels={"작성글수": "수집된 포스팅 수", "블로거명": "블로거 이름"},
            color="작성글수",
            color_continuous_scale="Viridis",
            template="plotly_white"
        )
        # y축 반전하여 큰 값이 위로 올라오게 설정
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab3:
        selected_kw = st.selectbox("조회할 검색 키워드 선택", options=["전체"] + keywords_list)
        df_filtered = df_blog if selected_kw == "전체" else df_blog[df_blog["검색키워드"] == selected_kw]
        
        st.markdown("#### 📝 블로그 검색 포스팅 리스트")
        # 포스팅 보기 편하게 가공
        df_disp = df_filtered.copy()
        df_disp['작성일'] = df_disp['작성일'].dt.strftime('%Y-%m-%d')
        
        # 목록 출력
        for index, row in df_disp.iterrows():
            with st.container():
                st.markdown(f"##### [{row['검색키워드']}] [{row['제목']}]({row['포스트링크']})")
                st.markdown(f"**작성일**: {row['작성일']} | **블로거**: [{row['블로거명']}]({row['블로그링크']})")
                st.write(row['요약'])
                st.markdown("---")
