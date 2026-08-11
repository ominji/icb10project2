import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

from embedding_utils import get_or_create_embeddings, search_similarity
from chroma_utils import initialize_chroma_db
from hybrid_search import create_bm25_index, search_hybrid
from chatbot import render_chatbot_tab, get_groq_client, SYSTEM_PROMPT_TEMPLATE
from rag_eval import evaluate_rag_response

load_dotenv()

# 페이지 기본 설정
st.set_page_config(page_title="YES24 베스트셀러 대시보드 & AI 챗봇", layout="wide", page_icon="📚")

st.title("📚 YES24 베스트셀러 종합 대시보드 & AI 서비스")
st.markdown("YES24 베스트셀러 데이터 분석, AI 유사도 검색, Groq 추천 챗봇 및 RAGAS 품질 평가를 제공합니다.")

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
CSV_PATH = os.path.join(DATA_DIR, "yes24_bestsellers.csv")

# 데이터 및 검색 자원 로드
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH)
    df['sale_price'] = pd.to_numeric(df['sale_price'], errors='coerce')
    df['review_count'] = pd.to_numeric(df['review_count'], errors='coerce')
    df['rating_grade'] = pd.to_numeric(df['rating_grade'], errors='coerce')
    return df

@st.cache_resource
def load_search_resources(df):
    model, embeddings = get_or_create_embeddings(df, DATA_DIR)
    collection = initialize_chroma_db(df, embeddings, DATA_DIR)
    bm25_index = create_bm25_index(df)
    return model, embeddings, collection, bm25_index

try:
    df = load_data()
    with st.spinner("AI 모델, BM25 인덱스 및 ChromaDB 벡터 데이터베이스를 로딩 중입니다..."):
        model, embeddings, collection, bm25_index = load_search_resources(df)
except Exception as e:
    st.error(f"데이터 또는 데이터베이스를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 사이드바 (공통 및 API 키 입력)
st.sidebar.header("🔑 API 키 설정")
env_api_key = os.getenv("GROQ_API_KEY", "")

input_api_key = st.sidebar.text_input(
    "Groq API Key 입력", 
    value=env_api_key, 
    type="password", 
    help=".env 파일의 GROQ_API_KEY가 기본으로 적용되며, UI에서 직접 입력/수정할 경우 해당 키가 우선 적용됩니다."
)

user_api_key = input_api_key.strip() if input_api_key.strip() else env_api_key

if user_api_key:
    if input_api_key.strip() and input_api_key.strip() != env_api_key:
        st.sidebar.info("🔑 UI에서 입력한 사용자 API Key가 적용되었습니다.")
    elif env_api_key:
        st.sidebar.success("✅ `.env` 파일의 GROQ_API_KEY가 적용되었습니다.")

# 탭 생성 (4개 탭)
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 종합 대시보드", 
    "🔍 도서 검색 & AI 유사도 분석", 
    "🤖 Groq AI 챗봇", 
    "🧪 RAG 품질 평가 (RAGAS)"
])

