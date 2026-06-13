# 🔍 Naver API 연동 어플리케이션

이 프로젝트는 네이버 API를 통해 정보를 검색하고 분석을 진행하는 **네이버 API 연동 모듈**입니다.

## 🔗 Streamlit 서비스 접속 주소
- **바로가기:** [https://icb10project2-mg6qetkpk9xj88e6khuekr.streamlit.app/](https://icb10project2-mg6qetkpk9xj88e6khuekr.streamlit.app/)

---

## 🛠️ 주요 기능 (Key Features)
- **네이버 API 연동**: 블로그, 뉴스 등 다양한 네이버 검색 결과를 수집합니다.
- **OpenAI API 연동**: 검색 결과를 바탕으로 LLM을 활용한 스마트 요약 및 리포트 생성을 지원합니다.
- **디렉토리 연동**: `data/` 및 `report/` 폴더를 자동으로 식별하여 수집한 로우 데이터와 가공된 보고서 파일들을 체계적으로 보관합니다.

---

## 📂 프로젝트 구조 (Project Structure)
- [src/app.py](./src/app.py): Streamlit 기반의 Naver API 연동 및 제어용 메인 웹 어플리케이션 소스코드.
- [src/utils.py](./src/utils.py): 네이버 API 통신, 데이터 전처리, GPT 활용 요약 분석 등의 유틸리티 모듈.
- [data/](./data): API 검색 등을 통해 생성된 로우(Raw) 데이터가 보관되는 공간.
- [report/](./report): OpenAI API 등을 연동하여 요약하고 시각화한 결과 리포트가 저장되는 공간.

---

## ⚙️ 환경 설정 (Environment Setup)

프로젝트를 구동하기 전, `naver-api-app` 루트 폴더 내에 `.env` 파일을 생성하고 다음 API 키를 설정해야 합니다. (자세한 서식은 [.env.example](./.env.example) 파일 참고)

```env
# 네이버 API 인증 정보
NAVER_CLIENT_ID=YOUR_NAVER_CLIENT_ID
NAVER_CLIENT_SECRET=YOUR_NAVER_CLIENT_SECRET

# OpenAI API 인증 정보
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

> [!WARNING]
> `.env` 파일은 인증키가 포함되어 있으므로 **절대로 Git에 커밋하거나 외부로 유출해서는 안 됩니다.**
> 기본적으로 `.gitignore` 처리가 되어있어야 합니다.
