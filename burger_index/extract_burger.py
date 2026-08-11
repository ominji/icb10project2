import os
import glob
import pandas as pd

# 4대 버거 브랜드 한/영 키워드 매핑 정의
keywords = {
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
keywords_lower = [k.lower() for k in keywords.keys()]

# 데이터 디렉토리 설정
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))

# 데이터 디렉토리에서 원본 시도별 CSV 파일 목록 추출 (출력 파일 제외)
csv_files = [
    f for f in glob.glob(os.path.join(base_dir, "*.csv"))
    if "burger" not in os.path.basename(f) and "brand_crosstab" not in os.path.basename(f)
]

print(f"원본 데이터 파일 수: {len(csv_files)}")

# [1단계] 4대 브랜드 한/영 키워드 기준 추출
filtered_frames = []
for csv_path in csv_files:
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
    except Exception:
        df = pd.read_csv(csv_path, encoding="cp949", low_memory=False)
    
    # 상호명 컬럼 식별
    name_col = next((c for c in df.columns if "상호명" in c), None)
    if not name_col:
        continue
    
    series = df[name_col].astype(str).fillna("").str.lower()
    mask = series.apply(lambda x: any(kw in x for kw in keywords_lower))
    filtered = df[mask]
    if not filtered.empty:
        filtered_frames.append(filtered)

if filtered_frames:
    step1_df = pd.concat(filtered_frames, ignore_index=True)
    print(f"1단계 추출 데이터 건수: {len(step1_df)}")
    
    # [2단계] 'brand' 파생변수 매핑
    def infer_brand(name: str) -> str:
        name_lower = str(name).lower()
        for kw, brand in keywords.items():
            if kw.lower() in name_lower:
                return brand
        return None
    
    step1_df["brand"] = step1_df["상호명"].apply(infer_brand)
    step2_df = step1_df.dropna(subset=["brand"]).copy()
    print(f"2단계 브랜드 매핑 후 건수: {len(step2_df)}")
    
    # [3단계] 실제 음식 또는 소매업이 아닌 매장 제외 (음식, 소매 분류만 유지)
    step3_df = step2_df[step2_df["상권업종대분류명"].isin(["음식", "소매"])].copy()
    print(f"3단계 음식/소매 업종 필터링 후 건수: {len(step3_df)}")
    
    # [4단계] 상호명 + 도로명주소 기준 중복 제거
    step4_df = step3_df.drop_duplicates(subset=["상호명", "도로명주소"], keep="first").copy()
    print(f"4단계 중복 제거 후 최종 건수: {len(step4_df)}")
    
    # 정제된 데이터를 최종 burger.csv로 저장
    output_path = os.path.join(base_dir, "burger.csv")
    step4_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"최종 데이터 저장 완료: {output_path}")
    
    # 상권업종대분류명과 브랜드명으로 교차표 생성 및 저장
    crosstab = pd.crosstab(step4_df["brand"], step4_df["상권업종대분류명"])
    crosstab_path = os.path.join(base_dir, "brand_crosstab_cleaned.csv")
    crosstab.to_csv(crosstab_path, encoding="utf-8-sig")
    print(f"교차표 저장 완료: {crosstab_path}")
    
    print("\n--- 최종 교차표 빈도수 ---")
    print(crosstab)
else:
    print("매칭되는 데이터를 찾지 못했습니다.")
