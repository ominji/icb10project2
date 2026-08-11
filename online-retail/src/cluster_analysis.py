import pandas as pd
import numpy as np
import datetime as dt
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
import json

def analyze_rfm_and_clustering():
    raw_path = 'online-retail/data/online_retail (1).parquet'
    output_clusters_path = 'online-retail/data/customer_clusters.parquet'
    output_cust_path = 'online-retail/data/cleaned_customers.parquet'
    output_eval_path = 'online-retail/report/clustering_eval.json'
    
    print(f"Loading raw data from {raw_path}...")
    df = pd.read_parquet(raw_path)
    
    # 데이터 정제
    df = df.dropna(subset=['CustomerID', 'Description'])
    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    
    df['TotalSpend'] = df['Quantity'] * df['UnitPrice']
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    
    snapshot_date = df['InvoiceDate'].max() + dt.timedelta(days=1)
    
    # 1. RFM 원본 값 산출
    rfm = df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (snapshot_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('TotalSpend', 'sum')
    ).reset_index()
    
    rfm['Monetary'] = rfm['Monetary'].round(2)
    
    # 2. RFM Log 변환 값 산출
    rfm['Log_Recency'] = np.log1p(rfm['Recency']).round(4)
    rfm['Log_Frequency'] = np.log1p(rfm['Frequency']).round(4)
    rfm['Log_Monetary'] = np.log1p(rfm['Monetary']).round(4)
    
    # 3. RFM Score 산출 (1 ~ 5 점수화)
    r_labels = [5, 4, 3, 2, 1]
    rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=r_labels, duplicates='drop').astype(int)
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm['RFM_Score_Sum'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']
    
    # 4. RFM Rule-based Segment
    def assign_rfm_segment(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions (최우수 고객)'
        elif r >= 3 and f >= 3:
            return 'Loyal Customers (충성 고객)'
        elif r >= 3 and f <= 2:
            return 'Potential Loyalists (잠재 충성 고객)'
        elif r <= 2 and f >= 3:
            return 'At Risk (이탈 위기 고객)'
        else:
            return 'Hibernating / Lost (휴면/이탈 고객)'

    rfm['RFM_Segment'] = rfm.apply(assign_rfm_segment, axis=1)
    
    # 5. K-Means Clustering & K별 평가 지표 계산 (Elbow & Silhouette)
    rfm_log = rfm[['Log_Recency', 'Log_Frequency', 'Log_Monetary']]
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log)
    
    eval_metrics = {'k_list': [], 'inertia': [], 'silhouette_avg': []}
    
    for k in range(2, 9):
        km_test = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels_test = km_test.fit_predict(rfm_scaled)
        sil_avg = silhouette_score(rfm_scaled, labels_test)
        
        eval_metrics['k_list'].append(k)
        eval_metrics['inertia'].append(float(km_test.inertia_))
        eval_metrics['silhouette_avg'].append(float(sil_avg))
        
    # K=4 파이널 군집 모델
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm['KMeans_Cluster'] = kmeans.fit_predict(rfm_scaled)
    rfm['KMeans_Cluster_Name'] = rfm['KMeans_Cluster'].apply(lambda x: f"Cluster {x}")
    
    # 개별 샘플별 실루엣 값 연산
    rfm['Silhouette_Value'] = silhouette_samples(rfm_scaled, rfm['KMeans_Cluster']).round(4)
    overall_silhouette_mean = float(rfm['Silhouette_Value'].mean())
    
    eval_metrics['optimal_k'] = 4
    eval_metrics['overall_silhouette_mean'] = round(overall_silhouette_mean, 4)
    
    # 저장
    os.makedirs(os.path.dirname(output_clusters_path), exist_ok=True)
    rfm.to_parquet(output_clusters_path, index=False)
    
    os.makedirs(os.path.dirname(output_eval_path), exist_ok=True)
    with open(output_eval_path, 'w') as f:
        json.dump(eval_metrics, f, indent=2)
        
    print(f"Saved RFM, Log, Clusters, & Silhouette data to {output_clusters_path}")
    print(f"Saved Evaluation metrics to {output_eval_path}")

if __name__ == '__main__':
    analyze_rfm_and_clustering()
