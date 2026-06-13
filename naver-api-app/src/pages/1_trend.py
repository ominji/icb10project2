import streamlit as st
import pandas as pd
import plotly.express as px
from utils import get_search_trend, init_naver_credentials, inject_custom_css

# API 인증키 및 공통 세션 초기화
init_naver_credentials()
inject_custom_css()

st.set_page_config(page_title="검색어 트렌드 분석", layout="wide")

st.markdown("<h2 style='color: #03C75A;'>📈 네이버 검색어 트렌드 분석</h2>", unsafe_allow_html=True)
st.markdown("네이버 통합 검색어 트렌드 API를 통해 입력된 키워드들의 검색 추이를 비교합니다.")
st.markdown("---")

# API 인증 키 및 검색 조건 확인
client_id = st.session_state.get("client_id", "")
client_secret = st.session_state.get("client_secret", "")
keywords_list = st.session_state.get("keywords_list", [])
start_date = st.session_state.get("start_date")
end_date = st.session_state.get("end_date")
time_unit = st.session_state.get("time_unit", "date")

if not client_id or not client_secret:
    st.warning("⚠️ naver-api-app/.env 파일에 네이버 API Client ID와 Client Secret을 먼저 입력해 주세요.")
    st.stop()

if not keywords_list:
    st.warning("⚠️ 왼쪽 사이드바 메뉴에서 최소 하나 이상의 검색어를 입력해 주세요.")
    st.stop()

# 날짜 변환
start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

with st.spinner("네이버 검색어 트렌드 데이터를 수집하는 중..."):
    data, error = get_search_trend(
        client_id=client_id,
        client_secret=client_secret,
        keywords=keywords_list,
        start_date=start_str,
        end_date=end_str,
        time_unit=time_unit
    )

if error:
    st.error(f"데이터 수집 실패: {error}")
else:
    results = data.get("results", [])
    if not results or len(results[0].get("data", [])) == 0:
        st.info("조회 기간 및 조건에 일치하는 트렌드 데이터가 없습니다.")
    else:
        # 데이터프레임 변환
        all_dfs = []
        for res in results:
            title = res.get("title")
            df_item = pd.DataFrame(res.get("data"))
            if not df_item.empty:
                df_item = df_item.rename(columns={"ratio": title})
                df_item['period'] = pd.to_datetime(df_item['period'])
                df_item = df_item.set_index('period')
                all_dfs.append(df_item)
                
        if all_dfs:
            df_trend = pd.concat(all_dfs, axis=1).sort_index().reset_index()
            
            # 메트릭 카드 시각화 (각 키워드별 최대 검색 지수 및 평균)
            st.markdown("### 📊 키워드별 요약 메트릭")
            cols = st.columns(len(keywords_list))
            for i, res in enumerate(results):
                title = res.get("title")
                df_single = pd.DataFrame(res.get("data"))
                if not df_single.empty:
                    max_val = df_single["ratio"].max()
                    avg_val = df_single["ratio"].mean()
                    max_date = df_single.loc[df_single["ratio"].idxmax(), "period"]
                    with cols[i % len(keywords_list)]:
                        st.metric(label=f"🔥 {title} 최대값", value=f"{max_val:.1f}")
                        st.caption(f"최고치 도달일: {max_date}")
                        st.text(f"평균 지수: {avg_val:.1f}")
            
            st.markdown("---")
            
            # Plotly 라인 차트 시각화
            st.markdown("### 📈 기간별 상대 검색량 추이")
            df_melted = df_trend.melt(id_vars=["period"], var_name="키워드", value_name="상대 검색 지수(%)")
            
            fig = px.line(
                df_melted, 
                x="period", 
                y="상대 검색 지수(%)", 
                color="키워드",
                title=f"검색 트렌드 추이 ({start_str} ~ {end_str})",
                labels={"period": "날짜"},
                template="plotly_white",
                color_discrete_sequence=["#03C75A", "#10B981", "#3B82F6", "#F59E0B", "#EF4444"]
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
            # 데이터 상세 테이블 제공
            st.markdown("---")
            st.markdown("### 📋 수집된 데이터 상세 (상위 30행)")
            st.dataframe(df_trend.head(30), use_container_width=True)
        else:
            st.info("데이터 변환 결과가 비어 있습니다.")
