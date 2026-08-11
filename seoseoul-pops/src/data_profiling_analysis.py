import os
import sys
import pandas as pd
from data_profiling import ProfileReport

# 윈도우 환경에서 콘솔 출력 깨짐 방지를 위해 UTF-8 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 작업 디렉토리 설정 (상대 경로 기준)
src_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(src_dir)
data_dir = os.path.join(project_dir, "data")
report_dir = os.path.join(project_dir, "report")

os.makedirs(report_dir, exist_ok=True)

print("데이터 로딩 중...")
parquet_path = os.path.join(data_dir, "LOCAL_PEOPLE_DONG_202606.parquet")
excel_path = os.path.join(data_dir, "행정동코드_매핑정보_20241218.xlsx")

df_parquet = pd.read_parquet(parquet_path)
df_excel = pd.read_excel(excel_path)

# 엑셀 데이터 헤더 처리 및 행자부코드 변환 (eda_analysis.py와 동일한 전처리 적용)
df_excel = df_excel.iloc[1:].reset_index(drop=True)
df_excel['행자부행정동코드'] = df_excel['행자부행정동코드'].astype(int)

# 데이터 병합
print("데이터 병합 중...")
df = pd.merge(df_parquet, df_excel, left_on='행정동코드', right_on='행자부행정동코드', how='left')

# 날짜 파싱 및 요일 컬럼 생성
df['기준일자'] = pd.to_datetime(df['기준일ID'].astype(str), format='%Y%m%d')
df['요일'] = df['기준일자'].dt.dayofweek # 0:월 ~ 6:일
day_map = {0: '월요일', 1: '화요일', 2: '수요일', 3: '목요일', 4: '금요일', 5: '토요일', 6: '일요일'}
df['요일명'] = df['요일'].map(day_map)
df['주말여부'] = df['요일'].apply(lambda x: '주말' if x >= 5 else '평일')

# 데이터 크기가 매우 크므로 (8,547,840행), 대표성 있는 10만 행을 샘플링하여 프로파일링을 진행합니다.
print("데이터 샘플링 중 (10만 행)...")
df_sample = df.sample(n=100000, random_state=42)

print("데이터 프로파일링 보고서 생성 중...")
# data-profiling 패키지를 사용하여 프로파일링 리포트 객체 생성
profile = ProfileReport(df_sample, title="서울시 행정동별 생활인구 데이터 프로파일링 보고서", explorative=True)

# HTML 파일로 저장
output_html_path = os.path.join(report_dir, "EDA_Profiling_Report.html")
print(f"보고서 저장 중: {output_html_path}")
profile.to_file(output_html_path)
print("프로파일링 완료!")
