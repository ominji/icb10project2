import streamlit as st
import streamlit.components.v1 as components
import urllib.parse
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
from recommender import ContentRecommender
from cf_recommender import CustomerCFRecommender

st.set_page_config(
    page_title="GitBook Documentation | 온라인 리테일 추천 & 군집 분석 대시보드",
    page_icon="📖",
    layout="wide"
)

# ------------------ GitBook 전용 커스텀 CSS 및 힌트 컴포넌트 ------------------
GITBOOK_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
  }

  /* GitBook 스타일 카드 메트릭 및 상자 */
  .gitbook-card {
    background-color: #1e2029;
    border: 1px solid #2e3244;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  /* GitBook 힌트 콜아웃 박스 (% hint style="info" %) */
  .gitbook-hint {
    border-left: 4px solid #3b82f6;
    background-color: rgba(59, 130, 246, 0.08);
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 14px 0;
    color: #e2e8f0;
    font-size: 14.5px;
    line-height: 1.6;
  }

  .gitbook-hint-tip {
    border-left: 4px solid #10b981;
    background-color: rgba(16, 185, 129, 0.08);
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 14px 0;
    color: #e2e8f0;
    font-size: 14.5px;
    line-height: 1.6;
  }

  .gitbook-hint-warning {
    border-left: 4px solid #f59e0b;
    background-color: rgba(245, 158, 11, 0.08);
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 14px 0;
    color: #e2e8f0;
    font-size: 14.5px;
    line-height: 1.6;
  }

  .gitbook-badge {
    display: inline-block;
    padding: 3px 8px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 4px;
    background-color: #334155;
    color: #94a3b8;
    margin-right: 6px;
  }
</style>
"""

def render_gitbook_hint(text: str, style: str = "info"):
    icon = "ℹ️"
    css_class = "gitbook-hint"
    if style == "tip":
        icon = "💡"
        css_class = "gitbook-hint-tip"
    elif style == "warning":
        icon = "⚠️"
        css_class = "gitbook-hint-warning"

    html = f"""
    <div class="{css_class}">
        <strong>{icon} GitBook Hint:</strong> {text}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ------------------ Mermaid 차트 렌더링 헬퍼 (GitBook 테마 적용) ------------------
def render_mermaid(code: str, height: int = 340, width_pct: int = 85):
    encoded_code = urllib.parse.quote(code.strip())
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
      <style>
        * {{
          box-sizing: border-box;
        }}
        html, body {{
          background-color: transparent;
          color: #ffffff;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          margin: 0;
          padding: 0;
          width: 100%;
          overflow: hidden;
        }}
        #container {{
          width: 100%;
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 0px;
        }}
        .mermaid {{
          width: {width_pct}% !important;
          max-width: {width_pct}% !important;
          display: flex;
          justify-content: center;
          margin: 0 auto;
        }}
        .mermaid svg {{
          width: 100% !important;
          max-width: 100% !important;
          height: auto !important;
        }}
        text {{
          font-size: 13px !important;
          font-weight: 500 !important;
        }}
        .actor {{
          font-size: 14px !important;
          font-weight: bold !important;
        }}
        .messageText {{
          font-size: 12px !important;
          font-weight: 500 !important;
        }}
      </style>
    </head>
    <body>
      <div id="container">
        <div class="mermaid" id="mermaid-target"></div>
      </div>
      <script>
        const rawCode = decodeURIComponent("{encoded_code}");
        const target = document.getElementById("mermaid-target");
        
        mermaid.initialize({{
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {{
            fontSize: '13px',
            actorFontSize: '14px',
            messageFontSize: '12px'
          }},
          flowchart: {{ useMaxWidth: true, htmlLabels: true }},
          sequence: {{ useMaxWidth: true, boxMargin: 5, noteMargin: 5, messageMargin: 30 }}
        }});

        mermaid.render('mermaid-svg', rawCode).then(res => {{
          target.innerHTML = res.svg;
          const svgEl = target.querySelector('svg');
          if (svgEl) {{
            svgEl.removeAttribute('height');
            svgEl.style.width = '100%';
            svgEl.style.height = 'auto';
            svgEl.style.maxWidth = '100%';
          }}
        }});
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)

def load_engines():
    content_rec = ContentRecommender()
    cf_rec = CustomerCFRecommender()
    return content_rec, cf_rec

@st.cache_data
def load_metrics_and_clusters():
    prod_metrics_path = 'online-retail/report/evaluation_metrics.json'
    cf_metrics_path = 'online-retail/report/cf_evaluation_metrics.json'
    clusters_path = 'online-retail/data/customer_clusters.parquet'
    clustering_eval_path = 'online-retail/report/clustering_eval.json'
    
    prod_metrics = json.load(open(prod_metrics_path, 'r')) if os.path.exists(prod_metrics_path) else None
    cf_metrics = json.load(open(cf_metrics_path, 'r')) if os.path.exists(cf_metrics_path) else None
    df_clusters = pd.read_parquet(clusters_path) if os.path.exists(clusters_path) else None
    clustering_eval = json.load(open(clustering_eval_path, 'r')) if os.path.exists(clustering_eval_path) else None
            
    return prod_metrics, cf_metrics, df_clusters, clustering_eval

