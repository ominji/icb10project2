import pandas as pd
import re
import os

def clean_data():
    raw_path = 'online-retail/data/online_retail (1).parquet'
    prod_output_path = 'online-retail/data/cleaned_products.parquet'
    cust_output_path = 'online-retail/data/cleaned_customers.parquet'
    purch_output_path = 'online-retail/data/customer_purchases.parquet'
    
    print(f"Reading raw data from {raw_path}...")
    df = pd.read_parquet(raw_path)
    
    # 1. Description null 제거
    df = df.dropna(subset=['Description'])
    
    # 2. Description 및 StockCode 문자열 변환 및 양끝 공백 제거
    df['StockCode'] = df['StockCode'].astype(str).str.strip()
    df['Description'] = df['Description'].astype(str).str.strip()
    
    # 3. 취소건 및 비정상/테스트 데이터 제거
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df = df[df['Quantity'] > 0]
    df = df[df['UnitPrice'] > 0]
    
    # 시스템/수수료성 항목 제외
    invalid_codes = ['POST', 'D', 'M', 'BANK CHARGES', 'PADS', 'DOT', 'CRUK']
    df = df[~df['StockCode'].isin(invalid_codes)]
    
    # Description 정제: 대문자화, 연속 공백 정리
    df['Description_clean'] = df['Description'].apply(lambda x: re.sub(r'\s+', ' ', x).upper())
    
    # 4. 상품 마스터 생성 (StockCode & Description_clean 기준 중복 제거)
    prod_counts = df.groupby(['StockCode', 'Description_clean']).size().reset_index(name='count')
    prod_counts = prod_counts.sort_values(by=['StockCode', 'count'], ascending=[True, False])
    unique_prods = prod_counts.drop_duplicates(subset=['StockCode'], keep='first').copy()
    unique_prods = unique_prods[unique_prods['Description_clean'].str.len() >= 3]
    unique_prods = unique_prods[~unique_prods['Description_clean'].str.isnumeric()]
    
    item_stats = df.groupby('StockCode').agg(
        total_quantity=('Quantity', 'sum'),
        order_count=('InvoiceNo', 'nunique'),
        customer_count=('CustomerID', 'nunique')
    ).reset_index()
    
    final_prods = pd.merge(unique_prods, item_stats, on='StockCode', how='inner')
    final_prods = final_prods.rename(columns={'Description_clean': 'Description'})
    final_prods = final_prods[['StockCode', 'Description', 'count', 'total_quantity', 'order_count', 'customer_count']]
    
    os.makedirs(os.path.dirname(prod_output_path), exist_ok=True)
    final_prods.to_parquet(prod_output_path, index=False)
    print(f"Saved {len(final_prods)} unique products to {prod_output_path}")

    # 5. 고객 마스터 및 고객 구매 이력 생성
    df_valid_cust = df.dropna(subset=['CustomerID']).copy()
    df_valid_cust['CustomerID'] = df_valid_cust['CustomerID'].astype(int).astype(str)
    df_valid_cust['TotalSpend'] = df_valid_cust['Quantity'] * df_valid_cust['UnitPrice']

    # 유효한 정제 상품 목록에 포함되는 거래만 필터링
    valid_stock_codes = set(final_prods['StockCode'])
    df_valid_cust = df_valid_cust[df_valid_cust['StockCode'].isin(valid_stock_codes)]

    # 고객별 구매 이력 집계
    cust_purchases = df_valid_cust.groupby(['CustomerID', 'StockCode']).agg(
        quantity_sum=('Quantity', 'sum'),
        spend_sum=('TotalSpend', 'sum'),
        order_count=('InvoiceNo', 'nunique')
    ).reset_index()

    # 상품명 매핑 추가
    stock_to_desc = dict(zip(final_prods['StockCode'], final_prods['Description']))
    cust_purchases['Description'] = cust_purchases['StockCode'].map(stock_to_desc)

    cust_purchases.to_parquet(purch_output_path, index=False)
    print(f"Saved {len(cust_purchases)} customer purchase records to {purch_output_path}")

    # 고객 통계 마스터 생성
    cust_stats = cust_purchases.groupby('CustomerID').agg(
        total_orders=('order_count', 'sum'),
        unique_items_bought=('StockCode', 'nunique'),
        total_items_bought=('quantity_sum', 'sum'),
        total_spend=('spend_sum', 'sum')
    ).reset_index()

    cust_stats['total_spend'] = cust_stats['total_spend'].round(2)
    cust_stats.to_parquet(cust_output_path, index=False)
    print(f"Saved {len(cust_stats)} unique customer statistics to {cust_output_path}")

if __name__ == '__main__':
    clean_data()