# =============================================================================
# TAB 1: 종합 대시보드
# =============================================================================
with tab1:
    st.sidebar.header("🔍 대시보드 필터")
    categories = ["전체"] + list(df['goods_sort_nm'].dropna().unique())
    selected_category = st.sidebar.selectbox("카테고리 선택", categories, key="tab1_cat")

    publishers = ["전체"] + list(df['publisher'].dropna().unique())
    selected_publisher = st.sidebar.selectbox("출판사 선택", publishers, key="tab1_pub")

    filtered_df = df.copy()
    if selected_category != "전체":
        filtered_df = filtered_df[filtered_df['goods_sort_nm'] == selected_category]
    if selected_publisher != "전체":
        filtered_df = filtered_df[filtered_df['publisher'] == selected_publisher]

    st.subheader("📊 주요 지표")
    col1, col2, col3, col4 = st.columns(4)

    total_books = len(filtered_df)
    avg_price = filtered_df['sale_price'].mean()
    avg_rating = filtered_df['rating_grade'].mean()
    avg_review = filtered_df['review_count'].mean()

    col1.metric("총 도서 수", f"{total_books:,} 권")
    col2.metric("평균 판매가", f"{avg_price:,.0f} 원" if not pd.isna(avg_price) else "N/A")
    col3.metric("평균 평점", f"{avg_rating:.1f} / 10.0" if not pd.isna(avg_rating) else "N/A")
    col4.metric("평균 리뷰 수", f"{avg_review:,.0f} 개" if not pd.isna(avg_review) else "N/A")

    st.divider()

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("🏆 상위 10위 베스트셀러")
        top_10 = filtered_df.sort_values(by='rank').head(10)
        fig_top10 = px.bar(
            top_10, 
            x='sale_price', 
            y='goods_name', 
            orientation='h',
            hover_data=['rank', 'author', 'publisher'],
            color='rating_grade',
            labels={'sale_price': '판매가(원)', 'goods_name': '도서명', 'rating_grade': '평점'}
        )
        fig_top10.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top10, use_container_width=True)

    with col_chart2:
        st.subheader("📈 카테고리 분포 (상위 10개)")
        category_counts = filtered_df['goods_sort_nm'].value_counts().reset_index()
        category_counts.columns = ['카테고리', '도서 수']
        fig_cat = px.pie(
            category_counts.head(10), 
            values='도서 수', 
            names='카테고리', 
            hole=0.4
        )
        fig_cat.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_cat, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("💰 판매가 분포")
        fig_price = px.histogram(
            filtered_df, 
            x='sale_price', 
            nbins=50, 
            marginal="box",
            labels={'sale_price': '판매가(원)'},
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig_price, use_container_width=True)

    with col_chart4:
        st.subheader("⭐ 평점 vs 리뷰 수 관계")
        fig_scatter = px.scatter(
            filtered_df, 
            x='rating_grade', 
            y='review_count', 
            hover_name='goods_name', 
            color='goods_sort_nm',
            labels={'rating_grade': '평점', 'review_count': '리뷰 수', 'goods_sort_nm': '카테고리'},
            opacity=0.7
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    st.subheader("📋 전체 도서 목록")
    st.dataframe(
        filtered_df[['rank', 'goods_name', 'author', 'publisher', 'sale_price', 'rating_grade', 'review_count', 'goods_sort_nm']],
        use_container_width=True,
        hide_index=True
    )

# =============================================================================
# TAB 2: 도서 검색 & AI 유사도 분석
# =============================================================================
with tab2:
    st.header("🔎 도서 검색 및 AI 유사도 탐색")
    st.markdown("일반 키워드 검색 또는 AI 임베딩 모델을 활용한 자연어 문장 유사도 검색을 수행할 수 있습니다.")

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        min_threshold = st.slider("최저 유사도 임계값 (Min Similarity Threshold)", min_value=0.0, max_value=1.0, value=0.3, step=0.05,
                                  help="이 값 이상의 유사도를 가진 도서만 검색 결과에 표시됩니다.")
    with col_opt2:
        top_k = st.number_input("최대 출력 도서 수 (Top K)", min_value=1, max_value=100, value=10, step=1,
                                help="검색 결과로 표출할 최대 도서 개수입니다.")

    st.divider()

    search_tab1, search_tab2 = st.tabs(["🤖 AI 문장 유사도 검색", "🔤 일반 키워드 검색"])

    with search_tab1:
        st.subheader("🤖 자연어 의미 기반 유사도 검색")
        semantic_query = st.text_input("찾고 싶은 책의 주제, 내용, 느낌을 자유롭게 입력해 보세요.", 
                                       placeholder="예: 초보자가 쉽게 따라할 수 있는 인공지능 자습서, 파이썬 업무 자동화, 가벼운 읽을거리")

        if semantic_query:
            results_df = search_similarity(semantic_query, df, embeddings, model, top_k=top_k, min_threshold=min_threshold)
            
            if not results_df.empty:
                st.success(f"검색어 **'{semantic_query}'**에 대해 유사도 {min_threshold} 이상인 결과 총 {len(results_df)}건을 찾았습니다.")
                
                display_df = results_df[['rank', 'goods_name', 'author', 'publisher', 'sale_price', 'rating_grade', 'similarity', 'goods_sort_nm', 'tags']].copy()
                display_df['similarity'] = display_df['similarity'].apply(lambda x: f"{x * 100:.1f}%")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "rank": "순위",
                        "goods_name": "도서명",
                        "author": "저자",
                        "publisher": "출판사",
                        "sale_price": st.column_config.NumberColumn("판매가(원)", format="%d원"),
                        "rating_grade": "평점",
                        "similarity": "유사도",
                        "goods_sort_nm": "카테고리",
                        "tags": "태그"
                    }
                )
            else:
                st.warning(f"유사도 {min_threshold} 이상을 만족하는 도서가 없습니다. 임계값을 낮춰보세요.")

    with search_tab2:
        st.subheader("🔤 도서명/저자/출판사/태그 키워드 검색")
        keyword = st.text_input("검색할 단어를 입력하세요.", placeholder="예: 클로드, 엑셀, 파이썬, 한빛미디어")

        if keyword:
            kw = keyword.strip().lower()
            mask = (
                df['goods_name'].astype(str).str.lower().str.contains(kw) |
                df['goods_name_sub'].astype(str).str.lower().str.contains(kw) |
                df['author'].astype(str).str.lower().str.contains(kw) |
                df['publisher'].astype(str).str.lower().str.contains(kw) |
                df['tags'].astype(str).str.lower().str.contains(kw)
            )
            kw_results = df[mask].head(top_k)

            if not kw_results.empty:
                st.success(f"키워드 **'{keyword}'** 검색 결과 총 {len(kw_results)}건 (상위 {len(kw_results)}개 표시):")
                st.dataframe(
                    kw_results[['rank', 'goods_name', 'author', 'publisher', 'sale_price', 'rating_grade', 'review_count', 'goods_sort_nm']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning(f"키워드 **'{keyword}'**에 일치하는 도서가 없습니다.")

    st.divider()
    
    st.subheader("🌐 Google Embedding Projector 시각화용 TSV 파일")
    st.markdown("임베딩 결과를 [Google Embedding Projector](https://projector.tensorflow.org/)에 업로드하여 시각화할 수 있습니다.")
    
    tensors_file = os.path.join(DATA_DIR, "tensors.tsv")
    metadata_file = os.path.join(DATA_DIR, "metadata.tsv")
    
    col_dl1, col_dl2 = st.columns(2)
    if os.path.exists(tensors_file) and os.path.exists(metadata_file):
        with open(tensors_file, "rb") as f:
            col_dl1.download_button("📥 tensors.tsv (임베딩 텐서) 다운로드", f, file_name="tensors.tsv", mime="text/tab-separated-values")
        with open(metadata_file, "rb") as f:
            col_dl2.download_button("📥 metadata.tsv (도서 메타데이터) 다운로드", f, file_name="metadata.tsv", mime="text/tab-separated-values")

# =============================================================================
# TAB 3: Groq AI 챗봇
# =============================================================================
with tab3:
    render_chatbot_tab(df, model, embeddings, collection, bm25_index, user_api_key)

# =============================================================================
# TAB 4: RAG 품질 평가 (RAGAS)
# =============================================================================
with tab4:
    st.header("🧪 RAGAS 기반 RAG 챗봇 품질 자동 평가")
    st.markdown("""
    **RAGAS(Retrieval-Augmented Generation Assessment)** 프레임워크 핵심 3대 지표를 이용해 RAG 파이프라인의 성능을 평가합니다:
    - **Faithfulness (충실도)**: 생성된 답변이 검색된 도서 문맥에 충실하며 할루시네이션(환각)이 없는지 검증
    - **Answer Relevance (답변 관련성)**: 생성된 답변이 사용자의 질문 의도를 정확하게 해결하는지 검증
    - **Context Relevance (문맥 정확도)**: RAG로 검색된 베스트셀러 도서들이 질문과 적절하게 매칭되었는지 검증
    """)

    client = get_groq_client(user_api_key)
    if not client:
        st.warning("⚠️ Groq API Key가 설정되지 않았습니다. 사이드바에서 API Key를 설정해야 평가를 실행할 수 있습니다.")
    else:
        st.subheader("📋 벤치마크 샘플 평가 실행")
        sample_queries = [
            "초보자가 읽기 쉬운 파이썬 입문 책 추천해줘",
            "클로드 코드로 개발하는 AI 에이전틱 관련 책 있어?",
            "직장인을 위한 엑셀 실무 및 업무 자동화 책",
            "조선시대 역사 소설 알려줘" # 일부러 베스트셀러에 적은 쿼리로 테스트
        ]

        selected_query = st.selectbox("테스트할 질문을 선택하거나 직접 입력하세요:", sample_queries)
        custom_query = st.text_input("직접 입력할 질문 (선택 사항):", placeholder="예: 구글 제미나이 활용법 책 추천해줘")

        eval_query = custom_query.strip() if custom_query.strip() else selected_query

        if st.button("🚀 선택한 쿼리로 RAGAS 품질 평가 실행"):
            with st.spinner("1. RAG 하이브리드 도서 검색 진행 중..."):
                results_list, context_str = search_hybrid(
                    query=eval_query, df=df, embeddings=embeddings, model=model,
                    bm25_index=bm25_index, top_k=5, min_threshold=0.2, alpha=0.5
                )

            with st.spinner("2. Groq LLM 대답 생성 중..."):
                sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context_str)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": eval_query}],
                    temperature=0.3
                )
                generated_answer = completion.choices[0].message.content

            with st.spinner("3. RAGAS 3대 지표 LLM-as-a-Judge 평가 수행 중..."):
                eval_res = evaluate_rag_response(client, eval_query, context_str, generated_answer)

            st.divider()

            # 평가 결과 시각화
            st.subheader("📊 RAGAS 평가 결과 리포트")
            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            c_m1.metric("종합 RAG Score", f"{eval_res.get('overall_score')} 점")
            c_m2.metric("Faithfulness (충실도)", f"{eval_res.get('faithfulness')} 점")
            c_m3.metric("Answer Relevance (관련성)", f"{eval_res.get('answer_relevance')} 점")
            c_m4.metric("Context Relevance (문맥수준)", f"{eval_res.get('context_relevance')} 점")

            col_radar, col_detail = st.columns([1, 1])

            with col_radar:
                # 레이더 차트 시각화
                categories_r = ['Faithfulness', 'Answer Relevance', 'Context Relevance']
                scores_r = [eval_res.get('faithfulness'), eval_res.get('answer_relevance'), eval_res.get('context_relevance')]

                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=scores_r + [scores_r[0]],
                    theta=categories_r + [categories_r[0]],
                    fill='toself',
                    name='RAGAS Score',
                    line_color='#636EFA'
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    title="RAGAS 지표 레이더 차트"
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            with col_detail:
                st.markdown("##### 📝 챗봇 답변 및 평가 심층 소평")
                st.info(f"**💡 평가 사유**: {eval_res.get('reasoning')}")
                
                with st.expander("🔍 생성된 챗봇 답변 확인"):
                    st.write(generated_answer)
                
                with st.expander("📚 검색된 RAG 도서 문맥 확인"):
                    st.text(context_str)
