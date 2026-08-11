import os
import pandas as pd
import re
from tqdm import tqdm

extract_dir = os.path.join("card", "data", "경기도 카드소비데이터_2025", "extracted")
files = [f for f in os.listdir(extract_dir) if f.endswith(".csv")]

print(f"총 {len(files)}개 파일에 대해 그룹화 및 요약 작업을 진행합니다.")

agg_list = []

for f in tqdm(files):
    file_path = os.path.join(extract_dir, f)
    
    # 파일명에서 연월 및 지역 추출
    # 예: tbsh_gyeonggi_day_202503_안산.csv
    match = re.search(r"(\d{6})_(.+)\.csv", f)
    if match:
        ym = match.group(1)
        region = match.group(2)
    else:
        ym = "unknown"
        region = "unknown"
        
    try:
        # 데이터 읽기
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 필요한 정보만 그룹화
        # cty_rgn_no (시군구) 등도 함께 사용
        df_agg = df.groupby(['card_tpbuz_nm_1', 'sex', 'age']).agg({
            'amt': 'sum',
            'cnt': 'sum'
        }).reset_index()
        
        # 연월 및 지역 정보 추가
        df_agg['year_month'] = ym
        df_agg['region'] = region
        
        agg_list.append(df_agg)
        
    except Exception as e:
        print(f"\n{f} 처리 중 에러 발생: {e}")

# 전체 요약 데이터 병합
if agg_list:
    final_df = pd.concat(agg_list, ignore_index=True)
    out_path = os.path.join("card", "data", "경기도 카드소비데이터_2025", "aggregated_summary.csv")
    final_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"\n요약 데이터 생성 완료! 최종 shape: {final_df.shape}")
    print(f"저장 경로: {out_path}")
else:
    print("요약할 데이터가 없습니다.")
