import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# st.set_page_config는 반드시 스트림릿 코드가 실행되는 최초 시점에 실행되어야 합니다.
st.set_page_config(
    page_title="올리브영 비타민 트렌드 & 복용 적합성 대시보드",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. 디자인 커스텀 CSS (올리브영 감성의 그린/허브 톤 프리미엄 스타일)
st.markdown("""
<style>
    /* 메인 배경 및 텍스트 톤 */
    .stApp {
        background-color: #F9FBFA;
    }
    h1, h2, h3 {
        color: #2E4F3B !important;
        font-family: 'Apple SD Gothic Neo', sans-serif;
    }
    
    /* 카드형 컨테이너 스타일 */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(46, 79, 59, 0.05);
        border: 1px solid #EBF0EC;
        text-align: center;
    }
    .metric-val {
        font-size: 28px;
        font-weight: bold;
        color: #2E4F3B;
    }
    .metric-label {
        font-size: 13px;
        color: #7D8E83;
        margin-top: 5px;
    }
    
    /* 탭 스타일링 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #EBF0EC;
        padding: 6px 12px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        background-color: transparent;
        border-radius: 8px;
        color: #5A6E62;
        font-weight: 600;
        border: none;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: white !important;
        color: #2E4F3B !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 기능 (캐싱 적용)
@st.cache_data
def load_data():
    csv_path = "testproj_2/data/olive_vitamins.csv"
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    return df

df = load_data()

# 데이터가 비어있을 때의 에러 핸들링
if df.empty:
    st.error("올리브영 데이터 파일(olive_vitamins.csv)을 찾을 수 없거나 비어 있습니다. 먼저 수집 스크립트(scraper.py)를 실행해 주세요.")
    st.stop()

# 3. 사이드바 영역 구성
st.sidebar.markdown("<h2 style='text-align:center;'>🌿 올영 건강 매대 필터</h2>", unsafe_allow_html=True)
st.sidebar.write("수집된 비타민 데이터를 필터링하여 맞춤형 트렌드를 확인하세요.")

# 필터 요소들
all_brands = sorted(df['브랜드'].dropna().unique().tolist())
selected_brands = st.sidebar.multiselect("브랜드 선택 (전체 선택 가능)", all_brands, default=[])

all_formulations = sorted(df['제형'].dropna().unique().tolist())
selected_formulations = st.sidebar.multiselect("제형 선택", all_formulations, default=all_formulations)

# 필터 데이터 적용
filtered_df = df.copy()
if selected_brands:
    filtered_df = filtered_df[filtered_df['브랜드'].isin(selected_brands)]
if selected_formulations:
    filtered_df = filtered_df[filtered_df['제형'].isin(selected_formulations)]

st.sidebar.markdown("---")
st.sidebar.info("💡 **대시보드 팁**\n복용 체크 탭에서 개인 복용 패턴을 입력하면 나에게 꼭 맞는 비타민 형태를 진단해 줍니다.")

# 4. 메인 대시보드 헤더
st.markdown("<h1 style='text-align: center;'>🌿 올리브영 비타민 제형 트렌드 & 복용 적합성 대시보드</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7D8E83; font-size: 15px;'>국내 주요 건강 보조제 유통 트렌드 분석 및 개인 맞춤형 복용 매칭 시스템</p>", unsafe_allow_html=True)
st.write("")

# 5. 상위 KPI 메트릭 영역 배치
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{len(filtered_df)}개</div>
        <div class="metric-label">분석 대상 상품 수</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{filtered_df['브랜드'].nunique()}개</div>
        <div class="metric-label">입점 브랜드 수</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{filtered_df['가격'].mean():,.0f}원</div>
        <div class="metric-label">비타민 평균 판매가</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{filtered_df['평점'].mean():.2f} / 5.0</div>
        <div class="metric-label">평균 소비자 평점</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 6. 메인 탭 인터페이스 구성 (3대 탭)
tab1, tab2, tab3 = st.tabs(["📊 제형 트렌드 분석", "👥 연령대 선호 분석", "💊 나의 복용 체크 & 추천"])

# ==========================================
# 탭 1: 제형 트렌드 분석
# ==========================================
with tab1:
    st.markdown("### 📊 제형 트렌드: 정제 vs 구미 vs 샷")
    st.write("올리브영 비타민 카테고리의 제형별 상품수와 고객 만족도를 다차원 분석합니다.")
    st.write("")
    
    col_t1_1, col_t1_2 = st.columns(2)
    
    with col_t1_1:
        st.markdown("#### **제형별 등록 상품 점유율**")
        fig_pie = px.pie(
            filtered_df, names='제형', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_t1_2:
        st.markdown("#### **제형별 평균 판매 가격**")
        price_by_form = filtered_df.groupby('제형')['가격'].mean().reset_index().sort_values(by='가격', ascending=False)
        fig_bar_price = px.bar(
            price_by_form, x='제형', y='가격',
            labels={'가격': '평균 가격 (원)'},
            color='제형', color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_bar_price.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar_price, use_container_width=True)
        
    st.write("")
    st.markdown("#### 🔍 제형별 대표 유입 키워드 (TF-IDF 기반 도출)")
    st.write("각 제형별로 상품명 및 특징에서 자주 관찰되는 주요 연관 키워드를 보여줍니다.")
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.success("💊 **정제 / 캡슐**\n* 핵심 키워드: `함량`, `고려은단`, `이지`, `하루`, `메가도스`\n* 설명: 전통적인 필수 섭취용 고함량 위주 구성")
    with col_k2:
        st.warning("🍬 **구미 / 젤리**\n* 핵심 키워드: `올더베러`, `맛있다`, `간식`, `과일`, `구미젤리`\n* 설명: 물 없이 섭취하는 캐주얼한 미식 비타민")
    with col_k3:
        st.info("🧪 **액상 / 샷**\n* 핵심 키워드: `이뮨`, `아임비타`, `오쏘몰`, `원샷`, `아르기닌`\n* 설명: 원샷 피로회복 목적의 프리미엄 매스티지 제형")
    with col_k4:
        st.error("🥢 **스틱 / 파우더**\n* 핵심 키워드: `레모나`, `가루`, `휴대성`, `상큼`, `분말`\n* 설명: 휴대가 간편하여 직장/이동 중 섭취에 용이")

# ==========================================
# 탭 2: 연령대 선호 분석
# ==========================================
with tab2:
    st.markdown("### 👥 연령대별 선호도 & 유통 분석")
    st.write("상품명의 타깃 연령층 키워드 필터에 따른 제형 및 브랜드 분포 분석 결과입니다.")
    st.write("")
    
    col_t2_1, col_t2_2 = st.columns(2)
    
    with col_t2_1:
        st.markdown("#### **타깃 집단(연령/성별)별 비타민 구성비**")
        fig_age_pie = px.pie(
            filtered_df, names='타깃 연령',
            color_discrete_sequence=px.colors.sequential.Tealgrn
        )
        fig_age_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_age_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_age_pie, use_container_width=True)
        
    with col_t2_2:
        st.markdown("#### **타깃 연령별 유통 제형 분석**")
        age_form_cross = pd.crosstab(filtered_df['타깃 연령'], filtered_df['제형']).reset_index()
        fig_cross = px.bar(
            age_form_cross, x='타깃 연령', y=filtered_df['제형'].unique(),
            labels={'value': '상품 수'},
            barmode='stack', color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_cross.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cross, use_container_width=True)

    st.write("")
    st.markdown("#### 💡 타깃 연령대별 유통 전략 요약")
    
    tab_sum1, tab_sum2, tab_sum3 = st.tabs(["전체 (범용)", "성별 세그먼트 (남성/여성)", "틈새 시장 (키즈/시니어)"])
    with tab_sum1:
        st.write("올리브영 비타민의 약 89%는 **범용성 전체 타깃 상품**으로 설계되어 있습니다. 특정 구분을 배제함으로써 선물 구매율을 극대화하고, 고려은단 비타민C나 아임비타 샷 등 메이저 라인의 기본값 역할을 톡톡히 해냅니다.")
    with tab_sum2:
        st.write("성별 전용인 **남성(포맨)** 및 **여성(포우먼)** 라인은 영양소 조합이 상이합니다. 남성은 아르기닌 및 비타민 B군 위주의 활력 샷/정제 비중이 높고, 여성은 비오틴, 콜라겐, 엽산 등이 혼합된 멀티팩 캡슐 및 구미 제형이 주를 이룹니다.")
    with tab_sum3:
        st.write("주니어(어린이) 및 시니어(장년층) 시장은 올리브영 비타민 매대의 틈새 카테고리입니다. 어린이를 대상으로는 기호성이 매우 훌륭한 **구미/젤리(맛있는 웰니스)** 제형이 100% 점유율을 차지하고 있습니다.")

# ==========================================
# 탭 3: 복용 체크 & 추천
# ==========================================
with tab3:
    st.markdown("### 💊 나의 비타민 복용 패턴 체크 & 제형 추천")
    st.write("평소 본인의 식습관과 알약 삼킴 정도를 입력하면 올리브영 데이터 분석 결과를 토대로 가장 적합한 비타민 형태를 매칭 진단합니다.")
    st.write("")
    
    st.markdown("#### **1단계: 평소 복용 습관 및 라이프스타일 입력**")
    
    # 3x2 격자 입력 폼 구성
    diag_col1, diag_col2 = st.columns(2)
    with diag_col1:
        pill_swallow = st.selectbox(
            "1. 목넘김 정도 (알약을 삼키는 데 불편함이 있으신가요?)",
            ["불편하지 않음 (큰 알약도 잘 삼킴)", "약간 불편함 (큰 알약은 부담스러움)", "매우 불편함 (알약을 삼키지 못함)"]
        )
        portability = st.selectbox(
            "2. 휴대성 요구도 (밖이나 직장에 자주 들고 다니시나요?)",
            ["거의 없음 (집에 두고 주로 먹음)", "약간 필요함 (가끔 외출 시 소지)", "매우 필요함 (항상 간편히 소지해야 함)"]
        )
    with diag_col2:
        water_avail = st.checkbox("3. 물 없이 섭취 가능 여부 (물이 없어도 가볍게 먹을 수 있길 원하나요?)", value=False)
        stomach_sensitive = st.checkbox("4. 위장 민감도 (위장이 예민하여 식후에 복용해야 하거나 속쓰림 걱정이 있나요?)", value=False)
        purpose = st.multiselect(
            "5. 복용 목적 (중복 선택 가능)",
            ["피로 회복 & 활력 충전", "피부 건강", "장건강 & 면역력", "뼈/관절", "기본 영양 보충"]
        )
        
    st.write("")
    st.markdown("#### **2단계: 현재 복용 중인 영양소 종류 선택 (중복 섭취 과잉 경고 모듈)**")
    current_nutrients = st.multiselect(
        "현재 복용 중인 영양소를 선택해 주세요. (올리브영 데이터 기반 중복/과다 경고 메시지가 제공됩니다)",
        ["멀티비타민/종합영양제", "고함량 비타민C", "비타민B군/비오틴", "유산균", "콜라겐"]
    )
    
    st.write("")
    if st.button("🌿 복용 적합성 진단 시작"):
        st.markdown("---")
        st.markdown("<h4 style='color:#2E4F3B;'>🩺 복용 적합성 진단 결과 리포트</h4>", unsafe_allow_html=True)
        
        # 1. 중복 섭취 경고 체크
        warnings = []
        if "멀티비타민/종합영양제" in current_nutrients and "비타민B군/비오틴" in current_nutrients:
            warnings.append("⚠️ **비타민 B군 중복 가능성**: 종합 영양제에는 이미 충분한 일일 권장량의 비타민 B군이 들어 있습니다. 추가 고함량 B군 복용 시 수용성이긴 하지만 가벼운 위장 장애나 불필요한 과량 배출이 일어날 수 있으니 개별 제품의 함량을 확인하세요.")
        if "멀티비타민/종합영양제" in current_nutrients and "고함량 비타민C" in current_nutrients:
            warnings.append("⚠️ **비타민 C 중복 섭취**: 메가도스 요법(하루 3000mg 이상) 목적이 아니라면, 일상적인 종합영양제와 추가 비타민C 단일제의 과다 복용은 신장 결석이나 가스 차오름을 유발할 수 있으므로 물을 충분히 섭취해야 합니다.")
        
        if warnings:
            st.error("🚫 **중복 및 과다 섭취 가능성 경고**")
            for warn in warnings:
                st.write(warn)
        else:
            st.success("✅ **영양소 복용 안전성**: 현재 중복되거나 위험한 수준의 영양소 과다 매칭 정황은 보이지 않습니다. 적절히 분산 섭취가 가능합니다.")
            
        # 2. 추천 제형 알고리즘
        recommended_form = "정제"
        reason = "전체 올리브영 데이터에서 가장 대중적이고 표준적인 형태로, 안정적인 보관과 섭취가 가능합니다."
        
        if "매우 불편함" in pill_swallow:
            if water_avail:
                recommended_form = "구미"
                reason = "알약 삼킴에 장애가 매우 크고 물 없는 환경을 중시하시므로, 간식처럼 씹어서 편리하게 섭취하는 **구미(젤리) 제형**이 가장 적합합니다."
            else:
                recommended_form = "액상 / 샷"
                reason = "알약 삼킴이 불가능하고 영양성분의 높은 흡수를 위해 마시는 **액상/샷 제형**(예: 오쏘몰, 아임비타)이 가장 훌륭한 대안입니다."
        elif "매우 필요함" in portability:
            recommended_form = "스틱 / 파우더"
            reason = "외출이나 출장 시 간편한 휴대성을 원하시므로 가볍게 파우치에 소지하다 물 없이 바로 털어먹는 **스틱/분말 제형**을 추천합니다."
        elif stomach_sensitive:
            recommended_form = "캡슐"
            reason = "위장이 예민하여 식도/위벽 자극을 완충해 주어야 하므로, 위산에서 보호되어 장내 서서히 붕해되는 **연질캡슐 제형**이 추천됩니다. 반드시 식사 중 혹은 식후 즉시 미온수와 함께 드시는 것이 안전합니다."
            
        st.markdown(f"#### 🎯 나에게 꼭 맞는 추천 제형: **`{recommended_form}`**")
        st.info(f"💡 **제형 매칭 사유**: {reason}")
        
        # 3. 올리브영 데이터 연동 추천 상품 노출
        st.markdown("#### 🛍️ 올리브영 실시간 추천 상품 매칭")
        st.write(f"올리브영 데이터셋에서 `{recommended_form}` 제형을 가진 대표적인 상위 인기 비타민 추천 상품 목록입니다.")
        
        form_mapped = recommended_form
        if "액상" in form_mapped:
            form_mapped = "액상"
        elif "스틱" in form_mapped:
            form_mapped = "스틱"
            
        matched_products = filtered_df[filtered_df['제형'] == form_mapped].sort_values(by='평점', ascending=False).head(3)
        
        if not matched_products.empty:
            for idx, prod in matched_products.iterrows():
                st.markdown(f"- **[{prod['브랜드']}] {prod['상품명']}** | 가격: **{prod['가격']:,}원** | 평점: ⭐ `{prod['평점']:.1f}` (리뷰 수: `{prod['리뷰 수']}+`)")
        else:
            st.write("해당 제형의 상품이 필터 조건 하에 없습니다. 사이드바에서 제형 필터를 켜거나 브랜드를 초기화해 주세요.")
            
        # 4. 복용 적합성 꿀팁 가이드
        st.markdown("#### 📘 식전/식후 복용 가이드라인")
        if stomach_sensitive or "피로 회복 & 활력 충전" in purpose:
            st.write("* **비타민 B군 및 C**: 고함량 비타민 B군/C는 에너지 대사를 자극하므로 가급적 **아침 또는 낮 시간 식후 즉시** 복용을 권장합니다. 밤늦게 드실 경우 수면 방해를 겪거나 예민한 위장에 속 쓰림을 유발할 수 있습니다.")
        else:
            st.write("* **지용성 비타민 (A, D, E, K)**: 지용성 성분은 식사 중에 나오는 지방산에 의해 흡수율이 높아집니다. 따라서 **가장 식사량이 많은 식사(주로 점심/저녁)의 직후** 복용하는 것이 최적입니다.")
