import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
from sklearn.feature_extraction.text import TfidfVectorizer
import time

def run_eda():
    # 경로 설정 (상대 경로 기준)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "kyobo_bestseller_all.csv")
    image_dir = os.path.join(base_dir, "images")
    report_dir = os.path.join(base_dir, "report")
    
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    # 1. 데이터 로드 및 탐색
    if not os.path.exists(data_path):
        print(f"데이터 파일이 존재하지 않습니다: {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # 데이터 기본 정보
    shape_info = df.shape
    duplicate_count = df.duplicated().sum()
    duplicate_title_count = df['도서명'].duplicated().sum()
    
    # 전처리: 출판일 전처리 (YYYYMMDD -> datetime)
    df['출판일'] = df['출판일'].astype(str)
    # 날짜 파싱 (예외 처리)
    df['출판일_dt'] = pd.to_datetime(df['출판일'], format='%Y%m%d', errors='coerce')
    df['출판년도'] = df['출판일_dt'].dt.year
    df['출판월'] = df['출판일_dt'].dt.month
    df['출판년월'] = df['출판일_dt'].dt.to_period('M')
    
    # 통계 테이블 데이터 수집
    raw_markdown = []
    
    raw_markdown.append("# 교보문고 컴퓨터/IT 분야 베스트셀러 1000 데이터 분석 기초 보고서\n")
    raw_markdown.append(f"- **데이터 원본 경로**: `kyobobook/data/kyobo_bestseller_all.csv`")
    raw_markdown.append(f"- **전체 행 수**: {shape_info[0]}행")
    raw_markdown.append(f"- **전체 열 수**: {shape_info[1]}열")
    raw_markdown.append(f"- **전체 데이터 중복 건수**: {duplicate_count}건")
    raw_markdown.append(f"- **중복 도서명 건수**: {duplicate_title_count}건\n")
    
    # 상위 5행 및 하위 5행 마크다운 추가
    raw_markdown.append("## 데이터 미리보기")
    raw_markdown.append("### 상위 5개 행")
    raw_markdown.append(df.head(5).to_markdown(index=False))
    raw_markdown.append("\n### 하위 5개 행")
    raw_markdown.append(df.tail(5).to_markdown(index=False))
    raw_markdown.append("\n")
    
    # info() 유사 정보 추가
    raw_markdown.append("## 데이터 기본 정보 (df.info())")
    info_df = pd.DataFrame({
        "컬럼명": df.columns,
        "결측치 처리 전 데이터 타입": [str(t) for t in df.dtypes],
        "결측치가 아닌 값 개수": [df[col].count() for col in df.columns],
        "결측치 개수": [df[col].isnull().sum() for col in df.columns]
    })
    raw_markdown.append(info_df.to_markdown(index=False))
    raw_markdown.append("\n")
    
    # 기술통계 데이터
    raw_markdown.append("## 변수 기술통계")
    
    # 수치형
    desc_num = df[['순위', '정가', '할인가', '할인율']].describe()
    raw_markdown.append("### 수치형 변수 기술통계")
    raw_markdown.append(desc_num.to_markdown())
    raw_markdown.append("\n")
    
    # 범주형 (일부 전처리 컬럼 포함)
    df_cat = df[['저자', '출판사', '출판일', 'ISBN']].astype(str)
    desc_cat = df_cat.describe()
    raw_markdown.append("### 범주형 변수 기술통계")
    raw_markdown.append(desc_cat.to_markdown())
    raw_markdown.append("\n")
    
    # ----------------------------------------------------
    # 시각화 플롯 설정 (Seaborn 테마 사용 금지 규칙 준수)
    # Matplotlib 기본값 설정 조율
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.unicode_minus'] = False
    
    # 그래프 1: 정가 분포 (단변량 - 수치형)
    plt.figure()
    plt.hist(df['정가'], bins=30, color='royalblue', edgecolor='black', alpha=0.7)
    plt.title('도서 정가 분포')
    plt.xlabel('정가 (원)')
    plt.ylabel('도서 수 (권)')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g1_path = os.path.join(image_dir, "g1_original_price_dist.png")
    plt.savefig(g1_path, dpi=150)
    plt.close()
    
    # 그래프 2: 할인가 분포 (단변량 - 수치형)
    plt.figure()
    plt.hist(df['할인가'].dropna(), bins=30, color='darkorange', edgecolor='black', alpha=0.7)
    plt.title('도서 할인가 분포')
    plt.xlabel('할인가 (원)')
    plt.ylabel('도서 수 (권)')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g2_path = os.path.join(image_dir, "g2_sale_price_dist.png")
    plt.savefig(g2_path, dpi=150)
    plt.close()
    
    # 그래프 3: 할인율 분포 (단변량 - 범주/수치형)
    plt.figure()
    discount_counts = df['할인율'].value_counts().sort_index()
    plt.bar(discount_counts.index.astype(str), discount_counts.values, color='mediumseagreen', edgecolor='black', alpha=0.7)
    plt.title('도서 할인율 분포')
    plt.xlabel('할인율 (%)')
    plt.ylabel('도서 수 (권)')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g3_path = os.path.join(image_dir, "g3_discount_rate_dist.png")
    plt.savefig(g3_path, dpi=150)
    plt.close()
    
    # 그래프 4: 출판사별 도서 수 상위 30개 (단변량 - 범주형)
    plt.figure(figsize=(12, 7))
    pub_counts = df['출판사'].value_counts().head(30)
    plt.barh(pub_counts.index[::-1], pub_counts.values[::-1], color='dodgerblue', edgecolor='black', alpha=0.7)
    plt.title('출판사별 도서 점유율 (상위 30개)')
    plt.xlabel('도서 수 (권)')
    plt.ylabel('출판사')
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g4_path = os.path.join(image_dir, "g4_publisher_dist.png")
    plt.savefig(g4_path, dpi=150)
    plt.close()
    
    # 그래프 5: 저자별 도서 수 상위 30개 (단변량 - 범주형)
    plt.figure(figsize=(12, 7))
    author_counts = df['저자'].value_counts().head(30)
    plt.barh(author_counts.index[::-1], author_counts.values[::-1], color='orchid', edgecolor='black', alpha=0.7)
    plt.title('저자별 도서 점유율 (상위 30개)')
    plt.xlabel('도서 수 (권)')
    plt.ylabel('저자')
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g5_path = os.path.join(image_dir, "g5_author_dist.png")
    plt.savefig(g5_path, dpi=150)
    plt.close()
    
    # 그래프 6: 출판년도별 도서 수 (단변량 - 범주형)
    plt.figure()
    year_counts = df['출판년도'].value_counts().sort_index()
    # 최근 트렌드를 보기 위해 결측치 제외 및 연도 타입 정렬
    year_counts = year_counts[year_counts.index >= 2015] # 2015년 이후만 시각화
    plt.bar(year_counts.index.astype(int).astype(str), year_counts.values, color='gold', edgecolor='black', alpha=0.7)
    plt.title('연도별 도서 출판 수 (2015년 이후)')
    plt.xlabel('출판년도')
    plt.ylabel('도서 수 (권)')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    g6_path = os.path.join(image_dir, "g6_year_dist.png")
    plt.savefig(g6_path, dpi=150)
    plt.close()
    
    # 그래프 7: 순위와 할인가의 상관관계 (이변량 - 수치 vs 수치)
    plt.figure()
    plt.scatter(df['순위'], df['할인가'], color='crimson', alpha=0.6, edgecolors='none')
    plt.title('순위별 도서 할인가 분포')
    plt.xlabel('순위')
    plt.ylabel('할인가 (원)')
    plt.grid(linestyle='--', alpha=0.5)
    # 추세선 그리기
    z = np.polyfit(df['순위'], df['할인가'].fillna(0), 1)
    p = np.poly1d(z)
    plt.plot(df['순위'], p(df['순위']), "r--", alpha=0.8, label='추세선')
    plt.legend()
    plt.tight_layout()
    g7_path = os.path.join(image_dir, "g7_rank_vs_price.png")
    plt.savefig(g7_path, dpi=150)
    plt.close()
    
    # 그래프 8: 상위 10대 출판사의 평균 할인율 및 정가비교 (이변량 - 범주 vs 수치)
    top10_pubs = df['출판사'].value_counts().head(10).index
    df_top10 = df[df['출판사'].isin(top10_pubs)]
    pub_price_mean = df_top10.groupby('출판사')['정가'].mean().reindex(top10_pubs)
    pub_sale_mean = df_top10.groupby('출판사')['할인가'].mean().reindex(top10_pubs)
    
    plt.figure(figsize=(12, 6))
    x = np.arange(len(top10_pubs))
    width = 0.35
    plt.bar(x - width/2, pub_price_mean, width, label='평균 정가', color='cornflowerblue', edgecolor='black', alpha=0.7)
    plt.bar(x + width/2, pub_sale_mean, width, label='평균 할인가', color='salmon', edgecolor='black', alpha=0.7)
    plt.title('상위 10대 출판사별 평균 가격 비교')
    plt.xlabel('출판사')
    plt.ylabel('가격 (원)')
    plt.xticks(x, top10_pubs, rotation=30)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g8_path = os.path.join(image_dir, "g8_top10_pub_prices.png")
    plt.savefig(g8_path, dpi=150)
    plt.close()
    
    # 그래프 9: 출판일 기준 최근 2년간 월별 도서 출판 추이 (이변량 - 시계열)
    plt.figure(figsize=(12, 6))
    # 최근 24개월에 한하여 트렌드 파악
    recent_months = df['출판일_dt'].dropna()
    recent_months = recent_months[recent_months >= '2024-06-01']
    monthly_trend = recent_months.dt.to_period('M').value_counts().sort_index()
    
    plt.plot(monthly_trend.index.astype(str), monthly_trend.values, marker='o', color='purple', linewidth=2)
    plt.title('최근 2년간 월별 도서 출판 수 추이 (2024년 6월 이후)')
    plt.xlabel('출판년월')
    plt.ylabel('출판 도서 수 (권)')
    plt.grid(linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    g9_path = os.path.join(image_dir, "g9_monthly_trend.png")
    plt.savefig(g9_path, dpi=150)
    plt.close()
    
    # 그래프 10: 할인율별 도서 순위 분포 (이변량/다변량 - 범주 vs 수치)
    plt.figure()
    # 할인율을 범주형으로 취급하여 순위 분포 시각화 (Boxplot)
    # 할인율이 소수점 형태일 수 있으므로 정수형 변환 후 처리
    df['할인율_int'] = df['할인율'].fillna(0).astype(int)
    # 데이터가 충분한 할인율 그룹만 선택 (빈도가 5개 이상)
    valid_discounts = df['할인율_int'].value_counts()
    valid_discounts = valid_discounts[valid_discounts >= 5].index
    df_box = df[df['할인율_int'].isin(valid_discounts)]
    
    # seaborn boxplot 대신 matplotlib boxplot으로 수작업 구성 (Seaborn 테마 제한으로 스타일 일치화)
    groups = df_box.groupby('할인율_int')['순위']
    labels = sorted(df_box['할인율_int'].unique())
    data_to_plot = [groups.get_group(l).values for l in labels]
    
    plt.boxplot(data_to_plot, tick_labels=[f"{l}%" for l in labels])
    plt.title('할인율에 따른 도서 베스트셀러 순위 분포')
    plt.xlabel('할인율')
    plt.ylabel('순위 (낮을수록 상위)')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g10_path = os.path.join(image_dir, "g10_discount_vs_rank_box.png")
    plt.savefig(g10_path, dpi=150)
    plt.close()
    
    # 그래프 11: 도서명 키워드 TF-IDF 상위 30개 (텍스트 데이터 분석)
    # 텍스트 컬럼: '도서명'
    # TF-IDF 벡터화 진행 (띄어쓰기 기준 단어로 분석)
    # 한국어 형태소 분석기 미사용 규칙 준수
    tfidf = TfidfVectorizer(max_features=30, stop_words=None, token_pattern=r'(?u)\b\w\w+\b')
    tfidf_matrix = tfidf.fit_transform(df['도서명'].fillna(''))
    
    feature_names = tfidf.get_feature_names_out()
    # 중요도 평균 합산 계산
    mean_weights = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
    tfidf_ranking = pd.DataFrame({'키워드': feature_names, 'TF-IDF 중요도': mean_weights})
    tfidf_ranking = tfidf_ranking.sort_values(by='TF-IDF 중요도', ascending=False)
    
    plt.figure(figsize=(12, 7))
    plt.barh(tfidf_ranking['키워드'][::-1], tfidf_ranking['TF-IDF 중요도'][::-1], color='teal', edgecolor='black', alpha=0.7)
    plt.title('베스트셀러 도서명 TF-IDF 키워드 상위 30개')
    plt.xlabel('평균 중요도')
    plt.ylabel('키워드')
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    g11_path = os.path.join(image_dir, "g11_tfidf_keywords.png")
    plt.savefig(g11_path, dpi=150)
    plt.close()
    
    # ----------------------------------------------------
    # 각 시각화별 데이터 테이블 추출
    raw_markdown.append("## 시각화 동반 데이터 테이블 및 메타정보\n")
    
    # T1: 정가 통계
    raw_markdown.append("### [표 1] 도서 정가 도수 분포 데이터 (구간별)")
    price_bins = pd.cut(df['정가'], bins=[0, 10000, 20000, 30000, 40000, 50000, 100000, 1000000])
    raw_markdown.append(price_bins.value_counts().sort_index().to_markdown())
    raw_markdown.append("\n")
    
    # T2: 할인가 통계
    raw_markdown.append("### [표 2] 도서 할인가 도수 분포 데이터 (구간별)")
    sale_bins = pd.cut(df['할인가'].dropna(), bins=[0, 10000, 20000, 30000, 40000, 50000, 100000, 1000000])
    raw_markdown.append(sale_bins.value_counts().sort_index().to_markdown())
    raw_markdown.append("\n")
    
    # T3: 할인율 통계
    raw_markdown.append("### [표 3] 도서 할인율 빈도 데이터")
    raw_markdown.append(df['할인율'].value_counts().sort_index().to_markdown())
    raw_markdown.append("\n")
    
    # T4: 출판사 빈도 상위 30
    raw_markdown.append("### [표 4] 출판사별 베스트셀러 도서 수 (상위 30개)")
    raw_markdown.append(df['출판사'].value_counts().head(30).to_markdown())
    raw_markdown.append("\n")
    
    # T5: 저자 빈도 상위 30
    raw_markdown.append("### [표 5] 저자별 베스트셀러 도서 수 (상위 30개)")
    raw_markdown.append(df['저자'].value_counts().head(30).to_markdown())
    raw_markdown.append("\n")
    
    # T6: 연도별 도서 수
    raw_markdown.append("### [표 6] 연도별 베스트셀러 도서 출판 수 (2015년 이후)")
    raw_markdown.append(year_counts.to_markdown())
    raw_markdown.append("\n")
    
    # T7: 순위 vs 할인가 상관계수
    corr = df[['순위', '할인가']].corr().iloc[0, 1]
    raw_markdown.append("### [표 7] 순위와 할인가의 피어슨 상관계수")
    raw_markdown.append(f"| 수치형 변수 쌍 | 피어슨 상관계수 (Pearson Correlation) |\n| :--- | :--- |\n| 순위 - 할인가 | {corr:.4f} |")
    raw_markdown.append("\n")
    
    # T8: 상위 10대 출판사의 평균 가격 및 할인율
    raw_markdown.append("### [표 8] 상위 10대 출판사별 평균 정가 및 할인가 데이터")
    top10_stats = df_top10.groupby('출판사')[['정가', '할인가', '할인율']].mean().reindex(top10_pubs)
    raw_markdown.append(top10_stats.to_markdown())
    raw_markdown.append("\n")
    
    # T9: 최근 2년간 월별 도서 출판 수 데이터
    raw_markdown.append("### [표 9] 최근 2년간 월별 도서 출판 수 추이 데이터")
    raw_markdown.append(monthly_trend.to_markdown())
    raw_markdown.append("\n")
    
    # T10: 할인율별 순위 분포 기술통계
    raw_markdown.append("### [표 10] 할인율 그룹별 순위 요약 통계 (Boxplot 원본 데이터)")
    raw_markdown.append(groups.describe().to_markdown())
    raw_markdown.append("\n")
    
    # T11: TF-IDF 중요 단어 테이블
    raw_markdown.append("### [표 11] 도서명 TF-IDF 키워드 상위 30개 및 중요도 점수")
    raw_markdown.append(tfidf_ranking.to_markdown(index=False))
    raw_markdown.append("\n")
    
    # 마크다운 파일 저장
    report_raw_path = os.path.join(report_dir, "eda_report_raw.md")
    with open(report_raw_path, "w", encoding="utf-8") as f:
        f.write("\n".join(raw_markdown))
        
    print(f"기초 보고서 데이터가 성공적으로 저장되었습니다: {report_raw_path}")
    print(f"총 {len(raw_markdown)} 라인의 마크다운 정보 수집 및 11개 이미지 저장 완료.")

if __name__ == "__main__":
    run_eda()
