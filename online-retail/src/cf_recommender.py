import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from recommender import ContentRecommender

class CustomerCFRecommender:
    def __init__(self, 
                 prod_path='online-retail/data/cleaned_products.parquet',
                 cust_path='online-retail/data/cleaned_customers.parquet',
                 purch_path='online-retail/data/customer_purchases.parquet'):
        
        self.df_prods = pd.read_parquet(prod_path)
        self.df_custs = pd.read_parquet(cust_path)
        self.df_purchs = pd.read_parquet(purch_path)
        
        # 추천엔진 (TF-IDF & Embeddings 로드)
        self.content_rec = ContentRecommender(data_path=prod_path)
        
        # 빠른 매핑 dictionary
        self.stock_to_idx = self.content_rec.stock_to_idx
        self.idx_to_stock = self.content_rec.idx_to_stock
        
        # 고객별 구매 이력 딕셔너리 구성 {customer_id: {stock_code: weight}}
        self.cust_purchased_dict = {}
        for cust_id, group in self.df_purchs.groupby('CustomerID'):
            self.cust_purchased_dict[str(cust_id)] = dict(zip(group['StockCode'], group['spend_sum']))

    def get_customer_info(self, customer_id):
        cust_id_str = str(customer_id)
        row = self.df_custs[self.df_custs['CustomerID'] == cust_id_str]
        if len(row) > 0:
            return row.iloc[0].to_dict()
        return None

    def get_customer_purchases(self, customer_id):
        cust_id_str = str(customer_id)
        purch_df = self.df_purchs[self.df_purchs['CustomerID'] == cust_id_str].copy()
        purch_df = purch_df.sort_values(by='spend_sum', ascending=False)
        return purch_df

    def recommend_for_customer(self, customer_id, method='tfidf', top_k=10, filter_purchased=True):
        cust_id_str = str(customer_id)
        if cust_id_str not in self.cust_purchased_dict:
            return None
        
        purchased_map = self.cust_purchased_dict[cust_id_str]
        if not purchased_map:
            return None

        purchased_indices = []
        weights = []
        
        for code, weight in purchased_map.items():
            if code in self.stock_to_idx:
                purchased_indices.append(self.stock_to_idx[code])
                # 가중치는 log(1 + spend_sum) 또는 spend_sum 정규화
                weights.append(np.log1p(weight))

        if not purchased_indices:
            return None

        weights = np.array(weights)
        weights_sum = weights.sum()
        if weights_sum == 0:
            weights_sum = 1.0

        # 유저 프로필 벡터 생성 (User Profile Vector)
        if method == 'tfidf':
            # TF-IDF 행렬 가중치 평균
            purchased_vecs = self.content_rec.tfidf_matrix[purchased_indices]
            # scipy csr_matrix 가중합
            user_profile_vec = purchased_vecs.T.dot(weights) / weights_sum
            user_profile_vec = np.asarray(user_profile_vec).reshape(1, -1)
            sim_scores = cosine_similarity(user_profile_vec, self.content_rec.tfidf_matrix).flatten()

        elif method == 'embedding':
            purchased_vecs = self.content_rec.pretrained_matrix[purchased_indices] # (N, dim)
            user_profile_vec = np.average(purchased_vecs, axis=0, weights=weights).reshape(1, -1)
            sim_scores = cosine_similarity(user_profile_vec, self.content_rec.pretrained_matrix).flatten()
        else:
            raise ValueError("Method must be 'tfidf' or 'embedding'")

        # 정렬 및 추천 필터링
        sorted_indices = np.argsort(sim_scores)[::-1]
        purchased_set = set(purchased_indices)
        
        results = []
        for i in sorted_indices:
            if filter_purchased and i in purchased_set:
                continue
            
            score = float(sim_scores[i])
            row = self.df_prods.iloc[i]
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
    cf = CustomerCFRecommender()
    sample_cust = cf.df_custs['CustomerID'].iloc[0]
    print(f"\n--- Customer CF Test for CustomerID: {sample_cust} ---")
    print("Purchased Items Sample:")
    print(cf.get_customer_purchases(sample_cust).head(3))
    
    print("\n[TF-IDF Customer Recommendations]")
    print(cf.recommend_for_customer(sample_cust, method='tfidf', top_k=5))
    
    print("\n[Embedding Customer Recommendations]")
    print(cf.recommend_for_customer(sample_cust, method='embedding', top_k=5))
