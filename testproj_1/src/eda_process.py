import pandas as pd
import os
import sys

# Windows 터미널 한글 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "식품의약품안전처_건강기능식품영양성분정보_20251230.csv"))

encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
for enc in encodings:
    try:
        # 100행을 읽어 테스트
        df = pd.read_csv(csv_path, encoding=enc, nrows=100)
        out_path = os.path.join(os.path.dirname(__file__), "encoding_test.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"Encoding Success: {enc}\n")
            f.write(f"Shape: {df.shape}\n")
            f.write("Columns:\n")
            f.write(", ".join(df.columns.tolist()) + "\n\n")
            f.write("First 3 rows:\n")
            f.write(df.head(3).to_string())
        print(f"Written test output to {out_path} using encoding {enc}")
        break
    except Exception as e:
        print(f"Failed with {enc}: {e}")

