import os
import sys
import json
import streamlit as st
from groq import Groq

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

EVAL_PROMPT = """너는 RAGAS(Retrieval-Augmented Generation Assessment) 평가 전문가이다.
제시되는 [사용자 질문], [검색된 도서 문맥(Context)], [챗봇 답변]을 분석하여 RAG 시스템의 품질을 평가해라.

다음 3가지 평가 지표를 0점에서 100점 사이 점수(숫자만)로 산출하고 짧은 이유를 작성해라:

1. faithfulness (충실도 / 할루시네이션 평가): 챗봇 답변이 제공된 [검색된 도서 문맥]의 사실에만 충실하게 근거하였는가? (없는 내용을 지어냈다면 감점)
2. answer_relevance (답변 관련성): 챗봇 답변이 [사용자 질문]의 의도를 정확하고 명확하게 해결해 주었는가?
3. context_relevance (문맥 관련성): [검색된 도서 문맥]이 [사용자 질문]을 답변하기에 유용하고 적절한 도서들인가?

반드시 아래 JSON 형식으로만 엄격하게 응답해라 (다른 설명 금지):
{{
    "faithfulness": 90,
    "answer_relevance": 95,
    "context_relevance": 85,
    "reasoning": "답변이 문맥에 존재하는 도서만을 기반으로 작성되었으며 사용자 질문에 잘 부합함."
}}

[사용자 질문]
{query}

[검색된 도서 문맥]
{context}

[챗봇 답변]
{answer}
"""

def evaluate_rag_response(client: Groq, query: str, context: str, answer: str) -> dict:
    """
    RAGAS 프레임워크 3대 지표 기반 LLM-as-a-Judge 평가 수행
    """
    if not client:
        return {"error": "Groq API Key가 필요합니다."}

    prompt = EVAL_PROMPT.format(query=query, context=context, answer=answer)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        raw_res = completion.choices[0].message.content
        res_json = json.loads(raw_res)

        faithfulness = int(res_json.get("faithfulness", 0))
        answer_relevance = int(res_json.get("answer_relevance", 0))
        context_relevance = int(res_json.get("context_relevance", 0))
        reasoning = str(res_json.get("reasoning", "평가 완료"))

        overall = round((faithfulness + answer_relevance + context_relevance) / 3.0, 1)

        return {
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "context_relevance": context_relevance,
            "overall_score": overall,
            "reasoning": reasoning
        }
    except Exception as e:
        return {
            "faithfulness": 0,
            "answer_relevance": 0,
            "context_relevance": 0,
            "overall_score": 0.0,
            "reasoning": f"평가 중 오류 발생: {e}"
        }
