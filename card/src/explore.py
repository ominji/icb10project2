import pandas as pd
import os

file_path = os.path.join("card", "data", "지역별 소비유형별 개인 신용카드_11134440.csv")
df = pd.read_csv(file_path, encoding='utf-8')
df['소비유형코드'] = df['소비유형코드'].str.strip()
unique_sectors = df['소비유형코드'].unique()

out_path = os.path.join("card", "src", "unique_sectors.txt")
with open(out_path, 'w', encoding='utf-8') as f:
    for s in unique_sectors:
        f.write(s + "\n")
        
print("소비유형코드 고유값 리스트를 저장했습니다.")
