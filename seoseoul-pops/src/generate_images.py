import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os

# 파일 경로 정의 (상대 경로 사용)
PARQUET_PATH = "seoseoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet"
EXCEL_PATH = "seoseoul-pops/data/행정동코드_매핑정보_20241218.xlsx"
IMAGE_DIR = "seoseoul-pops/images"

# 이미지 저장 폴더 확인 및 생성
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

print("1. 데이터 로드 중...")
df_parquet = pd.read_parquet(PARQUET_PATH)
df_excel = pd.read_excel(EXCEL_PATH)
df_excel = df_excel.iloc[1:].reset_index(drop=True)
df_excel['행자부행정동코드'] = pd.to_numeric(df_excel['행자부행정동코드']).astype(int)

df = pd.merge(
    df_parquet,
    df_excel,
    left_on="행정동코드",
    right_on="행자부행정동코드",
    how="left"
)

# 날짜 매핑 딕셔너리
date_map = {}
for day in range(1, 31):
    date_id = 20260600 + day
    dt = pd.to_datetime(str(date_id), format='%Y%m%d')
    weekday_kor = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}[dt.weekday()]
    date_map[date_id] = (weekday_kor, day)
    
df['요일'] = df['기준일ID'].map(lambda x: date_map[x][0])
df['일자'] = df['기준일ID'].map(lambda x: date_map[x][1])

print("2. 이미지 생성 및 저장 중...")

# 1. 성별 생활인구 비율
print("- gender_ratio.png")
fig, ax = plt.subplots(figsize=(6, 5))
gender_data = df.groupby('성별', observed=False)['생활인구수'].sum()
gender_data.plot.pie(autopct='%1.1f%%', startangle=90, colors=['#4C72B0', '#DD8452'], ax=ax)
ax.set_ylabel('')
ax.set_title('성별 생활인구 비율')
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/gender_ratio.png", dpi=150)
plt.close()

# 2. 연령대별 생활인구 분포
print("- age_distribution.png")
fig, ax = plt.subplots(figsize=(10, 5))
age_data = df.groupby('연령대', observed=False)['생활인구수'].sum()
age_data.plot.bar(color='#55A868', ax=ax)
ax.set_title('연령대별 생활인구 분포')
ax.set_ylabel('총 생활인구수')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/age_distribution.png", dpi=150)
plt.close()

# 3. 시간대별 평균 생활인구 추이
print("- hourly_trend.png")
fig, ax = plt.subplots(figsize=(10, 5))
hourly_data = df.groupby('시간대구분')['생활인구수'].mean()
hourly_data.plot(marker='o', color='#C44E52', ax=ax)
ax.set_title('시간대별 평균 생활인구 추이')
ax.set_xlabel('시간대 (시)')
ax.set_ylabel('평균 생활인구수')
ax.set_xticks(range(24))
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/hourly_trend.png", dpi=150)
plt.close()

# 4. 요일별 평균 생활인구 비교
print("- weekday_comparison.png")
fig, ax = plt.subplots(figsize=(8, 5))
weekday_order = ['월', '화', '수', '목', '금', '토', '일']
weekday_data = df.groupby('요일')['생활인구수'].mean()
weekday_data = weekday_data.reindex(weekday_order)
weekday_data.plot.bar(color='#8172B3', ax=ax)
ax.set_title('요일별 평균 생활인구 비교')
ax.set_ylabel('평균 생활인구수')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/weekday_comparison.png", dpi=150)
plt.close()

# 5. 자치구별 총 생활인구 순위
print("- gu_ranking.png")
fig, ax = plt.subplots(figsize=(10, 8))
gu_data = df.groupby('시군구명')['생활인구수'].sum().sort_values(ascending=True)
gu_data.plot.barh(color='#937860', ax=ax)
ax.set_title('자치구별 총 생활인구 순위')
ax.set_xlabel('총 생활인구수')
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/gu_ranking.png", dpi=150)
plt.close()

# 6. 성별 및 연령대별 생활인구 분포
print("- gender_age_distribution.png")
fig, ax = plt.subplots(figsize=(12, 6))
gender_age_data = df.groupby(['연령대', '성별'], observed=False)['생활인구수'].sum().unstack()
gender_age_data.plot.bar(ax=ax, color=['#4C72B0', '#DD8452'], width=0.8)
ax.set_title('성별 및 연령대별 생활인구 분포')
ax.set_ylabel('총 생활인구수')
plt.xticks(rotation=45)
plt.legend(title='성별')
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/gender_age_distribution.png", dpi=150)
plt.close()

# 7. 시간대별 성별 평균 생활인구 추이
print("- hourly_gender_trend.png")
fig, ax = plt.subplots(figsize=(10, 5))
hourly_gender_data = df.groupby(['시간대구분', '성별'], observed=False)['생활인구수'].mean().unstack()
hourly_gender_data.plot(marker='o', ax=ax, color=['#4C72B0', '#DD8452'])
ax.set_title('시간대별 성별 평균 생활인구 추이')
ax.set_xlabel('시간대 (시)')
ax.set_ylabel('평균 생활인구수')
ax.set_xticks(range(24))
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/hourly_gender_trend.png", dpi=150)
plt.close()

# 8. 자치구별 시간대별 생활인구 분포 히트맵
print("- gu_hourly_heatmap.png")
fig, ax = plt.subplots(figsize=(12, 10))
heatmap_data = df.groupby(['시군구명', '시간대구분'])['생활인구수'].mean().unstack()
im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
ax.set_title('자치구별 시간대별 평균 생활인구 분포 (히트맵)')
ax.set_xlabel('시간대 (시)')
ax.set_ylabel('자치구')
ax.set_xticks(range(24))
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index)
fig.colorbar(im, ax=ax, label='평균 생활인구수')
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/gu_hourly_heatmap.png", dpi=150)
plt.close()

# 9. 생활인구 상위 10개 행정동 분석
print("- top_dong_analysis.png")
fig, ax = plt.subplots(figsize=(10, 5))
dong_data = df.groupby('행정동명')['생활인구수'].sum().sort_values(ascending=True).tail(10)
dong_data.plot.barh(color='#BCBD22', ax=ax)
ax.set_title('생활인구 상위 10개 행정동')
ax.set_xlabel('총 생활인구수')
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/top_dong_analysis.png", dpi=150)
plt.close()

# 10. 6월 일자별 전체 생활인구 변화 추이
print("- daily_trend.png")
fig, ax = plt.subplots(figsize=(10, 5))
daily_data = df.groupby('일자')['생활인구수'].mean()
daily_data.plot(marker='o', color='#17BECF', ax=ax)
ax.set_title('6월 일자별 평균 생활인구 변화 추이')
ax.set_xlabel('일자 (6월)')
ax.set_ylabel('평균 생활인구수')
ax.set_xticks(range(1, 31))
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(f"{IMAGE_DIR}/daily_trend.png", dpi=150)
plt.close()

print("모든 이미지 저장 완료!")
