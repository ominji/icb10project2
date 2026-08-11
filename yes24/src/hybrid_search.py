import os
import sys
import re
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from embedding_utils import prepare_embedding_text

def tokenize_korean(text: str) -> list[str]:
    """간단하고 빠른 한국어 어절 및 구두점 분리 토큰화"""
    if not isinstance(text, str):
        return []
    # 특수문자 제거 및 소문자화
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    tokens = [w for w in cleaned.split() if len(w) > 1 or w.isalnum()]
    return tokens

def create_bm25_index(df: pd.DataFrame) -> BM25Okapi:
    """도서 데이터프레임 기반 BM25Okapi 인덱스 생성"""
    texts = prepare_embedding_text(df).tolist()
    tokenized_corpus = [tokenize_korean(t) for t in texts]
    return BM25Okapi(tokenized_corpus)

def search_hybrid(
    query: str, 
    df: pd.DataFrame, 
    embeddings: np.ndarray, 
    model, 
    bm25_index: BM25Okapi,
    top_k: int = 5, 
    min_threshold: float = 0.2, 
    alpha: float = 0.5
):
    """
    BM25 키워드 점수와 벡터 유사도 점수를 결합한 하이브리드 검색
    - alpha: 벡터 점수 가중치 (1.0 = 벡터 100%, 0.0 = BM25 100%, 0.5 = 50:50)
    """
    if not query.strip():
        return [], "검색어가 입력되지 않았습니다."

    query_tokens = tokenize_korean(query)
    
    # 1. BM25 점수 계산 및 0~1 정규화
    bm25_raw_scores = bm25_index.get_scores(query_tokens)
    max_bm25 = np.max(bm25_raw_scores) if len(bm25_raw_scores) > 0 and np.max(bm25_raw_scores) > 0 else 1.0
    bm25_scores = bm25_raw_scores / max_bm25

    # 2. 벡터 유사도 점수 계산 (Cosine Similarity)
    query_vector = model.encode([query])
    vector_scores = cosine_similarity(query_vector, embeddings)[0]
    # 음수 유사도는 0으로 클리핑
    vector_scores = np.clip(vector_scores, 0, 1)

    # 3. 가중 합산 점수 계산
    final_scores = (alpha * vector_scores) + ((1.0 - alpha) * bm25_scores)

    res_df = df.copy()
    res_df['combined_score'] = final_scores
    res_df['vector_score'] = vector_scores
    res_df['bm25_score'] = bm25_scores

    # 임계값 필터링 및 상위 Top K 추출
    filtered_df = res_df[res_df['combined_score'] >= min_threshold]
    filtered_df = filtered_df.sort_values(by='combined_score', ascending=False).head(top_k)

    if filtered_df.empty:
        return [], "조건에 부합하는 베스트셀러 도서가 없습니다."

    # LLM 전달용 컨텍스트 텍스트 생성
    context_str = "[[ YES24 베스트셀러 검색결과 목록 ]]\n"
    results_list = []

    for i, (_, row) in enumerate(filtered_df.iterrows()):
        item = {
            "goods_name": str(row['goods_name']),
            "author": str(row['author']),
            "publisher": str(row['publisher']),
            "goods_sort_nm": str(row['goods_sort_nm']),
            "sale_price": int(row['sale_price']) if not pd.isna(row['sale_price']) else 0,
            "rating_grade": float(row['rating_grade']) if not pd.isna(row['rating_grade']) else 0.0,
            "tags": str(row['tags']) if not pd.isna(row['tags']) else '',
            "combined_score": float(row['combined_score']),
            "vector_score": float(row['vector_score']),
            "bm25_score": float(row['bm25_score'])
        }
        results_list.append(item)

        context_str += (
            f"\n{i+1}. 도서명: {item['goods_name']}\n"
            f"   - 저자: {item['author']}\n"
            f"   - 출판사: {item['publisher']}\n"
            f"   - 카테고리: {item['goods_sort_nm']}\n"
            f"   - 판매가: {item['sale_price']:,}원\n"
            f"   - 평점: {item['rating_grade']}\n"
            f"   - 종합유사도: {item['combined_score']*100:.1f}%\n"
            f"   - 태그/키워드: {item['tags']}\n"
        )

    return results_list, context_str
