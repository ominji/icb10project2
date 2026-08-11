import os
import pickle
import json
import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LIGHT_MODEL_NAME = "jhgan/ko-sroberta-multitask"
VECTOR_STORE_PATH = os.path.join("samsungfire", "data", "vector_store.pkl")
CHUNKS_PATH = os.path.join("samsungfire", "data", "chunks.json")

class LightweightRetriever:
    """
    저사양 노트북을 위한 하이브리드/경량 텍스트 검색기.
    - TF-IDF Vectorizer: CPU 및 메모리 부담 제로, 0.1초 즉시 인덱싱 지원
    - Ko-SRoBERTa SBERT: 세밀한 문맥 의미 파악 (필요 시 빌드)
    """
    def __init__(self, mode: str = "tfidf"):
        self.mode = mode
        self.chunks: List[Dict] = []
        self.embeddings: np.ndarray = None
        self.model = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None

    def load_or_build_index(self, chunks: List[Dict] = None, force_rebuild: bool = False, use_sbert: bool = False):
        """저장된 인덱스가 있으면 로드하고, 없으면 빠르게 TF-IDF 인덱스를 빌드합니다."""
        if not force_rebuild and os.path.exists(VECTOR_STORE_PATH):
            try:
                with open(VECTOR_STORE_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.chunks = data["chunks"]
                    self.embeddings = data.get("embeddings")
                    self.tfidf_vectorizer = data.get("tfidf_vectorizer")
                    self.tfidf_matrix = data.get("tfidf_matrix")
                    self.mode = data.get("mode", self.mode)
                return
            except Exception as e:
                print(f"[WARNING] 캐시 로드 실패 ({e}), 새로 생성합니다.")

        if chunks is None:
            if os.path.exists(CHUNKS_PATH):
                with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
            else:
                from samsungfire.src.pdf_parser import process_pdf_and_save_chunks
                chunks = process_pdf_and_save_chunks()

        self.chunks = chunks
        contents = [c["content"] for c in chunks]

        # 1. TF-IDF 벡터 인덱스 (초경량, 0.1초 인덱싱)
        print("[INFO] TF-IDF 초경량 벡터라이저 인덱싱 중...")
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)
        self.mode = "tfidf"

        # 2. 사용자가 원할 경우 SBERT 임베딩 생성 시도
        if use_sbert:
            try:
                print(f"[INFO] SentenceTransformers({LIGHT_MODEL_NAME}) 임베딩 생성...")
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(LIGHT_MODEL_NAME)
                self.embeddings = self.model.encode(contents, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
                self.mode = "sbert"
            except Exception as e:
                print(f"[WARNING] SBERT 모델 로드/임베딩 실패 ({e}). TF-IDF 인덱스로 유지합니다.")

        # 인덱스 파일 저장
        os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
        with open(VECTOR_STORE_PATH, "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "embeddings": self.embeddings,
                "tfidf_vectorizer": self.tfidf_vectorizer,
                "tfidf_matrix": self.tfidf_matrix,
                "mode": self.mode
            }, f)
        print(f"[INFO] 인덱스 저장 완료: {VECTOR_STORE_PATH} (모드: {self.mode})")

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict, float]]:
        """쿼리와 가장 유사한 top_k 개의 청크와 유사도 점수를 반환합니다."""
        if not self.chunks or self.tfidf_matrix is None:
            self.load_or_build_index()

        # SBERT 검색 모드
        if self.mode == "sbert" and self.embeddings is not None:
            try:
                if self.model is None:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer(LIGHT_MODEL_NAME)
                query_vec = self.model.encode([query], normalize_embeddings=True)
                similarities = np.dot(self.embeddings, query_vec.T).squeeze(1)
                top_indices = np.argsort(similarities)[::-1][:top_k]
                
                return [(self.chunks[idx], float(similarities[idx])) for idx in top_indices]
            except Exception as e:
                print(f"[WARNING] SBERT 검색 중 오류 ({e}), TF-IDF로 검색합니다.")

        # TF-IDF 초경량 검색 모드
        query_vec = self.tfidf_vectorizer.transform([query])
        similarities = cosine_similarity(self.tfidf_matrix, query_vec).squeeze(1)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [(self.chunks[idx], float(similarities[idx])) for idx in top_indices]

if __name__ == "__main__":
    retriever = LightweightRetriever()
    retriever.load_or_build_index(force_rebuild=True, use_sbert=False)
    test_query = "보상하는 손해"
    res = retriever.search(test_query, top_k=3)
    print(f"\n[TF-IDF 검색 결과 - 쿼리: '{test_query}']")
    for item, score in res:
        print(f"- (페이지 {item['page']}, 점수: {score:.4f}): {item['content'][:80]}...")
