import streamlit as st
import datetime
from utils import init_naver_credentials, inject_custom_css

# API 인증키 및 공통 세션 초기화
init_naver_credentials()
inject_custom_css()

# 페이지 기본 설정
st.set_page_config(
    page_title="Naver API Multi-Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# .env 파일에서 불러온 네이버 API 인증 정보 사용
client_id = st.session_state["client_id"]
client_secret = st.session_state["client_secret"]

st.sidebar.markdown("## 🔑 네이버 API 인증 정보")
if client_id and client_secret:
    st.sidebar.success("🟢 환경 변수(.env)에서 API 키 로드 완료")
    st.sidebar.text_input("Client ID", value=f"{client_id[:4]}***" if len(client_id) > 4 else "***", disabled=True)
else:
    st.sidebar.error("🔴 환경 변수(.env) API 키 누락")
    st.sidebar.info("naver-api-app/.env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 입력해 주세요.")

st.sidebar.markdown("---")
st.sidebar.markdown("## 🔍 공통 검색 조건 설정")

# 검색어 입력받기 (,로 구분)
keywords_input = st.sidebar.text_area(
    "검색어 입력 (쉼표 ','로 구분)",
    value=st.session_state["keywords"],
    help="여러 검색어를 분석하려면 쉼표로 구분하여 입력하세요. 예: 노트북, 태블릿, 데스크탑"
)
# 검색어 리스트 파싱
keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
st.session_state["keywords"] = keywords_input
st.session_state["keywords_list"] = keywords_list

# 검색 기간 설정
today = datetime.date.today()
default_start = today - datetime.timedelta(days=90)

start_date = st.sidebar.date_input("시작일", st.session_state["start_date"], max_value=today)
end_date = st.sidebar.date_input("종료일", st.session_state["end_date"], max_value=today)

if start_date > end_date:
    st.sidebar.error("시작일은 종료일보다 이전이어야 합니다.")

st.session_state["start_date"] = start_date
st.session_state["end_date"] = end_date

# 조회 주기 설정
time_unit = st.sidebar.selectbox(
    "조회 주기 (트렌드 API용)",
    options=["date", "week", "month"],
    index=["date", "week", "month"].index(st.session_state["time_unit"]),
    format_func=lambda x: "일간" if x == "date" else "주간" if x == "week" else "월간"
)
st.session_state["time_unit"] = time_unit

# 메인 페이지 화면
st.markdown("<h1 style='text-align: center; color: #03C75A;'>📊 네이버 오픈 API 통합 분석 대시보드</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555;'>네이버 Datalab 트렌드 정보와 검색 서비스의 데이터를 한눈에 분석하고 시각화합니다.</p>", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("""
    ### ⚙️ 시작하기 안내
    1. `naver-api-app/.env` 파일에 **네이버 개발자 센터**에서 발급받은 `Client ID`와 `Client Secret`을 입력하세요.
    2. 수집 및 분석하고자 하는 **검색어 목록**(쉼표로 구분)과 **검색 기간**을 지정하세요.
    3. 왼쪽 메뉴에서 원하는 분석 서비스 페이지를 클릭하여 상세 대시보드를 확인하세요.
    
    ### 🚀 지원되는 대시보드 페이지
    - **📈 검색어 트렌드**: 네이버 통합 검색어의 기간별 트렌드 추이 비교
    - **🛍️ 쇼핑 트렌드**: 쇼핑 카테고리 내 특정 키워드들의 클릭량 추이 비교
    - **📦 쇼핑 검색**: 쇼핑 검색 데이터 수집, 최저가 분석 및 판매처 현황
    - **📝 블로그 검색**: 블로그 포스팅 수집 및 최신 여론 트렌드 분석
    - **☕ 카페글 검색**: 카페 커뮤니티 내 언급 정보 분석
    - **📰 뉴스 검색**: 실시간 언론 보도 정보 수집 및 핵심 이슈 분석
    """)

with col2:
    st.info("💡 **네이버 API 키 설정 방법**\n\n"
            "1. [네이버 개발자 센터](https://developers.naver.com/)에 접속하여 로그인합니다.\n"
            "2. **Application > 애플리케이션 등록** 메뉴로 이동합니다.\n"
            "3. 서비스할 API 목록에서 **'데이터랩(검색어트렌드)', '데이터랩(쇼핑인사이트)', '검색'**을 선택하여 등록합니다.\n"
            "4. 생성된 애플리케이션의 Client ID와 Client Secret을 `naver-api-app/.env` 파일에 저장해 주세요.")
    
    # 설정 상태 요약
    st.markdown("### 🛠️ 현재 설정 정보")
    status_data = {
        "구분": ["인증 상태", "설정된 검색어", "분석 기간", "조회 주기"],
        "설정값": [
            "🟢 입력 완료" if client_id and client_secret else "🔴 미입력 (.env 설정 필요)",
            ", ".join(keywords_list) if keywords_list else "없음",
            f"{start_date} ~ {end_date}",
            "일간" if time_unit == "date" else "주간" if time_unit == "week" else "월간"
        ]
    }
    st.table(status_data)
