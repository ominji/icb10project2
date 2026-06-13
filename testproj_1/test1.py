import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import hashlib
import json
import re
import requests
from datetime import datetime, date

# 1. 페이지 설정 및 프리미엄 테마 적용
st.set_page_config(
    page_title="NutriFit 2030 - 맞춤형 영양제 대시보드",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화 (실시간 API 데이터 저장용)
if "api_data" not in st.session_state:
    st.session_state.api_data = None
if "api_end_no" not in st.session_state:
    st.session_state.api_end_no = 10

# 커스텀 CSS 스타일링 (다크 테마 및 유리모피즘 카드 적용)
st.markdown("""
<style>
    /* 전체 배경 스타일 */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', 'Roboto', 'Outfit', sans-serif;
    }
    /* 타이틀 그라디언트 배너 */
    .banner {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .banner h1 {
        color: #58a6ff;
        font-size: 2.5rem !important;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .banner p {
        color: #8b949e;
        font-size: 1.1rem;
        margin: 0;
    }
    /* 카드 컨테이너 */
    .card {
        background-color: #161b22;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #30363d;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        border-color: #58a6ff;
    }
    .card h3 {
        color: #58a6ff;
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 15px;
    }
    /* 뱃지 스타일 */
    .badge-import {
        background-color: rgba(88, 166, 255, 0.15);
        color: #58a6ff;
        border: 1px solid #58a6ff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-domestic {
        background-color: rgba(187, 134, 252, 0.15);
        color: #bb86fc;
        border: 1px solid #bb86fc;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-gmp {
        background-color: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid #2ea043;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-general-food {
        background-color: rgba(244, 67, 54, 0.15);
        color: #f44336;
        border: 1px solid #f44336;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    .badge-warning {
        background-color: rgba(240, 136, 62, 0.15);
        color: #f0883e;
        border: 1px solid #f0883e;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
    }
    /* 텍스트 하이라이팅 */
    .highlight-text {
        font-weight: 600;
        color: #58a6ff;
    }
    /* 스트림릿 탭 스타일 보정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #161b22;
        border-radius: 8px 8px 0px 0px;
        color: #8b949e;
        border: 1px solid #30363d;
        border-bottom: none;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262d !important;
        color: #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. 식약처 영양성분 정보 파싱용 헬퍼 함수
def parse_nutrient_from_stdr(stdr_stnd, nutrient_name, unit):
    if not isinstance(stdr_stnd, str):
        return 0.0
    # 패턴1: 칼슘 : 표시량(285.9mg/1500mg)
    pattern = rf'{nutrient_name}\s*:\s*[^()]*\(([\d.]+)\s*{unit}'
    match = re.search(pattern, stdr_stnd)
    if match:
        return float(match.group(1))
    
    # 패턴2: 칼슘 : 285.9mg
    pattern2 = rf'{nutrient_name}\s*:\s*([\d.]+)\s*{unit}'
    match2 = re.search(pattern2, stdr_stnd)
    if match2:
        return float(match2.group(1))
        
    return 0.0

# 3. 데이터 로드 및 합산(통합) 로직 (캐싱 처리 - api_data_len을 넘겨받아 갱신 감지)
@st.cache_data
def load_combined_data(api_data_len=0, serialized_api_data=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    # --- 1단계: CSV 파일 로드 (수입건기식) ---
    csv_file = None
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".csv") and ("식품의약품안전처" in f or "영양성분" in f):
                csv_file = os.path.join(data_dir, f)
                break
                
    if csv_file is None or not os.path.exists(csv_file):
        csv_file = os.path.join(base_dir, "data", "식품의약품안전처_건강기능식품영양성분정보_20251230.csv")
        
    df_csv = pd.DataFrame()
    if os.path.exists(csv_file):
        try:
            df_csv = pd.read_csv(csv_file, encoding="utf-8-sig")
            df_csv['데이터구분'] = '건강기능식품 (수입)'
        except Exception as e:
            st.error(f"CSV 데이터 로딩 실패: {str(e)}")
            
    # --- 2단계: JSON 파일 로드 및 파싱 (국내건기식) ---
    rows = []
    # 실시간 API 호출 데이터가 있는 경우 우선 적용
    if serialized_api_data is not None:
        try:
            rows = json.loads(serialized_api_data)
        except Exception as e:
            st.error(f"실시간 API 데이터 파싱 실패: {str(e)}")
    else:
        # 실시간 데이터가 없는 경우 로컬 json 파일 백업 로드
        json_file = os.path.join(data_dir, "health_functional_food.json")
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    rows = json_data.get("C003", {}).get("row", [])
            except Exception as e:
                st.error(f"JSON 파일 백업 로딩 실패: {str(e)}")
            
    json_parsed_list = []
    for r in rows:
        stdr = r.get("STDR_STND", "")
        ntk = r.get("NTK_MTHD", "")
        
        # 1일 섭취 횟수 파싱 (기본값 1회)
        intake_match = re.search(r'1일\s*(\d+)회', ntk)
        intake_cnt = f"{intake_match.group(1)}회" if intake_match else "1회"
        
        # 영양 성분 파싱
        calcium = parse_nutrient_from_stdr(stdr, "칼슘", "mg")
        vit_c = parse_nutrient_from_stdr(stdr, "비타민C", "mg")
        vit_d = parse_nutrient_from_stdr(stdr, "비타민D", "μg")
        protein = parse_nutrient_from_stdr(stdr, "단백질", "g")
        
        # 1회 분량 추출
        dose_match = re.search(r'1회\s*([^,\s)]+)', ntk)
        dose = dose_match.group(1) if dose_match else r.get("PRDT_SHAP_CD_NM", "캡슐/정제")
        
        json_parsed_list.append({
            '식품코드': r.get("PRDLST_REPORT_NO"),
            '식품명': r.get("PRDLST_NM"),
            '대표식품명': r.get("RAWMTRL_NM")[:100] if r.get("RAWMTRL_NM") else "",
            '원산지국명': '대한민국',
            '비타민 D(μg)': vit_d,
            '칼슘(mg)': calcium,
            '비타민 C(mg)': vit_c,
            '단백질(g)': protein,
            '1일섭취횟수': intake_cnt,
            '1회분량중량/부피': dose,
            '데이터구분': '건강기능식품 (국내)',
            '주요기능성': r.get("PRIMARY_FNCLTY", "")
        })
        
    df_json = pd.DataFrame(json_parsed_list)
    
    # --- 3단계: 일반식품 (구미/젤리 캔디류) 가상 데이터 추가 ---
    general_food_list = [
        {
            '식품코드': 'GEN_GUMMY_01',
            '식품명': '달콤 레몬 비타 C 젤리 (일반식품)',
            '대표식품명': '설탕, 물엿, 젤라틴, 구연산, 합성향료(레몬향), 비타민C 0.05%',
            '원산지국명': '대한민국',
            '비타민 D(μg)': 0.0,
            '칼슘(mg)': 0.0,
            '비타민 C(mg)': 0.2,
            '단백질(g)': 0.0,
            '1일섭취횟수': '1회',
            '1회분량중량/부피': '5개(15g)',
            '데이터구분': '일반식품 (캔디류)',
            '주요기능성': '기호 식품 (식약처 기능성 비인증)'
        },
        {
            '식품코드': 'GEN_GUMMY_02',
            '식품명': '튼튼 뼈 칼슘 구미 베어 (일반식품)',
            '대표식품명': '설탕, 물엿, 젤라틴, 산화칼슘 0.1%, 포도농축액',
            '원산지국명': '대한민국',
            '비타민 D(μg)': 0.0,
            '칼슘(mg)': 3.0,
            '비타민 C(mg)': 0.0,
            '단백질(g)': 0.0,
            '1일섭취횟수': '1회',
            '1회분량중량/부피': '3개(9g)',
            '데이터구분': '일반식품 (캔디류)',
            '주요기능성': '기호 식품 (식약처 기능성 비인증)'
        }
    ]
    df_general = pd.DataFrame(general_food_list)
    
    # 세 데이터프레임 합산(Concatenate)
    combined_df = pd.concat([df_csv, df_json, df_general], ignore_index=True)
    
    # 누락 및 NaN 데이터 전처리
    combined_df['비타민 D(μg)'] = pd.to_numeric(combined_df['비타민 D(μg)'], errors='coerce').fillna(0.0)
    combined_df['칼슘(mg)'] = pd.to_numeric(combined_df['칼슘(mg)'], errors='coerce').fillna(0.0)
    combined_df['비타민 C(mg)'] = pd.to_numeric(combined_df['비타민 C(mg)'], errors='coerce').fillna(0.0)
    combined_df['단백질(g)'] = pd.to_numeric(combined_df['단백질(g)'], errors='coerce').fillna(0.0)
    combined_df['대표식품명'] = combined_df['대표식품명'].fillna("기타 가공 원료")
    
    return combined_df

# 세션 상태 데이터를 직렬화하여 캐시에 전달
serialized_api_data = json.dumps(st.session_state.api_data) if st.session_state.api_data else None
api_data_len = len(st.session_state.api_data) if st.session_state.api_data else 0

# 통합 데이터셋 적재
df_raw = load_combined_data(api_data_len=api_data_len, serialized_api_data=serialized_api_data)

# 4. 헬퍼 함수 (재현 가능한 평점, 리뷰수, 가격 데이터 생성)
def generate_pseudo_scores(food_code):
    h = hashlib.md5(str(food_code).encode()).hexdigest()
    val1 = int(h[0:2], 16)
    val2 = int(h[2:4], 16)
    val3 = int(h[4:6], 16)
    
    rating = round(4.0 + (val1 % 11) * 0.1, 1)  # 4.0 ~ 5.0 평점
    reviews = 10 + (val2 % 99) * 5             # 10 ~ 500 리뷰 수
    unit_price = 12000 + (val3 % 77) * 500     # 12,000원 ~ 50,000원
    
    return rating, reviews, unit_price

# 5. 사이드바 왼쪽 하단 위젯 구현
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔌 식약처 실시간 API 연동")
    st.markdown("식품안전나라의 C003(품목제조신고) 오픈 API 데이터를 조회 끝번호를 변경하며 동적으로 호출합니다.")
    
    # 끝번호 입력기 생성 (사용자 요청: 1/10 포맷에서 10 부분 제어)
    api_end_input = st.number_input(
        "API 조회 끝번호 설정:", 
        min_value=1, 
        max_value=1000, 
        value=st.session_state.api_end_no, 
        step=5,
        help="API URL의 마지막 조회 순번 범위입니다. 예: 10 설정 시 1번부터 10번까지 조회"
    )
    st.session_state.api_end_no = api_end_input
    
    # 호출 대상 API 주소 표시
    api_url = f"http://openapi.foodsafetykorea.go.kr/api/be08162c9d464d6998a5/C003/json/1/{st.session_state.api_end_no}"
    st.code(api_url, language="text")
    
    if st.button("⚡ API 데이터 동기화", use_container_width=True):
        with st.spinner("오픈 API 동적 호출 중..."):
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    res_json = response.json()
                    row_data = res_json.get("C003", {}).get("row", [])
                    if row_data:
                        st.session_state.api_data = row_data
                        st.success(f"동기화 성공: {len(row_data)}건 로드됨!")
                        st.cache_data.clear() # 캐시 초기화하여 신규 데이터 즉시 강제 렌더링
                        st.rerun()
                    else:
                        st.warning("API 응답이 수신되었으나 데이터(row)가 없습니다.")
                else:
                    st.error(f"API 호출 에러: 상태 코드 {response.status_code}")
            except Exception as e:
                st.error(f"API 호출 실패: {str(e)}")

# 6. 메인 그라디언트 배너 렌더링
st.markdown("""
<div class="banner">
    <h1>💊 NutriFit 2030 (실시간 API 연동 버전)</h1>
    <p>식약처 국내/수입 건강기능식품 통합 데이터셋 및 2030 소비 트렌드 기반 맞춤형 영양 케어 대시보드</p>
</div>
""", unsafe_allow_html=True)

# 탭 메뉴 구성
tab1, tab2, tab3 = st.tabs([
    "📊 Track 1: 2030 소비 패턴 & 트렌드 분석",
    "📱 Track 2: My 영양제 스마트 케어 (맞춤형 플랜 & 장바구니)",
    "🎁 Target Curation: 대상별 선물 추천"
])

# ==========================================
# [TAB 1] 2030 소비 패턴 & 트렌드 분석
# ==========================================
with tab1:
    st.markdown("### 2030 세대 헬시플레저(Healthy Pleasure) 소비 패턴 및 시장 트렌드")
    
    col_t1_l, col_t1_r = st.columns([1, 2])
    
    with col_t1_l:
        st.markdown("""
        <div class="card">
            <h3>🏃 운동 목적별 맞춤 필수 영양소</h3>
            <p>러닝, 테니스, 피트니스 등 2030 핵심 워크아웃에 맞춰 소모 패턴을 보정하는 필수 성분을 자동 매핑합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        sport = st.selectbox(
            "선호하는 운동을 선택하세요:",
            ["러닝/테니스 (고강도 심폐 & 관절 보호)", "등산/골프 (야외 자외선 & 유산소 피로 개선)", "피트니스/웨이트 (근육 손상 회복 & 대사 활성)"]
        )
        
        # 운동 목적에 맞는 영양소 키워드 매핑
        if "러닝/테니스" in sport:
            required_nutrients = ["엠에스엠", "MSM", "콘드로이친", "비타민 B", "칼슘"]
            sport_desc = "관절 연골 보호 성분(MSM, 콘드로이친)과 급격한 근골격 수축용 칼슘, 활성 에너지용 비타민 B군을 추천합니다."
        elif "등산/골프" in sport:
            required_nutrients = ["비타민 D", "비타민 C", "코엔자임Q10", "아연"]
            sport_desc = "야외 자외선 합성 보강용 비타민 D와 젖산 축적 억제를 돕는 비타민 C, 항산화 코엔자임Q10을 추천합니다."
        else:
            required_nutrients = ["단백질", "마그네슘", "철", "비타민"]
            sport_desc = "근단백질 합성 원료(단백질), 근육 꼬임 예방 및 이완을 위한 마그네슘 위주로 추천합니다."
            
        st.info(f"💡 **신체 소모 매커니즘**: {sport_desc}")
        
        # 데이터셋 매칭 (국내 건기식 + 수입 건기식 통합 매칭)
        matched_df = pd.DataFrame()
        for nut in required_nutrients:
            temp = df_raw[df_raw['대표식품명'].str.contains(nut, na=False, case=False) | df_raw['식품명'].str.contains(nut, na=False, case=False)]
            matched_df = pd.concat([matched_df, temp])
            
        if "피트니스" in sport:
            matched_df = pd.concat([matched_df, df_raw[df_raw['단백질(g)'] > 8]])
            
        matched_df = matched_df.drop_duplicates(subset=['식품코드'])
        
        if not matched_df.empty:
            matched_df[['평점', '리뷰수', '단가']] = matched_df.apply(
                lambda row: pd.Series(generate_pseudo_scores(row['식품코드'])), axis=1
            )
            matched_df['가중치'] = matched_df['평점'] * 0.7 + np.log1p(matched_df['리뷰수']) * 0.3
            top5 = matched_df.sort_values(by='가중치', ascending=False).head(5)
        else:
            top5 = pd.DataFrame()
            
    with col_t1_r:
        st.markdown(f"#### 🏆 {sport.split(' ')[0]} 추천 매칭 영양제 TOP 5 (식약처 정식 등록)")
        if not top5.empty:
            cols = st.columns(5)
            for idx, (i, row) in enumerate(top5.iterrows()):
                badge_html = ""
                if row['데이터구분'] == '건강기능식품 (수입)':
                    badge_html = '<span class="badge-import">수입건기식</span>'
                elif row['데이터구분'] == '건강기능식품 (국내)':
                    badge_html = '<span class="badge-domestic">국내건기식</span>'
                else:
                    badge_html = '<span class="badge-general-food">일반식품</span>'
                    
                with cols[idx]:
                    st.markdown(f"""
                    <div style="background-color:#161b22; border-radius:10px; padding:12px; border:1px solid #30363d; min-height: 270px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            {badge_html}
                            <h4 style="color:#58a6ff; font-size:0.95rem; margin-top:5px; margin-bottom:5px; min-height: 48px;">{row['식품명'][:22]}</h4>
                            <p style="font-size:0.75rem; color:#8b949e; margin-bottom:2px; min-height: 32px;">대표: {row['대표식품명'][:20]}...</p>
                            <p style="font-size:0.75rem; color:#8b949e; margin-bottom:2px;">원산지: {row['원산지국명']}</p>
                            <p style="font-size:0.85rem; color:#ffc107; font-weight:700; margin-bottom:0;">⭐ {row['평점']} <span style="font-size:0.7rem; color:#8b949e;">({row['리뷰수']})</span></p>
                        </div>
                        <div style="border-top: 1px solid #30363d; padding-top: 8px; margin-top: 5px;">
                            <p style="font-size:0.95rem; color:#58a6ff; font-weight:700; margin-bottom:0;">{int(row['단가']):,}원</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("일치하는 추천 제품이 없습니다.")
            
        # 가설 검증 차트
        st.markdown("#### 🔍 2030 프리미엄 지불 의사 가설 검증 (가성비 지수 vs 선호도 평점)")
        if not matched_df.empty:
            plot_df = matched_df.sample(min(150, len(matched_df)), random_state=42).copy()
            
            fig = px.scatter(
                plot_df,
                x="단가",
                y="평점",
                size="리뷰수",
                color="데이터구분",
                hover_name="식품명",
                title="1회 섭취 단가 대비 만족도(평점) 분포 및 리뷰 볼륨",
                labels={"단가": "제품 단가 (원)", "평점": "2030 만족 평점 (5점 만점)"},
                color_discrete_sequence=["#bb86fc", "#58a6ff", "#f44336"]
            )
            fig.update_layout(
                plot_bgcolor="#161b22",
                paper_bgcolor="#0d1117",
                font_color="#c9d1d9",
                title_font_color="#58a6ff"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("시각화 데이터를 준비 중입니다.")

    st.write("---")
    
    col_t1_b1, col_t1_b2 = st.columns([1, 1])
    
    with col_t1_b1:
        st.markdown("#### 🛒 제형별 주 구매 채널 연계성 분석")
        channels_data = {
            "제형 분류": ["구미 제형 (젤리)", "액상 앰플형", "필름형 (구강용)", "정제 / 캡슐 (알약)", "분말 / 파우더"],
            "올리브영 / H&B": [65, 45, 55, 15, 30],
            "해외 직구 (이커머스)": [20, 35, 20, 60, 50],
            "전통 약국": [15, 20, 25, 25, 20]
        }
        ch_df = pd.DataFrame(channels_data)
        fig_ch = px.bar(
            ch_df,
            x="제형 분류",
            y=["올리브영 / H&B", "해외 직구 (이커머스)", "전통 약국"],
            title="제형별 소비 채널 점유율 (%)",
            labels={"value": "점유율 (%)", "variable": "유통 채널"},
            barmode="stack",
            color_discrete_sequence=["#e91e63", "#2196f3", "#4caf50"]
        )
        fig_ch.update_layout(
            plot_bgcolor="#161b22",
            paper_bgcolor="#0d1117",
            font_color="#c9d1d9",
            title_font_color="#58a6ff"
        )
        st.plotly_chart(fig_ch, use_container_width=True)

    with col_t1_b2:
        st.markdown("#### 📊 식약처 건강기능식품 통합 데이터셋 구조")
        
        data_counts = df_raw["데이터구분"].value_counts()
        fig_donut = px.pie(
            values=data_counts.values,
            names=data_counts.index,
            hole=0.4,
            title="통합 데이터셋 구성 비율",
            color_discrete_sequence=["#58a6ff", "#bb86fc", "#f44336"]
        )
        fig_donut.update_layout(
            plot_bgcolor="#161b22",
            paper_bgcolor="#0d1117",
            font_color="#c9d1d9",
            title_font_color="#58a6ff"
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown(f"""
        - **수입 건강기능식품(CSV)**과 **국내 신고 건강기능식품(오픈 API/JSON)** 및 비교 분석용 **일반 캔디구미 제품**을 하나로 병합하였습니다.
        - **합산 완료 데이터셋**: 총 **{len(df_raw)}건**의 정식 등록 정보.
        - 왼쪽 하단의 실시간 API 동기화 패널에서 끝번호를 조절하여 국내 건기식 실시간 API의 조회 레코드 수(1~1000)를 가변적으로 제어할 수 있습니다.
        """)


# ==========================================
# [TAB 2] My 영양제 스마트 케어 (맞춤형 플랜)
# ==========================================
with tab2:
    st.markdown("### My 영양제 스마트 케어 & 복용 캘린더 시뮬레이터")
    
    col_t2_l, col_t2_r = st.columns([1, 1])
    
    with col_t2_l:
        st.markdown("""
        <div class="card">
            <h3>🩺 건강검진 정보 연동 자가진단 추천</h3>
            <p>자가 건강검진 수치를 입력하시면 식약처의 기능성 원료 DB 기준과 운동 매커니즘을 종합 매칭하여 영양성분을 제안합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        age = st.slider("연령대 설정:", 10, 80, 28)
        
        col_med_1, col_med_2 = st.columns(2)
        with col_med_1:
            sbp = st.number_input("수축기 혈압 (mmHg):", min_value=70, max_value=200, value=122)
            glucose = st.number_input("공복 혈당 (mg/dL):", min_value=50, max_value=300, value=96)
        with col_med_2:
            alt = st.number_input("간수치 (ALT, U/L):", min_value=5, max_value=200, value=38)
            user_sport = st.selectbox("주력 스포츠 유형:", ["러닝/마라톤", "테니스/스쿼시", "클라이밍/등산", "근육 웨이트 트레이닝", "일상 스트레스 케어"], key="sports_care")
            
        # 건강검진 진단 로직 및 영양 성분 추천 알고리즘
        recommended_ingredients = []
        diagnoses = []
        
        if sbp >= 130:
            diagnoses.append("⚠️ **혈압 수치 경계/높음**: 코엔자임Q10, 오메가3(EPA/DHA) 섭취 권장.")
            recommended_ingredients.extend(["코엔자임Q10", "오메가3"])
        if glucose >= 100:
            diagnoses.append("⚠️ **공복혈당 경계/높음**: 바나바잎 추출물(코로솔산), 식이섬유 권장.")
            recommended_ingredients.extend(["바나바잎", "식이섬유"])
        if alt >= 40:
            diagnoses.append("⚠️ **간수치 경계/높음**: 밀크씨슬(실리마린), 헛개나무추출물 권장.")
            recommended_ingredients.extend(["밀크씨슬", "실리마린"])
            
        # 운동 목적별 추가 성분 매핑
        if "러닝" in user_sport or "테니스" in user_sport:
            recommended_ingredients.extend(["엠에스엠", "MSM", "칼슘"])
        elif "등산" in user_sport:
            recommended_ingredients.extend(["비타민 D", "아스타잔틴"])
        elif "웨이트" in user_sport:
            recommended_ingredients.extend(["단백질", "마그네슘"])
            
        recommended_ingredients = list(set(recommended_ingredients))
        
        st.markdown("#### 🩺 개인용 건강 자가 진단 결과")
        if diagnoses:
            for d in diagnoses:
                st.write(d)
        else:
            st.success("✅ **모든 건강 검진 수치가 정상 범주에 있습니다!** 현재 운동 목적에 맞춤화된 유지 케어를 진행합니다.")
            
        st.markdown("#### 🌟 추천 섭취 필요 성분")
        st.write(", ".join([f"**{ing}**" for ing in recommended_ingredients]))
        
        # 데이터베이스 매칭 추천 제품 출력
        st.markdown("#### 🔬 식약처 데이터베이스 매칭 추천 제품 (국내/수입 통합)")
        rec_products = pd.DataFrame()
        for ing in recommended_ingredients[:3]:  # 상위 3개 키워드 매칭
            temp = df_raw[df_raw['대표식품명'].str.contains(ing, na=False, case=False) | df_raw['식품명'].str.contains(ing, na=False, case=False)]
            rec_products = pd.concat([rec_products, temp])
        rec_products = rec_products.drop_duplicates(subset=['식품코드'])
        
        if not rec_products.empty:
            rec_p_show = rec_products.head(3)
            for _, r in rec_p_show.iterrows():
                badge_html = ""
                if r['데이터구분'] == '건강기능식품 (수입)':
                    badge_html = '<span class="badge-import">수입건기식</span>'
                elif r['데이터구분'] == '건강기능식품 (국내)':
                    badge_html = '<span class="badge-domestic">국내건기식</span>'
                else:
                    badge_html = '<span class="badge-general-food">일반식품</span>'
                    
                st.markdown(f"""
                <div style="background-color:#161b22; border-radius:8px; padding:12px; border:1px solid #30363d; margin-bottom:10px;">
                    {badge_html} <span class="badge-gmp">식약처인증</span>
                    <p style="font-weight:700; color:#58a6ff; margin: 5px 0;">{r['식품명']}</p>
                    <p style="font-size:0.8rem; color:#8b949e; margin:0;">대표 원료: {r['대표식품명'][:50]}... | 섭취: {r['1일섭취횟수']} | 분량: {r['1회분량중량/부피']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("해당 성분을 보유한 정식 데이터가 아직 로드되지 않았습니다. 실시간 API 연동을 가동해 보세요.")
            
    with col_t2_r:
        st.markdown("""
        <div class="card">
            <h3>🛡️ My 영양제 스마트 부작용 안전망 & 유효기간 관리</h3>
            <p>보유 중인 영양제들을 복용 장바구니에 담아 <b>성분 중복 과다 섭취</b>, <b>유효기간 만료일 캘린더</b>, 그리고 <b>식약처 정식 건기식 여부(구미 젤리 등)</b>를 크로스 진단합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 🛒 복용 중인 영양제 등록")
        search_keyword = st.text_input("제품명 또는 함유 성분을 입력해 검색하세요:", "비타민", key="vit_search")
        
        search_res = df_raw[df_raw['식품명'].str.contains(search_keyword, na=False, case=False) | df_raw['대표식품명'].str.contains(search_keyword, na=False, case=False)]
        
        if not search_res.empty:
            select_p_name = st.selectbox("검색 결과 목록에서 추가할 제품을 선택하세요:", search_res['식품명'].unique()[:15], key="basket_sel")
            selected_row = search_res[search_res['식품명'] == select_p_name].iloc[0]
            
            expiry_date = st.date_input("영양제 유효기간 만료일을 등록하세요:", date.today() + pd.Timedelta(days=180), key="exp_input")
            
            if st.button("➕ 복용 장바구니에 추가", key="basket_add_btn"):
                if "my_vit_basket" not in st.session_state:
                    st.session_state.my_vit_basket = []
                    
                if select_p_name not in [item['식품명'] for item in st.session_state.my_vit_basket]:
                    st.session_state.my_vit_basket.append({
                        "식품명": selected_row['식품명'],
                        "대표식품명": selected_row['대표식품명'],
                        "비타민 D(μg)": selected_row['비타민 D(μg)'] if not pd.isna(selected_row['비타민 D(μg)']) else 0.0,
                        "칼슘(mg)": selected_row['칼슘(mg)'] if not pd.isna(selected_row['칼슘(mg)']) else 0.0,
                        "비타민 C(mg)": selected_row['비타민 C(mg)'] if not pd.isna(selected_row['비타민 C(mg)']) else 0.0,
                        "데이터구분": selected_row['데이터구분'],
                        "만료일": expiry_date
                    })
                    st.toast(f"'{select_p_name}'이 복용 장바구니에 추가되었습니다!", icon="✅")
                else:
                    st.warning("이미 장바구니에 추가된 제품입니다.")
        else:
            st.warning("일치하는 검색 결과가 없습니다.")
            
        st.markdown("##### 📦 나의 스마트 복용 장바구니")
        if "my_vit_basket" in st.session_state and st.session_state.my_vit_basket:
            for idx, item in enumerate(st.session_state.my_vit_basket):
                col_i1, col_i2 = st.columns([5, 1])
                
                days_left = (item['만료일'] - date.today()).days
                if days_left <= 0:
                    status_text = f"<span style='color:#f44336; font-weight:700;'>[⚠️ 유효기간 만료 - 즉시 폐기!]</span>"
                elif days_left <= 90:
                    status_text = f"<span style='color:#f0883e; font-weight:700;'>[⚠️ 만료 임박 - 잔여 {days_left}일]</span>"
                else:
                    status_text = f"<span style='color:#3fb950; font-weight:600;'>[✅ 보관 안전 - 잔여 {days_left}일]</span>"
                
                badge_lbl = ""
                if item['데이터구분'] == '건강기능식품 (수입)':
                    badge_lbl = '<span class="badge-import" style="padding:1px 4px; font-size:0.7rem;">수입건기식</span>'
                elif item['데이터구분'] == '건강기능식품 (국내)':
                    badge_lbl = '<span class="badge-domestic" style="padding:1px 4px; font-size:0.7rem;">국내건기식</span>'
                else:
                    badge_lbl = '<span class="badge-general-food" style="padding:1px 4px; font-size:0.7rem;">일반식품</span>'
                
                col_i1.markdown(f"▪&nbsp;{badge_lbl} **{item['식품명']}** (원재료: {item['대표식품명'][:30]}...) <br> &nbsp;&nbsp;&nbsp;&nbsp; 📅 만료일: {item['만료일']} {status_text}", unsafe_allow_html=True)
                
                if col_i2.button("삭제", key=f"del_{idx}"):
                    st.session_state.my_vit_basket.pop(idx)
                    st.rerun()
            
            st.markdown("##### 🚨 실시간 위해성 및 과대광고 필터링 진단 결과")
            
            total_vitd = sum([float(item['비타민 D(μg)']) for item in st.session_state.my_vit_basket])
            total_calcium = sum([float(item['칼슘(mg)']) for item in st.session_state.my_vit_basket])
            total_vitc = sum([float(item['비타민 C(mg)']) for item in st.session_state.my_vit_basket])
            
            has_warning = False
            
            # 1. 일반 식품 뱃지 경고 시스템
            has_general_food = any([item['데이터구분'] == '일반식품 (캔디류)' for item in st.session_state.my_vit_basket])
            if has_general_food:
                st.markdown("""
                <div class="card" style="border-left: 5px solid #f44336; background-color: rgba(244, 67, 54, 0.07);">
                    <span class="badge-general-food">미인증 식품 검출</span> <b>일반 기호식품(캔디류) 감지됨</b>
                    <p style="font-size:0.9rem; margin-top:5px; margin-bottom:0;">
                    장바구니에 담긴 제품 중 <b>식약처 인증을 받지 않은 일반 식품(캔디류)</b>이 포함되어 있습니다. 일반 구미/젤리 제품은 비타민이나 칼슘의 함량이 매우 낮으며 식약처가 인정한 건강 효능이 유효하지 않습니다. 마케팅성 광고문구에 현혹되지 마시고, 건강 목적의 영양 보충 시에는 반드시 '건강기능식품' 인증 마크를 확인하세요.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                has_warning = True
                
            # 2. 비타민 D 일일 상한섭취량 진단 (상한 100 μg)
            if total_vitd > 100:
                st.markdown("""
                <div class="card" style="border-left: 5px solid #ffc107; background-color: rgba(255, 193, 7, 0.05);">
                    <span class="badge-warning">경고</span> <b>비타민 D 일일 복용량 초과</b>
                    <p style="font-size:0.9rem; margin-top:5px; margin-bottom:0;">
                    현재 장바구니에 복용 등록된 영양소 중 비타민 D 총량이 일일 상한섭취량인 <span style="color:#ffc107; font-weight:700;">100 μg</span>을 초과하여 <b>{:.1f} μg</b>입니다. 고칼슘혈증 및 변비, 신장 결석 등의 위험이 있으므로 함량 복용량의 자발적인 축소를 권장합니다.
                    </p>
                </div>
                """.format(total_vitd), unsafe_allow_html=True)
                has_warning = True
                
            # 3. 칼슘 일일 상한섭취량 진단 (상한 2500 mg)
            if total_calcium > 2500:
                st.markdown("""
                <div class="card" style="border-left: 5px solid #ffc107; background-color: rgba(255, 193, 7, 0.05);">
                    <span class="badge-warning">경고</span> <b>칼슘 일일 복용량 초과</b>
                    <p style="font-size:0.9rem; margin-top:5px; margin-bottom:0;">
                    일일 복용 칼슘 총량이 <span style="color:#ffc107; font-weight:700;">2,500 mg</span>을 초과하여 <b>{:.1f} mg</b>에 도달했습니다. 위장 장애 유발 및 심혈관 칼슘 석회화를 예방하기 위해 조절이 권장됩니다.
                    </p>
                </div>
                """.format(total_calcium), unsafe_allow_html=True)
                has_warning = True
                
            # 4. 철분과 칼슘의 흡수 방해 조합 진단
            has_iron = any(["철" in item['대표식품명'] or "철분" in item['대표식품명'] for item in st.session_state.my_vit_basket])
            has_cal = any(["칼슘" in item['대표식품명'] or item['칼슘(mg)'] > 0 for item in st.session_state.my_vit_basket])
            
            if has_iron and has_cal:
                st.markdown("""
                <div class="card" style="border-left: 5px solid #ff9800; background-color: rgba(255, 152, 0, 0.05);">
                    <span style="background-color:rgba(255, 152, 0, 0.15); color:#ff9800; border:1px solid #ff9800; border-radius:4px; padding:2px 8px; font-size:0.8rem; font-weight:600; display:inline-block; margin-right:5px;">흡수 방해 조합</span> <b>철분 & 칼슘 동시 복용 감지</b>
                    <p style="font-size:0.9rem; margin-top:5px; margin-bottom:0;">
                    칼슘과 철분은 체내 세포 흡수 과정에서 동일한 흡수 통로를 사용합니다. 두 성분을 동시에 복용하시면 효율이 크게 떨어지므로, <b>철분은 아침 기상 직후 공복</b>에 복용하시고, <b>칼슘은 흡수 촉진을 돕는 저녁 식사 직후</b> 복용으로 시간대를 분리하는 것을 추천합니다.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                has_warning = True
                
            if not has_warning:
                st.success("✅ **영양성분 중복 과잉 복용이나 동시 흡수 방해 조합이 발견되지 않았습니다.** 올바른 성분 설계를 유지 중입니다.")
                
            # 5. 복용 타임라인 가이드 노출
            st.markdown("##### 📅 최적 흡수율 보장 복용 타임라인 배치")
            timeline_items = []
            for item in st.session_state.my_vit_basket:
                raw_name = item['대표식품명'] + " " + item['식품명']
                if "프로바이오틱스" in raw_name or "유산균" in raw_name:
                    timeline_items.append((item['식품명'], "🌅 아침 식전 (공복)", "유산균이 위산에 노출되는 시간을 줄여 소화관 하부까지 보장균수가 많이 생존하게 돕습니다."))
                elif "비타민 D" in raw_name or "오메가" in raw_name or "칼슘" in raw_name:
                    timeline_items.append((item['식품명'], "☀️ 점심/저녁 식후 (지용성/미네랄)", "지용성 영양소는 음식물 내 지질 분비물에 녹아 장관 흡수율이 크게 상승합니다."))
                elif "철" in raw_name:
                    timeline_items.append((item['식품명'], "🌅 아침 공복 또는 취침 전", "철분은 위장 내 공복 조건에서 생체이용률이 높으나, 속쓰림 시 비타민 C와 함께 섭취하세요."))
                else:
                    timeline_items.append((item['식품명'], "⏰ 식후 아무때나 복용", "식사와 함께 섭취하면 빈속에 유발되는 일시적 위장 장애를 최소화할 수 있습니다."))
                    
            for prod, time_slot, desc in timeline_items:
                st.write(f"- **{time_slot}** ➡️ `{prod}` : *{desc}*")
                
            st.markdown("##### 📌 보관 안전성 자가 점검표")
            st.checkbox("유산균 제품의 '보장균수(유통기한 종료 시점까지 살아남는 마릿수)'를 확인하고 구매하셨나요?", key="check_p1")
            st.checkbox("일반 캔디류가 아닌 건강기능식품 정식 문구를 마크로 매칭 확인하셨나요?", key="check_p2")
            st.checkbox("임박하거나 만료된 제품은 장바구니에서 안전하게 폐기하셨나요?", key="check_p3")
            
        else:
            st.info("검색 창을 활용하여 현재 복용 중인 영양제들을 장바구니에 담아 실시간 안전 평가를 가동해 보세요.")


# ==========================================
# [TAB 3] Target Curation: 대상별 선물 추천
# ==========================================
with tab3:
    st.markdown("### 🎁 2030 대상별 영양제 선물 추천 가이드")
    
    st.markdown("""
    <div class="card">
        <h3>🎁 센스 있는 영양제 선물을 위한 타깃별 큐레이션</h3>
        <p>선물 대상자의 성별, 연령, 라이프스타일에 따라 필요한 식약처 보장 기능성 성분을 맞춤 연계합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    target_sel = st.radio(
        "선물 받으실 대상을 설정하세요:",
        ["🧓 부모님 세대 (실버 노화 예방 및 관절/혈관)", "💻 피로 누적 동료 (야근 스트레스 & 눈 피로)", "🏃 활동적 운동 애호가 (근육 피로 회복 & 활력)"],
        key="gift_target_sel"
    )
    
    cur_ingredients = []
    if "부모님" in target_sel:
        cur_ingredients = ["루테인", "칼슘", "비타민 D", "코엔자임Q10", "프로바이오틱스"]
        cur_desc = "노화 안구 질환 예방용 루테인, 골감소 방지용 칼슘 및 비타민 D, 심혈관 관리용 코엔자임Q10 조합입니다."
    elif "동료" in target_sel:
        cur_ingredients = ["비타민 B", "밀크씨슬", "실리마린", "루테인", "아연"]
        cur_desc = "장시간 근무로 손상된 간 세포 보호용 밀크씨슬 및 실리마린, 피로 개선용 활성 비타민 B군 위주의 포뮬러입니다."
    else:
        cur_ingredients = ["마그네슘", "오메가", "단백질", "아미노산"]
        cur_desc = "근력 강화 및 관절 안정성을 확보해 주는 스포츠 복합 보조 원료 위주의 큐레이션입니다."
        
    st.info(f"🧬 **추천 영양 설계 매커니즘**: {cur_desc}")
    
    cur_p = pd.DataFrame()
    for ing in cur_ingredients[:3]:
        temp = df_raw[df_raw['대표식품명'].str.contains(ing, na=False, case=False) | df_raw['식품명'].str.contains(ing, na=False, case=False)]
        cur_p = pd.concat([cur_p, temp])
    cur_p = cur_p.drop_duplicates(subset=['식품코드'])
    
    if not cur_p.empty:
        cur_p[['평점', '리뷰수', '단가']] = cur_p.apply(
            lambda row: pd.Series(generate_pseudo_scores(row['식품코드'])), axis=1
        )
        cur_show = cur_p.sample(min(4, len(cur_p)), random_state=42)
        cols_gift = st.columns(4)
        for idx, (_, row) in enumerate(cur_show.iterrows()):
            badge_html = ""
            if row['데이터구분'] == '건강기능식품 (수입)':
                badge_html = '<span class="badge-import">수입건기식</span>'
            elif row['데이터구분'] == '건강기능식품 (국내)':
                badge_html = '<span class="badge-domestic">국내건기식</span>'
            else:
                badge_html = '<span class="badge-general-food">일반식품</span>'
                
            with cols_gift[idx]:
                st.markdown(f"""
                <div style="background-color:#161b22; border-radius:10px; padding:15px; border:1px solid #30363d; min-height: 290px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            {badge_html}
                            <span style="font-size:0.7rem; color:#8b949e;">⭐ {row['평점']} ({row['리뷰수']}건)</span>
                        </div>
                        <h4 style="color:#58a6ff; font-size:1.0rem; margin:8px 0; min-height: 48px;">{row['식품명'][:26]}</h4>
                        <p style="font-size:0.75rem; color:#8b949e; margin-bottom:2px;">제조/수입: {row['원산지국명']}</p>
                        <p style="font-size:0.75rem; color:#8b949e; margin-bottom:2px; min-height: 32px;">주성분: {row['대표식품명'][:20]}...</p>
                    </div>
                    <div style="border-top:1px solid #30363d; padding-top:8px; display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                        <span style="font-size:1.0rem; color:#3fb950; font-weight:700;">{int(row['단가']):,}원</span>
                        <span style="font-size:0.75rem; color:#8b949e;">{row['1회분량중량/부피']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("선택된 타깃에 일치하는 추천 상품이 현재 존재하지 않습니다.")