def main():
    st.markdown(GITBOOK_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #2e3244; padding-bottom: 12px; margin-bottom: 20px;">
      <div>
        <span class="gitbook-badge">v2.0.0</span>
        <span class="gitbook-badge">GitBook Doc Style</span>
        <h1 style="display: inline; margin-left: 10px; font-size: 26px; font-weight: 700;">📖 Online Retail Docs & Dashboard</h1>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("추천 엔진 및 군집화 데이터를 로드 중입니다..."):
        content_rec, cf_rec = load_engines()
        prod_metrics, cf_metrics, df_clusters, clustering_eval = load_metrics_and_clusters()

    # ------------------ 메인 페이지 네비게이션 ------------------
    main_page = st.radio(
        "📌 GitBook 도큐멘테이션 섹션을 선택하세요:",
        options=["🛍️ 상품 추천 페이지", "👤 고객 맞춤 추천 페이지", "📊 고객 군집화 & RFM 분석 페이지"],
        horizontal=True,
        index=0
    )

    st.markdown("---")

    # =========================================================================
    # PAGE 1: 🛍️ 상품 페이지 (Product Recommendation)
    # =========================================================================
    if main_page == "🛍️ 상품 추천 페이지":
        st.header("🛍️ 상품 목록 및 유사 상품 콘텐츠 추천")
        render_gitbook_hint("특정 상품을 선택하면 해당 상품과 textual/semantic 유사도가 높은 유사 상품 10선을 추천합니다.", "info")

        st.sidebar.header("⚙️ 상품 추천 파라미터")
        selected_method = st.sidebar.radio(
            "상품 추천 모델 선택",
            options=["비교 보기 (TF-IDF vs 임베딩)", "TF-IDF 단독", "사전학습 임베딩 단독"],
            index=0
        )
        top_k = st.sidebar.slider("추천 상품 상위 개수 (Top-K)", 1, 30, 10, 1)
        min_threshold = st.sidebar.slider("최소 유사도 임계값 (Similarity Threshold)", 0.0, 1.0, 0.1, 0.05)

        df_prods = content_rec.df
        st.sidebar.metric("총 등록 상품 수", f"{len(df_prods):,} 개")

        tab_p1, tab_p2, tab_p3 = st.tabs([
            "🔎 상품 검색 및 유사 상품 추천",
            "📊 상품 추천 성능 평가 지표",
            "💡 콘텐츠 기반 추천 기술 아키텍처"
        ])

        with tab_p1:
            prod_options = [f"[{row['StockCode']}] {row['Description']}" for _, row in df_prods.iterrows()]
            search_kw = st.text_input("상품명 검색 (예: HEART, CAKE, BOTTLE, STAR)", "")
            
            filtered_opts = [opt for opt in prod_options if search_kw.upper() in opt.upper()] if search_kw else prod_options
            if not filtered_opts:
                st.warning("검색 조건에 일치하는 상품이 없어 전체 목록을 노출합니다.")
                filtered_opts = prod_options

            selected_option = st.selectbox("대상 상품 선택", options=filtered_opts, index=0)
            selected_code = selected_option.split("]")[0].replace("[", "").strip()
            target_prod = df_prods[df_prods['StockCode'] == selected_code].iloc[0]

            render_gitbook_hint(f"선택 상품: <strong>[{target_prod['StockCode']}] {target_prod['Description']}</strong> (총 거래 건수: {target_prod['order_count']:,}회)", "tip")

            if selected_method == "비교 보기 (TF-IDF vs 임베딩)":
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🔤 TF-IDF 기반 유사 상품")
                    res_tfidf = content_rec.recommend(selected_code, method='tfidf', top_k=top_k, min_threshold=min_threshold)
                    if res_tfidf is not None and len(res_tfidf) > 0:
                        st.dataframe(res_tfidf[['StockCode', 'Description', 'Similarity', 'OrderCount']].style.format({'Similarity': '{:.4f}'}), use_container_width=True)
                        fig1 = px.bar(res_tfidf, x='Similarity', y='Description', orientation='h', title="TF-IDF 유사도 Top-K", color='Similarity', color_continuous_scale='Blues')
                        fig1.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350)
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.warning("설정한 임계값을 만족하는 추천 상품이 없습니다.")

                with col2:
                    st.subheader("🧠 사전학습 임베딩 기반 유사 상품")
                    res_emb = content_rec.recommend(selected_code, method='embedding', top_k=top_k, min_threshold=min_threshold)
                    if res_emb is not None and len(res_emb) > 0:
                        st.dataframe(res_emb[['StockCode', 'Description', 'Similarity', 'OrderCount']].style.format({'Similarity': '{:.4f}'}), use_container_width=True)
                        fig2 = px.bar(res_emb, x='Similarity', y='Description', orientation='h', title="Sentence Embedding 유사도 Top-K", color='Similarity', color_continuous_scale='Greens')
                        fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350)
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("설정한 임계값을 만족하는 추천 상품이 없습니다.")
            else:
                m_key = 'tfidf' if selected_method == "TF-IDF 단독" else 'embedding'
                res = content_rec.recommend(selected_code, method=m_key, top_k=top_k, min_threshold=min_threshold)
                if res is not None and len(res) > 0:
                    st.dataframe(res[['StockCode', 'Description', 'Similarity', 'OrderCount']].style.format({'Similarity': '{:.4f}'}), use_container_width=True)

        with tab_p2:
            st.subheader("📈 상품 콘텐츠 추천 성능 평가 (4가지 정량 지표)")
            if prod_metrics:
                m_tfidf = prod_metrics.get('tfidf', {})
                m_emb = prod_metrics.get('embedding', {})
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("평균 유사도 (Avg Sim)", f"{m_tfidf.get('Average_Similarity',0):.3f} / {m_emb.get('Average_Similarity',0):.3f}")
                c2.metric("다양성 (ILD)", f"{m_tfidf.get('Intra_List_Diversity',0):.3f} / {m_emb.get('Intra_List_Diversity',0):.3f}")
                c3.metric("카탈로그 커버리지 (%)", f"{m_tfidf.get('Catalog_Coverage_Pct',0):.1f}% / {m_emb.get('Catalog_Coverage_Pct',0):.1f}%")
                c4.metric("신선도 (Novelty)", f"{m_tfidf.get('Novelty',0):.2f} / {m_emb.get('Novelty',0):.2f}")

        # --- 💡 콘텐츠 기반 추천 기술 아키텍처 탭 ---
        with tab_p3:
            st.subheader("💡 콘텐츠 기반 추천 시스템 기술 프로세스 및 구조")
            render_gitbook_hint("""
            <strong>콘텐츠 기반 추천(Content-based Filtering)</strong>은 입력된 타겟 상품의 텍스트 메타데이터(Description) 특성을 벡터 공간에 사상하고, 수록된 3,917개 타 상품 벡터들과의 코사인 유사도(Cosine Similarity)를 계산하여 유사도가 높은 상품을 정렬 추출하는 기술입니다.
            """, "tip")
            
            st.markdown("""
            본 시스템은 **TF-IDF (Term Frequency-Inverse Document Frequency)** 단어 희소 행렬 방식과 사전학습 딥러닝 **Sentence-Transformer (`all-MiniLM-L6-v2`)** 밀집 문장 임베딩 방식을 동시 지원합니다. TF-IDF 방식은 상품명 내 명사/단어의 희귀도와 빈도를 계산하여 정밀한 키워드 일치를 보장하며, 문장 임베딩 방식은 Transformer 인코더를 통해 단어의 표면적 철자가 달라도 '의미론적 유사성(Semantic Context)'을 추출하여 높은 의외성(Serendipity)을 제공합니다. 

            산출된 유사도 $Sim(A, B) = \\frac{\\mathbf{v}_A \\cdot \\mathbf{v}_B}{\\|\\mathbf{v}_A\\| \\|\\mathbf{v}_B\\|}$ 수치에 대해 사용자가 설정한 최소 유사도 임계값(Threshold)을 필터링하고 상위 K개를 사용자 화면에 실시간 시각화합니다.
            """)
            
            st.markdown("---")
            st.markdown("#### 1️⃣ 기술 처리 파이프라인 플로우차트 (Flowchart - Left to Right)")
            
            cbf_flow = """
flowchart LR
    A[상품 데이터] --> B[ Description 전처리 ]
    B --> C1[ TF-IDF 벡터화 ]
    B --> C2[ Sentence-Transformer ]
    C1 --> D1[ 희소 코사인 유사도 ]
    C2 --> D2[ 밀집 코사인 유사도 ]
    D1 --> E[ 타겟 상품 쿼리 ]
    D2 --> E
    E --> F[ Threshold 필터 & Top-K 정렬 ]
    F --> G[ 추천 목록 및 차트 출력 ]
"""
            render_mermaid(cbf_flow, height=180, width_pct=85)

            st.markdown("---")
            st.markdown("#### 2️⃣ 시스템 처리 시퀀스 다이어그램 (Sequence Diagram)")
            
            cbf_seq = """
sequenceDiagram
    participant User as 사용자
    participant UI as Streamlit UI
    participant Engine as Recommender Engine
    participant Matrix as Vector Matrix

    User->>UI: 1. 타겟 상품 선택
    UI->>Engine: 2. recommend(code) 요청
    Engine->>Matrix: 3. 인덱스 벡터 조회
    Matrix-->>Engine: 4. 쿼리 및 상품 벡터 반환
    Engine->>Engine: 5. 코사인 유사도 계산 및 정렬
    Engine-->>UI: 6. Top-K 결과 반환
    UI-->>User: 7. 추천 목록 렌더링
"""
            render_mermaid(cbf_seq, height=350, width_pct=80)

    # =========================================================================
    # PAGE 2: 👤 고객 페이지 (Customer Collaborative Filtering & Cluster Info)
    # =========================================================================
    elif main_page == "👤 고객 맞춤 추천 페이지":
        st.header("👤 고객 목록 및 개인 맞춤형 협업 필터링 추천 (군집 정보 연동)")
        render_gitbook_hint("고객을 선택하여 고객의 RFM 군집 세그먼트, 과거 구매 내역, 및 맞춤형 추천 상품 Top-10을 조회합니다.", "info")

        df_custs = cf_rec.df_custs

        st.subheader("📋 고객 목록 (정렬 및 검색)")
        sort_col1, sort_col2 = st.columns([2, 2])
        with sort_col1:
            sort_by = st.selectbox(
                "고객 정렬 기준 선택",
                options=["총 구매 금액(Total Spend) 높은 순", "구매 상품 종류 수(Unique Items) 많은 순", "총 구매 수량(Total Items) 많은 순", "총 주문 건수(Total Orders) 많은 순"]
            )
        with sort_col2:
            search_cust_id = st.text_input("고객 ID 검색 (예: 17850, 14646)", "")

        if sort_by == "총 구매 금액(Total Spend) 높은 순":
            df_custs_sorted = df_custs.sort_values(by='total_spend', ascending=False)
        elif sort_by == "구매 상품 종류 수(Unique Items) 많은 순":
            df_custs_sorted = df_custs.sort_values(by='unique_items_bought', ascending=False)
        elif sort_by == "총 구매 수량(Total Items) 많은 순":
            df_custs_sorted = df_custs.sort_values(by='total_items_bought', ascending=False)
        else:
            df_custs_sorted = df_custs.sort_values(by='total_orders', ascending=False)

        if search_cust_id:
            df_custs_sorted = df_custs_sorted[df_custs_sorted['CustomerID'].str.contains(search_cust_id.strip())]

        disp_cols = ['CustomerID', 'total_spend', 'unique_items_bought', 'total_items_bought', 'total_orders']
        if 'RFM_Segment' in df_custs_sorted.columns:
            disp_cols.append('RFM_Segment')
        if 'KMeans_Cluster_Name' in df_custs_sorted.columns:
            disp_cols.append('KMeans_Cluster_Name')

        st.dataframe(
            df_custs_sorted[disp_cols].head(100).style.format({'total_spend': '${:,.2f}'}),
            use_container_width=True
        )

        st.markdown("---")

        st.subheader("🎯 특정 고객 선택 및 군집 결과 & 맞춤 추천")
        cust_list = df_custs_sorted['CustomerID'].tolist()
        if not cust_list:
            st.error("조건에 일치하는 고객이 없습니다.")
            return

        selected_cust_id = st.selectbox("상세 조회 및 추천할 고객 ID 선택", options=cust_list, index=0)
        cust_row = df_custs[df_custs['CustomerID'] == selected_cust_id]
        cust_info = cust_row.iloc[0].to_dict() if len(cust_row) > 0 else {}
        
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
        col_c1.metric("고객 ID", selected_cust_id)
        col_c2.metric("총 구매 금액", f"${cust_info.get('total_spend', 0):,.2f}")
        col_c3.metric("구매 상품 종류", f"{cust_info.get('unique_items_bought', 0):,} 개")
        col_c4.metric("RFM 세그먼트", str(cust_info.get('RFM_Segment', 'N/A')))
        col_c5.metric("K-Means 군집", str(cust_info.get('KMeans_Cluster_Name', 'N/A')))

        tab_c1, tab_c2, tab_c3, tab_c4 = st.tabs([
            "🛒 고객 구매 제품 목록",
            "✨ 맞춤 추천 (TF-IDF vs 임베딩)",
            "📈 협업 필터링 성능 평가",
            "💡 협업 필터링 기술 아키텍처"
        ])

        with tab_c1:
            st.markdown(f"#### 🛍️ 고객 `[{selected_cust_id}]` 님의 과거 구매 제품 목록")
            purch_df = cf_rec.get_customer_purchases(selected_cust_id)
            st.dataframe(
                purch_df[['StockCode', 'Description', 'quantity_sum', 'spend_sum', 'order_count']].style.format({'spend_sum': '${:,.2f}'}),
                use_container_width=True
            )

        with tab_c2:
            st.markdown(f"#### ✨ 고객 `[{selected_cust_id}]` 님을 위한 미구매 추천 상품 Top-10 (군집 특성 반영)")
            col_rec1, col_rec2 = st.columns(2)
            with col_rec1:
                st.subheader("🔤 TF-IDF 유저 프로필 기반 추천")
                cf_tfidf = cf_rec.recommend_for_customer(selected_cust_id, method='tfidf', top_k=10)
                if cf_tfidf is not None and len(cf_tfidf) > 0:
                    st.dataframe(cf_tfidf[['StockCode', 'Description', 'Similarity', 'OrderCount']].style.format({'Similarity': '{:.4f}'}), use_container_width=True)
                    fig_c1 = px.bar(cf_tfidf, x='Similarity', y='Description', orientation='h', title="TF-IDF 협업 추천 유사도 Top-10", color='Similarity', color_continuous_scale='Purples')
                    fig_c1.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350)
                    st.plotly_chart(fig_c1, use_container_width=True)

            with col_rec2:
                st.subheader("🧠 문장 임베딩 유저 프로필 기반 추천")
                cf_emb = cf_rec.recommend_for_customer(selected_cust_id, method='embedding', top_k=10)
                if cf_emb is not None and len(cf_emb) > 0:
                    st.dataframe(cf_emb[['StockCode', 'Description', 'Similarity', 'OrderCount']].style.format({'Similarity': '{:.4f}'}), use_container_width=True)
                    fig_c2 = px.bar(cf_emb, x='Similarity', y='Description', orientation='h', title="Embedding 협업 추천 유사도 Top-10", color='Similarity', color_continuous_scale='Oranges')
                    fig_c2.update_layout(yaxis={'categoryorder': 'total ascending'}, height=350)
                    st.plotly_chart(fig_c2, use_container_width=True)

        with tab_c3:
            st.subheader("📊 협업 필터링 성능 평가 결과 (Holdout Evaluation)")
            if cf_metrics:
                m_tfidf_cf = cf_metrics.get('tfidf', {})
                m_emb_cf = cf_metrics.get('embedding', {})

                c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                c_m1.metric("Precision@10 (정밀도)", f"{m_tfidf_cf.get('Precision_At_10',0):.4f} / {m_emb_cf.get('Precision_At_10',0):.4f}")
                c_m2.metric("Recall@10 (재현율)", f"{m_tfidf_cf.get('Recall_At_10',0):.4f} / {m_emb_cf.get('Recall_At_10',0):.4f}")
                c_m3.metric("MAP@10 (순위 정밀도)", f"{m_tfidf_cf.get('MAP_At_10',0):.4f} / {m_emb_cf.get('MAP_At_10',0):.4f}")
                c_m4.metric("Intra-List Diversity (다양성)", f"{m_tfidf_cf.get('Intra_List_Diversity',0):.4f} / {m_emb_cf.get('Intra_List_Diversity',0):.4f}")

        # --- 💡 협업 필터링 기술 아키텍처 탭 ---
        with tab_c4:
            st.subheader("💡 고객 맞춤형 협업 필터링(Collaborative Filtering) 기술 구조")
            render_gitbook_hint("""
            <strong>유저 프로필 기반 협업 필터링(User-Profile Collaborative Recommendation)</strong> 방식을 적용하였습니다. 특정 고객 U가 과거에 구매했던 모든 상품 내역에 지출 금액 가중치를 부여하여 고차원 유저 프로필 벡터를 형성합니다.
            """, "tip")

            st.markdown("""
            $$\\mathbf{v}_U = \\frac{\\sum_{i \\in I_U} w_{U,i} \\cdot \\mathbf{x}_i}{\\sum_{i \\in I_U} w_{U,i}}$$

            이후 고객이 아직 일절 구매하지 않은(Unpurchased) 미지의 상품들을 대상으로 유저 프로필 벡터와의 코사인 유사도를 연산하여, 고객의 취향과 가장 부합하는 타겟 상품 Top-10을 개인화 추천합니다. 

            성능 평가 시에는 구매 이력이 5개 이상인 고객을 대상으로 **80% 학습(Train) / 20% 홀드아웃(Test)** 검증을 실시하여, 실제 미래에 구매한 상품을 얼마나 정밀하게 예측하는지 **Precision@10, Recall@10, MAP@10 및 다양성(ILD)** 4가지 지표로 다각도 분석합니다.
            """)

            st.markdown("---")
            st.markdown("#### 1️⃣ 협업 필터링 처리 파이프라인 플로우차트 (Flowchart - Left to Right)")
            
            cf_flow = """
flowchart LR
    A[구매 이력 DB] --> B[상품 & 지출 가중치 추출]
    B --> C1[TF-IDF 유저 프로필]
    B --> C2[임베딩 유저 프로필]
    C1 --> D[미구매 상품 탐색]
    C2 --> D
    D --> E[프로필 vs 미구매 코사인 유사도]
    E --> F[Top-10 개인화 추천]
    F --> G[Precision / Recall / MAP 검증]
"""
            render_mermaid(cf_flow, height=180, width_pct=85)

            st.markdown("---")
            st.markdown("#### 2️⃣ 시스템 처리 시퀀스 다이어그램 (Sequence Diagram)")
            
            cf_seq = """
sequenceDiagram
    participant User as 사용자
    participant UI as Streamlit UI
    participant CF as CustomerCFRecommender
    participant DB as Purchases DB

    User->>UI: 1. 고객 선택
    UI->>CF: 2. 구매내역 요청
    CF->>DB: 3. 구매상품 및 지출액 조회
    DB-->>CF: 4. 내역 및 가중치 반환
    UI->>CF: 5. recommend 요청
    CF->>CF: 6. 유저 프로필 벡터 연산
    CF->>CF: 7. 미구매 유사도 정렬
    CF-->>UI: 8. Top-10 추천 반환
    UI-->>User: 9. 맞춤 추천 렌더링
"""
            render_mermaid(cf_seq, height=350, width_pct=80)

    # =========================================================================
    # PAGE 3: 📊 고객 군집화 & RFM 분석 페이지 (확장)
    # =========================================================================
    else:
        st.header("📊 고객 RFM 군집화 분석 & 3D (원본 vs 로그변환 vs 점수) 시각화 & 실루엣 평가")
        render_gitbook_hint("Recency(최근성), Frequency(구매빈도), Monetary(구매금액) 기반 RFM 세그먼트와 K-Means 머신러닝 군집화, 그리고 군집화 실루엣 다이어그램 평가를 제공합니다.", "info")

        if df_clusters is None:
            st.warning("군집화 데이터가 로드되지 않았습니다. `cluster_analysis.py`를 먼저 실행하세요.")
            return

        tab_cl1, tab_cl2, tab_cl3, tab_cl4, tab_cl5 = st.tabs([
            "📋 RFM 세그먼트 vs K-Means 군집 비교",
            "🌐 3차원 RFM 시각화 (원본 vs 로그변환 vs 점수 3열 비교)",
            "📈 군집화 성능 평가 (엘보우 & 실루엣 분석 다이어그램)",
            "🎯 군집별 비즈니스 액션플랜",
            "💡 RFM & 군집화 기술 아키텍처"
        ])

        # ------------------ TAB 1: RFM 세그먼트 vs K-Means 군집 비교 ------------------
        with tab_cl1:
            st.subheader("📊 RFM 세그먼트별 고객 평균 특성 및 군집 분포")
            seg_summary = df_clusters.groupby('RFM_Segment').agg(
                고객수=('CustomerID', 'count'),
                평균_Recency_일=('Recency', 'mean'),
                평균_Frequency_회=('Frequency', 'mean'),
                평균_Monetary_달러=('Monetary', 'mean')
            ).reset_index()
            
            seg_summary['평균_Recency_일'] = seg_summary['평균_Recency_일'].round(1)
            seg_summary['평균_Frequency_회'] = seg_summary['평균_Frequency_회'].round(1)
            seg_summary['평균_Monetary_달러'] = seg_summary['평균_Monetary_달러'].map('${:,.2f}'.format)
            
            st.dataframe(seg_summary, use_container_width=True)

            st.markdown("### 📊 군집별 & 세그먼트별 고객 수 분포 (가로 서브플롯 시각화)")
            col_bar_1, col_bar_2 = st.columns(2)
            
            with col_bar_1:
                km_counts = df_clusters['KMeans_Cluster_Name'].value_counts().reset_index()
                km_counts.columns = ['KMeans_Cluster_Name', 'Customer_Count']
                fig_km_bar = px.bar(
                    km_counts, x='KMeans_Cluster_Name', y='Customer_Count', color='KMeans_Cluster_Name',
                    text='Customer_Count', title="K-Means 군집별 고객(데이터) 수 분포",
                    labels={'KMeans_Cluster_Name': 'K-Means 군집', 'Customer_Count': '고객 수 (명)'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_km_bar.update_traces(textposition='outside')
                fig_km_bar.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_km_bar, use_container_width=True)

            with col_bar_2:
                seg_counts = df_clusters['RFM_Segment'].value_counts().reset_index()
                seg_counts.columns = ['RFM_Segment', 'Customer_Count']
                fig_seg_bar = px.bar(
                    seg_counts, x='RFM_Segment', y='Customer_Count', color='RFM_Segment',
                    text='Customer_Count', title="RFM 세그먼트별 고객(데이터) 수 분포",
                    labels={'RFM_Segment': 'RFM 세그먼트', 'Customer_Count': '고객 수 (명)'},
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_seg_bar.update_traces(textposition='outside')
                fig_seg_bar.update_layout(showlegend=False, height=400)
                fig_seg_bar.update_xaxes(tickangle=-15)
                st.plotly_chart(fig_seg_bar, use_container_width=True)

            col_cl_a, col_cl_b = st.columns(2)
            with col_cl_a:
                fig_seg_pie = px.pie(df_clusters, names='RFM_Segment', title="RFM 세그먼트별 고객 수 비율", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig_seg_pie, use_container_width=True)

            with col_cl_b:
                fig_km_pie = px.pie(df_clusters, names='KMeans_Cluster_Name', title="K-Means 머신러닝 군집별 고객 수 비율", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_km_pie, use_container_width=True)

            st.markdown("### 🔀 RFM 세그먼트와 K-Means 군집 크로스 교차표")
            cross_tab = pd.crosstab(df_clusters['RFM_Segment'], df_clusters['KMeans_Cluster_Name'], margins=True)
            st.dataframe(cross_tab, use_container_width=True)

        # ------------------ TAB 2: 3차원 RFM 시각화 (원본 vs 로그변환 vs 점수 3열 비교) ------------------
        with tab_cl2:
            st.subheader("🌐 3차원(3D) RFM 산점도 시각화 (원본 vs 로그변환 vs 점수 3열 서브플롯 비교)")
            st.write("1열은 **원본 RFM 실제 수치**, 2열은 **로그 변환된 RFM 수치(`Log(1 + RFM)`)**, 3열은 **1~5점 분위수 점수**를 나타내며, 지정한 세그먼트/군집별 색상이 적용됩니다.")

            color_target = st.radio(
                "3D 그래프 색상 구분 기준 선택:",
                options=["RFM 세그먼트 (RFM_Segment)", "K-Means 군집 (KMeans_Cluster_Name)"],
                horizontal=True
            )
            color_col = 'RFM_Segment' if color_target == "RFM 세그먼트 (RFM_Segment)" else 'KMeans_Cluster_Name'

            col_3d_1, col_3d_2, col_3d_3 = st.columns(3)

            with col_3d_1:
                st.markdown("#### 1️⃣ [원본 RFM 수치] 3D 그래프")
                fig_3d_raw = px.scatter_3d(
                    df_clusters,
                    x='Recency', y='Frequency', z='Monetary',
                    color=color_col,
                    hover_data=['CustomerID', 'R_Score', 'F_Score', 'M_Score'],
                    title="원본 RFM 실제 수치",
                    opacity=0.8, height=520
                )
                fig_3d_raw.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                st.plotly_chart(fig_3d_raw, use_container_width=True)

            with col_3d_2:
                st.markdown("#### 2️⃣ [로그 변환 RFM 수치] 3D 그래프")
                fig_3d_log = px.scatter_3d(
                    df_clusters,
                    x='Log_Recency', y='Log_Frequency', z='Log_Monetary',
                    color=color_col,
                    hover_data=['CustomerID', 'Recency', 'Frequency', 'Monetary'],
                    title="로그 변환 RFM 수치 Log(1+RFM)",
                    opacity=0.8, height=520
                )
                fig_3d_log.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                st.plotly_chart(fig_3d_log, use_container_width=True)

            with col_3d_3:
                st.markdown("#### 3️⃣ [RFM 분위수 점수] 3D 그래프")
                fig_3d_score = px.scatter_3d(
                    df_clusters,
                    x='R_Score', y='F_Score', z='M_Score',
                    color=color_col,
                    hover_data=['CustomerID', 'Recency', 'Frequency', 'Monetary'],
                    title="RFM 분위수 점수 (1~5점)",
                    opacity=0.8, height=520
                )
                fig_3d_score.update_layout(margin=dict(l=0, r=0, b=0, t=30))
                st.plotly_chart(fig_3d_score, use_container_width=True)

        # ------------------ TAB 3: 군집화 성능 평가 (엘보우 & 실루엣 분석) ------------------
        with tab_cl3:
            st.subheader("📈 K-Means 군집 분석 성능 평가 및 실루엣 다이어그램 분석")
            st.write("하단 서브플롯에서 **엘보우 기법(Inertia)**, **K별 평균 실루엣 점수**, 그리고 **군집별 실루엣 계수 분포 다이어그램**을 비교 평가합니다.")

            if clustering_eval:
                k_list = clustering_eval.get('k_list', [])
                inertia = clustering_eval.get('inertia', [])
                sil_avg = clustering_eval.get('silhouette_avg', [])
                overall_sil_mean = clustering_eval.get('overall_silhouette_mean', 0.35)

                col_ev1, col_ev2 = st.columns(2)

                with col_ev1:
                    st.markdown("#### 📉 1. 엘보우 메소드 (Elbow Method - Inertia/WCSS)")
                    fig_elbow = px.line(
                        x=k_list, y=inertia, markers=True,
                        title="K 값 변화에 따른 Inertia (WCSS) 감소 그래프",
                        labels={'x': 'Number of Clusters (K)', 'y': 'Inertia (WCSS)'}
                    )
                    fig_elbow.add_vline(x=4, line_dash="dash", line_color="red", annotation_text="Selected K=4")
                    fig_elbow.update_traces(line_color='#1f77b4', marker=dict(size=8))
                    st.plotly_chart(fig_elbow, use_container_width=True)

                with col_ev2:
                    st.markdown("#### 📊 2. K별 평균 실루엣 계수 (Average Silhouette Score per K)")
                    fig_sil_k = px.line(
                        x=k_list, y=sil_avg, markers=True,
                        title="K 값 변화에 따른 평균 실루엣 점수 그래프",
                        labels={'x': 'Number of Clusters (K)', 'y': 'Average Silhouette Score'}
                    )
                    fig_sil_k.add_vline(x=4, line_dash="dash", line_color="red", annotation_text="Selected K=4")
                    fig_sil_k.update_traces(line_color='#2ca02c', marker=dict(size=8))
                    st.plotly_chart(fig_sil_k, use_container_width=True)

            st.markdown("---")

            st.markdown("#### 🎨 3. 군집별 개별 실루엣 계수 분포 다이어그램 (Silhouette Diagram by Cluster)")
            df_sil_sorted = df_clusters.sort_values(by=['KMeans_Cluster', 'Silhouette_Value'], ascending=[True, True]).reset_index(drop=True)
            df_sil_sorted['y_idx'] = np.arange(len(df_sil_sorted))

            fig_sil_diag = go.Figure()
            cluster_names = sorted(df_sil_sorted['KMeans_Cluster_Name'].unique())
            colors = px.colors.qualitative.Plotly

            for idx, c_name in enumerate(cluster_names):
                c_data = df_sil_sorted[df_sil_sorted['KMeans_Cluster_Name'] == c_name]
                fig_sil_diag.add_trace(go.Bar(
                    x=c_data['Silhouette_Value'],
                    y=c_data['y_idx'],
                    orientation='h',
                    name=c_name,
                    marker_color=colors[idx % len(colors)],
                    hovertext=c_data['CustomerID'].apply(lambda cid: f"Customer: {cid}")
                ))

            overall_sil_val = float(df_clusters['Silhouette_Value'].mean())
            fig_sil_diag.add_vline(
                x=overall_sil_val, line_dash="dash", line_color="red", line_width=2,
                annotation_text=f"전체 평균 실루엣: {overall_sil_val:.3f}", annotation_position="top right"
            )

            fig_sil_diag.update_layout(
                title="K=4 군집별 실루엣 계수 분포 다이어그램 (Silhouette Plot)",
                xaxis_title="Silhouette Coefficient Value",
                yaxis_title="Customer Sample Index (Grouped by Cluster)",
                showlegend=True, height=500, bargap=0.0
            )
            fig_sil_diag.update_yaxes(showticklabels=False)
            st.plotly_chart(fig_sil_diag, use_container_width=True)

        # ------------------ TAB 4: 군집별 비즈니스 액션플랜 ------------------
        with tab_cl4:
            st.subheader("🎯 군집별 맞춤형 비즈니스 액션플랜 (Business Action Plans)")
            st.markdown("""
            ### 👑 1. Champions (최우수 고객)
            - **고객 특성**: 최근 구매일(Recency)이 매우 짧고, 구매 횟수(Frequency) 및 지출액(Monetary)이 상위 20%인 핵심 VVIP 고객군.
            - **비즈니스 액션플랜**:
              - **VIP 전용 얼리버드 혜택**: 신제품 출시 시 VIP 전용 사전 구매 기회 제공
              - **전담 로열티 케어**: 무료 배송/반품 혜택 및 연말 프리미엄 감사 기프트 증정
              - **추천 전략**: 신규 럭셔리 카테고리 및 고단가 상품 추천

            ---

            ### 💎 2. Loyal Customers (충성 고객)
            - **고객 특성**: 정기적으로 꾸준히 방문하여 구매하지만 최상위 단가에는 다다르지 않은 안정적 결제 그룹.
            - **비즈니스 액션플랜**:
              - **업셀링 (Upselling)**: 구매 금액 목표 달성 시 추가 리워드 쿠폰 증정
              - **크로스셀링 (Cross-selling)**: 자주 찾는 상품과 연계된 부속/악세사리 맞춤 추천

            ---

            ### 🌱 3. Potential Loyalists (잠재 충성 고객)
            - **고객 특성**: 최근에 첫 구매 후 최근성은 좋으나 아직 구매 횟수가 적은 성장 가능성 높은 고객군.
            - **비즈니스 액션플랜**:
              - **2차 재구매 프로모션**: 첫 구매 14일 이내 사용 가능한 "2차 구매 15% 할인 웰컴 쿠폰" 발송
              - **카테고리 온보딩**: 인기 카테고리 베스트셀러 큐레이션 추천 제공

            ---

            ### ⚠️ 4. At Risk (이탈 위기 고객)
            - **고객 특성**: 과거에는 자주 구매하고 지출도 높았으나 최근 구매일(Recency)이 멀어진 이탈 위험 그룹.
            - **비즈니스 액션플랜**:
              - **"We Miss You" 복귀 캠페인**: 카카오톡 알림톡/이메일로 강력한 복귀 전용 할인 코드 제공
              - **이탈 원인 설문조사**: 서비스 만족도 조사 참여 시 마일리지 지급

            ---

            ### 💤 5. Hibernating / Lost (휴면 / 이탈 고객)
            - **고객 특성**: 구매 횟수가 적고 방문한 지 매우 오래된 가성비 저효율 고객군.
            - **비즈니스 액션플랜**:
              - **대량 리액티베이션 이벤트**: 시즌 세일 및 대규모 할인 행사 시 한정 자동 알림 메시지 발송
              - **마케팅 비용 최소화**: 개인화 타겟팅 비용을 최소화하고 자동화 캠페인에만 포함
            """)

        # --- 💡 RFM & 군집화 기술 아키텍처 탭 ---
        with tab_cl5:
            st.subheader("💡 고객 RFM 분석 & K-Means 군집화 기술 구조")
            render_gitbook_hint("""
            고객 군집화 파이프라인은 4,338명의 거래 고객을 대상으로 Recency(최근성), Frequency(구매빈도), Monetary(구매금액) 3가지 고객 가치 축을 기준으로 정량 데이터 분석을 수행합니다.
            """, "tip")

            st.markdown("""
            원본 RFM 데이터는 편향성(Skewness)이 크기 때문에, $y = \\log(1 + x)$ 수식으로 로그 변환(Log Transformation)한 후 `StandardScaler`를 통해 평균 0, 표준편차 1로 스케일링합니다. 이후 **K-Means 머신러닝 알고리즘**을 통해 유클리디안 거리를 최소화하는 4개 중심점(Centroid)을 반복 최적화하여 고객 군집(`Cluster 0~3`)을 형성합니다.

            군집 성능 검증을 위해 **Inertia(WCSS)**를 이용한 **엘보우 기법(Elbow Method)**과 개별 데이터가 본인 군집에 얼마나 밀집해 있는지를 정량화하는 **실루엣 계수(Silhouette Coefficient)** 분석을 실시하며, 3D 공간 시각화 및 실루엣 프로필 다이어그램을 통해 군집화 분리 성능을 검증합니다.
            """)

            st.markdown("---")
            st.markdown("#### 1️⃣ 군집 분석 처리 파이프라인 플로우차트 (Flowchart - Left to Right)")
            
            cluster_flow = """
flowchart LR
    A[원본 거래 로그] --> B[RFM 원본값 산출]
    B --> C1[RFM Score 할당]
    B --> C2[Log1p 변환 & 정규화]
    C2 --> D[K-Means Clustering 연산]
    D --> E1[Elbow WCSS 평가]
    D --> E2[개별 실루엣 계수 계산]
    E1 --> F[3D 시각화 & 실루엣 다이어그램]
    E2 --> F
"""
            render_mermaid(cluster_flow, height=180, width_pct=85)

            st.markdown("---")
            st.markdown("#### 2️⃣ 시스템 처리 시퀀스 다이어그램 (Sequence Diagram)")
            
            cluster_seq = """
sequenceDiagram
    participant User as 사용자
    participant UI as Streamlit UI
    participant Analyzer as ClusterAnalysis
    participant SKLearn as Scikit-Learn KMeans

    User->>UI: 1. 군집화 페이지 선택
    UI->>Analyzer: 2. 데이터 로드 요청
    Analyzer->>SKLearn: 3. StandardScaler & KMeans 실행
    SKLearn-->>Analyzer: 4. Labels & Silhouette 반환
    UI->>UI: 5. 세그먼트 교차표 렌더링
    UI->>UI: 6. 3D 3열 산점도 생성
    UI->>UI: 7. 엘보우 & 실루엣 다이어그램 생성
    UI-->>User: 8. 군집 분석 결과 렌더링
"""
            render_mermaid(cluster_seq, height=350, width_pct=80)

if __name__ == '__main__':
    main()
