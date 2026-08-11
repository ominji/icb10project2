import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

# 윈도우 환경에서 콘솔 출력 깨짐 방지를 위해 UTF-8 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 작업 디렉토리 설정 (상대 경로 기준)
src_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(src_dir)
data_dir = os.path.join(project_dir, "data")
images_dir = os.path.join(project_dir, "images")
report_dir = os.path.join(project_dir, "report")

# 이미지 폴더가 없으면 생성
os.makedirs(images_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

# 1. 데이터 로드 및 전처리
print("1. 데이터 로드 중...")
parquet_path = os.path.join(data_dir, "LOCAL_PEOPLE_DONG_202606.parquet")
excel_path = os.path.join(data_dir, "행정동코드_매핑정보_20241218.xlsx")

df_parquet = pd.read_parquet(parquet_path)
df_excel = pd.read_excel(excel_path)

# 엑셀 데이터 헤더 처리 및 행자부코드 변환
df_excel = df_excel.iloc[1:].reset_index(drop=True)
df_excel['행자부행정동코드'] = df_excel['행자부행정동코드'].astype(int)

# 데이터 병합
print("2. 데이터 병합 중...")
df = pd.merge(df_parquet, df_excel, left_on='행정동코드', right_on='행자부행정동코드', how='left')

# 날짜 파싱 및 요일 컬럼 생성
df['기준일자'] = pd.to_datetime(df['기준일ID'].astype(str), format='%Y%m%d')
df['요일'] = df['기준일자'].dt.dayofweek # 0:월 ~ 6:일
day_map = {0: '월요일', 1: '화요일', 2: '수요일', 3: '목요일', 4: '금요일', 5: '토요일', 6: '일요일'}
df['요일명'] = df['요일'].map(day_map)
df['주말여부'] = df['요일'].apply(lambda x: '주말' if x >= 5 else '평일')

# 기술통계 데이터 확보
print("3. 기술통계 및 테이블 데이터 생성 중...")

# 수치형 기술통계
numeric_desc = df[['생활인구수', '시간대구분']].describe()
# 범주형 기술통계
categorical_cols = ['성별', '연령대', '시군구명', '행정동명', '요일명', '주말여부']
categorical_desc_list = []
for col in categorical_cols:
    categorical_desc_list.append({
        '변수명': col,
        '고유값수': df[col].nunique(),
        '최빈값': df[col].mode()[0],
        '최빈값빈도': df[col].value_counts().iloc[0],
        '최빈값비율(%)': (df[col].value_counts().iloc[0] / len(df)) * 100
    })
categorical_desc = pd.DataFrame(categorical_desc_list)

# 마크다운 표 변환 함수
def to_markdown_table(df_input):
    return df_input.to_markdown(index=True)

# 시각화 설정
sns.set_theme(style="whitegrid", font="Malgun Gothic")
plt.rcParams['axes.unicode_minus'] = False

# 시각화 1. 생활인구수 분포 (Histogram & Boxplot)
print("시각화 1 생성 중...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
# 대용량 데이터이므로 10만 행 샘플링하여 시각화 속도 개선
sample_pop = df['생활인구수'].sample(n=100000, random_state=42)
sns.histplot(sample_pop, bins=50, kde=True, ax=axes[0], color='skyblue')
axes[0].set_title('생활인구수 분포 히스토그램 (10만 행 샘플)')
axes[0].set_xlabel('생활인구수')
axes[0].set_ylabel('빈도')

sns.boxplot(y=sample_pop, ax=axes[1], color='lightpink')
axes[1].set_title('생활인구수 박스플롯 (10만 행 샘플)')
axes[1].set_ylabel('생활인구수')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "01_pop_distribution.png"), dpi=150)
plt.close()

# 시각화 2. 성별 생활인구 합계 및 평균 (Bar Chart)
print("시각화 2 생성 중...")
gender_agg = df.groupby('성별', observed=False)['생활인구수'].agg(['sum', 'mean']).reset_index()
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.barplot(data=gender_agg, x='성별', y='sum', ax=axes[0], hue='성별', palette='pastel', legend=False)
axes[0].set_title('성별 생활인구 합계')
axes[0].set_ylabel('생활인구 합계 (명)')
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))

sns.barplot(data=gender_agg, x='성별', y='mean', ax=axes[1], hue='성별', palette='pastel', legend=False)
axes[1].set_title('성별 생활인구 평균')
axes[1].set_ylabel('생활인구 평균 (명)')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "02_gender_pop.png"), dpi=150)
plt.close()

# 시각화 3. 연령대별 생활인구 분포 (Bar Chart)
print("시각화 3 생성 중...")
age_agg = df.groupby('연령대', observed=False)['생활인구수'].agg(['sum', 'mean']).reset_index()
fig, axes = plt.subplots(2, 1, figsize=(14, 10))
sns.barplot(data=age_agg, x='연령대', y='sum', ax=axes[0], hue='연령대', palette='viridis', legend=False)
axes[0].set_title('연령대별 생활인구 합계')
axes[0].set_ylabel('생활인구 합계 (명)')
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
axes[0].tick_params(axis='x', rotation=30)

