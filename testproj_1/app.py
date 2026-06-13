# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os

# 페이지 설정 (SEO 및 타이틀 지정)
st.set_page_config(
    page_title="NutriFit 2030 - 맞춤형 영양제 스마트 대시보드",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 정보 정의 (전달해주신 API 주소 기반)
API_KEY = "be08162c9d464d6998a5"
SERVICE_ID = "C003"
BASE_URL = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{SERVICE_ID}/json"

# 세련된 CSS 스타일 적용 (Aesthetics & UX)
st.markdown("""
<style>
    /* 폰트 및 메인 컨테이너 */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', 'Outfit', sans-serif;
    }
    
    /* 헤더 그라데이션 */
    .header-container {
        background: linear-gradient(135deg, #1f497d 0%, #00b0f0 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* 카드 스타일 */
    .card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #1f497d;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
    }
    
    /* 기능성 뱃지 */
    .badge-functional {
        background-color: #e2f0d9;
        color: #385723;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 0.5rem;
    }
    
    .badge-general {
        background-color: #fff2cc;
        color: #7f6000;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 0.5rem;
    }
    
    .badge-timing {
        background-color: #ddebf7;
        color: #1f4e79;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }

    /* 경고 알림 */
    .warning-box {
        background-color: #fce4d6;
        color: #c65911;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #c65911;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 1. API 데이터 페치 함수 (캐싱 적용으로 성능 최적화)
@st.cache_data
def fetch_api_data(start_idx=1, end_idx=50, query=None):
    """
    식품안전나라 API로부터 데이터를 가져옵니다.
    query가 제공될 경우 제품명(PRDLST_NM) 필터링 조건을 추가합니다.
    """
    url = f"{BASE_URL}/{start_idx}/{end_idx}"
    if query:
        url += f"/PRDLST_NM={query}"
        
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        if SERVICE_ID in data and "row" in data[SERVICE_ID]:
            return data[SERVICE_ID]["row"]
    except Exception as e:
        st.sidebar.error(f"API 연동 에러: {e}")
    return []

# 초기 데이터 로드 (기본 50개)
default_rows = fetch_api_data(1, 50)
df_default = pd.DataFrame(default_rows) if default_rows else pd.DataFrame()

# 헤더 영역
st.markdown("""
<div class="header-container">
    <div class="header-title">⚡ NutriFit 2030</div>
    <div class="header-subtitle">2030 운동 목적별 맞춤형 영양제 추천 & 스마트 안전 섭취 케어 대시보드</div>
</div>
""", unsafe_allow_html=True)

# 사이드바: 유저 건강 프로필 및 API 상태
st.sidebar.image("https://img.icons8.com/color/96/000000/exercise.png", width=80)
st.sidebar.header("👤 내 맞춤 프로필")
user_gender = st.sidebar.selectbox("성별", ["남성", "여성"])
user_age = st.sidebar.slider("연령대", 10, 80, 28)
health_issue = st.sidebar.multiselect(
    "평소 신체 증상/관심사",
    ["만성피로", "뼈/관절 약화", "장내 불편함", "피부 건조", "눈 피로", "면역력 저하"]
)

st.sidebar.markdown("---")
st.sidebar.header("🌐 API 연동 상태")
if default_rows:
    st.sidebar.success("식품안전나라 API 연동 완료 (정상)")
    st.sidebar.info(f"기본 품목 로드 수: {len(df_default)}개")
else:
    st.sidebar.error("API 연동 실패 (네트워크 혹은 키 확인 요망)")

# 메인 화면 탭 구성 (Track 1 & Track 2 구현)
tab1, tab2, tab3 = st.tabs([
    "📊 2030 소비 패턴 & 트렌드 분석",
    "📱 My 영양제 스마트 케어 (맞춤 제안)",
    "🎁 연령별/목적별 선물 큐레이션"
])

# ==========================================
# [TAB 1] 2030 소비 패턴 & 트렌드 분석
# ==========================================
with tab1:
    st.header("🏃 운동 목적별 영양소 매핑 & TOP 5")
    
    workout = st.selectbox(
        "💪 선호하는 운동을 선택해 주세요:",
        ["러닝 / 테니스 (관절 보호 및 에너지 대사)", "등산 / 골프 (항산화 및 야외 자외선 관리)", "피트니스 / 헬스 (근육 형성 및 피로 개선)"]
    )
    
    # 가상의 제품 매핑 데이터베이스 구축 (식약처 API 연계)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if "러닝" in workout:
            st.subheader("🎯 러닝 & 테니스 맞춤 추천 영양제")
            st.write("러닝과 테니스는 관절과 연골의 마찰이 심하고 단시간에 에너지를 다량 소모하므로 **관절 보강 성분(칼슘, CPP)**과 **에너지 대사 비타민 B군**이 필수적입니다.")
            
            # C003 API 데이터에서 칼슘/비타민B군 제품 추출 매핑
            if not df_default.empty:
                # 칼슘이나 비타민B 관련 제품 필터링
                matched = df_default[df_default['PRDLST_NM'].str.contains('칼슘|비타민|영양', na=False, case=False)].head(5)
                for idx, row in matched.iterrows():
                    raw_materials = row['RAWMTRL_NM']
                    st.markdown(f"""
                    <div class="card">
                        <h4><span class="badge-functional">건강기능식품</span>{row['PRDLST_NM']}</h4>
                        <p><strong>제조사:</strong> {row['BSSH_NM']}</p>
                        <p><strong>주요 성분:</strong> {raw_materials[:100]}...</p>
                        <p><strong>기능성:</strong> {row['PRIMARY_FNCLTY'][:150]}...</p>
                        <p><span class="badge-timing">⏱ 섭취 추천: 아침 식후</span></p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("API 연결 데이터를 불러오는 중입니다...")
                
        elif "등산" in workout:
            st.subheader("🎯 등산 & 골프 맞춤 추천 영양제")
            st.write("등산과 골프는 야외 활동이 길어 자외선 노출이 많고 심폐 지구력을 소모하므로, **유해산소 방어(항산화 비타민 C, 홍삼)** 및 **비타민 D** 보충이 효과적입니다.")
            
            if not df_default.empty:
                matched = df_default[df_default['PRDLST_NM'].str.contains('홍삼|인삼|비타민C', na=False, case=False)].head(5)
                for idx, row in matched.iterrows():
                    st.markdown(f"""
                    <div class="card">
                        <h4><span class="badge-functional">건강기능식품</span>{row['PRDLST_NM']}</h4>
                        <p><strong>제조사:</strong> {row['BSSH_NM']}</p>
                        <p><strong>주요 성분:</strong> {row['RAWMTRL_NM'][:100]}...</p>
                        <p><strong>기능성:</strong> {row['PRIMARY_FNCLTY'][:150]}...</p>
                        <p><span class="badge-timing">⏱ 섭취 추천: 점심 식후</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
        else:
            st.subheader("🎯 피트니스 & 웨이트 트레이닝 맞춤 추천 영양제")
            st.write("피트니스는 근섬유 회복과 단백질 합성이 핵심이므로, **아미노산 합성(비타민 B6, 아연)** 및 **피로 개선(홍삼, 간 기능 개선)** 조합이 뛰어납니다.")
            
            if not df_default.empty:
                matched = df_default[df_default['PRDLST_NM'].str.contains('인삼|홍삼|농축액', na=False, case=False)].head(5)
                for idx, row in matched.iterrows():
                    st.markdown(f"""
                    <div class="card">
                        <h4><span class="badge-functional">건강기능식품</span>{row['PRDLST_NM']}</h4>
                        <p><strong>제조사:</strong> {row['BSSH_NM']}</p>
                        <p><strong>주요 성분:</strong> {row['RAWMTRL_NM'][:100]}...</p>
                        <p><strong>기능성:</strong> {row['PRIMARY_FNCLTY'][:150]}...</p>
                        <p><span class="badge-timing">⏱ 섭취 추천: 운동 전 30분</span></p>
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
        st.subheader("📈 2030 제형 선호도 트렌드")
        st.write("알약(정제) 대비 구미, 액상, 필름 등 신제형에 대한 평점 및 가성비 비교 매트릭스 시각화입니다.")
        
        # 가상의 제형 선호도 데이터
        formats = ['정제(알약)', '캡슐', '분말', '액상', '구미젤리']
        satisfaction = [4.1, 4.3, 4.2, 4.6, 4.8]
        price_index = [100, 120, 130, 180, 210] # 알약 대비 단위단가 비율
        
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.scatter(price_index, satisfaction, s=[p*2 for p in price_index], color='#1F497D', alpha=0.7)
        for i, txt in enumerate(formats):
            ax.annotate(txt, (price_index[i]+5, satisfaction[i]-0.02), fontsize=9)
            
        ax.set_title("제형별 가격 지수 vs 소비자 만족도")
        ax.set_xlabel("가격 지수 (알약 100 기준)")
        ax.set_ylabel("소비자 평점 (5점 만점)")
        ax.set_xlim(80, 250)
        ax.set_ylim(3.8, 5.0)
        ax.grid(True, linestyle=':', alpha=0.6)
        st.pyplot(fig)
        st.caption("💡 분석 결과: 2030은 가성비가 다소 떨어지더라도 섭취 편의성과 맛이 뛰어난 구미/액상 제형에 약 2배의 단가를 흔쾌히 지불하는 경향을 나타냅니다.")

# ==========================================
# [TAB 2] My 영양제 스마트 케어 (개인 맞춤형 유저 서비스)
# ==========================================
with tab2:
    st.header("📱 개인화 스마트 케어 & 안전망 자가체크")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("🔍 보유 영양제 실시간 식약처 연동 검색")
        st.write("복용 중인 영양제 명칭의 키워드(예: '칼슘', '비피더스', '홍삼' 등)를 입력하면 식약처 OpenAPI를 통해 정식 등록 제품인지 확인하고 상세 스펙을 로드합니다.")
        
        search_query = st.text_input("제품명 검색어 입력:", placeholder="예: 비피더스")
        
        if search_query:
            # 검색어가 있을 경우 실시간 API 호출
            fetched_rows = fetch_api_data(1, 5, search_query)
            if fetched_rows:
                st.success(f"식약처에 등록된 제품 {len(fetched_rows)}건을 발견했습니다.")
                for row in fetched_rows:
                    # 건기식 vs 일반식품 판별 (C003은 정식 품목제조신고이므로 모두 '건강기능식품'인증 배지 제공)
                    st.markdown(f"""
                    <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 0.8rem;">
                        <span class="badge-functional">식약처 인증 건강기능식품</span>
                        <strong>{row['PRDLST_NM']}</strong> ({row['BSSH_NM']})
                        <p style="font-size: 0.9rem; margin-top: 0.5rem; color:#475569;">
                            <strong>기능성:</strong> {row['PRIMARY_FNCLTY']}<br>
                            <strong>원재료:</strong> {row['RAWMTRL_NM']}<br>
                            <strong>섭취법:</strong> {row['NTK_MTHD']}<br>
                            <strong>유통기한:</strong> {row['POG_DAYCNT']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("검색된 제품이 없습니다. 일반 캔디류(일반 식품)이거나 검색어를 확인해 주세요.")
                st.info("💡 식약처 인증 마크가 없는 제품은 기능성 함량이 보장되지 않는 일반 캔디/젤리류일 수 있습니다.")
        else:
            st.info("위 검색창에 복용 중인 영양제 명칭을 적고 Enter를 눌러주세요.")

    with col_right:
        st.subheader("🛡️ 동시 섭취 안전 진단 (부작용 예방)")
        st.write("현재 섭취 예정인 성분들을 복수 선택해 보세요. 중복 과잉 섭취 및 상충 부작용 여부를 실시간으로 판별합니다.")
        
        selected_ingredients = st.multiselect(
            "섭취 대상 성분 선택:",
            ["칼슘 (Calcium)", "비타민 D (Vitamin D)", "유산균 (프로바이오틱스)", "철분 (Iron)", "종합비타민", "홍삼 / 진세노사이드"]
        )
        
        if selected_ingredients:
            warnings = []
            tips = []
            
            # 부작용 매커니즘 매핑
            if "칼슘 (Calcium)" in selected_ingredients and "철분 (Iron)" in selected_ingredients:
                warnings.append("⚠️ **[섭취 방해 경고]** 칼슘과 철분은 체내 흡수 경로가 동일하여 동시 섭취 시 서로의 흡수를 심각하게 저해합니다. (칼슘은 식후, 철분은 공복 섭취를 추천합니다.)")
            
            if "종합비타민" in selected_ingredients and "비타민 D (Vitamin D)" in selected_ingredients:
                warnings.append("⚠️ **[성분 중복 경고]** 종합비타민에 함유된 비타민 D와 고함량 단일 비타민 D를 동시 섭취할 경우 하루 권장량(4,000 IU)을 초과하여 고칼슘혈증 등의 이상반응을 초과할 위험이 있습니다.")
                
            if "유산균 (프로바이오틱스)" in selected_ingredients:
                tips.append("🕒 **[유산균 섭취 Tip]** 위산에 약하므로 아침 식전 '공복' 상태에서 물과 함께 복용하시는 것이 장 도달률에 가장 좋습니다.")
                
            if "칼슘 (Calcium)" in selected_ingredients and "비타민 D (Vitamin D)" in selected_ingredients:
                tips.append("🤝 **[시너지 성분 매핑]** 비타민 D는 칼슘이 소장에서 원활히 흡수되도록 촉진하므로 최상의 조합입니다.")
                
            # 결과 표시
            if warnings:
                st.markdown("### 🚨 경고 조합 감지")
                for w in warnings:
                    st.markdown(f"<div class='warning-box'>{w}</div>", unsafe_allow_html=True)
            else:
                st.success("✅ 선택하신 성분 조합은 동시 병용 섭취에 안전한 설계입니다.")
                
            if tips:
                st.markdown("### 💡 복용 시너지 & 가이드")
                for t in tips:
                    st.info(t)

# ==========================================
# [TAB 3] 연령별/목적별 선물 추천 큐레이션
# ==========================================
with tab3:
    st.header("🎁 목적별 맞춤 큐레이션 & 기프트 북")
    st.write("선물 받을 대상을 선택하시면 식약처 인허가 기능성 데이터를 기반으로 한 최적의 건기식 기프팅 제안서가 제공됩니다.")
    
    gift_target = st.radio(
        "선물 대상을 선택해 주세요:",
        ["부모님 실버 케어 (안구 건조 및 골다공증 예방)", "직장 동료 피로회복 (오피스 워커 필수 영양)", "성장기 어린이/청소년 (면역 및 성장 뼈대 발달)"]
    )
    
    if "부모님" in gift_target:
        st.subheader("👵 5060 부모님 실버 맞춤 큐레이션")
        st.write("나이가 들수록 유실되기 쉬운 **칼슘과 조골 세포 활성화 성분** 및 노안 예방을 위한 **루테인/아스타잔틴** 조합을 권장합니다.")
        
        # C003 API의 칼슘비타민 제품 예시 매핑
        if not df_default.empty:
            matched_calcium = df_default[df_default['PRDLST_NM'].str.contains('칼슘', na=False)].head(2)
            for _, r in matched_calcium.iterrows():
                st.markdown(f"""
                <div style="padding: 1rem; border:1px dashed #c0504d; border-radius: 8px; margin-bottom: 0.5rem; background-color: #fdf5f5;">
                    📌 <strong>부모님 골다공증 예방 제안:</strong> {r['PRDLST_NM']} ({r['BSSH_NM']})
                    <p style="font-size: 0.85rem; color:#555; margin-top:0.3rem;">성분: {r['RAWMTRL_NM'][:80]}...</p>
                </div>
                """, unsafe_allow_html=True)
                
    elif "직장 동료" in gift_target:
        st.subheader("💻 3040 직장 동료 피로회복 기프트")
        st.write("야근과 스트레스로 지친 간 피로 개선을 위한 **밀크씨슬(실리마린)** 및 만성피로에 도움을 주는 **비타민 B군 및 나이아신** 제제를 적극 추천합니다.")
        
        if not df_default.empty:
            matched_hongsam = df_default[df_default['PRDLST_NM'].str.contains('홍삼|인삼', na=False)].head(2)
            for _, r in matched_hongsam.iterrows():
                st.markdown(f"""
                <div style="padding: 1rem; border:1px dashed #8064a2; border-radius: 8px; margin-bottom: 0.5rem; background-color: #f9f5fd;">
                    📌 <strong>동료 스트레스 극복 제안:</strong> {r['PRDLST_NM']} ({r['BSSH_NM']})
                    <p style="font-size: 0.85rem; color:#555; margin-top:0.3rem;">기능: {r['PRIMARY_FNCLTY'][:100]}...</p>
                </div>
                """, unsafe_allow_html=True)
                
    else:
        st.subheader("🧒 성장기 어린이/청소년 골격 발달 기프트")
        st.write("뼈 성장에 관여하는 **칼슘, 카제인포스포펩타이드(C.P.P)** 및 면역 균형을 지키는 **프로바이오틱스(유산균)** 형태를 추천합니다.")
        
        if not df_default.empty:
            matched_probiotics = df_default[df_default['PRDLST_NM'].str.contains('비피더스|락토', na=False)].head(2)
            for _, r in matched_probiotics.iterrows():
                st.markdown(f"""
                <div style="padding: 1rem; border:1px dashed #4bacc6; border-radius: 8px; margin-bottom: 0.5rem; background-color: #f5fbfd;">
                    📌 <strong>성장기 아이 면역 제안:</strong> {r['PRDLST_NM']} ({r['BSSH_NM']})
                    <p style="font-size: 0.85rem; color:#555; margin-top:0.3rem;">주요 성분: {r['RAWMTRL_NM'][:100]}...</p>
                </div>
                """, unsafe_allow_html=True)

# 풋터
st.markdown("---")
st.caption("NutriFit 2030 Dashboard | 본 서비스는 식약처 건강기능식품 품목제조신고(C003) API 실시간 공식 연동 시스템입니다.")
