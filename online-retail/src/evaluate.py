import numpy as np
import pandas as pd
from recommender import ContentRecommender
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

def evaluate_recommenders(sample_size=300, top_k=10):
    print("Loading recommender engine for evaluation...")
    rec = ContentRecommender()
    
    # 평가를 위한 샘플 쿼리 상품선정
    all_codes = rec.df['StockCode'].tolist()
    total_products = len(all_codes)
    np.random.seed(42)
    sample_codes = np.random.choice(all_codes, size=min(sample_size, total_products), replace=False)
    
    # 전체 주문수 합산 (Novelty 계산용)
    total_orders = rec.df['order_count'].sum()
    order_counts = dict(zip(rec.df['StockCode'], rec.df['order_count']))
    
    metrics = {
        'tfidf': {'avg_sim': [], 'ild': [], 'novelty': [], 'recommended_items': set()},
        'embedding': {'avg_sim': [], 'ild': [], 'novelty': [], 'recommended_items': set()}
    }

    for code in sample_codes:
        idx = rec.stock_to_idx[code]
        
        for method in ['tfidf', 'embedding']:
            res = rec.recommend(code, method=method, top_k=top_k)
            if res is None or len(res) == 0:
                continue
                
            rec_codes = res['StockCode'].tolist()
            metrics[method]['recommended_items'].update(rec_codes)
            
            # 1. Avg Similarity
            sims = res['Similarity'].tolist()
            metrics[method]['avg_sim'].append(np.mean(sims))
            
            # 2. Intra-List Diversity (ILD)
            rec_indices = [rec.stock_to_idx[c] for c in rec_codes if c in rec.stock_to_idx]
            if len(rec_indices) > 1:
                if method == 'tfidf':
                    matrix = rec.tfidf_matrix[rec_indices].toarray()
                else:
                    matrix = rec.pretrained_matrix[rec_indices]
                
                sim_matrix = cosine_similarity(matrix)
                # 상삼각 행렬 항목 추출 (자기 자신 제외)
                n = len(rec_indices)
                upper_tri = sim_matrix[np.triu_indices(n, k=1)]
                ild = 1.0 - np.mean(upper_tri)
                metrics[method]['ild'].append(ild)
            
            # 3. Novelty: -log2(P(item))
            novelties = []
            for r_code in rec_codes:
                cnt = order_counts.get(r_code, 1)
                p_item = cnt / total_orders
                novelties.append(-np.log2(p_item))
            metrics[method]['novelty'].append(np.mean(novelties))

    final_results = {}
    for method in ['tfidf', 'embedding']:
        cov = (len(metrics[method]['recommended_items']) / total_products) * 100
        final_results[method] = {
            'Average_Similarity': round(float(np.mean(metrics[method]['avg_sim'])), 4),
            'Intra_List_Diversity': round(float(np.mean(metrics[method]['ild'])), 4),
            'Novelty': round(float(np.mean(metrics[method]['novelty'])), 4),
            'Catalog_Coverage_Pct': round(float(cov), 2),
            'Total_Recommended_Unique_Items': len(metrics[method]['recommended_items']),
            'Sample_Queries_Evaluated': len(sample_codes)
        }

    print("\n================ Evaluation Results ================")
    print(json.dumps(final_results, indent=2))
    
    os.makedirs('online-retail/report', exist_ok=True)
    with open('online-retail/report/evaluation_metrics.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    print("Saved evaluation metrics to online-retail/report/evaluation_metrics.json")
    
    return final_results

if __name__ == '__main__':
    evaluate_recommenders()
