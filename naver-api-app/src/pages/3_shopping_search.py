import streamlit as st
import pandas as pd
import re
import plotly.express as px
from utils import search_naver, init_naver_credentials

# API 인증키 및 공통 세션 초기화
init_naver_credentials()

st.set_page_config(page_title="쇼핑 검색 분석", layout="wide")

st.markdown("<h2 style='color: #00C73C;'>📦 네이버 쇼핑 상품 검색 및 가격 분석</h2>", unsafe_allow_html=True)
st.markdown("네이버 쇼핑 검색 API를 통해 입력된 키워드들의 실제 판매 상품 정보를 수집하고 가격을 분석합니다.")
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
    options=["sim", "date", "asc", "dsc"],
    format_func=lambda x: "유사도순" if x == "sim" else "날짜순" if x == "date" else "가격 오름차순" if x == "asc" else "가격 내림차순"
)

# HTML 태그 제거 함수
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# 데이터 수집 진행
all_items = []
with st.spinner("네이버 쇼핑 상품 데이터를 수집하는 중..."):
    for kw in keywords_list:
        data, error = search_naver(
            client_id=client_id,
            client_secret=client_secret,
            api_type="shop",
            query=kw,
            display=50,
            sort=sort_option
        )
        if error:
            st.error(f"'{kw}' 검색 실패: {error}")
        else:
            items = data.get("items", [])
            for item in items:
                # 데이터 전처리
                try:
                    lprice = int(item.get("lprice", 0)) if item.get("lprice") else 0
                except ValueError:
                    lprice = 0
                    
                all_items.append({
                    "검색키워드": kw,
                    "상품명": remove_html_tags(item.get("title", "")),
                    "최저가": lprice,
                    "판매처": item.get("mallName", "알수없음"),
                    "브랜드": item.get("brand", "알수없음"),
                    "제조사": item.get("maker", "알수없음"),
                    "링크": item.get("link", ""),
                    "이미지": item.get("image", "")
                })

if not all_items:
    st.info("수집된 상품 정보가 없습니다.")
else:
    df_shop = pd.DataFrame(all_items)
    
    # 1. 요약 통계 카드
    st.markdown("### 📋 수집 요약")
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    sum_col1.metric("총 수집 상품 수", f"{len(df_shop)} 개")
    sum_col2.metric("평균 가격", f"{int(df_shop['최저가'].mean()):,} 원")
    sum_col3.metric("최고 가격", f"{df_shop['최저가'].max():,} 원")
    
    st.markdown("---")
    
    # 2. 시각화 탭
    tab1, tab2, tab3 = st.tabs(["💵 가격 분포 및 비교", "🏬 주요 판매처 분포", "🔍 상품 상세 데이터"])
    
    with tab1:
        # 키워드별 가격 박스플롯
        st.markdown("#### 키워드별 상품 가격 분포 (Box Plot)")
        fig_box = px.box(
            df_shop[df_shop['최저가'] > 0], 
            x="검색키워드", 
            y="최저가", 
            color="검색키워드",
            points="all",
            title="키워드별 최저가 분포 비교",
            labels={"최저가": "가격 (원)"},
            template="plotly_white"
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
        # 키워드별 평균 가격
        st.markdown("#### 키워드별 평균 가격 비교")
        df_avg = df_shop[df_shop['최저가'] > 0].groupby("검색키워드")["최저가"].mean().reset_index()
        fig_bar = px.bar(
            df_avg, 
            x="검색키워드", 
            y="최저가", 
            color="검색키워드",
            text="최저가",
            title="키워드별 평균 가격",
            labels={"최저가": "평균 가격 (원)"},
            template="plotly_white"
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f}원', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab2:
        # 판매처별 분포
        st.markdown("#### 전체 판매처 TOP 10 분포")
        df_mall = df_shop["판매처"].value_counts().reset_index()
        df_mall.columns = ["판매처", "상품수"]
        
        fig_pie = px.pie(
            df_mall.head(10), 
            values="상품수", 
            names="판매처", 
            title="상위 10개 판매처 점유율",
            template="plotly_white",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # 판매처별 상품 수 테이블
        st.dataframe(df_mall, use_container_width=True)
        
    with tab3:
        # 검색어 필터링
        selected_kw = st.selectbox("조회할 검색 키워드 선택", options=["전체"] + keywords_list)
        df_filtered = df_shop if selected_kw == "전체" else df_shop[df_shop["검색키워드"] == selected_kw]
        
        # 테이블 내 이미지 렌더링을 위한 가공
        st.markdown("#### 수집된 상품 목록")
        
        # 썸네일 이미지 및 링크를 HTML형태로 렌더링
        df_display = df_filtered.copy()
        df_display["가격(원)"] = df_display["최저가"].map(lambda x: f"{x:,}")
        
        # streamlit 테이블로 보기좋게 정리
        st.dataframe(
            df_display[["검색키워드", "상품명", "가격(원)", "판매처", "브랜드", "제조사", "링크"]],
            use_container_width=True
        )
        
        # 카드 형태로 상위 10개 상품 썸네일 보기
        st.markdown("#### 🖼️ 상위 상품 갤러리")
        gallery_cols = st.columns(5)
        gallery_items = df_filtered.head(10).to_dict('records')
        for idx, item in enumerate(gallery_items):
            col_idx = idx % 5
            with gallery_cols[col_idx]:
                if item["이미지"]:
                    st.image(item["이미지"], use_container_width=True)
                st.markdown(f"**[{item['검색키워드']}]**")
                st.markdown(f"[{item['상품명'][:30]}...]({item['링크']})")
                st.markdown(f"**가격**: {item['최저가']:,}원")
                st.caption(f"판매처: {item['판매처']}")
                st.markdown("---")
