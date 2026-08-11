import pandas as pd
import numpy as np
import sqlite3
import json
import os

PARQUET_PATH = "seoseoul-pops/data/LOCAL_PEOPLE_DONG_202606.parquet"
EXCEL_PATH = "seoseoul-pops/data/행정동코드_매핑정보_20241218.xlsx"
DB_PATH = "seoseoul-pops/data/seoul_pops.db"

def build_database():
    print("1. 데이터 로드 및 결합 중...")
    # 1. Parquet 데이터 로드
    df_parquet = pd.read_parquet(PARQUET_PATH)
    
    # 2. Excel 매핑 데이터 로드
    df_excel = pd.read_excel(EXCEL_PATH)
    df_excel = df_excel.iloc[1:].reset_index(drop=True)
    df_excel['행자부행정동코드'] = pd.to_numeric(df_excel['행자부행정동코드']).astype(int)
    
    # 3. 데이터 결합
    df = pd.merge(
        df_parquet,
        df_excel,
        left_on="행정동코드",
        right_on="행자부행정동코드",
        how="left"
    )
    
    # 4. 날짜/요일/일자 전처리
    date_map = {}
    for day in range(1, 31):
        date_id = 20260600 + day
        dt = pd.to_datetime(str(date_id), format='%Y%m%d')
        weekday_kor = {0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'}[dt.weekday()]
        date_map[date_id] = (weekday_kor, day)
        
    df['요일'] = df['기준일ID'].map(lambda x: date_map[x][0])
    df['일자'] = df['기준일ID'].map(lambda x: date_map[x][1])
    df['adm_cd2_str'] = df['행정동코드'].astype(str) + "00"
    
    if '행자부행정동코드' in df.columns:
        df.drop(columns=['행자부행정동코드'], inplace=True)

    print("2. SQLite 연결 및 메타데이터 저장 중...")
    conn = sqlite3.connect(DB_PATH)
    
    # 메타데이터 구조 작성
    shape_rows, shape_cols = df.shape
    null_count = int(df.isnull().sum().sum())
    dup_count = int(df.duplicated().sum())
    
    head_json = df.head(10).to_json(orient='records', force_ascii=False)
    tail_json = df.tail(10).to_json(orient='records', force_ascii=False)
    
    info_dict = {
        "columns": df.columns.tolist(),
        "dtypes": [str(t) for t in df.dtypes],
        "nulls": df.isnull().sum().tolist(),
        "uniques": [df[c].nunique() for c in df.columns]
    }
    info_json = json.dumps(info_dict, ensure_ascii=False)
    
    df_meta = pd.DataFrame([{
        "shape_rows": shape_rows,
        "shape_cols": shape_cols,
        "null_count": null_count,
        "dup_count": dup_count,
        "head_json": head_json,
        "tail_json": tail_json,
        "info_json": info_json
    }])
    df_meta.to_sql("metadata", conn, if_exists="replace", index=False)

    print("3. 대시보드 통계 및 시각화용 집계 데이터 저장 중...")
    
    # 3-1. 성별 집계
    print(" - agg_gender")
    agg_gender = df.groupby(['시군구명', '성별'], observed=False)['생활인구수'].sum().reset_index()
    agg_gender.to_sql("agg_gender", conn, if_exists="replace", index=False)
    
    # 3-2. 연령대별 집계
    print(" - agg_age")
    agg_age = df.groupby(['시군구명', '연령대'], observed=False)['생활인구수'].sum().reset_index()
    agg_age.to_sql("agg_age", conn, if_exists="replace", index=False)
    
    # 3-3. 시간대별 평균
    print(" - agg_hourly")
    agg_hourly = df.groupby(['시군구명', '시간대구분'])['생활인구수'].mean().reset_index()
    agg_hourly.to_sql("agg_hourly", conn, if_exists="replace", index=False)
    
    # 3-4. 요일별 평균
    print(" - agg_weekday")
    agg_weekday = df.groupby(['시군구명', '요일'])['생활인구수'].mean().reset_index()
    agg_weekday.to_sql("agg_weekday", conn, if_exists="replace", index=False)
    
    # 3-5. 성별 x 연령대별 합계
    print(" - agg_gender_age")
    agg_gender_age = df.groupby(['시군구명', '성별', '연령대'], observed=False)['생활인구수'].sum().reset_index()
    agg_gender_age.to_sql("agg_gender_age", conn, if_exists="replace", index=False)
    
    # 3-6. 시간대별 성별 평균
    print(" - agg_hourly_gender")
    agg_hourly_gender = df.groupby(['시군구명', '시간대구분', '성별'], observed=False)['생활인구수'].mean().reset_index()
    agg_hourly_gender.to_sql("agg_hourly_gender", conn, if_exists="replace", index=False)
    
    # 3-7. 히트맵 데이터 (구별 및 동별)
    print(" - agg_heatmap_gu")
    agg_heatmap_gu = df.groupby(['시군구명', '시간대구분'])['생활인구수'].mean().reset_index()
    agg_heatmap_gu.to_sql("agg_heatmap_gu", conn, if_exists="replace", index=False)
    
    print(" - agg_heatmap_dong")
    agg_heatmap_dong = df.groupby(['행정동명', '시간대구분'])['생활인구수'].mean().reset_index()
    agg_heatmap_dong.to_sql("agg_heatmap_dong", conn, if_exists="replace", index=False)
    
    # 3-8. 행정동별 생활인구수 합계
    print(" - agg_dong")
    agg_dong = df.groupby(['시군구명', '행정동명'])['생활인구수'].sum().reset_index()
    agg_dong.to_sql("agg_dong", conn, if_exists="replace", index=False)
    
    # 3-9. 일자별 평균
    print(" - agg_daily")
    agg_daily = df.groupby(['시군구명', '일자'])['생활인구수'].mean().reset_index()
    agg_daily.to_sql("agg_daily", conn, if_exists="replace", index=False)
    
    # 3-10. 지도 시각화 최적화용 (시간대별 / 구별 / 동별 평균 생활인구)
    print(" - map_sig_hourly")
    map_sig_hourly = df.groupby(['시군구명', '시간대구분'])['생활인구수'].mean().reset_index()
    map_sig_hourly.to_sql("map_sig_hourly", conn, if_exists="replace", index=False)
    
    print(" - map_dong_hourly")
    map_dong_hourly = df.groupby(['adm_cd2_str', '행정동명', '시군구명', '시간대구분'])['생활인구수'].mean().reset_index()
    map_dong_hourly.to_sql("map_dong_hourly", conn, if_exists="replace", index=False)
    
    # DB 인덱스 생성하여 쿼리 성능 향상
    print("4. SQLite 인덱스 생성 중...")
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gender_gu ON agg_gender (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_age_gu ON agg_age (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hourly_gu ON agg_hourly (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekday_gu ON agg_weekday (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gender_age_gu ON agg_gender_age (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hourly_gender_gu ON agg_hourly_gender (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dong_gu ON agg_dong (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_gu ON agg_daily (시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_map_sig ON map_sig_hourly (시간대구분, 시군구명);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_map_dong ON map_dong_hourly (시간대구분, 시군구명);")
    
    conn.commit()
    conn.close()
    print("모든 사전 집계 데이터가 SQLite DB에 성공적으로 저장되었습니다!")

if __name__ == "__main__":
    build_database()
