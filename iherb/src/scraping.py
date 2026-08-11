import json
import sys
import pandas as pd
import requests
import os
import time
import math

# 표준 출력을 UTF-8로 설정하여 윈도우 콘솔 한글 깨짐 및 인코딩 에러 방지
sys.stdout.reconfigure(encoding='utf-8')

def fetch_sports_specials_page(page=1, page_size=18):
    """
    iHerb 스포츠 Specials API로부터 특정 페이지의 상품 데이터를 수집합니다.
    """
    url = "https://catalog.app.iherb.com/category/sports/specials"
    params = {
        "isMobile": "false",
        "page": str(page),
        "pageSize": str(page_size)
    }
    headers = {
        "origin": "https://kr.iherb.com",
        "referer": "https://kr.iherb.com/",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API 요청 실패 (페이지: {page}). 상태 코드: {response.status_code}")
            return None
    except Exception as e:
        print(f"API 요청 중 예외 발생 (페이지: {page}): {str(e)}")
        return None

def fetch_all_sports_specials(page_size=18):
    """
    모든 페이지의 상품 데이터를 수집합니다.
    (products가 비어있거나 모든 상품이 중복될 때까지 계속 페이지를 넘기며 수집합니다.)
    """
    all_products = []
    seen_product_ids = set()
    page = 1
    
    print("전체 페이지 데이터 수집을 시작합니다...")
    while True:
        print(f"페이지 {page} 요청 중...")
        page_data = fetch_sports_specials_page(page=page, page_size=page_size)
        
        if not page_data:
            print(f"{page}페이지 데이터를 가져오지 못했습니다. 수집을 종료합니다.")
            break
            
        products = page_data.get("products", [])
        if not products:
            print(f"{page}페이지에 상품 데이터가 없습니다. 수집을 완료합니다.")
            break
            
        # 이번 페이지에서 새로 추가된 상품 필터링
        new_products_count = 0
        for p in products:
            p_id = p.get("productId")
            if p_id and p_id not in seen_product_ids:
                seen_product_ids.add(p_id)
                all_products.append(p)
                new_products_count += 1
                
        print(f"{page}페이지 수집 완료: 가져온 상품 {len(products)}개 중 신규 상품 {new_products_count}개 (누적 수집: {len(all_products)}개)")
        
        # 만약 이번 페이지에서 신규 상품이 하나도 없다면 마지막 페이지를 지난 것이므로 종료
        if new_products_count == 0:
            print("신규 상품이 더 이상 존재하지 않습니다. 수집을 완료합니다.")
            break
            
        page += 1
        time.sleep(1) # 서버 부하 방지를 위해 딜레이 추가
        
    print(f"전체 수집 완료! 중복 없는 총 {len(all_products)}개의 상품 데이터를 가져왔습니다.")
    return all_products

def save_to_csv(products, output_path="iherb/data/sports_specials.csv"):
    """
    수집한 상품 리스트를 CSV 파일로 저장합니다.
    """
    if not products:
        print("저장할 데이터가 없습니다.")
        return

    # pandas의 json_normalize를 활용해 중첩 딕셔너리를 평탄화하여 데이터프레임 생성
    df_normalized = pd.json_normalize(products)

    # 데이터 저장 폴더가 존재하는지 확인
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 한글 깨짐 방지를 위해 utf-8-sig 인코딩으로 저장
    df_normalized.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"데이터를 성공적으로 CSV로 저장했습니다. 저장 경로: {output_path}")
    print(f"데이터 프레임 형태: {df_normalized.shape} (행, 열)")
    print("\n상위 5개 데이터 컬럼 예시:")
    print(df_normalized[['productId', 'displayName', 'brandName', 'listPrice', 'discountPrice']].head())

if __name__ == "__main__":
    # 안전하게 18개씩 전체 데이터를 가져옵니다.
    all_products = fetch_all_sports_specials(page_size=18)
    save_to_csv(all_products)
