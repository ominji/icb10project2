import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os

# 디렉토리 설정
data_path = os.path.join("card", "data", "지역별 소비유형별 개인 신용카드_11134440.csv")
image_dir = os.path.join("card", "images")
report_dir = os.path.join("card", "report")

os.makedirs(image_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

# 1. 데이터 로드 및 전처리
df = pd.read_csv(data_path, encoding='utf-8')

# 소비유형코드 공백 제거
df['소비유형코드'] = df['소비유형코드'].str.strip()

# 월별 데이터 컬럼 (2022/08 ~ 2023/08)
month_cols = [col for col in df.columns if '/' in col]

# 숫자 변환 (쉼표 제거 후 float 변환)
for col in month_cols:
    df[col] = df[col].astype(str).str.replace(',', '').astype(float)

# '총액' 데이터만 필터링
df_total = df[df['금액구분코드'] == '총액'].copy()

# '합계' 제외한 업종별 데이터
df_sectors = df_total[df_total['소비유형코드'] != '합계'].copy()

# 데이터 기본 정보 텍스트 파일 저장용 사전
basic_info = {}
basic_info['shape'] = df.shape
basic_info['columns'] = list(df.columns)
basic_info['sectors_count'] = df_sectors['소비유형코드'].nunique()
basic_info['sectors'] = list(df_sectors['소비유형코드'].unique())

# 월별 합계 데이터
df_overall = df_total[df_total['소비유형코드'] == '합계'].iloc[0]
overall_months_val = df_overall[month_cols].values
overall_series = pd.Series(overall_months_val, index=month_cols)

# 월간 총액 전월대비 증감율 계산 (MoM)
mom_pct = overall_series.pct_change() * 100

# ----------------- 시각화 및 데이터 추출 -----------------

# [시각화 1] 전국 총 신용카드 사용액 추이
plt.figure(figsize=(10, 5))
plt.plot(overall_series.index, overall_series.values / 1000000, marker='o', color='#1f77b4', linewidth=2)
plt.title("전국 신용카드 총 사용액 추이 (2022/08 ~ 2023/08)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("사용액 (조 원)", fontsize=11, labelpad=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "01_total_spending_trend.png"), dpi=150)
plt.close()

# [시각화 2] 주요 소비유형별 누적 사용액 비중 (상위 10개 업종)
sector_total = df_sectors.set_index('소비유형코드')[month_cols].sum(axis=1).sort_values(ascending=False)
top_sectors = sector_total.head(10)
other_sectors_sum = sector_total.iloc[10:].sum()
pie_data = pd.concat([top_sectors, pd.Series({'기타': other_sectors_sum})])

plt.figure(figsize=(8, 8))
colors = plt.cm.tab20(np.linspace(0, 1, len(pie_data)))
plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140, colors=colors, 
        textprops={'fontsize': 10}, wedgeprops={'edgecolor': 'w', 'linewidth': 1})
plt.title("주요 소비유형별 신용카드 사용액 누적 비중", fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "02_sector_spending_share.png"), dpi=150)
plt.close()

# [시각화 3] 전월 대비 총액 증감율 추이 (MoM %)
plt.figure(figsize=(10, 5))
colors_mom = ['#d62728' if x < 0 else '#2ca02c' for x in mom_pct.fillna(0)]
plt.bar(mom_pct.index[1:], mom_pct.dropna(), color=colors_mom[1:], alpha=0.8, edgecolor='black', linewidth=0.5)
plt.axhline(0, color='black', linewidth=1, linestyle='-')
plt.title("전월 대비 신용카드 총 사용액 증감율 (MoM %)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("증감율 (%)", fontsize=11, labelpad=10)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "03_mom_percentage_change.png"), dpi=150)
plt.close()

# [시각화 4] 소비유형별 월간 변동계수(CV = 표준편차/평균) 비교 (변동성 높은 상위 15개 업종)
sector_mean = df_sectors.set_index('소비유형코드')[month_cols].mean(axis=1)
sector_std = df_sectors.set_index('소비유형코드')[month_cols].std(axis=1)
sector_cv = (sector_std / sector_mean).sort_values(ascending=False).head(15)

plt.figure(figsize=(10, 6))
plt.barh(sector_cv.index[::-1], sector_cv.values[::-1], color='#e377c2', alpha=0.8, edgecolor='black', linewidth=0.5)
plt.title("소비유형별 월간 변동계수 (상위 15개 업종)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("변동계수 (CV)", fontsize=11, labelpad=10)
plt.ylabel("소비유형", fontsize=11)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "04_sector_volatility_cv.png"), dpi=150)
plt.close()

