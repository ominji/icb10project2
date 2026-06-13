import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import sys

# Windows 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
src_dir = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(src_dir)
csv_path = os.path.join(proj_dir, "data", "식품의약품안전처_건강기능식품영양성분정보_20251230.csv")
images_dir = os.path.join(proj_dir, "images")
os.makedirs(images_dir, exist_ok=True)

print(f"Loading data from: {csv_path}")
# 1. 데이터 로드
df = pd.read_csv(csv_path, encoding='utf-8-sig')

# 2. 기본 정보 저장
info_summary = []
info_summary.append(f"Shape: {df.shape}")
info_summary.append(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
info_summary.append(f"Duplicates: {df.duplicated().sum()}")

# df.info()를 문자열로 받기
import io
buffer = io.StringIO()
df.info(buf=buffer)
info_summary.append("\n=== info() ===\n" + buffer.getvalue())

# 상위 5행, 하위 5행 정보 기록
info_summary.append("\n=== Head 5 Rows ===\n" + df.head(5).to_string())
info_summary.append("\n=== Tail 5 Rows ===\n" + df.tail(5).to_string())

with open(os.path.join(src_dir, "info_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(info_summary))

# 3. 기술 통계
# 수치형 변수 자동 선택 및 기술 통계 구하기
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
desc_num = df[num_cols].describe().transpose()
desc_num.to_csv(os.path.join(src_dir, "desc_num.csv"), encoding="utf-8-sig")

# 범주형 변수 자동 선택 및 기술 통계 구하기
cat_cols = df.select_dtypes(include=[object]).columns.tolist()
desc_cat = df[cat_cols].describe().transpose()
desc_cat.to_csv(os.path.join(src_dir, "desc_cat.csv"), encoding="utf-8-sig")

# 4. 시각화 11개 생성
# 1) 단변량 - 에너지 분포
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x="에너지(kcal)", kde=True, bins=50, color="skyblue")
plt.title("에너지(kcal) 분포")
plt.xlabel("에너지 (kcal)")
plt.ylabel("빈도수")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "01_energy_distribution.png"), dpi=150)
plt.close()

# 2) 단변량 - 식품대분류명 빈도 (고유값 확인하여 바 차트 그리기)
plt.figure(figsize=(10, 6))
cat_counts = df["식품대분류명"].value_counts()
# 상위 30개만 선택 (규칙 적용)
if len(cat_counts) > 30:
    cat_counts = cat_counts.head(30)
sns.barplot(x=cat_counts.values, y=cat_counts.index, palette="viridis")
plt.title("식품대분류명 빈도 분포")
plt.xlabel("빈도수")
plt.ylabel("식품대분류명")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "02_food_category_distribution.png"), dpi=150)
plt.close()

# 3) 단변량 - 수입여부 빈도
plt.figure(figsize=(8, 8))
import_counts = df["수입여부"].value_counts()
plt.pie(import_counts.values, labels=import_counts.index, autopct='%1.1f%%', startangle=140, colors=["lightcoral", "lightgreen"])
plt.title("수입여부 비율")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "03_import_ratio.png"), dpi=150)
plt.close()

# 4) 이변량 - 주요 원산지국명(Top 10) 제품 수
plt.figure(figsize=(12, 6))
origin_counts = df["원산지국명"].value_counts().head(10)
sns.barplot(x=origin_counts.index, y=origin_counts.values, palette="magma")
plt.title("상위 10개 원산지국명별 제품 수")
plt.xlabel("원산지국명")
plt.ylabel("제품 수")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "04_origin_country_count.png"), dpi=150)
plt.close()

# 5) 이변량 - 식품대분류별 에너지(kcal) 평균 (박스플롯)
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x="식품대분류명", y="에너지(kcal)", palette="Set3")
plt.title("식품대분류별 에너지(kcal) 분포")
plt.xlabel("식품대분류명")
plt.ylabel("에너지 (kcal)")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "05_energy_by_category.png"), dpi=150)
plt.close()

# 6) 이변량 - 단백질 vs 탄수화물 산점도
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x="단백질(g)", y="탄수화물(g)", alpha=0.5, color="purple")
plt.title("단백질(g) vs 탄수화물(g) 상관관계")
plt.xlabel("단백질 (g)")
plt.ylabel("탄수화물 (g)")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "06_protein_vs_carbo.png"), dpi=150)
plt.close()

# 7) 이변량 - 비타민 D vs 비타민 C 함량 관계
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x="비타민 D(μg)", y="비타민 C(mg)", alpha=0.5, color="orange")
plt.title("비타민 D(μg) vs 비타민 C(mg) 상관관계")
plt.xlabel("비타민 D (μg)")
plt.ylabel("비타민 C (mg)")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "07_vitd_vs_vitc.png"), dpi=150)
plt.close()

# 8) 다변량 - 주요 영양성분 상관관계 히트맵
plt.figure(figsize=(10, 8))
selected_nutrients = ["에너지(kcal)", "단백질(g)", "지방(g)", "탄수화물(g)", "당류(g)", "식이섬유(g)", "나트륨(mg)"]
corr_df = df[selected_nutrients].fillna(0)
sns.heatmap(corr_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=.5)
plt.title("주요 영양성분 간의 상관관계 히트맵")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "08_nutrition_correlation.png"), dpi=150)
plt.close()

