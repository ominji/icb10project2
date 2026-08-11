import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os

# 경로 설정
summary_path = os.path.join("card", "data", "경기도 카드소비데이터_2025", "aggregated_summary.csv")
image_dir = os.path.join("card", "images")
report_dir = os.path.join("card", "report")

os.makedirs(image_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

# 데이터 로드
df = pd.read_csv(summary_path)

# 문자열 공백 제거 및 타입 확인
df['card_tpbuz_nm_1'] = df['card_tpbuz_nm_1'].str.strip()
df['region'] = df['region'].str.strip()
df['year_month'] = df['year_month'].astype(str)

# 월별 정렬 순서 정의
months_sorted = sorted(df['year_month'].unique())

# 요약 보고용 딕셔너리
summary_data = {}

# [시각화 1] 월별 신용카드 총 매출액 추이
monthly_total = df.groupby('year_month')['amt'].sum().loc[months_sorted]
summary_data['vis_1'] = monthly_total

plt.figure(figsize=(10, 5))
plt.plot(monthly_total.index, monthly_total.values / 1e8, marker='o', color='#2ca02c', linewidth=2)
plt.title("경기도 신용카드 총 사용액 추이 (2025년 3월 ~ 12월)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("사용액 (억 원)", fontsize=11, labelpad=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_01_monthly_spending_trend.png"), dpi=150)
plt.close()

# [시각화 2] 주요 업종 대분류별 누적 매출 비중
sector_total = df.groupby('card_tpbuz_nm_1')['amt'].sum().sort_values(ascending=False)
top_sectors = sector_total.head(10)
other_sectors = sector_total.iloc[10:].sum()
pie_data = pd.concat([top_sectors, pd.Series({'기타': other_sectors})])
summary_data['vis_2'] = sector_total

plt.figure(figsize=(8, 8))
colors = plt.cm.tab20(np.linspace(0, 1, len(pie_data)))
plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140, colors=colors,
        textprops={'fontsize': 10}, wedgeprops={'edgecolor': 'w', 'linewidth': 1})
plt.title("업종 대분류별 누적 매출 비중", fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_02_sector_share.png"), dpi=150)
plt.close()

# [시각화 3] 전월 대비 총액 증감율 추이 (MoM %)
mom_pct = monthly_total.pct_change() * 100
summary_data['vis_3'] = mom_pct

plt.figure(figsize=(10, 5))
colors_mom = ['#d62728' if x < 0 else '#1f77b4' for x in mom_pct.fillna(0)]
plt.bar(mom_pct.index[1:], mom_pct.dropna(), color=colors_mom[1:], alpha=0.8, edgecolor='black', linewidth=0.5)
plt.axhline(0, color='black', linewidth=1)
plt.title("전월 대비 신용카드 총 사용액 증감율 (MoM %)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("증감율 (%)", fontsize=11, labelpad=10)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_03_mom_change_rate.png"), dpi=150)
plt.close()

# [시각화 4] 연령대별 총 카드 소비 비중
# age 컬럼 정보 요약
age_total = df.groupby('age')['amt'].sum().sort_values(ascending=False)
summary_data['vis_4'] = age_total

plt.figure(figsize=(10, 5))
plt.bar(age_total.index.astype(str), age_total.values / 1e8, color='#ff7f0e', alpha=0.8, edgecolor='black', linewidth=0.5)
plt.title("연령대별 총 카드 사용 규모 (억 원)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연령대 코드", fontsize=11, labelpad=10)
plt.ylabel("사용액 (억 원)", fontsize=11, labelpad=10)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_04_age_spending.png"), dpi=150)
plt.close()

# [시각화 5] 성별 매출 비중 추이 (M: 남성, F: 여성 또는 1, 2)
sex_monthly = df.groupby(['year_month', 'sex'])['amt'].sum().unstack().loc[months_sorted]
sex_monthly_pct = sex_monthly.div(sex_monthly.sum(axis=1), axis=0) * 100
summary_data['vis_5'] = sex_monthly_pct

