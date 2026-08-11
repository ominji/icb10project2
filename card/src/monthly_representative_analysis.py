import pandas as pd
import numpy as np
import os

# ----------------------------------------------------
# 1. 첫 번째 데이터: 전국 신용카드 데이터 (2022/08 ~ 2023/08)
# ----------------------------------------------------
file1_path = os.path.join("card", "data", "지역별 소비유형별 개인 신용카드_11134440.csv")
df1 = pd.read_csv(file1_path, encoding='utf-8')
df1['소비유형코드'] = df1['소비유형코드'].str.strip()

# '총액'만 필터링 및 '합계' 제외
df1 = df1[(df1['금액구분코드'] == '총액') & (df1['소비유형코드'] != '합계')]
month_cols_1 = [col for col in df1.columns if '/' in col]

for col in month_cols_1:
    df1[col] = df1[col].astype(str).str.replace(',', '').astype(float)

# 업종별-월별 매트릭스
df1_matrix = df1.set_index('소비유형코드')[month_cols_1]

# 각 업종별로 전체 기간 평균 매출 계산
avg_by_sector_1 = df1_matrix.mean(axis=1)

# 각 월의 매출이 해당 업종의 평균 대비 몇 배인지 계산 (지수화)
# Index = 업종, Column = 월
ratio_matrix_1 = df1_matrix.div(avg_by_sector_1, axis=0)

# 월별로 지수(ratio)가 가장 높은 업종 상위 1개(또는 2개) 추출
print("=== [데이터 1] 전국 신용카드 월별 대표 업종 (평균 대비 최고 배수 기준) ===")
rep_sectors_1 = []
for col in month_cols_1:
    sorted_sectors = ratio_matrix_1[col].sort_values(ascending=False)
    top_sector = sorted_sectors.index[0]
    ratio_val = sorted_sectors.values[0]
    amt_val = df1_matrix.loc[top_sector, col]
    
    # 전월 대비 증감율 계산용
    col_idx = month_cols_1.index(col)
    if col_idx > 0:
        prev_col = month_cols_1[col_idx - 1]
        prev_amt = df1_matrix.loc[top_sector, prev_col]
        mom_pct = ((amt_val - prev_amt) / prev_amt) * 100
        mom_str = f"{mom_pct:+.1f}%"
    else:
        mom_str = "N/A"
        
    rep_sectors_1.append({
        '월': col,
        '대표 업종': top_sector,
        '평균대비 지수': f"{ratio_val:.2f}배",
        '해당월 매출액(백만원)': f"{amt_val:,.0f}",
        '전월대비 증감율': mom_str
    })
    
df_rep_1 = pd.DataFrame(rep_sectors_1)
print(df_rep_1.to_string(index=False))


# ----------------------------------------------------
# 2. 두 번째 데이터: 경기도 카드 데이터 (2025/03 ~ 2025/12)
# ----------------------------------------------------
file2_path = os.path.join("card", "data", "경기도 카드소비데이터_2025", "aggregated_summary.csv")
df2 = pd.read_csv(file2_path)
df2['card_tpbuz_nm_1'] = df2['card_tpbuz_nm_1'].str.strip()
df2 = df2[df2['year_month'] != 'unknown']

# 업종별-월별 매출액 매트릭스 생성
df2_matrix = df2.groupby(['card_tpbuz_nm_1', 'year_month'])['amt'].sum().unstack()
month_cols_2 = sorted(df2_matrix.columns)

# 업종별 평균 매출 계산
avg_by_sector_2 = df2_matrix.mean(axis=1)

# 지수화 (평균 대비 배수)
ratio_matrix_2 = df2_matrix.div(avg_by_sector_2, axis=0)

print("\n=== [데이터 2] 경기도 카드 월별 대표 업종 (평균 대비 최고 배수 기준) ===")
rep_sectors_2 = []
for col in month_cols_2:
    sorted_sectors = ratio_matrix_2[col].sort_values(ascending=False)
    top_sector = sorted_sectors.index[0]
    ratio_val = sorted_sectors.values[0]
    amt_val = df2_matrix.loc[top_sector, col]
    
    col_idx = month_cols_2.index(col)
    if col_idx > 0:
        prev_col = month_cols_2[col_idx - 1]
        prev_amt = df2_matrix.loc[top_sector, prev_col]
        mom_pct = ((amt_val - prev_amt) / prev_amt) * 100
        mom_str = f"{mom_pct:+.1f}%"
    else:
        mom_str = "N/A"
        
    rep_sectors_2.append({
        '월': col,
        '대표 업종': top_sector,
        '평균대비 지수': f"{ratio_val:.2f}배",
        '해당월 매출액(억원)': f"{amt_val / 1e8:,.1f}억 원",
        '전월대비 증감율': mom_str
    })
    
df_rep_2 = pd.DataFrame(rep_sectors_2)
print(df_rep_2.to_string(index=False))

# 파일로 저장
out_path = os.path.join("card", "src", "monthly_representatives.txt")
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("=== [데이터 1] 전국 신용카드 월별 대표 업종 ===\n")
    f.write(df_rep_1.to_string(index=False) + "\n\n")
    f.write("=== [데이터 2] 경기도 카드 월별 대표 업종 ===\n")
    f.write(df_rep_2.to_string(index=False) + "\n\n")
