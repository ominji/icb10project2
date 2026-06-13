import streamlit as st
import pandas as pd
import re
import html
from urllib.parse import urlparse
import sys
import os

# 부모 폴더(src)를 모듈 검색 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import plotly.express as px
from utils import search_naver, init_naver_credentials, inject_custom_css

# API 인증키 및 공통 세션 초기화
init_naver_credentials()
inject_custom_css()

st.set_page_config(page_title="뉴스 검색 분석", layout="wide")

st.markdown("<h2 style='color: #03C75A;'>📰 네이버 뉴스 검색 분석</h2>", unsafe_allow_html=True)
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
    
    # 데이터 변경 시 AI 분석 결과 초기화
    if "news_df_json" not in st.session_state or st.session_state["news_df_json"] != df_news.to_json():
        st.session_state["news_df_json"] = df_news.to_json()
        st.session_state["news_analysis_results"] = None
        
    # 1. 요약 메트릭
    st.markdown("### 📋 수집 요약")
    sum_col1, sum_col2 = st.columns(2)
    sum_col1.metric("총 수집 뉴스 기사 수", f"{len(df_news)} 개")
    sum_col2.metric("고유 출처(도메인) 수", f"{df_news['출처도메인'].nunique()} 개")
    
    st.markdown("---")
    
    # 2. 분석 탭
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 보도 시간대별 분석", 
        "📰 주요 언론 채널(도메인) 분석", 
        "📋 뉴스 기사 목록",
        "🧠 AI 감성/여론 분석",
        "☁️ 핵심 키워드 워드클라우드"
    ])
    
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
                template="plotly_white",
                color_discrete_sequence=["#03C75A", "#10B981", "#3B82F6", "#F59E0B", "#EF4444"]
            )
            fig_line.update_layout(hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
            
    with tab2:
        st.markdown("#### 주요 뉴스 출처 Top 10 (도메인 기준)")
        df_source = df_news["출처도메인"].value_counts().reset_index()
        df_source.columns = ["출처도메인", "기사수"]
        
        fig_bar = px.bar(
            df_source.head(10),
            x="기사수",
            y="출처도메인",
            orientation='h',
            title="기사를 많이 보도한 상위 도메인 Top 10",
            labels={"기사수": "보도된 기사 수", "출처도메인": "도메인"},
            color="기사수",
            color_continuous_scale="Greens",
            template="plotly_white"
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with tab3:
        selected_kw = st.selectbox("조회할 검색 키워드 선택", options=["전체"] + keywords_list)
        df_filtered = df_news if selected_kw == "전체" else df_news[df_news["검색키워드"] == selected_kw]
        
        st.markdown("#### 📝 뉴스 검색 기사 리스트")
        
        analysis_results = st.session_state.get("news_analysis_results")
        doc_analyses = {}
        if analysis_results and "document_analyses" in analysis_results:
            doc_analyses = {item["id"]: item for item in analysis_results["document_analyses"]}
            
        # 목록 출력
        for index, row in df_filtered.iterrows():
            with st.container():
                # AI 감성 분석 결과 뱃지 매핑
                sentiment_badge = ""
                ai_summary = ""
                if index in doc_analyses:
                    analysis = doc_analyses[index]
                    s_label = analysis.get("sentiment", "neutral")
                    if s_label == "positive":
                        sentiment_badge = " <span style='background-color:#E2F9E5; color:#0F7B1C; padding:2px 6px; border-radius:4px; font-size:0.8rem; font-weight:bold;'>🟢 긍정</span>"
                    elif s_label == "negative":
                        sentiment_badge = " <span style='background-color:#FDE8E8; color:#E02424; padding:2px 6px; border-radius:4px; font-size:0.8rem; font-weight:bold;'>🔴 부정</span>"
                    else:
                        sentiment_badge = " <span style='background-color:#F3F4F6; color:#4B5563; padding:2px 6px; border-radius:4px; font-size:0.8rem; font-weight:bold;'>🟡 중립</span>"
                    ai_summary = f"<div style='background-color:#F9FAFB; border-left:4px solid #03C75A; padding:8px 12px; margin-top:8px; border-radius:0 4px 4px 0; font-size:0.9rem;'><b>💡 AI 감성 요약:</b> {analysis.get('summary', '')}</div>"
                
                st.markdown(f"##### [{row['검색키워드']}] [{row['제목']}]({row['원본링크']}){sentiment_badge}", unsafe_allow_html=True)
                st.markdown(f"**출처**: {row['출처도메인']} | **보도일시**: {row['보도시간']}")
                st.write(row['요약'])
                if ai_summary:
                    st.markdown(ai_summary, unsafe_allow_html=True)
                if row['네이버뉴스링크']:
                    st.markdown(f"[네이버 뉴스에서 보기]({row['네이버뉴스링크']})")
                st.markdown("---")

    with tab4:
        st.markdown("#### 🧠 AI 기반 뉴스 여론 및 감성 분석")
        openai_key = st.session_state.get("openai_api_key", "")
        
        if not openai_key:
            st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. naver-api-app/.env 파일에 OPENAI_API_KEY를 등록해 주세요.")
        else:
            analysis_results = st.session_state.get("news_analysis_results")
            
            # 분석 실행 버튼
            if st.button("🤖 AI 감성 분석 실행 (GPT-4o-mini)", key="btn_news_analysis"):
                # 최대 30개 문서만 샘플링하여 분석 (API 사용량 및 응답 속도 최적화)
                sample_df = df_news.head(30)
                docs = sample_df[["제목", "요약"]].rename(columns={"제목": "title", "요약": "description"}).to_dict('records')
                
                with st.spinner("AI가 수집된 기사의 맥락과 감성을 심층 분석하고 있습니다... (약 5~10초 소요)"):
                    from utils import analyze_sentiment_and_keywords
                    results, error = analyze_sentiment_and_keywords(openai_key, docs)
                    if error:
                        st.error(f"분석 실패: {error}")
                    else:
                        st.session_state["news_analysis_results"] = results
                        st.success("✅ AI 감성 분석이 성공적으로 완료되었습니다!")
                        st.rerun()
            
            if analysis_results:
                ratio = analysis_results.get("sentiment_ratio", {"positive": 0, "negative": 0, "neutral": 100})
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("🟢 긍정 비율", f"{ratio.get('positive', 0)}%")
                col_m2.metric("🔴 부정 비율", f"{ratio.get('negative', 0)}%")
                col_m3.metric("🟡 중립 비율", f"{ratio.get('neutral', 0)}%")
                
                st.markdown("---")
                st.markdown("##### 📊 여론 및 감성 분포 비율")
                df_pie = pd.DataFrame({
                    "감성": ["긍정", "부정", "중립"],
                    "비율": [ratio.get("positive", 0), ratio.get("negative", 0), ratio.get("neutral", 0)]
                })
                
                fig_pie = px.pie(
                    df_pie, 
                    values="비율", 
                    names="감성", 
                    hole=0.4,
                    color="감성",
                    color_discrete_map={"긍정": "#03C75A", "부정": "#E02424", "중립": "#9CA3AF"},
                    template="plotly_white"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                st.info("💡 각 기사의 구체적인 감성 정보와 코멘트는 **'📋 뉴스 기사 목록'** 탭에서 확인할 수 있습니다.")
            else:
                st.info("상단의 'AI 감성 분석 실행' 버튼을 클릭하여 수집된 뉴스 기사의 여론 추이 및 감성 분포를 확인해 보세요.")

    with tab5:
        st.markdown("#### ☁️ 핵심 키워드 워드클라우드")
        analysis_results = st.session_state.get("news_analysis_results")
        
        if not analysis_results:
            st.info("먼저 **'🧠 AI 감성/여론 분석'** 탭에서 분석을 완료해 주세요. 분석 결과를 바탕으로 워드클라우드가 생성됩니다.")
        else:
            keywords_data = analysis_results.get("keywords", [])
            if not keywords_data:
                st.warning("분석 결과 내에 키워드 데이터가 존재하지 않습니다.")
            else:
                import os
                from wordcloud import WordCloud
                import matplotlib.pyplot as plt
                
                word_freq = {item['word']: item['weight'] for item in keywords_data}
                
                # 윈도우 한글 폰트 경로 목록
                font_paths = [
                    "C:/Windows/Fonts/malgun.ttf",       # 맑은 고딕
                    "C:/Windows/Fonts/malgunbd.ttf",     # 맑은 고딕 Bold
                    "C:/Windows/Fonts/gulim.ttc",        # 굴림
                    "C:/Windows/Fonts/batang.ttc"        # 바탕
                ]
                
                selected_font = None
                for fp in font_paths:
                    if os.path.exists(fp):
                        selected_font = fp
                        break
                        
                with st.spinner("워드클라우드를 생성하는 중..."):
                    try:
                        wc = WordCloud(
                            font_path=selected_font,
                            background_color="white",
                            width=800,
                            height=400,
                            max_words=100,
                            colormap="viridis"
                        )
                        wc.generate_from_frequencies(word_freq)
                        
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wc, interpolation="bilinear")
                        ax.axis("off")
                        st.pyplot(fig)
                        
                        st.markdown("---")
                        st.markdown("##### 📊 주요 키워드 언급 가중치 Top 15")
                        df_kw = pd.DataFrame(keywords_data).sort_values("weight", ascending=True).tail(15)
                        fig_kw = px.bar(
                            df_kw,
                            x="weight",
                            y="word",
                            orientation='h',
                            labels={"weight": "가중치 (AI 빈도 점수)", "word": "키워드"},
                            color="weight",
                            color_continuous_scale="Greens",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_kw, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"워드클라우드 생성 중 오류 발생: {str(e)}")

