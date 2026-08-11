# 삼성화재 약관 PDF 기반 RAG 챗봇 프로젝트

이 프로젝트는 삼성화재 약관 PDF 문서를 다운로드받아 텍스트 추출 및 청킹 후, 저사양 노트북 환경에서도 원활히 동작하는 한국어 경량 문장 임베딩(`jhgan/ko-sroberta-multitask`)과 Groq API (LLaMA 3.3 70B 등)를 활용하여 질문에 답변하는 Streamlit RAG 챗봇입니다.

## 📁 폴더 구조

```text
samsungfire/
├── data/               # 다운로드한 PDF (20071_0_20250816_file1.pdf), chunks.json, vector_store.pkl
├── docs/               # 프로젝트 가이드 문서 (README.md 등)
├── images/             # UI/캡처 이미지 저장용
├── report/             # 파싱 및 분석 보고서
├── src/                # 소스 코드
│   ├── pdf_parser.py   # PDF 다운로드, 텍스트 추출 및 청킹 모듈
│   ├── embedding.py    # 저사양 최적화 한국어 문장 임베딩 & 코사인 유사도 검색 모듈
│   └── app.py          # Groq API 연동 Streamlit 대화형 UI 챗봇
└── .env                # GROQ_API_KEY 설정 파일 (선택)
```

## 🚀 실행 방법

### 1. 가상환경 및 패키지 확인
워크스페이스 최상단 가상환경(`.venv`)을 사용하며 필요한 패키지(`streamlit`, `groq`, `sentence-transformers`, `pypdf`, `python-dotenv`, `scikit-learn` 등)가 설치되어 있습니다.

### 2. Streamlit 챗봇 앱 실행
다음 명령어로 Streamlit 웹 앱을 실행합니다:

```bash
uv run streamlit run samsungfire/src/app.py --server.port 8520
```

### 3. 사용 가이드
1. 브라우저에서 실행된 페이지의 **좌측 사이드바**에 `Groq API Key`를 입력합니다. (Groq 콘솔: https://console.groq.com)
2. 약관 관련 궁금한 내용(예: "보상하는 손해 범위는?", "계약 해지 조건")을 입력하면 약관 문서를 실시간 검색하여 근거와 함께 답변을 제공합니다.
3. 답변 하단의 `📄 참고한 약관 본문 청크 보기` 접기 메뉴를 클릭하면 추출된 원본 약관 본문과 페이지 번호를 직접 확인할 수 있습니다.