# 9) 다변량 - 식품대분류명 및 수입여부별 제품 수 교차 분석
plt.figure(figsize=(12, 6))
sns.countplot(data=df, x="식품대분류명", hue="수입여부", palette="pastel")
plt.title("식품대분류명 및 수입여부별 제품 수 비교")
plt.xlabel("식품대분류명")
plt.ylabel("제품 수")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "09_category_import_stacked.png"), dpi=150)
plt.close()

# 10) 이변량 - 1일 섭취 횟수 분포
plt.figure(figsize=(10, 6))
intake_counts = df["1일섭취횟수"].value_counts().head(10)
sns.barplot(x=intake_counts.index, y=intake_counts.values, palette="cool")
plt.title("상위 10개 1일 섭취 횟수 빈도")
plt.xlabel("1일 섭취 횟수")
plt.ylabel("제품 수")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "10_daily_intake_frequency.png"), dpi=150)
plt.close()

# 11) 텍스트 분석 - 식품명 TF-IDF 키워드 상위 30개
df_clean = df.dropna(subset=['식품명'])
# 한국어 토크나이저를 사용하지 않고 띄어쓰기를 기준으로 토큰화
vectorizer = TfidfVectorizer(max_features=30, stop_words=None)
tfidf_matrix = vectorizer.fit_transform(df_clean['식품명'])
feature_names = vectorizer.get_feature_names_out()
sums = tfidf_matrix.sum(axis=0)

data = []
for col, term in enumerate(feature_names):
    data.append((term, sums[0, col]))

ranking = pd.DataFrame(data, columns=['keyword', 'tfidf_score'])
ranking = ranking.sort_values('tfidf_score', ascending=False)
ranking.to_csv(os.path.join(src_dir, "tfidf_result.csv"), index=False, encoding="utf-8-sig")

plt.figure(figsize=(12, 8))
sns.barplot(x='tfidf_score', y='keyword', data=ranking, palette="rocket")
plt.title("식품명 TF-IDF 핵심 키워드 상위 30개")
plt.xlabel("TF-IDF 스코어 합계")
plt.ylabel("키워드")
plt.tight_layout()
plt.savefig(os.path.join(images_dir, "11_tfidf_keywords.png"), dpi=150)
plt.close()

# 5. 시각화 동반 테이블 데이터 저장
# 1) 에너지 분포 테이블
energy_stats = df["에너지(kcal)"].describe()
energy_stats.to_csv(os.path.join(src_dir, "tbl_01_energy.csv"), encoding="utf-8-sig")

# 2) 식품대분류 빈도 테이블
cat_counts_df = pd.DataFrame({"빈도수": cat_counts.values, "비율(%)": (cat_counts.values / cat_counts.sum()) * 100}, index=cat_counts.index)
cat_counts_df.to_csv(os.path.join(src_dir, "tbl_02_food_category.csv"), encoding="utf-8-sig")

# 3) 수입여부 비율 테이블
import_counts_df = pd.DataFrame({"빈도수": import_counts.values, "비율(%)": (import_counts.values / import_counts.sum()) * 100}, index=import_counts.index)
import_counts_df.to_csv(os.path.join(src_dir, "tbl_03_import.csv"), encoding="utf-8-sig")

# 4) 상위 원산지국명 테이블
origin_counts_df = pd.DataFrame({"제품수": origin_counts.values}, index=origin_counts.index)
origin_counts_df.to_csv(os.path.join(src_dir, "tbl_04_origin.csv"), encoding="utf-8-sig")

# 5) 식품대분류별 에너지 평균 테이블
energy_by_cat_df = df.groupby("식품대분류명")["에너지(kcal)"].describe()
energy_by_cat_df.to_csv(os.path.join(src_dir, "tbl_05_energy_by_cat.csv"), encoding="utf-8-sig")

# 6) 단백질 vs 탄수화물 상관 계수 테이블
prot_carbo_corr = df[["단백질(g)", "탄수화물(g)"]].corr()
prot_carbo_corr.to_csv(os.path.join(src_dir, "tbl_06_protein_vs_carbo.csv"), encoding="utf-8-sig")

# 7) 비타민 D vs 비타민 C 상관 계수 테이블
vitd_vitc_corr = df[["비타민 D(μg)", "비타민 C(mg)"]].corr()
vitd_vitc_corr.to_csv(os.path.join(src_dir, "tbl_07_vitd_vs_vitc.csv"), encoding="utf-8-sig")

# 8) 주요 영양성분 상관계수 테이블
corr_matrix = corr_df.corr()
corr_matrix.to_csv(os.path.join(src_dir, "tbl_08_nutrition_corr.csv"), encoding="utf-8-sig")

# 9) 식품대분류명 x 수입여부 교차표
crosstab_cat_import = pd.crosstab(df["식품대분류명"], df["수입여부"])
crosstab_cat_import.to_csv(os.path.join(src_dir, "tbl_09_crosstab.csv"), encoding="utf-8-sig")

# 10) 1일 섭취 횟수 빈도 테이블
intake_df = pd.DataFrame({"제품수": intake_counts.values}, index=intake_counts.index)
intake_df.to_csv(os.path.join(src_dir, "tbl_10_intake.csv"), encoding="utf-8-sig")

print("EDA analysis generation completed!")
