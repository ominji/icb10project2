import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "jhgan/ko-sroberta-multitask"

def get_model():
    """SentenceTransformer 모델 로드"""
    return SentenceTransformer(MODEL_NAME)

def prepare_embedding_text(df: pd.DataFrame) -> pd.Series:
    """임베딩에 사용될 결합 텍스트 생성"""
    goods_name = df['goods_name'].fillna('')
    goods_sub = df['goods_name_sub'].fillna('')
    author = df['author'].fillna('')
    publisher = df['publisher'].fillna('')
    tags = df['tags'].fillna('')
    
    combined_text = goods_name + " " + goods_sub + " " + author + " " + publisher + " " + tags
    return combined_text

def export_embedding_projector_files(df: pd.DataFrame, embeddings: np.ndarray, data_dir: str):
    """Google Embedding Projector에 사용할 tensors.tsv와 metadata.tsv 파일 생성"""
    tensors_path = os.path.join(data_dir, "tensors.tsv")
    metadata_path = os.path.join(data_dir, "metadata.tsv")
    
    # 1. Tensors TSV 저장
    np.savetxt(tensors_path, embeddings, delimiter='\t', fmt='%.6f')
    
    # 2. Metadata TSV 저장
    meta_cols = ['goods_name', 'author', 'publisher', 'goods_sort_nm']
    meta_df = df[meta_cols].copy()
    
    # TSV 포맷 오염 방지를 위해 탭 및 줄바꿈 제거
    for col in meta_cols:
        meta_df[col] = meta_df[col].astype(str).str.replace('\t', ' ').str.replace('\n', ' ')
        
    meta_df.to_csv(metadata_path, sep='\t', index=False, encoding='utf-8')

def get_or_create_embeddings(df: pd.DataFrame, data_dir: str):
    """
    임베딩 파일(embeddings.npy)이 존재하는지 확인하고,
    없으면 새로 생성하여 npy 파일 및 TSV 파일들을 저장 후 반환
    """
    npy_path = os.path.join(data_dir, "embeddings.npy")
    model = get_model()
    
    if os.path.exists(npy_path):
        embeddings = np.load(npy_path)
    else:
        texts = prepare_embedding_text(df).tolist()
        embeddings = model.encode(texts, show_progress_bar=True)
        # .npy 파일 저장
        np.save(npy_path, embeddings)
        # Embedding Projector TSV 파일 생성
        export_embedding_projector_files(df, embeddings, data_dir)
        
    return model, embeddings

def search_similarity(query: str, df: pd.DataFrame, embeddings: np.ndarray, model: SentenceTransformer, top_k: int = 10, min_threshold: float = 0.0) -> pd.DataFrame:
    """
    쿼리와 도서 임베딩 간의 코사인 유사도를 계산하여 결과 반환
    """
    if not query.strip():
        return pd.DataFrame()
        
    query_vector = model.encode([query])
    similarities = cosine_similarity(query_vector, embeddings)[0]
    
    res_df = df.copy()
    res_df['similarity'] = similarities
    
    # 임계값 필터링
    res_df = res_df[res_df['similarity'] >= min_threshold]
    
    # 유사도 내림차순 정렬 및 top_k 상위 추출
    res_df = res_df.sort_values(by='similarity', ascending=False).head(top_k)
    
    return res_df
