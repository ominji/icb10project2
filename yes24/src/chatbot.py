import os
import sys
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hybrid_search import search_hybrid
from rag_eval import evaluate_rag_response

load_dotenv()

SYSTEM_PROMPT_TEMPLATE = """너는 YES24 베스트셀러 전용 AI 도서 추천 챗봇이다.

다음 규칙을 철저히 엄수해서 답변해라:
1. 답변의 첫 문장은 반드시 "친절한 도서 검색 도우미입니다." 라는 인사로 시작해야 한다.
2. 아래 제공되는 [ YES24 베스트셀러 검색결과 목록 ]에 기반해서만 도서를 추천하고 질문에 답변해라.
3. 만약 사용자의 질문에 부합하는 도서가 목록에 없거나 관련 정보가 전혀 없다면, 절대로 목록 이외의 임의 도서를 메이크업하여 추천하지 말고 반드시 "해당하는 도서가 예스24 베스트셀러 목록에 없습니다."라고 답변해라.
4. 도서를 추천할 때에는 반드시 (1) 도서 제목/저자/가격/평점 정보와 함께 (2) 해당 도서를 추천하는 명확한 이유(추천 이유)를 구체적으로 설명해야 한다.

[ YES24 베스트셀러 검색결과 목록 ]
{context}
"""

def get_groq_client(api_key: str = None):
    """Groq 클라이언트 객체 생성 (API 키 우선순위: UI 입력키 -> .env 변수)"""
    key = api_key if api_key else os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)

def render_chatbot_tab(df, model, embeddings, collection, bm25_index, user_api_key: str = None):
    st.header("🤖 YES24 AI 도서 추천 챗봇 (BM25 + Vector 하이브리드 RAG)")
    st.markdown("ChromaDB 벡터 검색과 BM25 키워드 검색을 결합한 하이브리드 엔진 기반의 도서 추천 도우미입니다.")

    client = get_groq_client(user_api_key)
    if not client:
        st.warning("⚠️ Groq API Key가 설정되지 않았습니다. 사이드바 메뉴에서 Groq API Key를 입력하거나 `.env` 파일에 `GROQ_API_KEY`를 설정해 주세요.")
        st.info("💡 Groq API 키는 [Groq Console](https://console.groq.com/keys)에서 무료로 발급받으실 수 있습니다.")
        return

    # 챗봇 RAG 검색 & LLM 파라미터 설정 (Expander)
    with st.expander("⚙️ 챗봇 RAG 검색 & Groq LLM 파라미터 설정 (Temperature, Top-P, RAG)", expanded=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("##### 🔍 RAG 검색 파라미터")
            min_threshold = st.slider("최저 유사도 임계값", min_value=0.0, max_value=1.0, value=0.20, step=0.05, key="cb_th")
            top_k = st.slider("검색 도서 수 (Top K)", min_value=1, max_value=20, value=5, step=1, key="cb_topk")
            alpha = st.slider("검색 비율 (Vector vs BM25)", min_value=0.0, max_value=1.0, value=0.5, step=0.1, key="cb_alpha")

        with col_c2:
            st.markdown("##### 🤖 Groq LLM 생성 파라미터")
            temperature = st.slider("Temperature (창의성/무작위성)", min_value=0.0, max_value=1.0, value=0.30, step=0.05,
                                    help="낮을수록 사실 기반의 안정적인 응답을 생성하고, 높을수록 표현이 다양해집니다.")
            top_p = st.slider("Top P (Nucleus Sampling)", min_value=0.0, max_value=1.0, value=1.0, step=0.05,
                              help="상위 누적 확률 p 범위 내의 토큰에서 샘플링합니다.")

    st.divider()

    # 대화 히스토리 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 이전 메시지 표시
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Assistant 메시지이며 Context가 저장된 경우 RAGAS 평가 버튼 제공
            if message["role"] == "assistant" and "context" in message and message.get("context"):
                eval_key = f"eval_{idx}"
                if st.button(f"🧪 이 응답 RAGAS 평가하기", key=eval_key):
                    with st.spinner("RAGAS 3대 지표(Faithfulness, Relevance)를 평가 중입니다..."):
                        prev_user_msg = st.session_state.messages[idx-1]["content"] if idx > 0 else ""
                        eval_res = evaluate_rag_response(client, prev_user_msg, message["context"], message["content"])
                        
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("종합 점수", f"{eval_res.get('overall_score')}점")
                        m2.metric("Faithfulness (충실도)", f"{eval_res.get('faithfulness')}점")
                        m3.metric("Answer Relevance", f"{eval_res.get('answer_relevance')}점")
                        m4.metric("Context Relevance", f"{eval_res.get('context_relevance')}점")
                        st.info(f"💡 **평가 사유**: {eval_res.get('reasoning')}")

    # 채팅 입력
    if prompt := st.chat_input("어떤 책을 찾고 계신가요? (예: 파이썬 업무 자동화 관련 책 추천해줘)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # BM25 + Vector 하이브리드 검색 수행
        with st.spinner("BM25 키워드 & ChromaDB 벡터 하이브리드 검색 중..."):
            results_list, context_str = search_hybrid(
                query=prompt,
                df=df,
                embeddings=embeddings,
                model=model,
                bm25_index=bm25_index,
                top_k=top_k,
                min_threshold=min_threshold,
                alpha=alpha
            )

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context_str)

        # LLM 응답 생성
        with st.chat_message("assistant"):
            if results_list:
                st.caption(f"🔍 RAG 검색 결과 {len(results_list)}건 참조 (Temp: {temperature}, Top-P: {top_p}, Threshold: {min_threshold})")
            
            message_placeholder = st.empty()
            full_response = ""

            try:
                messages_payload = [{"role": "system", "content": system_prompt}]
                for msg in st.session_state.messages[-5:]:
                    messages_payload.append({"role": msg["role"], "content": msg["content"]})

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_payload,
                    temperature=temperature,
                    top_p=top_p,
                    stream=True
                )

                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"오류가 발생했습니다: {e}"
                message_placeholder.error(full_response)

        # 메시지와 컨텍스트 저장
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "context": context_str
        })
