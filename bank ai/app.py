import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 초기 설정 및 테마
st.set_page_config(
    page_title="iM뱅크 PB Money Move 방어 대시보드 v2",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 네이버 나눔스퀘어라운드 및 Google Outfit 폰트 연동
st.markdown("""
<style>
    /* 폰트 로드 */
    @import url('https://hangeul.pstatic.net/hangeul_static/css/nanum-square-round.css');
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'NanumSquareRound', 'Outfit', sans-serif !important;
        font-size: 13px !important; /* 전체 기본 폰트 축소 */
    }
    
    /* 제목 스타일 조밀화 */
    h1, h2, h3, h4, h5, h6, .stSubheader, .stHeader {
        margin-top: 2px !important;
        margin-bottom: 2px !important;
    }
    
    /* 메인 컨테이너 패딩 조절로 상단 툴바 간섭 해소 및 꽉 차는 레이아웃 */
    .block-container {
        padding-top: 2.8rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }
    
    /* 콤팩트 카드 디자인 */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        border: 1.5px solid #e2f1f0;
        box-shadow: 0 2px 6px rgba(0, 189, 167, 0.02);
        transition: all 0.2s ease;
        text-align: center;
        margin-bottom: 5px;
    }
    
    /* 영업 제언 카드 */
    .playbook-card {
        background-color: #ffffff;
        border-left: 5px solid #00bda7;
        padding: 12px;
        border-radius: 4px 8px 8px 4px;
        border-top: 1.5px solid #e2f1f0;
        border-right: 1.5px solid #e2f1f0;
        border-bottom: 1.5px solid #e2f1f0;
        box-shadow: 0 2px 6px rgba(0, 189, 167, 0.01);
        font-size: 12px !important;
    }
    
    /* 대본 상자 */
    .script-box {
        background-color: #fffbeb;
        border-left: 4px solid #fbbf24;
        padding: 8px;
        border-radius: 4px;
        color: #78350f;
        margin: 6px 0;
        font-size: 11.5px;
        line-height: 1.4;
        font-weight: 500;
    }
    
    /* CRM 로그 */
    .crm-log {
        font-size: 11px;
        color: #475569;
        background-color: #f8fafc;
        padding: 5px 8px;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        margin-bottom: 4px;
    }
    
    /* 위험 등급 색상 표기 */
    .risk-high { color: #f87171; font-weight: 700; }
    .risk-medium { color: #fb923c; font-weight: 700; }
    .risk-low { color: #00bda7; font-weight: 700; }

    /* 모든 streamlit 버튼에 대한 iM뱅크 브랜드 스타일 오버라이드 */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #e2f1f0 !important;
        border-radius: 8px !important;
        padding: 6px 4px !important; /* 패딩 축소 */
        width: 100% !important;
        box-shadow: 0 2px 6px rgba(0, 189, 167, 0.01) !important;
        transition: all 0.2s ease !important;
        text-align: center !important;
        font-family: 'NanumSquareRound', sans-serif !important;
        font-size: 11.5px !important; /* 글씨 크기 축소 */
        font-weight: 600 !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        line-height: 1.25 !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(0, 189, 167, 0.04) !important;
        border-color: #00bda7 !important;
        background-color: #fafdfd !important;
    }
    div.stButton > button:focus {
        border-color: #00bda7 !important;
        box-shadow: 0 0 0 1.5px rgba(0, 189, 167, 0.15) !important;
    }
    /* 선택된 KPI 카드 (Primary 버튼) */
    div.stButton > button[kind="primary"] {
        background-color: #e2f1f0 !important;
        color: #00bda7 !important;
        border: 1.5px solid #00bda7 !important;
        font-weight: 700 !important;
    }
    /* 선택되지 않은 KPI 카드 또는 일반 버튼 (Secondary 버튼) */
    div.stButton > button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #e2f1f0 !important;
    }
    
    /* 추천 상품 칩/배지 스타일 */
    .product-chip {
        display: inline-block;
        background-color: #fafdfd;
        border: 1.2px solid #00bda7;
        color: #00bda7;
        border-radius: 20px;
        padding: 3px 10px;
        margin: 3px 4px;
        font-size: 11px;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0, 189, 167, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 로드 및 전처리
@st.cache_data
def load_data():
    df = pd.read_csv('customer_data_v2.csv')
    
    # Risk_Score 기반 위험 등급 분류
    def classify_risk(score):
        if score > 60: return "고위험"
        elif score >= 40: return "중위험"
        else: return "저위험"
        
    df['Risk_Level'] = df['Risk_Score'].apply(classify_risk)
    df['Risk_Level'] = pd.Categorical(df['Risk_Level'], categories=["고위험", "중위험", "저위험"], ordered=True)
    
    # 유출 위험 자산 (평잔 * 월급날 이체 비중)
    df['Outflow_Risk_Asset'] = (df['Avg_Balance'] * df['Salary_Day_Transfer']).astype(int)
    
    return df

# 2.4 defended_customers 세션 상태 초기화
if 'defended_customers' not in st.session_state:
    st.session_state['defended_customers'] = set()

try:
    df_raw = load_data()
    df = df_raw.copy()
    
    # 방어 성공(Money Magnet 작동) 시 자산 누수율 및 이체 비율을 0으로 오버라이드
    if st.session_state['defended_customers']:
        for cust_id in st.session_state['defended_customers']:
            df.loc[df['Customer_ID'] == cust_id, 'Risk_Score'] = 0.0
            df.loc[df['Customer_ID'] == cust_id, 'Salary_Day_Transfer'] = 0.0
            df.loc[df['Customer_ID'] == cust_id, 'Outflow_Risk_Asset'] = 0
            df.loc[df['Customer_ID'] == cust_id, 'Risk_Level'] = '저위험'
except Exception as e:
    st.error(f"v2 데이터 파일을 불러오는 데 실패했습니다. 'customer_data_v2.csv'가 존재하는지 확인해 주세요. 에러: {e}")
    st.stop()

# 2.5 KPI 선택 상태 초기화
if 'selected_kpi' not in st.session_state:
    st.session_state['selected_kpi'] = 'total_aum'

# 2.6 테마별 추천 상품 목록 정의
products = {
    '반도체': ['피델리티 글로벌 테크놀로지 펀드', 'AB 미국 그로스 펀드', '하나 반도체 포커스 펀드', 'KODEX 반도체 특정금전신탁', 'TIGER 미국테크TOP10 특정금전신탁', 'KODEX 미국AI테크TOP10+15%프리미엄 신탁'],
    '항공/방산': ['한화 K방산 펀드', 'TIGER 우주항공방산 특정금전신탁', 'ARIRANG K방산Fn 특정금전신탁', '맥쿼리인프라 특정금전신탁'],
    '2차전지': ['KB 2차전지 포커스 펀드', '한국투자 글로벌 전기차&배터리 펀드', 'TIGER 2차전지테마 특정금전신탁', 'KODEX 2차전지산업 특정금전신탁'],
    '리츠/배당': ['신영 밸류 고배당 펀드', '베어링 고배당 펀드', 'TIGER 미국배당+7%프리미엄 신탁', 'TIGER 리츠부동산인프라 신탁'],
    '금융/은행': ['TIGER 은행고배당플러스TOP10 특정금전신탁', 'KODEX 은행 특정금전신탁']
}

# 3. 고정 헤더 레이아웃 (🧲 Operation: Money Magnet 타이틀 및 기준일자 표기)
current_date = datetime.now().strftime("%Y년 %m월 %d일")
st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0px; margin-bottom: 4px; border-bottom: 1.5px solid #e2f1f0; padding-bottom: 8px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 28px; font-weight: 800; color: #00bda7; font-family: 'Outfit'; letter-spacing: -1px;">🧲 Operation: Money Magnet</span>
        <span style="font-size: 20px; font-weight: 700; color: #1e293b; font-family: 'NanumSquareRound'; letter-spacing: -0.5px;">(머니무브 방어 사령부)</span>
    </div>
    <div style="text-align: right; font-family: 'NanumSquareRound'; font-size: 13px; color: #64748b; font-weight: 600; display: flex; align-items: center; gap: 6px;">
        <span>📅 기준일자:</span>
        <span style="color: #00bda7; font-weight: 700;">{current_date}</span>
    </div>
</div>
<div style="margin-top: 2px; margin-bottom: 12px; font-family: 'NanumSquareRound'; font-size: 13px; color: #475569; font-weight: 600;">
    나가는 돈도 다시 보자! 증권사로 향하는 자금을 자석처럼 끌어당기는 PB 관제탑
</div>
""", unsafe_allow_html=True)

# 4. 사이드바 로고 고정
col_sb_pad, col_sb_img, col_sb_pad2 = st.sidebar.columns([0.5, 5.0, 0.5])
with col_sb_img:
    st.image("im_bank_logo.png", use_container_width=True)
st.sidebar.markdown("<p style='text-align: center; font-size: 12px; color: #64748b; font-family: \"NanumSquareRound\"; margin-top: 5px; margin-bottom: 0;'>공식 자산 관리 관제 대시보드</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

col_flt_txt, col_flt_img = st.sidebar.columns([4, 1])
with col_flt_txt:
    st.sidebar.subheader("🔍 글로벌 필터")
with col_flt_img:
    st.image("dandi_mascot_2d.png", width=35)

# 직군 필터
selected_jobs = st.sidebar.multiselect(
    "고객 직군",
    options=list(df['Job_Type'].unique()),
    default=list(df['Job_Type'].unique())
)

# 자산 규모 필터
min_bal = int(df['Avg_Balance'].min())
max_bal = int(df['Avg_Balance'].max())
selected_bal_range = st.sidebar.slider(
    "평균 잔액 범위 (원)",
    min_value=min_bal,
    max_value=max_bal,
    value=(min_bal, max_bal),
    step=1000000,
    format="%d"
)

# 이체 비중 필터
selected_ratio_range = st.sidebar.slider(
    "월급날 이체 비중 범위",
    min_value=0.0,
    max_value=1.0,
    value=(0.0, 1.0),
    step=0.05
)

# 주력 관심 테마 필터
selected_themes = st.sidebar.multiselect(
    "주력 관심 테마",
    options=list(df['Main_Theme'].unique()),
    default=list(df['Main_Theme'].unique())
)

# 자산 누수 수준 다중 선택
selected_risk_levels = st.sidebar.multiselect(
    "⚠️ 자산 누수 등급",
    options=["고위험", "중위험", "저위험"],
    default=["고위험", "중위험", "저위험"]
)

# 필터링 적용 DataFrame
filtered_df = df[
    (df['Job_Type'].isin(selected_jobs)) &
    (df['Avg_Balance'] >= selected_bal_range[0]) &
    (df['Avg_Balance'] <= selected_bal_range[1]) &
    (df['Salary_Day_Transfer'] >= selected_ratio_range[0]) &
    (df['Salary_Day_Transfer'] <= selected_ratio_range[1]) &
    (df['Main_Theme'].isin(selected_themes)) &
    (df['Risk_Level'].isin(selected_risk_levels))
]

# 5. 상단 탭 구성 (배치 순서 변경: 은행 전체 통계가 첫 번째로 이동)
tab1, tab2, tab3 = st.tabs(["📊 은행 전체 통계", "🎯 고객 상세 분석", "📈 시장 인사이트"])

# ----------------- Tab 1: 은행 전체 통계 -----------------
with tab1:
    # 타이틀 옆에 미니 단디똑디 배치 (크기: 45px)
    col_t_txt, col_t_img = st.columns([12, 1])
    with col_t_txt:
        st.subheader("📊 은행 전체 자금 흐름 및 거시 요약 통계")
        st.markdown("글로벌 필터링이 반영된 은행 전체 고객군에 대하여 자산 규모 및 위험 포트폴리오 지표를 조회합니다.")
    with col_t_img:
        st.image("dandi_mascot_2d.png", width=55)
    st.markdown("---")
    
    if not filtered_df.empty:
        # 지표 연산
        total_aum = filtered_df['Avg_Balance'].sum()
        avg_balance = filtered_df['Avg_Balance'].mean()
        high_risk_count = len(filtered_df[filtered_df['Risk_Level'] == "고위험"])
        high_risk_ratio = (high_risk_count / len(filtered_df)) * 100
        potential_outflow = filtered_df['Outflow_Risk_Asset'].sum()
        avg_age = filtered_df['Age'].mean()
        top_theme = filtered_df['Main_Theme'].mode()[0] if not filtered_df['Main_Theme'].empty else "N/A"
        
        action_count = len(st.session_state.get('action_log', []))
        defense_rate = min(98.5, 75.0 + action_count * 2.0)
        monthly_target_achievement = min(100.0, 81.2 + action_count * 1.1)

        # 좌측 세로 요약지표 선택판, 우측 상세 시각화 차트 및 설명
        main_left_col, main_right_col = st.columns([1.1, 2.8])
        
        with main_left_col:
            st.markdown("##### 🎛️ 요약 지표 선택")
            
            # 가로 두칸(2열) 구조로 재배치하여 높이를 최소화
            l_btn_col, r_btn_col = st.columns(2)
            
            with l_btn_col:
                # 1. AUM
                is_selected = st.session_state['selected_kpi'] == 'total_aum'
                aum_lbl = f"{'🎯' if is_selected else '💰'} 총 관리 자산 (AUM)\n\n₩{total_aum:,}"
                if st.button(aum_lbl, key="kpi_aum", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'total_aum'
                    st.rerun()

                # 3. High Risk Count
                is_selected = st.session_state['selected_kpi'] == 'high_risk_count'
                risk_cnt_lbl = f"{'🎯' if is_selected else '🚨'} 누수 고위험 고객 수\n\n{high_risk_count}명 ({high_risk_ratio:.1f}%)"
                if st.button(risk_cnt_lbl, key="kpi_high_risk_count", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'high_risk_count'
                    st.rerun()

                # 5. Avg Age
                is_selected = st.session_state['selected_kpi'] == 'avg_age'
                age_lbl = f"{'🎯' if is_selected else '👥'} 대상 고객 평균 연령\n\n{avg_age:.1f} 세"
                if st.button(age_lbl, key="kpi_avg_age", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'avg_age'
                    st.rerun()

                # 7. Defense Rate
                is_selected = st.session_state['selected_kpi'] == 'defense_rate'
                defense_lbl = f"{'🎯' if is_selected else '🛡️'} 마케팅 방어 성공률\n\n{defense_rate:.1f}%"
                if st.button(defense_lbl, key="kpi_defense_rate", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'defense_rate'
                    st.rerun()

            with r_btn_col:
                # 2. Avg Balance
                is_selected = st.session_state['selected_kpi'] == 'avg_balance'
                avg_bal_lbl = f"{'🎯' if is_selected else '📊'} 고객 평균 자산\n\n₩{int(avg_balance):,}"
                if st.button(avg_bal_lbl, key="kpi_avg_bal", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'avg_balance'
                    st.rerun()

                # 4. Outflow Risk Asset
                is_selected = st.session_state['selected_kpi'] == 'potential_outflow'
                outflow_lbl = f"{'🎯' if is_selected else '💸'} 월급날 유출 우려 자산\n\n₩{int(potential_outflow):,}"
                if st.button(outflow_lbl, key="kpi_potential_outflow", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'potential_outflow'
                    st.rerun()

                # 6. Top Theme
                is_selected = st.session_state['selected_kpi'] == 'top_theme'
                theme_lbl = f"{'🎯' if is_selected else '⭐'} 최다 관심 테마 (1위)\n\n{top_theme}"
                if st.button(theme_lbl, key="kpi_top_theme", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'top_theme'
                    st.rerun()

                # 8. Target Achievement
                is_selected = st.session_state['selected_kpi'] == 'monthly_target_achievement'
                target_lbl = f"{'🎯' if is_selected else '📈'} 이달 목표 달성률\n\n{monthly_target_achievement:.1f}%"
                if st.button(target_lbl, key="kpi_target_achievement", type="primary" if is_selected else "secondary"):
                    st.session_state['selected_kpi'] = 'monthly_target_achievement'
                    st.rerun()
                
        with main_right_col:
            st.markdown("### 🔍 선택 지표 상세 분석 및 시각화")
            
            # 선택된 KPI 정보 추출
            kpi_info = {
                'total_aum': ('총 관리 자산 (AUM)', '💰'),
                'avg_balance': ('고객 평균 자산', '📊'),
                'high_risk_count': ('누수 고위험 고객 수', '🚨'),
                'potential_outflow': ('월급날 유출 우려 자산', '💸'),
                'avg_age': ('대상 고객 평균 연령', '👥'),
                'top_theme': ('최다 관심 테마 (1위)', '⭐'),
                'defense_rate': ('마케팅 방어 성공률', '🛡️'),
                'monthly_target_achievement': ('이달 마케팅 목표 달성률', '📈')
            }
            
            kpi_name, kpi_emoji = kpi_info[st.session_state['selected_kpi']]
            
            # 상세 차트와 단디의 해설 카드를 세로로 순차 배치
            det_chart_container = st.container()
            det_brief_container = st.container()
            
            with det_chart_container:
                st.markdown(f"##### {kpi_emoji} '{kpi_name}' 지표 정밀 진단 차트")
                
                selected = st.session_state['selected_kpi']
                if selected == 'total_aum':
                    # 자산 분포 히스토그램
                    fig_det = px.histogram(
                        filtered_df,
                        x="Avg_Balance",
                        nbins=30,
                        color_discrete_sequence=["#00bda7"],
                        labels={"Avg_Balance": "평균 잔액 (원)", "count": "고객 수"},
                        height=180
                    )
                    fig_det.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="#fafdfd",
                        paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="평균 자산 잔액 (원)",
                        yaxis_title="고객 수 (명)"
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "전체 자산의 분포를 보면 대다수 고객의 평잔 분포와 함께 VVIP 등급(로얄, 골드) 고객층이 차지하는 비중을 한눈에 볼 수 있어! 자산이 많은 VVIP 고객의 이탈을 특별히 신경 써야 해! 💰"
                    
                elif selected == 'avg_balance':
                    # 직군별 평균 자산 수평 바 차트
                    df_job_avg = filtered_df.groupby('Job_Type')['Avg_Balance'].mean().reset_index()
                    df_job_avg = df_job_avg.sort_values(by='Avg_Balance', ascending=True)
                    fig_det = px.bar(
                        df_job_avg,
                        x="Avg_Balance",
                        y="Job_Type",
                        orientation="h",
                        color="Avg_Balance",
                        color_continuous_scale="Mint",
                        labels={"Avg_Balance": "평균 자산 (원)", "Job_Type": "고객 직군"},
                        height=180
                    )
                    fig_det.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="#fafdfd",
                        paper_bgcolor="rgba(0,0,0,0)",
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "각 직군별 평균 자산 규모를 분석해보니 전문직과 IT/개발자 직군의 평잔이 상대적으로 아주 두텁게 나오고 있어. 직군 특성에 맞는 자산 포트폴리오 랩을 적극 제안해보자구! 📊"
                    
                elif selected == 'high_risk_count':
                    # 위험 등급 비율 도넛 차트
                    df_risk_ratio = filtered_df['Risk_Level'].value_counts().reset_index()
                    df_risk_ratio.columns = ['Risk_Level', 'Count']
                    fig_det = px.pie(
                        df_risk_ratio,
                        names='Risk_Level',
                        values='Count',
                        color='Risk_Level',
                        color_discrete_map={'고위험': '#f87171', '중위험': '#fb923c', '저위험': '#00bda7'},
                        hole=0.5,
                        height=180
                    )
                    fig_det.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "자산 누수 고위험군 고객의 비율을 항상 세심히 봐야 해! 이 비율이 높아진다면 즉각 마케팅 제안 발송(SMS, 이메일) 및 유선 약속 스케줄을 잡아야 지점 전체의 AUM 유출을 막을 수 있어! 🚨"
                    
                elif selected == 'potential_outflow':
                    # 주력 관심 테마별 유출 우려 자산 합계
                    df_theme_outflow = filtered_df.groupby('Main_Theme')['Outflow_Risk_Asset'].sum().reset_index()
                    fig_det = px.bar(
                        df_theme_outflow,
                        x="Main_Theme",
                        y="Outflow_Risk_Asset",
                        color="Main_Theme",
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        labels={"Outflow_Risk_Asset": "유출 우려 자산 합계 (원)", "Main_Theme": "주력 관심 테마"},
                        text_auto='.3s',
                        height=180
                    )
                    fig_det.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="#fafdfd",
                        paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "월급날 어떤 투자 테마로 자금이 빠져나갈 가능성이 높은지 보여주고 있어. 특정 테마 랩(Wrap) 상품을 선제 제안해 당행 자금으로 묶는 마케팅이 바로 Money Move 방어의 핵심이야! 💸"
                    
                elif selected == 'avg_age':
                    # 연령대별 고객 분포 및 평균 위험도
                    df_age = filtered_df.copy()
                    df_age['Age_Group'] = (df_age['Age'] // 5) * 5
                    df_age_group = df_age.groupby('Age_Group').agg(
                        고객수=('Customer_ID', 'count'),
                        평균위험점수=('Risk_Score', 'mean')
                    ).reset_index()
                    
                    fig_det = go.Figure()
                    fig_det.add_trace(go.Bar(
                        x=df_age_group['Age_Group'],
                        y=df_age_group['고객수'],
                        name='고객 수 (명)',
                        yaxis='y1',
                        marker_color='#e2f1f0'
                    ))
                    fig_det.add_trace(go.Scatter(
                        x=df_age_group['Age_Group'],
                        y=df_age_group['평균위험점수'],
                        name='평균 위험 점수',
                        yaxis='y2',
                        line=dict(color='#00bda7', width=3),
                        mode='lines+markers'
                    ))
                    
                    fig_det.update_layout(
                        height=180,
                        margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="#fafdfd",
                        paper_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(title="고객 수 (명)", side="left"),
                        yaxis2=dict(title="평균 위험 점수", side="right", overlaying="y", range=[0, 100]),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "연령대가 비교적 젊을수록 모바일 주식 거래 비중이 높기 때문에 이탈 위험 점수가 높게 책정되는 경향이 있어! 3040 세대를 대상으로는 스마트한 비대면 랩 솔루션을 권유해봐! 👥"
                    
                elif selected == 'top_theme':
                    # 5대 테마 평균 관심도 비교
                    theme_names = ["반도체", "항공/방산", "2차전지", "리츠/배당", "금융/은행"]
                    avg_scores = [filtered_df[t].mean() for t in theme_names]
                    df_theme_avg = pd.DataFrame({'테마': theme_names, '평균 관심도': avg_scores})
                    df_theme_avg = df_theme_avg.sort_values(by='평균 관심도', ascending=False)
                    
                    fig_det = px.bar(
                        df_theme_avg,
                        x="테마",
                        y="평균 관심도",
                        color="평균 관심도",
                        color_continuous_scale="Mint",
                        text_auto='.1f',
                        height=180
                    )
                    fig_det.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="#fafdfd",
                        paper_bgcolor="rgba(0,0,0,0)",
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "지점 고객들의 5대 섹터 관심도 평균이야. 최근 트렌드에 따라 특정 테마 선호가 높지만, 자산 포트폴리오 다각화 차원에서 차순위 테마(예: 리츠/배당, 금융/은행)의 절세 랩 제안도 훌륭한 전략이야! ⭐"
                    
                elif selected == 'defense_rate':
                    # 월별 마케팅 방어 성공률 추이 (최근 6개월 가상 시계열)
                    months = ["12월", "1월", "2월", "3월", "4월", "금월"]
                    # 마케팅 액션 수에 연동하여 금월 수치 계산
                    defense_history = [71.2, 73.5, 72.0, 74.8, 76.1, defense_rate]
                    fig_det = px.line(
                        x=months,
                        y=defense_history,
                        markers=True,
                        labels={"x": "기준월", "y": "방어 성공률 (%)"},
                        height=180
                    )
                    fig_det.update_traces(line_color="#00bda7", line_width=3, marker_size=8)
                    fig_det.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        plot_bgcolor="#fafdfd",
                        paper_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(range=[60, 100])
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "우리가 SMS나 이메일을 발송하고 상담 약속을 잡을 때마다 금월 마케팅 방어 성공률이 실시간으로 반영되고 있어! 방어율이 지속 우상향하도록 CRM 이력을 적극 늘려줘! 🛡️"
                    
                else: # monthly_target_achievement
                    # 이달 마케팅 목표 달성률 게이지 차트
                    fig_det = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = monthly_target_achievement,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "금월 목표 달성률 (%)", 'font': {'size': 16, 'family': 'NanumSquareRound'}},
                        number = {'suffix': "%", 'font': {'size': 36, 'color': '#00bda7', 'family': 'Outfit'}},
                        gauge = {
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#00bda7"},
                            'bar': {'color': "#00bda7"},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "#e2f1f0",
                            'steps': [
                                {'range': [0, 80], 'color': '#f8fafc'},
                                {'range': [80, 100], 'color': '#e2f1f0'}
                            ]
                        }
                    ))
                    fig_det.update_layout(
                        height=180,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_det, use_container_width=True)
                    det_comment = "이번 달 마케팅 달성도 현황이야. 100% 달성까지 얼마 남지 않았어! 유출 위험 TOP 10 고객들에게 집중적으로 당행 랩 상품을 가입시켜 성공적으로 목표를 돌파해보자구! 화이팅! 📈"
                    
            st.markdown(" ") # 여백 추가

            with det_brief_container:
                det_dandi_col, det_txt_col = st.columns([1, 20])
                with det_dandi_col:
                    st.image("dandi_mascot_2d.png", width=45)
                with det_txt_col:
                    st.markdown(f"###### 🐧 단디의 '{kpi_name}' 지표 족집게 해설")
                    
                st.markdown(f"""
                <div style="background-color: #f0fdf4; border: 2px solid #ccfbf1; padding: 16px; border-radius: 12px; line-height: 1.6; box-shadow: 0 4px 6px rgba(0, 189, 167, 0.02); font-size:13px; color: #0f766e; font-weight: 500; margin-top: -10px; margin-bottom: 15px;">
                    {det_comment}
                    <div style="margin-top: 10px; font-size:11.5px; color: #64748b; border-top: 1px dashed #ccfbf1; padding-top: 8px;">
                        💡 <b>Tip:</b> 글로벌 필터를 조정하면 해당 고객 집단의 차트로 즉각 재반영된다구!
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # 2x2 차트 그리드 레이아웃
        c_grid_title, c_grid_img = st.columns([12, 1])
        with c_grid_title:
            st.markdown("##### 📊 다차원 분석 시각화 그리드")
        with c_grid_img:
            st.image("dandi_mascot_2d.png", width=45)
        c_row1_col1, c_row1_col2 = st.columns(2)
        color_map = {"고위험": "#f87171", "중위험": "#fb923c", "저위험": "#00bda7"}
        
        with c_row1_col1:
            st.markdown("###### 📌 자산 규모 대비 월급날 이체 비중 (버블 크기 = 자산 누수율)")
            fig_scatter = px.scatter(
                filtered_df,
                x="Avg_Balance",
                y="Salary_Day_Transfer",
                size="Risk_Score",
                color="Risk_Level",
                color_discrete_map=color_map,
                hover_name="Name",
                hover_data={"Customer_ID": True, "Avg_Balance": ":,", "Salary_Day_Transfer": ":.2f", "Risk_Score": ":.1f", "Age": True, "Job_Type": True},
                labels={"Avg_Balance": "평균 잔액 (원)", "Salary_Day_Transfer": "월급날 이체 비중", "Risk_Level": "⚠️ 자산 누수 등급", "Risk_Score": "⚠️ 자산 누수율 (%)"},
                height=170
            )
            fig_scatter.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#fafdfd",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with c_row1_col2:
            st.markdown("###### 📌 주력 관심 테마별 자산 누적 규모 (v2 데이터 피드백)")
            df_theme_bal = filtered_df.groupby('Main_Theme')['Avg_Balance'].sum().reset_index()
            fig_theme_bal = px.bar(
                df_theme_bal,
                x='Main_Theme',
                y='Avg_Balance',
                color='Main_Theme',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                labels={'Avg_Balance': '총 자산 규모 (원)', 'Main_Theme': '주력 관심 테마'},
                text_auto='.2s',
                height=170
            )
            fig_theme_bal.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#fafdfd",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_theme_bal, use_container_width=True)
            
        c_row2_col1, c_row2_col2 = st.columns(2)
        with c_row2_col1:
            st.markdown("###### 📌 직군별 자금 누수 등급 분포")
            fig_job_bar = px.histogram(
                filtered_df,
                x="Job_Type",
                color="Risk_Level",
                color_discrete_map=color_map,
                barmode="group",
                labels={"Job_Type": "직군", "Risk_Level": "⚠️ 자산 누수 등급"},
                height=170
            )
            fig_job_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#fafdfd",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_job_bar, use_container_width=True)
            
        with c_row2_col2:
            st.markdown("###### 📌 주력 관심 테마별 고객 분포 현황")
            fig_theme_pie = px.pie(
                filtered_df,
                names="Main_Theme",
                color="Main_Theme",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hole=0.4,
                height=170
            )
            fig_theme_pie.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_theme_pie, use_container_width=True)

        st.markdown("---")

        # 단디 브리핑 및 집중 케어 대상 테이블 (브리핑란에 캐릭터 중간 크기 100px 배치)
        col_brief, col_table = st.columns([1.2, 2.5])
        with col_brief:
            # 텍스트와 캐릭터 배치
            col_b_t, col_b_i = st.columns([3, 1])
            with col_b_t:
                st.markdown("###### 📢 단디의 실시간 은행 전체 요약 보고")
            with col_b_i:
                st.image("dandi_mascot_2d.png", width=55)
                
            outflow_billions = potential_outflow / 100000000
            
            # 가장 위험 점수가 높은 직군 탐색
            highest_risk_job = "IT/개발"
            job_risks = filtered_df.groupby("Job_Type")["Risk_Score"].mean()
            if not job_risks.empty:
                highest_risk_job = job_risks.idxmax()
                
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 2px solid #ccfbf1; padding: 20px; border-radius: 12px; line-height: 1.7; box-shadow: 0 4px 6px rgba(0, 189, 167, 0.02); font-size:14px;">
                <p style="margin-top:0;">🐧 <b>은행 전체 브리핑:</b></p>
                <p>글로벌 필터가 적용된 은행 전체 고객 자산 중 월급날 유출 예상액은 총 <b>{outflow_billions:.2f}억 원</b>이라구! 🚨</p>
                <p>평균적으로 <b>'{highest_risk_job}'</b> 직군 고객군에서 자산 누수 위험이 가장 높게 포착되고 있어!</p>
                <p style="margin-bottom:0;">이체 한도가 큰 로얄/골드급 자산 누수 고위험 고객 TOP 10 목록을 참고해서 우선 상담 전화를 걸어줘! 💡</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_table:
            st.markdown("###### 🚨 유출 우려 자산 상위 집중 케어 대상 (TOP 10)")
            top_10_df = filtered_df.sort_values(by="Outflow_Risk_Asset", ascending=False).head(10).copy()
            top_10_df['Avg_Balance_Formatted'] = top_10_df['Avg_Balance'].apply(lambda x: f"{x:,} 원")
            top_10_df['Outflow_Risk_Formatted'] = top_10_df['Outflow_Risk_Asset'].apply(lambda x: f"{x:,} 원")
            top_10_df['Transfer_Out_Ratio_Formatted'] = top_10_df['Salary_Day_Transfer'].apply(lambda x: f"{x*100:.1f}%")
            top_10_df['Risk_Score_Formatted'] = top_10_df['Risk_Score'].apply(lambda x: f"{x:.1f}%")
            
            # 컬럼명 변경으로 가독성 향상
            top_10_disp = top_10_df[['Customer_ID', 'Name', 'Age', 'Job_Type', 'Avg_Balance_Formatted', 'Transfer_Out_Ratio_Formatted', 'Outflow_Risk_Formatted', 'Main_Theme', 'Risk_Score_Formatted', 'Risk_Level']].copy()
            top_10_disp.columns = ['고객 ID', '고객명', '연령', '직군', '평균 잔액', '월급날 이체 비중', '유출 우려 자산', '관심 테마', '자산 누수율', '누수 등급']
            st.dataframe(
                top_10_disp,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("조회 가능한 데이터가 없습니다.")

# ----------------- Tab 2: 고객 상세 분석 -----------------
with tab2:
    col_t2_txt, col_t2_img = st.columns([12, 1])
    with col_t2_txt:
        st.subheader("🎯 개별 고객 맞춤 상담 Cockpit (360도 뷰)")
        st.markdown("선택한 고객의 자산 구성 상태, 5대 테마 관심도, 마케팅 시나리오 및 CRM 로그를 통합 관제합니다.")
    with col_t2_img:
        st.image("dandi_mascot_2d.png", width=55)
    st.markdown("---")
    
    # 고객 검색 및 선택 영역 (Tab 2 내부 배치)
    col_search1, col_search2 = st.columns([2, 1])
    with col_search1:
        search_query = st.text_input("고객 번호(ID) 또는 이름 입력", "C00001", placeholder="예: C00001 또는 고객1")
    
    search_results = df[
        df['Customer_ID'].str.contains(search_query, case=False, na=False) |
        df['Name'].str.contains(search_query, case=False, na=False)
    ]
    
    customer_record = None
    if not search_results.empty:
        if len(search_results) > 1:
            with col_search2:
                options = [f"{row['Name']} ({row['Customer_ID']})" for idx, row in search_results.iterrows()]
                selected_option = st.selectbox("검색 결과 선택", options)
                selected_id = selected_option.split(" (")[-1][:-1]
                customer_record = df[df['Customer_ID'] == selected_id].iloc[0]
        else:
            customer_record = search_results.iloc[0]
            with col_search2:
                st.markdown("<div style='padding-top: 25px;'></div>", unsafe_allow_html=True)
                st.success(f"🔍 {customer_record['Name']} 고객 조회 완료")
    else:
        st.error("❌ 일치하는 고객이 없습니다.")

    st.markdown(" ")

    if customer_record is not None:
        # 1. 고객 다차원 진단 그리드
        st.markdown("##### 📋 1단계: 고객 다차원 종합 진단")
        prof_col1, prof_col2, prof_col3 = st.columns([1.2, 1.3, 1.1])
        
        # 1-1) 인적 요약 정보 (미니 똑디 배치 35px)
        with prof_col1:
            col_p_t, col_p_i = st.columns([4, 1])
            with col_p_t:
                st.markdown("###### 👥 고객 기본 요약")
            with col_p_i:
                st.image("dandi_mascot_2d.png", width=35)
                
            bal = customer_record['Avg_Balance']
            if bal >= 90000000:
                vip_level = "👑 로얄 (Royal) 고객"
            elif bal >= 75000000:
                vip_level = "🥇 골드 (Gold) 고객"
            elif bal >= 60000000:
                vip_level = "🥈 톱 (Top) 고객"
            elif bal >= 45000000:
                vip_level = "🥉 에이스 (Ace) 고객"
            else:
                vip_level = "🌱 프라임 (Prime) 고객"
                
            st.markdown(f"""
            <div style="background-color: #ffffff; border-radius: 12px; padding: 18px; border: 2px solid #e2f1f0; line-height: 1.8; box-shadow: 0 4px 6px rgba(0,0,0,0.01);">
                <p style="margin-top:0;">👤 <b>고객명:</b> {customer_record['Name']} ({customer_record['Age']}세)</p>
                <p>🆔 <b>고객 ID:</b> {customer_record['Customer_ID']}</p>
                <p>🏅 <b>고객 등급:</b> {vip_level}</p>
                <p style="margin-bottom:0;">🛠️ <b>직군 정보:</b> {customer_record['Job_Type']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        # 1-2) 5대 테마 관심도 시각화
        with prof_col2:
            st.markdown("###### 🧬 5대 테마 섹터별 관심도 분포")
            theme_names = ["반도체", "항공/방산", "2차전지", "리츠/배당", "금융/은행"]
            theme_scores = [customer_record[t] for t in theme_names]
            
            fig_theme_bar = go.Figure(data=[go.Bar(
                x=theme_scores,
                y=theme_names,
                orientation='h',
                marker_color='#00bda7',
                text=[f"{s}점" for s in theme_scores],
                textposition='auto',
            )])
            fig_theme_bar.update_layout(
                height=85,
                margin=dict(l=5, r=5, t=5, b=5),
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_theme_bar, use_container_width=True)
            
        # 1-3) 자산 누수율(Leakage Rate) 분석
        with prof_col3:
            st.markdown("###### ⚠️ 자산 누수율(Leakage Rate) 분석")
            r_score = customer_record['Risk_Score']
            r_level = customer_record['Risk_Level']
            risk_class = "risk-high" if r_level == "고위험" else ("risk-medium" if r_level == "중위험" else "risk-low")
            
            # 빨간색 느낌의 Progress Bar 생성 (0% 또는 저위험일 경우 다른 톤앤매너)
            bar_color = "#ef4444" if r_score > 0 else "#cbd5e1"
            progress_bar_html = f"""
            <div style="width: 100%; background-color: #f1f5f9; border-radius: 6px; height: 10px; margin-top: 6px; margin-bottom: 8px; overflow: hidden; border: 1px solid #e2f1f0;">
                <div style="width: {r_score:.1f}%; background-color: {bar_color}; height: 100%; border-radius: 6px;"></div>
            </div>
            """
            
            st.markdown(f"""
            <div style="background-color: #ffffff; border-radius: 12px; padding: 16px; border: 2px solid #e2f1f0; line-height: 1.8; box-shadow: 0 4px 6px rgba(0, 189, 167, 0.01);">
                <p style="margin-top:0; margin-bottom: 4px;">⚠️ <b>자산 누수율:</b> <span class="{risk_class}">{r_score:.1f}% ({r_level})</span></p>
                {progress_bar_html}
                <p style="margin-top: 4px; margin-bottom: 0;">💸 <b>월급날 이체비:</b> {customer_record['Salary_Day_Transfer']*100:.1f}%</p>
                <p style="margin-bottom:0;">⭐ <b>주력 관심 테마:</b> {customer_record['Main_Theme']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")

        # 2. 제언 시뮬레이션 & Playbook
        st.markdown("##### 💡 2단계: 자산 방어 시뮬레이션 및 마케팅 전략 제언")
        sim_col, playbook_col = st.columns([1.1, 1.3])
        
        # 2-1) 시뮬레이션
        with sim_col:
            sim_t_col, sim_i_col = st.columns([8, 1])
            with sim_t_col:
                st.markdown("###### 🎛️ 포트폴리오 자산 방어 시뮬레이터")
            with sim_i_col:
                st.image("dandi_mascot_2d.png", width=45)
            proposed_wrap_amt = st.slider(
                "테마 특화 랩 가입 제안 금액 (원)",
                min_value=0,
                max_value=int(customer_record['Avg_Balance']),
                value=int(customer_record['Outflow_Risk_Asset']),
                step=1000000,
                format="%d"
            )
            
            curr_deposit = customer_record['Avg_Balance'] * (1 - customer_record['Salary_Day_Transfer'])
            curr_outflow = customer_record['Avg_Balance'] * customer_record['Salary_Day_Transfer']
            current_expected_yield = (curr_deposit * 0.02) + (curr_outflow * 0.015)
            
            prop_wrap = proposed_wrap_amt
            prop_outflow = max(0.0, curr_outflow - proposed_wrap_amt)
            prop_deposit = customer_record['Avg_Balance'] - prop_wrap - prop_outflow
            proposed_expected_yield = (prop_deposit * 0.02) + (prop_outflow * 0.015) + (prop_wrap * 0.075)
            expected_tax_saving = int(prop_wrap * 0.075 * 0.154) if prop_wrap > 0 else 0
            
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border-radius: 12px; padding: 12px 18px; border: 1px solid #bbf7d0; margin-bottom:10px; text-align:center;">
                <span style="color: #166534; font-size:13px; font-weight:600;">💡 제안 포트폴리오의 연간 세액 절감 효과</span>
                <h4 style="margin: 3px 0 0 0; color: #15803d; font-weight:700;">연간 약 ₩{expected_tax_saving:,} 절세 예상</h4>
            </div>
            """, unsafe_allow_html=True)
            
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Bar(
                name='현재 종합 포트폴리오',
                x=['연간 기대 수익'],
                y=[current_expected_yield],
                marker_color='#cbd5e1',
                text=[f"{int(current_expected_yield):,}원"],
                textposition='auto',
            ))
            fig_sim.add_trace(go.Bar(
                name='제안 종합 포트폴리오',
                x=['연간 기대 수익'],
                y=[proposed_expected_yield],
                marker_color='#00bda7',
                text=[f"{int(proposed_expected_yield):,}원"],
                textposition='auto',
            ))
            fig_sim.update_layout(
                barmode='group',
                height=120,
                margin=dict(l=5, r=5, t=5, b=5),
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_sim, use_container_width=True)

        # 2-2) Playbook (크기 조정: 80px 마스코트 이미지 배치)
        with playbook_col:
            st.markdown("###### 🛡️ 단디의 🧲 마그넷 솔루션 추천")
            play_layout_dandi, play_layout_content = st.columns([1, 4.2])
            
            with play_layout_dandi:
                st.image("dandi_mascot_2d.png", width=80)
                st.markdown("""
                <div style="background-color: #f0fdf4; border: 1px solid #ccfbf1; padding: 6px; border-radius: 8px; font-size: 11px; text-align: center; color: #00bda7; font-weight: bold; margin-top: 5px;">
                    "1:1 맞춤<br>대본 보라구!"
                </div>
                """, unsafe_allow_html=True)
                
            with play_layout_content:
                theme = customer_record['Main_Theme']
                prod_chips = "".join([f'<span class="product-chip">{prod}</span>' for prod in products.get(theme, [])])
                if theme == "반도체":
                    st.markdown(f"""
                    <div class="playbook-card">
                        <h5 style="margin: 0; color: #00bda7; font-weight:700;">⚙️ 반도체 슈퍼사이클 랩 어카운트 제안 전략</h5>
                        <div class="script-box">
                            🗣 <b>상담 추천 제안 대본:</b><br>
                            "고객님, 매달 월급날마다 직접 증권사로 자금({customer_record['Salary_Day_Transfer']*100:.1f}%)을 이체하여 반도체 개별 종목을 매매하시는 것보다, 위험 통제력이 입증되고 연간 약 ₩{expected_tax_saving:,}의 절세 혜택도 가능한 당행의 <b>'iM 글로벌 AI 반도체 랩'</b>을 권유해 드립니다."
                        </div>
                        <div style="margin-top: 8px;">
                            <span style="font-size:11px; color:#475569; font-weight:600; display:block; margin-bottom:4px;">🧲 마그넷 솔루션 추천:</span>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">{prod_chips}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif theme == "2차전지":
                    st.markdown(f"""
                    <div class="playbook-card">
                        <h5 style="margin: 0; color: #00bda7; font-weight:700;">🔋 친환경 배터리 혁신 성장 랩 제안 전략</h5>
                        <div class="script-box">
                            🗣 <b>상담 추천 제안 대본:</b><br>
                            "고객님, 최근 급변하는 2차전지 주식 시장의 직간접 투자 변동성 위험을 감내하시기보다, 밸류체인 내 우량 핵심 기업 위주로 자동 분산하고 연간 약 ₩{expected_tax_saving:,}의 세금 이연 혜택이 적용되는 당행의 <b>'K-배터리 밸류체인 랩'</b>을 추천합니다."
                        </div>
                        <div style="margin-top: 8px;">
                            <span style="font-size:11px; color:#475569; font-weight:600; display:block; margin-bottom:4px;">🧲 마그넷 솔루션 추천:</span>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">{prod_chips}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif theme == "항공/방산":
                    st.markdown(f"""
                    <div class="playbook-card">
                        <h5 style="margin: 0; color: #00bda7; font-weight:700;">🚀 K-방산 글로벌 리더 랩 제안 전략</h5>
                        <div class="script-box">
                            🗣 <b>상담 추천 제안 대본:</b><br>
                            "고객님, 수출 호조로 장기 실적 우상향이 기대되는 항공/방산 섹터에 직접 투자하시는 대신, 당행의 체계적인 전략 포트폴리오를 통해 연간 약 ₩{expected_tax_saving:,}의 소득 이연 절세 혜택과 함께 장기 분산 운용하는 <b>'iM 방산 테마 랩'</b>을 검토해보십시오."
                        </div>
                        <div style="margin-top: 8px;">
                            <span style="font-size:11px; color:#475569; font-weight:600; display:block; margin-bottom:4px;">🧲 마그넷 솔루션 추천:</span>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">{prod_chips}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif theme == "리츠/배당":
                    st.markdown(f"""
                    <div class="playbook-card">
                        <h5 style="margin: 0; color: #00bda7; font-weight:700;">🏢 비과세 월배당 리츠 랩 제안 전략</h5>
                        <div class="script-box">
                            🗣 <b>상담 추천 제안 대본:</b><br>
                            "고객님, 안정적인 고정 캐시플로우 창출을 위해 주식을 직접 운용하시는 번거로움 대신, 매달 정기적으로 현금 배당을 수취하면서 연간 약 ₩{expected_tax_saving:,}의 우수한 절세 효과까지 적용되는 <b>'iM 글로벌 부동산 리츠 랩'</b>을 제안합니다."
                        </div>
                        <div style="margin-top: 8px;">
                            <span style="font-size:11px; color:#475569; font-weight:600; display:block; margin-bottom:4px;">🧲 마그넷 솔루션 추천:</span>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">{prod_chips}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="playbook-card">
                        <h5 style="margin: 0; color: #00bda7; font-weight:700;">📈 밸류업 금융지주 배당 강화 랩 제안 전략</h5>
                        <div class="script-box">
                            🗣 <b>상담 추천 제안 대본:</b><br>
                            "고객님, 최근 국가적 밸류업 프로그램 최대 수혜주인 우량 금융 및 은행 섹터 투자를 적극 고려 중이시라면, 연간 약 ₩{expected_tax_saving:,}의 금융소득 종합과세 절세 및 원천 이연 혜택이 적용되는 당행의 <b>'금융 밸류업 고배당 랩'</b>으로 장기 투자를 제안합니다."
                        </div>
                        <div style="margin-top: 8px;">
                            <span style="font-size:11px; color:#475569; font-weight:600; display:block; margin-bottom:4px;">🧲 마그넷 솔루션 추천:</span>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">{prod_chips}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # 인터랙티브 방어 버튼 (가장 중요)
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                cust_id = customer_record['Customer_ID']
                is_defended = cust_id in st.session_state['defended_customers']
                
                if is_defended:
                    st.button("✅ 자산 안전 고정 완료 (방어 성공)", key=f"defended_btn_{cust_id}", disabled=True, use_container_width=True)
                else:
                    if st.button("🚀 마그넷 솔루션 가동 (방어 실행)", key=f"defend_btn_{cust_id}", use_container_width=True, type="primary"):
                        import time
                        with st.spinner("솔루션 가동 중..."):
                            time.sleep(1.5) # 1.5초간 애니메이션 노출
                        st.session_state['defended_customers'].add(cust_id)
                        st.success("방어 성공! 자산이 iM뱅크 내로 안전하게 고정되었습니다.")
                        st.rerun()

        st.markdown("---")

        # 3. CRM 및 PB 액션 센터
        st.markdown("##### 📂 3단계: CRM 이력 관리 및 마케팅 실행")
        crm_col, action_col = st.columns([1.3, 1])
        
        with crm_col:
            crm_t_col, crm_i_col = st.columns([8, 1])
            with crm_t_col:
                st.markdown("###### 📁 상담 및 마케팅 이력 (CRM)")
            with crm_i_col:
                st.image("dandi_mascot_2d.png", width=35)
            st.markdown(f"""
            <div class="crm-log">🗓️ <b>2026-05-15</b>: 상반기 VIP 세무/상속 1:1 상담 초청장 발송 완료 (PB 담당자)</div>
            <div class="crm-log">🗓️ <b>2026-04-10</b>: 1분기 정기 예금 만기 재유치 성공 (AUM 방어 ₩4,000만)</div>
            <div class="crm-log">🗓️ <b>2026-03-02</b>: 신년 맞이 VIP 명절 특별 감사 기프트 세트 택배 전달 완료</div>
            """, unsafe_allow_html=True)
            
        with action_col:
            act_t_col, act_i_col = st.columns([8, 1])
            with act_t_col:
                st.markdown("###### ⚡ 실시간 PB 마케팅 액션")
            with act_i_col:
                st.image("dandi_mascot_2d.png", width=35)
            action_user = customer_record['Name']
            if 'action_log' not in st.session_state:
                st.session_state['action_log'] = []
                
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("📧 이메일 발송", use_container_width=True):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_msg = f"[{now}] {action_user}님께 '{theme}' 특화 랩 절세 혜택 시뮬레이션 보고서 메일 전송 완료."
                    st.session_state['action_log'].append(log_msg)
                    st.toast(f"📧 {action_user} 고객님께 이메일 전송 완료!", icon="✅")
            with btn_col2:
                if st.button("💬 SMS 제안", use_container_width=True):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_msg = f"[{now}] {action_user}님께 '{theme}' 테마 랩 특화 제안 SMS 발송 완료."
                    st.session_state['action_log'].append(log_msg)
                    st.toast(f"💬 {action_user} 고객님께 제안 문자 발송 완료!", icon="💬")
            with btn_col3:
                if st.button("📞 유선 예약", use_container_width=True):
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_msg = f"[{now}] {action_user}님 이탈 방어 유선 상담 약속 등록 완료."
                    st.session_state['action_log'].append(log_msg)
                    st.toast(f"📞 {action_user} 고객님 유선 상담 등록 완료!", icon="📞")
            
            if st.session_state['action_log']:
                st.caption(f"✨ 최근 기록: {st.session_state['action_log'][-1]}")
            else:
                st.caption("현재 세션에 기록된 마케팅 로그가 없습니다.")

            # PB 실전 피칭 가이드 추가 (사용자 요청 반영 및 iM뱅크 스타일 최적화)
            st.markdown("---")
            st.markdown("##### 🎙️ PB 실전 피칭 가이드 (Script Generator)")

            theme = customer_record['Main_Theme']
            magnet_solutions = {
                '반도체': 'iM 글로벌 AI 반도체 랩',
                '항공/방산': 'iM 방산 테마 랩',
                '2차전지': 'K-배터리 밸류체인 랩',
                '리츠/배당': 'iM 글로벌 부동산 리츠 랩',
                '금융/은행': '금융 밸류업 고배당 랩'
            }
            t_data = {
                '관심섹터': theme,
                '마그넷솔루션': magnet_solutions.get(theme, 'iM 특화 솔루션 랩')
            }

            pitching_scripts = {
                '반도체': f"\"고객님, 최근 직접 투자하신 반도체 종목들이 시장 변동성 때문에 밤새 주가 보시느라 신경 많이 쓰이셨죠? 자금을 증권사로 옮겨 직접 대응하시는 것보다, 저희 은행의 **{t_data['마그넷솔루션']}**를 활용하시면 전문가가 알아서 포트폴리오를 리밸런싱해 드립니다. 특히 ISA 절세 계좌와 연계하시면 수익에 대한 세금까지 아낄 수 있는데, 잠시 안내해 드려도 괜찮으실까요?\"",
                
                '항공/방산': f"\"고객님, 지정학적 이슈로 최근 방산 섹터에 자산 이동을 고려 중이신 것을 확인했습니다. 개별 종목 직접 투자는 타이밍을 잡기 매우 까다롭습니다. 안정적인 기관 자금이 유입되는 **{t_data['마그넷솔루션']}**를 통해 리스크를 분산하면서 트렌드를 따라가시는 방향을 강력히 추천해 드립니다.\"",
                
                '2차전지': f"\"고객님, 배터리 섹터의 장기 성장성은 확실하지만 최근 단기 조정으로 변동성이 매우 커진 상황입니다. 이럴 때일수록 거치식 직접 투자보다는, 은행의 적립식 랩 솔루션이나 **{t_data['마그넷솔루션']}**을 통해 분할 매수 효과를 누리시는 것이 자산을 안전하게 지키는 지름길입니다.\"",
                
                '리츠/배당': f"\"고객님, 최근 시장의 불확실성이 커지면서 매달 따박따박 들어오는 현금 흐름에 관심이 많으시죠? 증권사의 일반 고배당주는 원금 손실 위험이 크지만, 저희 은행에서 엄선한 **{t_data['마그넷솔루션']}**은 변동성을 극도로 낮추면서도 정기예금 금리의 2~3배에 달하는 월배당 효과를 기대할 수 있습니다.\"",
                
                '금융/은행': f"\"고객님, 밸류업 프로그램과 저PBR 우량주 트렌드를 아주 정확하게 포착하셨습니다. 저희 iM뱅크가 속한 금융 섹터의 강세를 포트폴리오에 담고 싶으시다면, 개별 은행주보다 섹터 전체를 추종하여 하방 경직성을 확보한 **{t_data['마그넷솔루션']}**이 현재 가장 유망한 대안입니다.\""
            }

            # 선택된 고객의 섹터에 맞는 스크립트 출력
            current_script = pitching_scripts.get(t_data['관심섹터'], "고객 맞춤형 제안 준비 중")

            st.markdown(f"""
            <div style="background-color: #fafdfd; padding: 15px; border-radius: 10px; border-left: 5px solid #00bda7; box-shadow: 0 2px 6px rgba(0, 189, 167, 0.02); margin-top: 5px;">
                <p style="font-style: italic; color: #334155; font-size: 11.5px; line-height: 1.5; margin: 0; font-weight: 500;">
                    {current_script}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("조회할 고객 번호 또는 이름을 입력해 주십시오.")

# ----------------- Tab 3: 시장 인사이트 -----------------
with tab3:
    col_t3_txt, col_t3_img = st.columns([12, 1])
    with col_t3_txt:
        st.subheader("📈 시장 섹터별 고객 분석 및 마케팅 인사이트")
        st.markdown("지점 전체 고객이 지닌 5대 메이저 테마 섹터에 대한 관심도를 바탕으로 섹터 특화 통계 및 마케팅 시나리오를 제공합니다.")
    with col_t3_img:
        st.image("dandi_mascot_2d.png", width=55)
    st.markdown("---")
    
    sectors = ["반도체", "항공/방산", "2차전지", "리츠/배당", "금융/은행"]
    selected_sector = st.selectbox("분석 및 마케팅 제안을 생성할 섹터를 선택하세요", sectors, index=0)
    
    if not filtered_df.empty:
        # 섹터 기준 데이터 분석
        sector_scores = filtered_df[selected_sector]
        avg_score = sector_scores.mean()
        high_interest_df = filtered_df[filtered_df[selected_sector] >= 60]
        high_interest_count = len(high_interest_df)
        high_interest_ratio = (high_interest_count / len(filtered_df)) * 100
        
        # 해당 섹터에 대한 총 평잔 자금 규모
        total_balance_sector = filtered_df[filtered_df['Main_Theme'] == selected_sector]['Avg_Balance'].sum()
        
        # 3대 분석 카드 배치
        sec_kpi1, sec_kpi2, sec_kpi3 = st.columns(3)
        with sec_kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <h6 style="color: #64748b; margin:0; font-weight:600;">'{selected_sector}' 평균 관심 점수</h6>
                <h3 style="color: #00bda7; margin: 4px 0 0 0; font-weight: 700; font-family: 'Outfit';">{avg_score:.1f} 점</h3>
            </div>
            """, unsafe_allow_html=True)
        with sec_kpi2:
            st.markdown(f"""
            <div class="kpi-card">
                <h6 style="color: #64748b; margin:0; font-weight:600;">고관심 고객 수 (60점 이상)</h6>
                <h3 style="color: #0d9488; margin: 4px 0 0 0; font-weight: 700; font-family: 'Outfit';">{high_interest_count}명 ({high_interest_ratio:.1f}%)</h3>
            </div>
            """, unsafe_allow_html=True)
        with sec_kpi3:
            st.markdown(f"""
            <div class="kpi-card">
                <h6 style="color: #64748b; margin:0; font-weight:600;">'{selected_sector}' 선호군 자산 규모</h6>
                <h3 style="color: #fb923c; margin: 4px 0 0 0; font-weight: 700; font-family: 'Outfit';">₩{total_balance_sector:,}</h3>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(" ")
        
        # 시각화 및 TOP 5 리스트 분할
        sec_chart_col, sec_list_col = st.columns([1.5, 1.2])
        
        with sec_chart_col:
            sec_t_col, sec_i_col = st.columns([8, 1])
            with sec_t_col:
                st.markdown(f"##### 📊 이탈 등급별 {selected_sector} 관심도 점수 분포")
            with sec_i_col:
                st.image("dandi_mascot_2d.png", width=45)
            fig_sec_hist = px.histogram(
                filtered_df,
                x=selected_sector,
                color='Risk_Level',
                color_discrete_map={'고위험': '#f87171', '중위험': '#fb923c', '저위험': '#00bda7'},
                labels={selected_sector: '관심도 점수'},
                nbins=25,
                barmode='overlay',
                height=180
            )
            fig_sec_hist.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#fafdfd",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_sec_hist, use_container_width=True)
            
        with sec_list_col:
            top_t_col, top_i_col = st.columns([8, 1])
            with top_t_col:
                st.markdown(f"##### 🎯 {selected_sector} 최선호 고관심 고객 TOP 5")
            with top_i_col:
                st.image("dandi_mascot_2d.png", width=45)
            top_5_sec = filtered_df.sort_values(by=selected_sector, ascending=False).head(5).copy()
            top_5_sec['Avg_Balance_Formatted'] = top_5_sec['Avg_Balance'].apply(lambda x: f"{x:,} 원")
            top_5_sec['Transfer_Out_Ratio_Formatted'] = top_5_sec['Salary_Day_Transfer'].apply(lambda x: f"{x*100:.1f}%")
            top_5_sec['Sector_Score_Formatted'] = top_5_sec[selected_sector].apply(lambda x: f"{x}점")
            
            st.dataframe(
                top_5_sec[['Customer_ID', 'Name', 'Job_Type', 'Avg_Balance_Formatted', 'Transfer_Out_Ratio_Formatted', 'Sector_Score_Formatted', 'Risk_Level']],
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("---")
        
        # 섹터 종합 코멘터리 (여기에도 미니 단디 마스코트 90px 배치)
        col_c_i, col_c_t = st.columns([1, 12])
        with col_c_i:
            st.image("dandi_mascot_2d.png", width=70)
        with col_c_t:
            st.markdown(f"##### 📝 단디의 '{selected_sector}' 섹터 종합 마케팅 코멘터리")
            
        if selected_sector == "반도체":
            comment = f"**반도체** 업종은 하드웨어 HBM 및 AI 연산 수요 급증으로 IT/개발자 및 연구 전문직군 고객들의 관심 비중이 높게 탐지됩니다. 현재 고관심 고객은 {high_interest_count}명이며, 이들의 자산 총액은 ₩{total_balance_sector:,}입니다. 자금 이탈율이 높은 고위험 성향에 대해서는 당행의 목표전환형 반도체 랩 상품 유치를 적극 추진하십시오."
        elif selected_sector == "2차전지":
            comment = f"**2차전지** 업종은 친환경 모빌리티 보급에 따른 높은 성장에 베팅하는 주식 성향이 짙은 고객군이 많습니다. 평균 관심 점수는 {avg_score:.1f}점으로 활발한 편이나 개별 주식 변동성에 따른 최근 평가손실 리스크가 있을 수 있으니, 당행의 핵심 양극재/배터리 셀 분산 랩 상품 가입을 유도하여 안정성을 제고하는 마케팅이 유리합니다."
        elif selected_sector == "항공/방산":
            comment = f"**항공/방산** 업종은 지정학적 불안 속에서 글로벌 국방 예산 확대에 힘입어 새로운 주도주로 정착하고 있습니다. 주로 안정적인 제조업 및 일반 사무직 성향의 자산 규모가 있는 고객군에서 고른 관심도를 보이고 있으며, 장기 성장이 명확한 당행 방산 매칭형 랩 어카운트로 자금을 방어하십시오."
        elif selected_sector == "리츠/배당":
            comment = f"**리츠/배당** 업종은 자산의 고정적인 월 배당 현금 흐름 창출을 최우선으로 선호하는 보수적/은퇴기 자산가들의 비중이 높습니다. 유출 위험 고객 중 리츠 고관심군인 {high_interest_count}명은 외부 증권사의 변동성이 높은 개별 배당주 매매보다, 세금 이연 혜택이 우수한 당행의 월배당 인컴 리츠 랩 가입을 적극 타겟팅하십시오."
        else: # 금융/은행
            comment = f"**금융/은행** 업종은 한국 증시 밸류업 프로그램 가시화 및 저PBR 금융 우량주의 정기 배당 매력으로 중장기 보수적 투자 가치가 증가하고 있습니다. 특히 안정 성향의 대형 자산가 고객층에서 안정적인 락인이 가능하며, 비과세 종합저축 최적화 및 밸류업 금융 연동 랩을 제안하는 것이 관계 락인에 효과적입니다."
            
        st.markdown(f"""
        <div style="background-color: #fafbfc; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; line-height: 1.8; box-shadow: 0 4px 6px rgba(0,0,0,0.01); font-size:14.5px; color:#334155; margin-top: 10px;">
            {comment}
        </div>
        """, unsafe_allow_html=True)
        
        # 섹터별 추천 상품 목록을 가로 칩 형태로 가독성 있게 표시
        st.markdown(" ")
        st.markdown(f"##### 📦 {selected_sector} 섹터 iM뱅크 추천 상품 포트폴리오")
        
        prod_html = "".join([f'<span class="product-chip">{prod}</span>' for prod in products.get(selected_sector, [])])
        st.markdown(f"""
        <div style="background-color: #ffffff; border-radius: 12px; padding: 12px 18px; border: 1.5px solid #e2f1f0; box-shadow: 0 2px 6px rgba(0, 189, 167, 0.01); margin-top: 5px;">
            <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                {prod_html}
            </div>
            <div style="margin-top: 8px; font-size: 11px; color: #64748b;">
                💡 <i>해당 상품들은 iM뱅크 PB 상품 매핑 알고리즘에 따라 선정된 최적의 펀드 및 신탁 상품 포트폴리오입니다.</i>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("필터에 부합하는 고객 데이터가 없습니다.")
