# -*- coding: utf-8 -*-
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# 한글 설정 확인 및 출력 설정
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# 1. 경로 정의 (상대경로 사용)
BASE_DIR = "testproj_1"
DATA_PATH = os.path.join(BASE_DIR, "data", "health_functional_food.json")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
REPORT_DIR = os.path.join(BASE_DIR, "report")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# 2. 데이터 로드
print("[INFO] 데이터를 로드합니다...")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

rows = raw_data["C003"]["row"]
df = pd.DataFrame(rows)

print("\n=== [1] 데이터 기본 정보 ===")
print(f"전체 행 수: {df.shape[0]}, 열 수: {df.shape[1]}")
print(f"중복 데이터 수: {df.duplicated().sum()}")

print("\n=== [2] 상위 5개 행 ===")
print(df.head(5))

print("\n=== [3] 하위 5개 행 ===")
print(df.tail(5))

print("\n=== [4] info() 정보 ===")
df.info()

# 3. 데이터 전처리
# 날짜형 데이터 변환
df['PRMS_DT_CLEAN'] = pd.to_datetime(df['PRMS_DT'], format='%Y%m%d', errors='coerce')
df['LAST_UPDT_DTM_CLEAN'] = pd.to_datetime(df['LAST_UPDT_DTM'].str[:8], format='%Y%m%d', errors='coerce')
df['YEAR'] = df['PRMS_DT_CLEAN'].dt.year
df['MONTH'] = df['PRMS_DT_CLEAN'].dt.month
df['UPDATE_GAP_DAYS'] = (df['LAST_UPDT_DTM_CLEAN'] - df['PRMS_DT_CLEAN']).dt.days

# 결측치 채우기
df['PRDT_SHAP_CD_NM'] = df['PRDT_SHAP_CD_NM'].replace("", "기타/미분류").fillna("기타/미분류")
df['BSSH_NM'] = df['BSSH_NM'].replace("", "알수없음").fillna("알수없음")
df['PRIMARY_FNCLTY'] = df['PRIMARY_FNCLTY'].replace("", "정보없음").fillna("정보없음")
df['RAWMTRL_NM'] = df['RAWMTRL_NM'].replace("", "정보없음").fillna("정보없음")
df['POG_DAYCNT'] = df['POG_DAYCNT'].replace("", "정보없음").fillna("정보없음")

print("\n=== [5] 결측치 확인 ===")
print(df.isnull().sum())

print("\n=== [6] 기술통계 (범주형 및 수치형) ===")
print("\n[수치형 변수 (연도, 월, 업데이트 소요 일수)]")
print(df[['YEAR', 'MONTH', 'UPDATE_GAP_DAYS']].describe(include='all'))

print("\n[범주형 변수]")
print(df[['PRDT_SHAP_CD_NM', 'BSSH_NM', 'POG_DAYCNT']].describe(include='all'))

# 통계 출력 저장용 버퍼 생성
stats_output = []

def log_stats(title, content):
    stats_output.append(f"## {title}\n")
    if isinstance(content, pd.DataFrame) or isinstance(content, pd.Series):
        stats_output.append(content.to_markdown() + "\n\n")
    else:
        stats_output.append(str(content) + "\n\n")

# 기본 기술통계 저장
log_stats("데이터 기본 통계량 (수치형)", df[['YEAR', 'MONTH', 'UPDATE_GAP_DAYS']].describe())
log_stats("데이터 기본 통계량 (범주형)", df[['PRDT_SHAP_CD_NM', 'BSSH_NM', 'POG_DAYCNT']].describe(include='all'))

# ==========================================
# 시각화 및 테이블 저장 (10개 그래프 생성)
# ==========================================
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11

# --- 그래프 1: 제품 형태(PRDT_SHAP_CD_NM) 빈도 분석 ---
fig, ax = plt.subplots()
shape_counts = df['PRDT_SHAP_CD_NM'].value_counts()
shape_counts.plot(kind='bar', color='#4F81BD', ax=ax)
ax.set_title("제품 형태별 제조 신고 건수")
ax.set_xlabel("제품 형태")
ax.set_ylabel("신고 건수 (건)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph1_product_shapes.png"), dpi=150)
plt.close()
log_stats("그래프 1: 제품 형태별 빈도 통계", shape_counts)