sns.barplot(data=age_agg, x='연령대', y='mean', ax=axes[1], hue='연령대', palette='viridis', legend=False)
axes[1].set_title('연령대별 생활인구 평균')
axes[1].set_ylabel('생활인구 평균 (명)')
axes[1].tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "03_age_pop.png"), dpi=150)
plt.close()

# 시각화 4. 시간대별 평균 생활인구수 (Line Chart)
print("시각화 4 생성 중...")
hourly_agg = df.groupby('시간대구분')['생활인구수'].mean().reset_index()
plt.figure(figsize=(12, 5))
sns.lineplot(data=hourly_agg, x='시간대구분', y='생활인구수', marker='o', color='darkorange', linewidth=2.5)
plt.title('시간대별 평균 생활인구수 변화 트렌드')
plt.xlabel('시간대 (시)')
plt.ylabel('평균 생활인구수 (명)')
plt.xticks(range(0, 24))
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "04_hourly_pop.png"), dpi=150)
plt.close()

# 시각화 5. 요일별 평균 생활인구수 (Bar Chart)
print("시각화 5 생성 중...")
weekday_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
weekly_agg = df.groupby('요일명')['생활인구수'].mean().reindex(weekday_order).reset_index()
plt.figure(figsize=(10, 5))
sns.barplot(data=weekly_agg, x='요일명', y='생활인구수', hue='요일명', palette='coolwarm', legend=False)
plt.title('요일별 평균 생활인구수')
plt.xlabel('요일')
plt.ylabel('평균 생활인구수 (명)')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "05_weekly_pop.png"), dpi=150)
plt.close()

# 시각화 6. 시군구별 평균 생활인구수 상위/하위 10개 (Bar Chart)
print("시각화 6 생성 중...")
sigungu_agg = df.groupby('시군구명')['생활인구수'].mean().sort_values(ascending=False).reset_index()
top_sigungu = sigungu_agg.head(10)
bottom_sigungu = sigungu_agg.tail(10)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
sns.barplot(data=top_sigungu, x='생활인구수', y='시군구명', ax=axes[0], hue='시군구명', palette='autumn', legend=False)
axes[0].set_title('시군구별 평균 생활인구수 상위 10개 지역')
axes[0].set_xlabel('평균 생활인구수 (명)')

sns.barplot(data=bottom_sigungu, x='생활인구수', y='시군구명', ax=axes[1], hue='시군구명', palette='winter', legend=False)
axes[1].set_title('시군구별 평균 생활인구수 하위 10개 지역')
axes[1].set_xlabel('평균 생활인구수 (명)')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "06_sigungu_pop.png"), dpi=150)
plt.close()

# 시각화 7. 성별에 따른 연령대별 평균 생활인구수 (Grouped Bar Chart)
print("시각화 7 생성 중...")
gender_age_agg = df.groupby(['연령대', '성별'], observed=False)['생활인구수'].mean().reset_index()
plt.figure(figsize=(14, 6))
sns.barplot(data=gender_age_agg, x='연령대', y='생활인구수', hue='성별', palette='muted')
plt.title('성별 및 연령대별 평균 생활인구수')
plt.xlabel('연령대')
plt.ylabel('평균 생활인구수 (명)')
plt.xticks(rotation=30)
plt.legend(title='성별')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "07_gender_age_pop.png"), dpi=150)
plt.close()

# 시각화 8. 시간대별 성별 평균 생활인구수 (Line Chart)
print("시각화 8 생성 중...")
hourly_gender_agg = df.groupby(['시간대구분', '성별'], observed=False)['생활인구수'].mean().reset_index()
plt.figure(figsize=(14, 6))
sns.lineplot(data=hourly_gender_agg, x='시간대구분', y='생활인구수', hue='성별', marker='s', linewidth=2, palette='Set1')
plt.title('시간대별 및 성별 평균 생활인구수 변화 추이')
plt.xlabel('시간대 (시)')
plt.ylabel('평균 생활인구수 (명)')
plt.xticks(range(0, 24))
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(title='성별')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "08_hourly_gender_pop.png"), dpi=150)
plt.close()

# 시각화 9. 요일별 시간대별 평균 생활인구수 (Heatmap)
print("시각화 9 생성 중...")
weekly_hourly_pivot = df.pivot_table(
    index='시간대구분', 
    columns='요일명', 
    values='생활인구수', 
    aggfunc='mean'
).reindex(columns=weekday_order)