# [시각화 5] 분기별 소비 유형별 매출액 히트맵 (주요 15개 업종)
# 2022 4분기 (10, 11, 12), 2023 1분기 (1, 2, 3), 2023 2분기 (4, 5, 6)
df_quarters = pd.DataFrame(index=df_sectors['소비유형코드'])
df_quarters['2022_Q4'] = df_sectors.set_index('소비유형코드')[['2022/10', '2022/11', '2022/12']].sum(axis=1)
df_quarters['2023_Q1'] = df_sectors.set_index('소비유형코드')[['2023/01', '2023/02', '2023/03']].sum(axis=1)
df_quarters['2023_Q2'] = df_sectors.set_index('소비유형코드')[['2023/04', '2023/05', '2023/06']].sum(axis=1)

top_15_quarters = df_quarters.loc[sector_total.head(15).index]
# 정규화하여 시각화 (업종별 크기 차이가 크므로 비율로 시각화하거나 로그스케일 고려)
top_15_quarters_norm = top_15_quarters.div(top_15_quarters.sum(axis=1), axis=0) * 100

plt.figure(figsize=(10, 8))
# Heatmap manually
im = plt.imshow(top_15_quarters_norm.values, cmap='YlOrRd', aspect='auto')
plt.colorbar(im, label='분기별 매출 비중 (%)')
plt.xticks(ticks=[0, 1, 2], labels=['2022 Q4', '2023 Q1', '2023 Q2'])
plt.yticks(ticks=range(len(top_15_quarters_norm)), labels=top_15_quarters_norm.index)
plt.title("주요 15개 업종의 분기별 매출 분포 비중 (%)", fontsize=14, fontweight='bold', pad=15)
# 각 셀에 텍스트 값 표시
for i in range(len(top_15_quarters_norm)):
    for j in range(3):
        plt.text(j, i, f"{top_15_quarters_norm.values[i, j]:.1f}%", ha='center', va='center', color='black', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "05_quarterly_distribution_heatmap.png"), dpi=150)
plt.close()

# [시각화 6] 명절 월 소비 특성 분석: 2023년 1월(설날) vs 2023년 2월 특정 업종 증감율 (%)
holiday_sectors = ['종합소매', '백화점', '대형마트/유통전문점', '슈퍼마켓', '편의점', '국산자동차신품', '항공사', '여행사/자동차임대']
# 필터링하여 실제 있는 업종 확인
available_sectors = [s for s in holiday_sectors if s in df_sectors['소비유형코드'].values]
df_holiday = df_sectors[df_sectors['소비유형코드'].isin(available_sectors)].set_index('소비유형코드')
holiday_diff_pct = ((df_holiday['2023/01'] - df_holiday['2023/02']) / df_holiday['2023/02']) * 100

plt.figure(figsize=(10, 5))
colors_holiday = ['#2ca02c' if x > 0 else '#d62728' for x in holiday_diff_pct]
plt.bar(holiday_diff_pct.index, holiday_diff_pct.values, color=colors_holiday, alpha=0.8, edgecolor='black', linewidth=0.5)
plt.axhline(0, color='black', linewidth=1)
plt.title("2023년 1월(설날 포함) vs 2월 주요 업종별 소비 증감율 (%)", fontsize=14, fontweight='bold', pad=15)
plt.ylabel("증감율 (%)", fontsize=11, labelpad=10)
plt.xticks(rotation=30, ha='right')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "06_holiday_effect_jan_vs_feb.png"), dpi=150)
plt.close()

# [시각화 7] 전자상거래 vs 오프라인 소비 추이 비교
# 오프라인 소비 = 합계 - 전자상거래/통신판매
df_ecommerce = df_sectors[df_sectors['소비유형코드'] == '전자상거래/통신판매'].set_index('소비유형코드')[month_cols].iloc[0]
df_offline = overall_series - df_ecommerce

plt.figure(figsize=(10, 5))
plt.plot(month_cols, df_offline.values / 1000000, label='오프라인 소비', marker='s', color='#2ca02c', linewidth=2)
plt.plot(month_cols, df_ecommerce.values / 1000000, label='전자상거래/통신판매', marker='o', color='#ff7f0e', linewidth=2)
plt.title("온라인(전자상거래) vs 오프라인 소비 규모 추이", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("사용액 (조 원)", fontsize=11, labelpad=10)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "07_online_vs_offline_trend.png"), dpi=150)
plt.close()

# [시각화 8] 2023년 5월(가정의 달) 전월(4월) 대비 증감액 상위 7개 업종
df_sectors_idx = df_sectors.set_index('소비유형코드')
may_diff = df_sectors_idx['2023/05'] - df_sectors_idx['2023/04']
top_may_inc = may_diff.sort_values(ascending=False).head(7)