# --- 그래프 2: 주요 제조업체(BSSH_NM) 빈도 분석 (상위 10개) ---
fig, ax = plt.subplots()
top_manufacturers = df['BSSH_NM'].value_counts().head(10)
top_manufacturers.plot(kind='barh', color='#C0504D', ax=ax)
ax.set_title("주요 제조업체 Top 10 신고 건수")
ax.set_xlabel("신고 건수 (건)")
ax.set_ylabel("제조업체명")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph2_top_manufacturers.png"), dpi=150)
plt.close()
log_stats("그래프 2: 주요 제조업체 Top 10 빈도 통계", top_manufacturers)

# --- 그래프 3: 연도별 품목제조신고 건수 추이 ---
fig, ax = plt.subplots()
year_counts = df['YEAR'].value_counts().sort_index()
year_counts.plot(kind='line', marker='o', color='#9BBB59', linewidth=2.5, ax=ax)
ax.set_title("연도별 품목제조신고 건수 추이")
ax.set_xlabel("연도")
ax.set_ylabel("신고 건수 (건)")
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph3_yearly_trends.png"), dpi=150)
plt.close()
log_stats("그래프 3: 연도별 신고 건수 통계", year_counts)

# --- 그래프 4: 월별 품목제조신고 건수 추이 ---
fig, ax = plt.subplots()
month_counts = df['MONTH'].value_counts().sort_index()
month_counts.plot(kind='bar', color='#8064A2', ax=ax)
ax.set_title("월별 품목제조신고 누적 건수")
ax.set_xlabel("월")
ax.set_ylabel("신고 건수 (건)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph4_monthly_trends.png"), dpi=150)
plt.close()
log_stats("그래프 4: 월별 신고 건수 통계", month_counts)

# --- 그래프 5: 유통기한(POG_DAYCNT) 유형 빈도 분석 (상위 15개) ---
fig, ax = plt.subplots()
expiry_counts = df['POG_DAYCNT'].value_counts().head(15)
expiry_counts.plot(kind='bar', color='#4BACC6', ax=ax)
ax.set_title("보존 및 유통기한 기준 빈도 Top 15")
ax.set_xlabel("유통기한 기준")
ax.set_ylabel("신고 건수 (건)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph5_expiry_trends.png"), dpi=150)
plt.close()
log_stats("그래프 5: 유통기한 기준 Top 15 통계", expiry_counts)

# --- 그래프 6: 제품 형태별 허가 연도 분포 (이변량 - Box Plot) ---
# 빈도가 높은 5개 형태만 선택하여 분석
top_shapes = df['PRDT_SHAP_CD_NM'].value_counts().head(5).index
df_filtered_shapes = df[df['PRDT_SHAP_CD_NM'].isin(top_shapes)]

fig, ax = plt.subplots()
# matplotlib boxplot
boxplot_data = [df_filtered_shapes[df_filtered_shapes['PRDT_SHAP_CD_NM'] == shape]['YEAR'].dropna() for shape in top_shapes]
ax.boxplot(boxplot_data, labels=top_shapes)
ax.set_title("주요 제품 형태별 허가 연도 분포")
ax.set_xlabel("제품 형태")
ax.set_ylabel("허가 연도")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph6_shape_year_distribution.png"), dpi=150)
plt.close()

# 기술 통계표 작성
shape_year_stats = df_filtered_shapes.groupby('PRDT_SHAP_CD_NM')['YEAR'].describe()
log_stats("그래프 6: 주요 제품 형태별 허가 연도 기술통계표", shape_year_stats)

# --- 그래프 7: 주요 제조업체별 제품 형태 구성 (이변량 - Stacked Bar Plot) ---
top_bssh = df['BSSH_NM'].value_counts().head(5).index
df_filtered_bssh = df[df['BSSH_NM'].isin(top_bssh)]
crosstab_shape_bssh = pd.crosstab(df_filtered_bssh['BSSH_NM'], df_filtered_bssh['PRDT_SHAP_CD_NM'])

