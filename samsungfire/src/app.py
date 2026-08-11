import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
import sys

# 프로젝트 루트 경로 추가 (상대 경로 임포트 지원)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from samsungfire.src.pdf_parser import process_pdf_and_save_chunks, PDF_SAVE_PATH
from samsungfire.src.embedding import LightweightRetriever, VECTOR_STORE_PATH

# 환경변수 로드 (.env 지원)
load_dotenv(os.path.join("samsungfire", ".env"))

st.set_page_config(
    page_title="삼성화재 약관 AI 챗봇",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0B2545;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .badge-info {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #1E40AF;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_retriever():
    """검색기 객체를 캐싱하여 빠른 응답 제공"""
    retriever = LightweightRetriever()
    retriever.load_or_build_index()
    return retriever

def main():
    st.markdown('<div class="main-header">🔥 삼성화재 약관 Q&A 챗봇</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">삼성화재 약관 PDF 문서를 기반으로 저사양 노트북 지원 임베딩 및 Groq LLaMA 3.3 LLM이 신속 정확하게 답변합니다.</div>', unsafe_allow_html=True)

    # ------------------ 사이드바 구성 ------------------
    with st.sidebar:
        st.header("⚙️ 서비스 설정")
        
        # Groq API 키 입력
        default_key = os.getenv("GROQ_API_KEY", "")
        api_key = st.text_input(
            "Groq API Key 입력", 
            value=default_key, 
            type="password",
            help="console.groq.com 에서 발급받은 API Key를 입력해주세요."
        )
        
        st.markdown("---")
        
        # Groq 모델 선택
        model_name = st.selectbox(
            "🤖 LLM 모델 선택 (Groq)",
            options=[
                "llama-3.3-70b-versatile",
                "llama3-8b-8192",
                "mixtral-8x7b-32768"
            ],
            index=0
        )
        
        top_k = st.slider("🔍 검색 문맥 개수 (Top-K)", min_value=1, max_value=5, value=3)
        
        st.markdown("---")
        st.subheader("💡 임베딩 검색 엔진 (저사양 최적화)")
        
        retriever = get_retriever()
        current_mode = getattr(retriever, "mode", "tfidf").upper()
        st.info(f"현재 활성 검색엔진: **{current_mode}**")

        embedding_choice = st.radio(
            "검색 모드 전환",
            options=["TF-IDF (초경량 / 0초 로딩)", "Ko-SRoBERTa SBERT (의미론적 검색)"],
            index=0 if current_mode == "TFIDF" else 1
        )

        if st.button("⚡ 선택한 임베딩 모드로 적용"):
            with st.spinner("임베딩 인덱스 적용 중..."):
                use_sbert = "SBERT" in embedding_choice
                retriever.load_or_build_index(force_rebuild=True, use_sbert=use_sbert)
                st.cache_resource.clear()
                st.success(f"검색 모드가 변경되었습니다!")
                st.rerun()

        st.markdown("---")
        st.subheader("📚 약관 문서 상태")
        if os.path.exists(VECTOR_STORE_PATH):
            st.success(f"✅ 총 {len(retriever.chunks)}개 약관 청크 로드됨")
        else:
            st.warning("⚠️ 인덱스 파일이 없습니다.")
            
        if st.button("🔄 약관 PDF 파싱 & 인덱스 재생성"):
            with st.spinner("PDF 파싱 및 인덱스를 재구축하고 있습니다..."):
                try:
                    process_pdf_and_save_chunks()
                    retriever.load_or_build_index(force_rebuild=True, use_sbert=False)
                    st.cache_resource.clear()
                    st.success("인덱스가 재생성되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    # ------------------ 메인 영역: 챗봇 ------------------
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "안녕하세요! 삼성화재 약관 문서에 대해 궁금하신 점을 자유롭게 질문해 주세요."}
        ]

    # 대화 히스토리 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "sources" in msg:
                with st.expander("📄 참고한 약관 본문 청크 보기"):
                    for idx, (chunk, score) in enumerate(msg["sources"], 1):
                        st.markdown(f"**[참고 {idx}]** (페이지 {chunk['page']} | 유사도: {score:.3f})")
                        st.text(chunk["content"])

    # 질문 입력
    if prompt := st.chat_input("삼성화재 약관에 대해 질문하세요... (예: 보상하지 않는 손해 항목은 무엇인가요?)"):
        if not api_key:
            st.warning("🔑 좌측 사이드바에 Groq API Key를 입력해 주세요.")
            st.stop()

        # 사용자 입력 등록
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # RAG 처리
        with st.chat_message("assistant"):
            with st.spinner("약관 문서를 검색하고 LLaMA가 답변을 작성 중입니다..."):
                retriever = get_retriever()
                retrieved_docs = retriever.search(prompt, top_k=top_k)

                context_str = "\n\n".join([
                    f"[약관 {i+1} - 페이지 {doc['page']}]\n{doc['content']}"
                    for i, (doc, score) in enumerate(retrieved_docs)
                ])

                system_prompt = (
                    "당신은 삼성화재 약관 전문 도우미입니다.\n"
                    "아래 제공된 [약관 참고 문서]만을 바탕으로 사용자의 질문에 정확하고 명쾌하게 한국어로 답변해 주세요.\n"
                    "약관에 명시되지 않은 정보는 지어내지 말고, 문서에 근거하여 안내하세요.\n\n"
                    f"[약관 참고 문서]\n{context_str}"
                )

                try:
                    client = Groq(api_key=api_key)
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        model=model_name,
                        temperature=0.2,
                        max_tokens=1024,
                        stream=True
                    )

                    response_placeholder = st.empty()
                    full_response = ""
                    for chunk in chat_completion:
                        delta = chunk.choices[0].delta.content or ""
                        full_response += delta
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)

                    with st.expander("📄 참고한 약관 본문 청크 보기"):
                        for idx, (chunk, score) in enumerate(retrieved_docs, 1):
                            st.markdown(f"**[참고 {idx}]** (페이지 {chunk['page']} | 유사도: {score:.3f})")
                            st.text(chunk["content"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": retrieved_docs
                    })

                except Exception as e:
                    st.error(f"Groq API 연동 실패: {e}")

if __name__ == "__main__":
    main()