plt.figure(figsize=(10, 5))
plt.bar(top_may_inc.index, top_may_inc.values / 1000, color='#9467bd', alpha=0.8, edgecolor='black', linewidth=0.5)
plt.title("2023년 5월(가정의 달) 전월 대비 소비 증가액 상위 7개 업종", fontsize=14, fontweight='bold', pad=15)
plt.ylabel("증가액 (십억 원)", fontsize=11, labelpad=10)
plt.xticks(rotation=30, ha='right')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "08_may_family_month_increase.png"), dpi=150)
plt.close()

# [시각화 9] 2023년 1분기 vs 2분기 업종별 증가액 상위 7개 업종
q_diff = df_quarters['2023_Q2'] - df_quarters['2023_Q1']
top_q_inc = q_diff.sort_values(ascending=False).head(7)

plt.figure(figsize=(10, 5))
plt.bar(top_q_inc.index, top_q_inc.values / 1000000, color='#17becf', alpha=0.8, edgecolor='black', linewidth=0.5)
plt.title("2023년 1분기 대비 2분기 소비 증가액 상위 7개 업종", fontsize=14, fontweight='bold', pad=15)
plt.ylabel("증가액 (조 원)", fontsize=11, labelpad=10)
plt.xticks(rotation=30, ha='right')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "09_q1_vs_q2_increase.png"), dpi=150)
plt.close()

# [시각화 10] 5대 주요 라이프스타일 업종의 월별 트렌드 추이 비교
# (의료/보건, 음식점, 여행사/자동차임대, 연료, 교육)
lifestyle_sectors = ['의료/보건', '음식점', '여행사/자동차임대', '연료', '교육']
df_lifestyle = df_sectors_idx.loc[lifestyle_sectors, month_cols]

plt.figure(figsize=(12, 6))
for sector in lifestyle_sectors:
    plt.plot(month_cols, df_lifestyle.loc[sector] / 1000, label=sector, marker='o', linewidth=2)
plt.title("5대 라이프스타일 업종 신용카드 사용 추이", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=10)
plt.ylabel("사용액 (십억 원)", fontsize=11, labelpad=10)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(image_dir, "10_lifestyle_sectors_trend.png"), dpi=150)
plt.close()


# 데이터 요약 정보 텍스트 파일 저장 (보고서 작성에 사용)
summary_out_path = os.path.join("card", "src", "analysis_summary.txt")
with open(summary_out_path, 'w', encoding='utf-8') as f:
    f.write("[시각화 1 데이터: 전국 총 신용카드 사용액 추이]\n")
    f.write(overall_series.to_string() + "\n\n")
    
    f.write("[시각화 2 데이터: 누적 사용액 비중 상위 10개 및 기타]\n")
    f.write(pie_data.to_string() + "\n\n")
    
    f.write("[시각화 3 데이터: 전월 대비 총액 증감율 (MoM %)]\n")
    f.write(mom_pct.to_string() + "\n\n")
    
    f.write("[시각화 4 데이터: 소비유형별 변동계수 상위 15개]\n")
    f.write(sector_cv.to_string() + "\n\n")
    
    f.write("[시각화 5 데이터: 분기별 매출 비중 주요 15개 업종]\n")
    f.write(top_15_quarters_norm.to_string() + "\n\n")
    
    f.write("[시각화 6 데이터: 2023년 1월 vs 2월 주요 업종별 증감율 (%)]\n")
    f.write(holiday_diff_pct.to_string() + "\n\n")
    
    f.write("[시각화 7 데이터: 온라인 vs 오프라인 소비 추이 (단위: 백만원)]\n")
    df_onoff = pd.DataFrame({'온라인(전자상거래)': df_ecommerce, '오프라인': df_offline})
    f.write(df_onoff.to_string() + "\n\n")
    
    f.write("[시각화 8 데이터: 2023년 5월 전월 대비 증가액 상위 7개 (단위: 백만원)]\n")
    f.write(top_may_inc.to_string() + "\n\n")
    
    f.write("[시각화 9 데이터: 2023년 1분기 대비 2분기 증가액 상위 7개 (단위: 백만원)]\n")
    f.write(top_q_inc.to_string() + "\n\n")
    
    f.write("[시각화 10 데이터: 5대 주요 라이프스타일 업종 추이 (단위: 백만원)]\n")
    f.write(df_lifestyle.to_string() + "\n\n")
    
print("모든 시각화 이미지 생성 및 요약 데이터 저장이 완료되었습니다.")
