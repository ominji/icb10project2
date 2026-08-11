import os
import pandas as pd

# 파일 경로 설정
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
burger_path = os.path.join(base_dir, "burger.csv")

# 데이터 읽기
df = pd.read_csv(burger_path, encoding="utf-8-sig", low_memory=False)

# 1. 브랜드 파생변수 생성
brand_keywords = {
    "버거킹": "버거킹",
    "burger king": "버거킹",
    "맥도날드": "맥도날드",
    "mcdonald": "맥도날드",
    "mcdonald's": "맥도날드",
    "kfc": "KFC",
    "케이에프씨": "KFC",
    "롯데리아": "롯데리아",
    "lotteria": "롯데리아",
}

def infer_brand(name: str) -> str:
    name_lower = str(name).lower()
    for kw, brand in brand_keywords.items():
        if kw.lower() in name_lower:
            return brand
    return None

df["brand"] = df["상호명"].apply(infer_brand)
df = df.dropna(subset=["brand"])

# 2. 실제 음식이나 소매가 아닌 매장 제외 (음식, 소매만 남김)
initial_count = len(df)
df_filtered = df[df["상권업종대분류명"].isin(["음식", "소매"])].copy()
removed_by_category = initial_count - len(df_filtered)

# 3. 중복 데이터 분석
# 중복된 행 확인 (상가업소번호 기준)
dup_mask = df_filtered.duplicated(subset=["상가업소번호"], keep=False)
dup_df = df_filtered[dup_mask]

# 어떻게 중복이 발생하는지 분석
# 중복 횟수별 매장 수
dup_counts = df_filtered.groupby("상가업소번호").size()
dup_counts_summary = dup_counts.value_counts()

# 중복 샘플 상세 내역 추출 (마크다운용)
dup_samples = []
if not dup_df.empty:
    grouped = dup_df.groupby("상가업소번호")
    count = 0
    for id_val, group in grouped:
        samples = []
        for idx, row in group.iterrows():
            samples.append({
                "상호명": row['상호명'],
                "도로명주소": row['도로명주소'],
                "상권업종대분류명": row['상권업종대분류명'],
                "시도명": row['시도명']
            })
        dup_samples.append({
            "상가업소번호": id_val,
            "중복횟수": len(group),
            "데이터": samples
        })
        count += 1
        if count >= 5:
            break

# 4. 중복 제거
df_cleaned = df_filtered.drop_duplicates(subset=["상가업소번호"], keep="first").copy()
final_count = len(df_cleaned)

# 5. 교차표 작성
crosstab = pd.crosstab(df_cleaned["brand"], df_cleaned["상권업종대분류명"])

# 리포트 생성 및 저장
report_path = os.path.join(os.path.dirname(__file__), "report", "duplicate_report.md")
os.makedirs(os.path.dirname(report_path), exist_ok=True)

with open(report_path, "w", encoding="utf-8") as f:
    f.write("# 🍔 버거 브랜드 데이터 중복 분석 및 정제 리포트\n\n")
    f.write("## 1. 데이터 필터링 요약\n")
    f.write(f"- **최초 브랜드 필터링 행 수**: {initial_count}개\n")
    f.write(f"- **음식/소매 이외 업종 제외 수**: {removed_by_category}개 (과학·기술, 교육 등 제외)\n")
    f.write(f"- **중복 제거 후 최종 매장 수**: {final_count}개\n\n")
    
    f.write("## 2. 중복 데이터 분석\n")
    f.write(f"- **상가업소번호 기준 중복 발생 행 수**: {len(dup_df)}개 행\n")
    f.write("### 중복 빈도 분포:\n")
    for limit, count_val in dup_counts_summary.items():
        f.write(f"  - {limit}회 중복되어 나타난 업소 수: {count_val}개\n")
    f.write("\n> **원인 분석**: 전국 17개 시도별 CSV 데이터를 개별 추출해 합치는 과정에서, 이전에 중복으로 스크립트가 실행되었거나 동일한 사업체가 여러 번 중복 병합되어 데이터가 정확히 2배로 불어난 상태였습니다. (모든 고유 업소가 정확히 2번씩 들어가 있음)\n\n")
    
    f.write("### 3. 중복 데이터 상세 샘플 (상위 5개)\n")
    for sample in dup_samples:
        f.write(f"#### 🔑 상가업소번호: `{sample['상가업소번호']}` (중복 횟수: {sample['중복횟수']}회)\n")
        f.write("| 상호명 | 도로명주소 | 업종대분류 | 시도명 |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for row in sample['데이터']:
            f.write(f"| {row['상호명']} | {row['도로명주소']} | {row['상권업종대분류명']} | {row['시도명']} |\n")
        f.write("\n")
        
    f.write("## 4. 최종 정제 후 교차표 (음식 vs 소매)\n")
    f.write("| 브랜드 | 소매 (빈도) | 음식 (빈도) | 합계 |\n")
    f.write("| :--- | :---: | :---: | :---: |\n")
    for brand in ["KFC", "롯데리아", "맥도날드", "버거킹"]:
        s_val = crosstab.loc[brand, "소매"] if "소매" in crosstab.columns and brand in crosstab.index else 0
        f_val = crosstab.loc[brand, "음식"] if "음식" in crosstab.columns and brand in crosstab.index else 0
        f.write(f"| **{brand}** | {s_val:,} | {f_val:,} | {s_val + f_val:,} |\n")
        
    # 총합 추가
    s_total = crosstab["소매"].sum() if "소매" in crosstab.columns else 0
    f_total = crosstab["음식"].sum() if "음식" in crosstab.columns else 0
    f.write(f"| **합계** | **{s_total:,}** | **{f_total:,}** | **{s_total + f_total:,}** |\n")

# 최종 교차표 결과 저장
crosstab.to_csv(os.path.join(base_dir, "brand_crosstab_cleaned.csv"), encoding="utf-8-sig")
print("리포트와 정제된 교차표가 성공적으로 작성되었습니다.")
