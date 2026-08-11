import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class ContentRecommender:
    def __init__(self, data_path='online-retail/data/cleaned_products.parquet'):
        self.data_path = data_path
        self.df = pd.read_parquet(data_path)
        self.df = self.df.reset_index(drop=True)
        
        # 상품코드 & 인덱스 매핑
        self.stock_to_idx = {code: idx for idx, code in enumerate(self.df['StockCode'])}
        self.idx_to_stock = {idx: code for idx, code in enumerate(self.df['StockCode'])}
        
        # TF-IDF 및 Pretrained Embedding 초기화
        self._init_tfidf()
        self._init_pretrained_embeddings()

    def _init_tfidf(self):
        print("Initializing TF-IDF Vectorizer...")
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.df['Description'])

    def _init_pretrained_embeddings(self, cache_path='online-retail/data/embeddings_minilm.npy'):
        print("Initializing Pretrained SentenceTransformer Embeddings...")
        if os.path.exists(cache_path):
            print(f"Loading cached embeddings from {cache_path}")
            self.pretrained_matrix = np.load(cache_path)
        else:
            print("Encoding descriptions with all-MiniLM-L6-v2 model...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            descriptions = self.df['Description'].tolist()
            embeddings = model.encode(descriptions, show_progress_bar=True, normalize_embeddings=True)
            self.pretrained_matrix = np.array(embeddings)
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            np.save(cache_path, self.pretrained_matrix)
            print(f"Embeddings saved to {cache_path}")

    def recommend(self, query_stock_code, method='tfidf', top_k=10, min_threshold=0.0):
        if query_stock_code not in self.stock_to_idx:
            return None
        
        idx = self.stock_to_idx[query_stock_code]
        
        if method == 'tfidf':
            query_vec = self.tfidf_matrix[idx]
            sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        elif method == 'embedding':
            query_vec = self.pretrained_matrix[idx].reshape(1, -1)
            sim_scores = cosine_similarity(query_vec, self.pretrained_matrix).flatten()
        else:
            raise ValueError("Method must be either 'tfidf' or 'embedding'")

        # 자기 자신 제외 정렬
        sorted_indices = np.argsort(sim_scores)[::-1]
        
        results = []
        for i in sorted_indices:
            if i == idx:
                continue
            score = float(sim_scores[i])
            if score < min_threshold:
                continue
            
            row = self.df.iloc[i]
            results.append({
                'StockCode': row['StockCode'],
                'Description': row['Description'],
                'Similarity': score,
                'OrderCount': int(row['order_count'])
            })
            if len(results) >= top_k:
                break
                
        return pd.DataFrame(results)

if __name__ == '__main__':
    rec = ContentRecommender()
    test_code = rec.df['StockCode'].iloc[0]
    print(f"\n--- Test Recommendations for StockCode: {test_code} ({rec.df['Description'].iloc[0]}) ---")
    print("\n[TF-IDF Recommendations]")
    print(rec.recommend(test_code, method='tfidf', top_k=5))
    print("\n[Pretrained Embedding Recommendations]")
    print(rec.recommend(test_code, method='embedding', top_k=5))
