import os
import sys
import pandas as pd
import numpy as np
import chromadb

# 모듈 위치 등록
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from embedding_utils import prepare_embedding_text

COLLECTION_NAME = "yes24_bestsellers"

def get_chroma_collection(data_dir: str):
    """ChromaDB PersistentClient 및 Collection 가져오기"""
    db_path = os.path.join(data_dir, "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection

def initialize_chroma_db(df: pd.DataFrame, embeddings: np.ndarray, data_dir: str):
    """
    ChromaDB 컬렉션에 도서 메타데이터 및 임베딩 벡터를 저장 (이미 저장된 경우 스킵)
    """
    collection = get_chroma_collection(data_dir)
    
    # 이미 데이터가 저장되어 있다면 새로 추가하지 않음
    if collection.count() >= len(df):
        return collection

    ids = [f"book_{i}" for i in range(len(df))]
    documents = prepare_embedding_text(df).tolist()
    
    # NaN 값 방지를 위해 fillna 처리 후 dict 생성
    clean_df = df.copy()
    clean_df['goods_name'] = clean_df['goods_name'].fillna('제목없음')
    clean_df['author'] = clean_df['author'].fillna('저자미상')
    clean_df['publisher'] = clean_df['publisher'].fillna('출판사미상')
    clean_df['goods_sort_nm'] = clean_df['goods_sort_nm'].fillna('기타')
    clean_df['sale_price'] = clean_df['sale_price'].fillna(0).astype(int)
    clean_df['rating_grade'] = clean_df['rating_grade'].fillna(0.0).astype(float)
    clean_df['tags'] = clean_df['tags'].fillna('')

    metadatas = []
    for _, row in clean_df.iterrows():
        metadatas.append({
            "goods_name": str(row['goods_name']),
            "author": str(row['author']),
            "publisher": str(row['publisher']),
            "goods_sort_nm": str(row['goods_sort_nm']),
            "sale_price": int(row['sale_price']),
            "rating_grade": float(row['rating_grade']),
            "tags": str(row['tags'])
        })

    # ChromaDB에 백치로 추가 (대용량일 경우 배치 분할 필요하지만 1000건 내외는 일괄 가능)
    embeddings_list = embeddings.tolist()
    collection.add(
        ids=ids,
        embeddings=embeddings_list,
        documents=documents,
        metadatas=metadatas
    )

    return collection

def search_chroma_context(query: str, model, collection, n_results: int = 5) -> str:
    """
    쿼리와 유사한 도서를 ChromaDB에서 조회하여 RAG 검색 문맥(Context) 텍스트로 생성
    """
    query_vector = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_vector,
        n_results=n_results
    )

    if not results or not results['metadatas'] or len(results['metadatas'][0]) == 0:
        return "검색된 베스트셀러 도서가 없습니다."

    context_str = "[[ YES24 베스트셀러 검색 검색결과 목록 ]]\n"
    metadatas = results['metadatas'][0]
    distances = results['distances'][0] if 'distances' in results and results['distances'] else [0]*len(metadatas)

    for i, meta in enumerate(metadatas):
        context_str += (
            f"\n{i+1}. 도서명: {meta.get('goods_name')}\n"
            f"   - 저자: {meta.get('author')}\n"
            f"   - 출판사: {meta.get('publisher')}\n"
            f"   - 카테고리: {meta.get('goods_sort_nm')}\n"
            f"   - 판매가: {meta.get('sale_price'):,}원\n"
            f"   - 평점: {meta.get('rating_grade')}\n"
            f"   - 태그/키워드: {meta.get('tags')}\n"
        )

    return context_str