plt.figure(figsize=(12, 8))
sns.heatmap(weekly_hourly_pivot, annot=False, cmap='YlOrRd', fmt='.0f', cbar_kws={'label': '평균 생활인구수 (명)'})
plt.title('요일 및 시간대별 평균 생활인구수 열지도(Heatmap)')
plt.xlabel('요일')
plt.ylabel('시간대 (시)')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "09_weekly_hourly_pop.png"), dpi=150)
plt.close()

# 시각화 10. 시군구별 연령대별 평균 생활인구수 (Heatmap)
print("시각화 10 생성 중...")
sigungu_age_pivot = df.pivot_table(
    index='시군구명', 
    columns='연령대', 
    values='생활인구수', 
    aggfunc='mean'
)
# 평균 생활인구 합계가 큰 자치구 순서로 정렬
sigungu_order = sigungu_agg['시군구명'].tolist()
sigungu_age_pivot = sigungu_age_pivot.reindex(sigungu_order)

plt.figure(figsize=(14, 10))
sns.heatmap(sigungu_age_pivot, annot=False, cmap='Purples', cbar_kws={'label': '평균 생활인구수 (명)'})
plt.title('시군구 및 연령대별 평균 생활인구수 열지도(Heatmap)')
plt.xlabel('연령대')
plt.ylabel('시군구명')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "10_sigungu_age_pop.png"), dpi=150)
plt.close()

# 시각화 11. 행정동별 평균 생활인구수 상위 30개 (Bar Chart)
print("시각화 11 생성 중...")
dong_agg = df.groupby(['행정동명', '시군구명'])['생활인구수'].mean().sort_values(ascending=False).reset_index()
top_dong_30 = dong_agg.head(30).copy()
top_dong_30['동명_구명'] = top_dong_30['행정동명'] + ' (' + top_dong_30['시군구명'] + ')'

plt.figure(figsize=(14, 8))
sns.barplot(data=top_dong_30, x='생활인구수', y='동명_구명', hue='동명_구명', palette='magma', legend=False)
plt.title('서울시 행정동별 평균 생활인구수 상위 30개 지역')
plt.xlabel('평균 생활인구수 (명)')
plt.ylabel('행정동 (자치구)')
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "11_dong_pop.png"), dpi=150)
plt.close()

# 마크다운용 텍스트 및 테이블 파일 생성 (보고서 작성에 활용)
print("4. 마크다운 리포트용 동반 테이블 데이터 파일 작성 중...")
tables_output_path = os.path.join(report_dir, "extracted_tables.txt")
with open(tables_output_path, "w", encoding="utf-8") as f:
    f.write("=== 수치형 기술통계 ===\n")
    f.write(to_markdown_table(numeric_desc) + "\n\n")
    
    f.write("=== 범주형 기술통계 ===\n")
    f.write(to_markdown_table(categorical_desc) + "\n\n")
    
    f.write("=== 테이블 2: 성별 생활인구 집계 ===\n")
    f.write(to_markdown_table(gender_agg) + "\n\n")
    
    f.write("=== 테이블 3: 연령대별 생활인구 집계 ===\n")
    f.write(to_markdown_table(age_agg) + "\n\n")
    
    f.write("=== 테이블 4: 시간대별 평균 생활인구 ===\n")
    f.write(to_markdown_table(hourly_agg) + "\n\n")
    
    f.write("=== 테이블 5: 요일별 평균 생활인구 ===\n")
    f.write(to_markdown_table(weekly_agg) + "\n\n")
    
    f.write("=== 테이블 6: 시군구별 평균 생활인구 (상위 10) ===\n")
    f.write(to_markdown_table(top_sigungu) + "\n\n")
    f.write("=== 테이블 6: 시군구별 평균 생활인구 (하위 10) ===\n")
    f.write(to_markdown_table(bottom_sigungu) + "\n\n")
    
    f.write("=== 테이블 7: 성별 연령대별 평균 생활인구 ===\n")
    f.write(to_markdown_table(gender_age_agg.pivot(index='연령대', columns='성별', values='생활인구수')) + "\n\n")
    
    f.write("=== 테이블 8: 시간대별 성별 평균 생활인구 ===\n")
    f.write(to_markdown_table(hourly_gender_agg.pivot(index='시간대구분', columns='성별', values='생활인구수')) + "\n\n")
    
    f.write("=== 테이블 9: 요일별 시간대별 평균 생활인구 ===\n")
    f.write(to_markdown_table(weekly_hourly_pivot) + "\n\n")
    
    f.write("=== 테이블 10: 시군구별 연령대별 평균 생활인구 ===\n")
    f.write(to_markdown_table(sigungu_age_pivot.head(15)) + " (상위 15개구 표기)\n\n")
    
    f.write("=== 테이블 11: 행정동별 평균 생활인구 (상위 30) ===\n")
    f.write(to_markdown_table(top_dong_30[['행정동명', '시군구명', '생활인구수']]) + "\n\n")

print("분석 스크립트 실행 완료! 시각화 차트와 마크다운용 테이블 추출이 완료되었습니다.")
