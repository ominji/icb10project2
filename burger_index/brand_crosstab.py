import os
import pandas as pd

# 버거 체인 키워드와 브랜드 매핑 (대소문자 구분 없이)
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

# 파일 경로 (스크립트 위치 기준 상대 경로)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
burger_path = os.path.join(base_dir, "burger.csv")

# CSV 읽기 (UTF-8‑sig 인코딩)
df = pd.read_csv(burger_path, encoding="utf-8-sig")

# 상호명에 포함된 키워드로 브랜드 컬럼 생성
def infer_brand(name: str) -> str:
    name_lower = str(name).lower()
    for kw, brand in brand_keywords.items():
        if kw.lower() in name_lower:
            return brand
    return None

# 브랜드 컬럼 추가 및 None 제거
df["brand"] = df["상호명"].apply(infer_brand)
df = df.dropna(subset=["brand"])

# 교차표 생성: 브랜드 vs. 상권업종대분류명
crosstab = pd.crosstab(df["brand"], df["상권업종대분류명"])  # 행: 브랜드, 열: 업종대분류명

# 결과 저장
output_path = os.path.join(base_dir, "brand_crosstab.csv")
crosstab.to_csv(output_path, encoding="utf-8-sig")
print(f"교차표가 {output_path}에 저장되었습니다.")
