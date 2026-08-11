import pandas as pd
import sys

# 표준 출력을 UTF-8로 변경 (윈도우 콘솔 대응)
sys.stdout.reconfigure(encoding='utf-8')

parquet_path = "seoseoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet"
df_parquet = pd.read_parquet(parquet_path)

excel_path = "seoseoul-pops/data/행정동코드_매핑정보_20241218.xlsx"
df_excel = pd.read_excel(excel_path)

with open("seoseoul-pops/report/data_inspection_result.txt", "w", encoding="utf-8") as f:
    f.write("=== Parquet Columns ===\n")
    f.write(str(df_parquet.columns.tolist()) + "\n\n")
    f.write("=== Parquet Head ===\n")
    f.write(df_parquet.head(10).to_string() + "\n\n")
    f.write("=== Parquet Value Counts (gender, age) ===\n")
    # 카테고리/범주형 데이터의 빈도 확인
    gender_col = df_parquet.columns[4]
    age_col = df_parquet.columns[5]
    f.write(f"Column 4 ({gender_col}) unique values:\n")
    f.write(str(df_parquet[gender_col].value_counts()) + "\n\n")
    f.write(f"Column 5 ({age_col}) unique values:\n")
    f.write(str(df_parquet[age_col].value_counts()) + "\n\n")
    
    f.write("=== Excel Head ===\n")
    f.write(df_excel.head(10).to_string() + "\n\n")

print("Inspection completed. Saved to report/data_inspection_result.txt")