fig, ax = plt.subplots()
crosstab_shape_bssh.plot(kind='bar', stacked=True, colormap='viridis', ax=ax)
ax.set_title("주요 5대 제조업체별 제품 형태 구성")
ax.set_xlabel("제조업체명")
ax.set_ylabel("신고 건수 (건)")
plt.xticks(rotation=30, ha='right')
plt.legend(title="제품 형태")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph7_manufacturer_shape_composition.png"), dpi=150)
plt.close()
log_stats("그래프 7: 주요 5대 제조업체별 제품 형태 구성 교차표", crosstab_shape_bssh)

# --- 그래프 8: 허가일과 최종수정일 간의 업데이트 소요 일수 분포 (이변량 - Histogram) ---
fig, ax = plt.subplots()
valid_gaps = df['UPDATE_GAP_DAYS'].dropna()
ax.hist(valid_gaps, bins=20, color='#F79646', edgecolor='white')
ax.set_title("허가일 대비 최종 수정일까지의 소요 일수 분포")
ax.set_xlabel("소요 일수 (일)")
ax.set_ylabel("빈도 (건)")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph8_update_gap_distribution.png"), dpi=150)
plt.close()

gap_stats = valid_gaps.describe()
log_stats("그래프 8: 업데이트 소요 일수 기술통계표", gap_stats)


# --- TF-IDF 텍스트 분석 (그래프 9, 10) ---
def get_tfidf_top_features(texts, max_features=30):
    vectorizer = TfidfVectorizer(max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # 단어별 TF-IDF 점수 합산
    scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()
    features = vectorizer.get_feature_names_out()
    
    df_tfidf = pd.DataFrame({'word': features, 'score': scores})
    df_tfidf = df_tfidf.sort_values(by='score', ascending=False).head(max_features)
    return df_tfidf

# --- 그래프 9: 주된 기능성(PRIMARY_FNCLTY) TF-IDF 키워드 상위 30개 ---
print("[INFO] 주된 기능성 TF-IDF 분석 중...")
fnclty_tfidf = get_tfidf_top_features(df['PRIMARY_FNCLTY'])

fig, ax = plt.subplots(figsize=(10, 8))
fnclty_tfidf.plot(kind='barh', x='word', y='score', color='#4F81BD', legend=False, ax=ax)
ax.set_title("주된 기능성 텍스트 TF-IDF 상위 30 키워드")
ax.set_xlabel("TF-IDF 가중치 합")
ax.set_ylabel("키워드")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph9_functionality_tfidf.png"), dpi=150)
plt.close()
log_stats("그래프 9: 주된 기능성 TF-IDF 상위 30 키워드 표", fnclty_tfidf)

# --- 그래프 10: 원재료명(RAWMTRL_NM) TF-IDF 키워드 상위 30개 ---
print("[INFO] 원재료명 TF-IDF 분석 중...")
raw_tfidf = get_tfidf_top_features(df['RAWMTRL_NM'])

fig, ax = plt.subplots(figsize=(10, 8))
raw_tfidf.plot(kind='barh', x='word', y='score', color='#C0504D', legend=False, ax=ax)
ax.set_title("원재료명 텍스트 TF-IDF 상위 30 키워드")
ax.set_xlabel("TF-IDF 가중치 합")
ax.set_ylabel("키워드")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "graph10_raw_material_tfidf.png"), dpi=150)
plt.close()
log_stats("그래프 10: 원재료명 TF-IDF 상위 30 키워드 표", raw_tfidf)


# 통계 데이터 파일로 작성
with open(os.path.join(REPORT_DIR, "eda_statistics.md"), "w", encoding="utf-8") as sf:
    sf.write("# 건강기능식품 데이터 EDA 통계 테이블 목록\n\n")
    sf.write("이 파일은 `eda_analysis.py` 스크립트에 의해 자동 생성된 통계 데이터 목록입니다.\n\n")
    sf.write("".join(stats_output))

print("[INFO] 분석 및 시각화가 완료되었습니다. 결과물이 testproj_1/images/ 및 testproj_1/report/ 에 저장되었습니다.")