plt.figure(figsize=(10, 5))
ax = sex_monthly_pct.plot(kind='bar', stacked=True, color=['#e377c2', '#17becf'], alpha=0.8, edgecolor='black', ax=plt.gca())
plt.title("성별 매출 비중 추이 (%)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("비중 (%)", fontsize=11, labelpad=10)
plt.legend(title='성별', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_05_sex_monthly_share.png"), dpi=150)
plt.close()

# [시각화 6] 경기도 내 상위 10대 지자체(지역)별 매출 비교
region_total = df.groupby('region')['amt'].sum().sort_values(ascending=False).head(10)
summary_data['vis_6'] = region_total

plt.figure(figsize=(10, 6))
plt.barh(region_total.index[::-1], region_total.values[::-1] / 1e8, color='#9467bd', alpha=0.8, edgecolor='black', linewidth=0.5)
plt.title("경기도 내 지역(시군구)별 총 사용 규모 상위 10대 지자체 (억 원)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("사용액 (억 원)", fontsize=11, labelpad=10)
plt.ylabel("지역", fontsize=11)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_06_top_regions.png"), dpi=150)
plt.close()

# [시각화 7] 분기별 대분류 업종 소비 비중 변화 (히트맵, 상위 10개 업종)
# Q2 (4,5,6월), Q3 (7,8,9월), Q4 (10,11,12월)
df['quarter'] = 'Q_others'
df.loc[df['year_month'].isin(['202504', '202505', '202506']), 'quarter'] = '2025 Q2'
df.loc[df['year_month'].isin(['202507', '202508', '202509']), 'quarter'] = '2025 Q3'
df.loc[df['year_month'].isin(['202510', '202511', '202512']), 'quarter'] = '2025 Q4'

df_quarters = df[df['quarter'] != 'Q_others'].groupby(['card_tpbuz_nm_1', 'quarter'])['amt'].sum().unstack()
top_10_sectors = sector_total.head(10).index
df_quarters_top10 = df_quarters.loc[top_10_sectors]
df_quarters_top10_pct = df_quarters_top10.div(df_quarters_top10.sum(axis=1), axis=0) * 100
summary_data['vis_7'] = df_quarters_top10_pct

plt.figure(figsize=(10, 8))
im = plt.imshow(df_quarters_top10_pct.values, cmap='Oranges', aspect='auto')
plt.colorbar(im, label='분기별 매출 분배 비중 (%)')
plt.xticks(ticks=range(len(df_quarters_top10_pct.columns)), labels=df_quarters_top10_pct.columns)
plt.yticks(ticks=range(len(df_quarters_top10_pct)), labels=df_quarters_top10_pct.index)
plt.title("주요 10대 업종의 분기별 매출 분배 비중 (%)", fontsize=14, fontweight='bold', pad=15)
for i in range(len(df_quarters_top10_pct)):
    for j in range(len(df_quarters_top10_pct.columns)):
        plt.text(j, i, f"{df_quarters_top10_pct.values[i, j]:.1f}%", ha='center', va='center', color='black', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_07_quarterly_share_heatmap.png"), dpi=150)
plt.close()

# [시각화 8] 연령대별 선호 업종 매출 비중 (상위 5개 연령대 x 상위 5개 업종)
top_5_ages = age_total.head(5).index
top_5_sectors = sector_total.head(5).index
df_age_sector = df[df['age'].isin(top_5_ages) & df['card_tpbuz_nm_1'].isin(top_5_sectors)].groupby(['card_tpbuz_nm_1', 'age'])['amt'].sum().unstack()
df_age_sector_pct = df_age_sector.div(df_age_sector.sum(axis=0), axis=1) * 100
summary_data['vis_8'] = df_age_sector_pct

plt.figure(figsize=(10, 6))
df_age_sector_pct.plot(kind='bar', ax=plt.gca(), edgecolor='black', alpha=0.8)
plt.title("연령대별 주요 업종 소비 비중 (%)", fontsize=14, fontweight='bold', pad=15)
# x축 라벨 회전 완화
plt.xticks(rotation=15, ha='right')
plt.xlabel("업종", fontsize=11, labelpad=10)
plt.ylabel("비중 (%)", fontsize=11, labelpad=10)
plt.legend(title='연령대 코드', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_08_age_sector_share.png"), dpi=150)
plt.close()

# [시각화 9] 전월 대비 변동액이 가장 큰 상위 7대 지자체 (2025년 8월 기준 전월대비 증감액)
df_aug = df[df['year_month'] == '202508'].groupby('region')['amt'].sum()
df_jul = df[df['year_month'] == '202507'].groupby('region')['amt'].sum()
aug_diff = (df_aug - df_jul).dropna().sort_values(key=abs, ascending=False).head(7)
summary_data['vis_9'] = aug_diff

plt.figure(figsize=(10, 5))
colors_diff = ['#2ca02c' if x > 0 else '#d62728' for x in aug_diff]
plt.bar(aug_diff.index, aug_diff.values / 1e8, color=colors_diff, alpha=0.8, edgecolor='black', linewidth=0.5)
plt.axhline(0, color='black', linewidth=1)
plt.title("2025년 8월 전월(7월) 대비 소비 증감액 상위 7개 지역 (억 원)", fontsize=14, fontweight='bold', pad=15)
plt.ylabel("증감액 (억 원)", fontsize=11, labelpad=10)
plt.xticks(rotation=30, ha='right')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_09_august_region_diff.png"), dpi=150)
plt.close()

# [시각화 10] 5대 주요 업종의 월별 트렌드 추이 비교
top_5_sectors_names = sector_total.head(5).index
df_top5_trend = df[df['card_tpbuz_nm_1'].isin(top_5_sectors_names)].groupby(['year_month', 'card_tpbuz_nm_1'])['amt'].sum().unstack().loc[months_sorted]
summary_data['vis_10'] = df_top5_trend

plt.figure(figsize=(12, 6))
for sector in top_5_sectors_names:
    plt.plot(df_top5_trend.index, df_top5_trend[sector] / 1e8, label=sector, marker='o', linewidth=2)
plt.title("5대 주요 업종 월별 매출액 추이 (억 원)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("매출액 (억 원)", fontsize=11, labelpad=10)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "2025_10_top5_sectors_trend.png"), dpi=150)
plt.close()

# 요약 정보 텍스트 파일 저장
out_summary = os.path.join("card", "src", "analysis_summary_2025.txt")
with open(out_summary, 'w', encoding='utf-8') as f:
    for k, v in summary_data.items():
        f.write(f"[{k} 데이터]\n")
        f.write(v.to_string() + "\n\n")

print("2025년도 카드 소비 데이터에 대한 시각화 이미지 10개 생성 및 요약 데이터 저장이 완료되었습니다.")
print(f"요약 정보 저장 완료: {out_summary}")
