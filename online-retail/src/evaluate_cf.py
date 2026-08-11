import numpy as np
import pandas as pd
from cf_recommender import CustomerCFRecommender
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

def evaluate_customer_cf(top_k=10, test_user_sample=300):
    print("Initializing Customer CF Recommender for evaluation...")
    cf = CustomerCFRecommender()
    
    # 구매한 상품 종류가 5개 이상인 고객을 대상으로 평가 (Holdout Split 용도)
    eligible_custs = cf.df_custs[cf.df_custs['unique_items_bought'] >= 5]['CustomerID'].tolist()
    
    np.random.seed(42)
    sample_cust_ids = np.random.choice(eligible_custs, size=min(test_user_sample, len(eligible_custs)), replace=False)
    
    metrics = {
        'tfidf': {'precision': [], 'recall': [], 'map': [], 'ild': []},
        'embedding': {'precision': [], 'recall': [], 'map': [], 'ild': []}
    }
    
    for cust_id in sample_cust_ids:
        purch_df = cf.get_customer_purchases(cust_id)
        if len(purch_df) < 5:
            continue
            
        # 80% Train, 20% Test Holdout split (랜덤 셔플)
        purch_codes = purch_df['StockCode'].tolist()
        np.random.shuffle(purch_codes)
        
        split_idx = max(1, int(len(purch_codes) * 0.8))
        train_codes = set(purch_codes[:split_idx])
        test_codes = set(purch_codes[split_idx:])
        
        # Train item들에 대한 가중치 유저 프로필 생성
        train_indices = [cf.stock_to_idx[c] for c in train_codes if c in cf.stock_to_idx]
        if not train_indices:
            continue

        train_weights = np.array([np.log1p(purch_df[purch_df['StockCode'] == c]['spend_sum'].values[0]) for c in train_codes if c in cf.stock_to_idx])
        w_sum = train_weights.sum()
        if w_sum == 0:
            w_sum = 1.0

        for method in ['tfidf', 'embedding']:
            if method == 'tfidf':
                user_vec = cf.content_rec.tfidf_matrix[train_indices].T.dot(train_weights) / w_sum
                user_vec = np.asarray(user_vec).reshape(1, -1)
                sims = cosine_similarity(user_vec, cf.content_rec.tfidf_matrix).flatten()
            else:
                user_vec = np.average(cf.content_rec.pretrained_matrix[train_indices], axis=0, weights=train_weights).reshape(1, -1)
                sims = cosine_similarity(user_vec, cf.content_rec.pretrained_matrix).flatten()

            sorted_indices = np.argsort(sims)[::-1]
            train_idx_set = set(train_indices)
            
            rec_codes = []
            rec_indices = []
            for idx in sorted_indices:
                if idx in train_idx_set:
                    continue
                code = cf.idx_to_stock[idx]
                rec_codes.append(code)
                rec_indices.append(idx)
                if len(rec_codes) >= top_k:
                    break

            # 1. Precision & Recall @ K
            hits = [1 if c in test_codes else 0 for c in rec_codes]
            hit_count = sum(hits)
            
            precision = hit_count / top_k
            recall = hit_count / len(test_codes) if len(test_codes) > 0 else 0.0
            
            # 2. MAP@K (Average Precision)
            ap = 0.0
            num_hits = 0.0
            for i, hit in enumerate(hits):
                if hit == 1:
                    num_hits += 1.0
                    ap += num_hits / (i + 1.0)
            map_score = ap / min(top_k, len(test_codes)) if len(test_codes) > 0 else 0.0
            
            # 3. ILD (Intra-List Diversity)
            if len(rec_indices) > 1:
                if method == 'tfidf':
                    mat = cf.content_rec.tfidf_matrix[rec_indices].toarray()
                else:
                    mat = cf.content_rec.pretrained_matrix[rec_indices]
                sim_m = cosine_similarity(mat)
                n = len(rec_indices)
                ild = 1.0 - np.mean(sim_m[np.triu_indices(n, k=1)])
            else:
                ild = 0.0
                
            metrics[method]['precision'].append(precision)
            metrics[method]['recall'].append(recall)
            metrics[method]['map'].append(map_score)
            metrics[method]['ild'].append(ild)

    results = {}
    for method in ['tfidf', 'embedding']:
        results[method] = {
            'Precision_At_10': round(float(np.mean(metrics[method]['precision'])), 4),
            'Recall_At_10': round(float(np.mean(metrics[method]['recall'])), 4),
            'MAP_At_10': round(float(np.mean(metrics[method]['map'])), 4),
            'Intra_List_Diversity': round(float(np.mean(metrics[method]['ild'])), 4),
            'Evaluated_Customers_Count': len(metrics[method]['precision'])
        }

    print("\n================ Collaborative Filtering Evaluation Results ================")
    print(json.dumps(results, indent=2))
    
    os.makedirs('online-retail/report', exist_ok=True)
    with open('online-retail/report/cf_evaluation_metrics.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved CF evaluation metrics to online-retail/report/cf_evaluation_metrics.json")
    
    return results

if __name__ == '__main__':
    evaluate_customer_cf()
