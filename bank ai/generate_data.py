import pandas as pd
import numpy as np

# 1. 기본 설정 (5,000명)
n = 5000
np.random.seed(42)

# 2. 데이터 생성
data = {
    'Customer_ID': [f'C{i:05d}' for i in range(1, n + 1)],
    'Name': [f'고객{i}' for i in range(1, n + 1)],
    'Age': np.random.randint(30, 50, n),
    'Job_Type': np.random.choice(['IT/개발', '제조업', '전문직', '일반사무'], n),
    'Avg_Balance': np.random.normal(60000000, 25000000, n).astype(int), # 수신평잔
    'Salary_Day_Transfer': np.random.uniform(0.1, 0.9, n), # 월급날 증권사 이체 비중
    
    # 5대 테마 섹터 관심도 (0~100)
    '반도체': np.random.randint(0, 100, n),
    '항공/방산': np.random.randint(0, 100, n),
    '2차전지': np.random.randint(0, 100, n),
    '리츠/배당': np.random.randint(0, 100, n),
    '금융/은행': np.random.randint(0, 100, n),
}

df = pd.DataFrame(data)

# 3. 분석용 파생 변수 추가
# 이탈 위험도 계산 로직: 이체 비중이 높고 공격적 섹터(반도체, 2차전지) 점수가 높을수록 위험
df['Risk_Score'] = (df['Salary_Day_Transfer'] * 0.6 + (df['반도체'] + df['2차전지'])/200 * 0.4) * 100
df['Main_Theme'] = df[['반도체', '항공/방산', '2차전지', '리츠/배당', '금융/은행']].idxmax(axis=1)

# 4. 파일 저장
df.to_csv('customer_data_v2.csv', index=False)
print("성공: 다양한 섹터가 추가된 'customer_data_v2.csv'가 생성되었습니다.")
