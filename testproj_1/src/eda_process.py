import pandas as pd
import os

# 상대 경로를 사용해 데이터 경로 지정
csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "식품의약품안전처_건강기능식품영양성분정보_20251230.csv")
csv_path = os.path.abspath(csv_path)

print(f"Target CSV path: {csv_path}")

encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
df = None
for enc in encodings:
    try:
        df = pd.read_csv(csv_path, encoding=enc, nrows=5)
        print(f"Success with {enc}")
        print("Columns:", df.columns.tolist())
        print(df.head())
        break
    except Exception as e:
        print(f"Failed with {enc}: {str(e)[:100]}")
