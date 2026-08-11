import os
import time
import re
import pandas as pd
from curl_cffi import requests
from bs4 import BeautifulSoup

def collect_iherb_specials():
    url = "https://catalog.app.iherb.com/category/supplements/specials"
    page_size = 18
    
    session = requests.Session()
    headers = {
        "origin": "https://kr.iherb.com",
        "referer": "https://kr.iherb.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/149.0.0.0 Safari/537.36"
    }
    
    print("iHerb 특가 상품 전체 데이터 수집 시작 (마지막 페이지까지)...")
    
    all_products = []
    page = 1
    max_safe_pages = 1000
    
    try:
        while page <= max_safe_pages:
            print(f"iHerb {page} 페이지 데이터 요청 중 (pageSize: {page_size})...")
            params = {
                "isMobile": "false",
                "page": page,
                "pageSize": page_size
            }
            
            if page > 1:
                time.sleep(1.0)  # 지연시간 1초
                
            retry_count = 3
            response = None
            while retry_count > 0:
                try:
                    response = session.get(url, params=params, headers=headers, impersonate="chrome120", timeout=30)
                    if response.status_code == 200:
                        break
                    else:
                        print(f"iHerb {page}페이지 요청 실패 (상태 코드: {response.status_code}). 5초 대기 후 {retry_count}회 재시도 남음...")
                        time.sleep(5)
                except Exception as e:
                    print(f"iHerb {page}페이지 요청 중 에러 발생: {e}. 5초 대기 후 {retry_count}회 재시도 남음...")
                    time.sleep(5)
                
                retry_count -= 1
            
            if response is None or response.status_code != 200:
                print(f"iHerb {page}페이지 최종 수집 실패. 수집을 조기 종료하고 기존 데이터만 저장합니다.")
                break
                
            data = response.json()
            products = data.get("products", [])
            
            if not products:
                print(f"iHerb {page}페이지에 데이터가 없습니다. 수집을 종료합니다.")
                break
                
            all_products.extend(products)
            print(f"iHerb {page}페이지 수집 완료: {len(products)}개 상품 추가 (누적: {len(all_products)}개)")
            
            if len(products) < page_size:
                print("iHerb 마지막 페이지에 도달했습니다. 수집을 종료합니다.")
                break
                
            page += 1
            
    except Exception as e:
        print(f"iHerb 데이터 수집 루프 중 중명세 에러 발생: {e}")
        
    if all_products:
        try:
            print(f"iHerb 데이터 저장 프로세스 시작. 수집 원본 로우 수: {len(all_products)}개")
            df = pd.DataFrame(all_products)
            
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['productId'], keep='first')
            after_dedup = len(df)
            print(f"iHerb 중복 제거 처리 완료: {before_dedup}개 -> {after_dedup}개 고유 상품")
            
            key_columns = [
                'productId', 'displayName', 'brandName', 'listPrice', 
                'discountPrice', 'rating', 'ratingCount', 'url', 'isOutOfStock'
            ]
            
            existing_keys = [col for col in key_columns if col in df.columns]
            other_keys = [col for col in df.columns if col not in key_columns]
            df = df[existing_keys + other_keys]
            
            output_dir = os.path.join("testproj_2", "data")
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, "specials_products.csv")
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"iHerb 데이터 수집 및 고유 데이터 CSV 저장 완료: {output_path}")
        except Exception as save_err:
            print(f"iHerb 데이터 저장 중 오류 발생: {save_err}")
    else:
        print("iHerb 저장할 데이터가 없습니다.")

def classify_formulation(name):
    name_lower = name.lower()
    if '구미' in name_lower or '젤리' in name_lower:
        return '구미'
    elif '캡슐' in name_lower or '소프트젤' in name_lower or '연질' in name_lower:
        return '캡슐'
    elif '정제' in name_lower or '정' in name_lower or '알약' in name_lower or '타블렛' in name_lower:
        return '정제'
    elif '파우더' in name_lower or '분말' in name_lower or '가루' in name_lower:
        return '파우더'
    elif '액상' in name_lower or '드롭' in name_lower or '앰플' in name_lower or '물약' in name_lower:
        return '액상'
    elif '샷' in name_lower:
        return '샷'
    elif '스틱' in name_lower:
        return '스틱'
    else:
        return '정제'

def classify_age(name):
    if '키즈' in name or '어린이' in name or '아동' in name:
        return '어린이'
    elif '실버' in name or '시니어' in name or '50+' in name:
        return '장년층'
    elif '임산부' in name or '임신' in name:
        return '임산부'
    elif '남성' in name or '포맨' in name:
        return '남성'
    elif '여성' in name or '포우먼' in name:
        return '여성'
    else:
        return '전체'

def parse_rating_and_reviews(point_el):
    if not point_el:
        return 0.0, 0
    
    rating = 0.0
    span_point = point_el.select_one(".point")
    if span_point and span_point.get("style"):
        style_str = span_point.get("style")
        match = re.search(r"width:\s*([\d.]+)%", style_str)
        if match:
            width_val = float(match.group(1))
            rating = round(width_val / 20.0, 1)
            
    review_count = 0
    text = point_el.get_text()
    match_rev = re.search(r"\(([\d,++]+)\)", text)
    if match_rev:
        rev_str = match_rev.group(1).replace(",", "").replace("+", "")
        if rev_str.isdigit():
            review_count = int(rev_str)
            
    return rating, review_count

def collect_olive_vitamins():
    url = "https://www.oliveyoung.co.kr/store/display/getMCategoryList.do"
    
    session = requests.Session()
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.oliveyoung.co.kr/store/main/main.do",
        "cache-control": "no-cache",
        "pragma": "no-cache"
    }
    
    print("올리브영 비타민 상품 데이터 수집 시작...")
    
    all_products = []
    page = 1
    max_pages = 25
    
    try:
        while page <= max_pages:
            print(f"올리브영 {page} 페이지 요청 중...")
            params = {
                "dispCatNo": "100000200010015",
                "fltDispCatNo": "",
                "prdSort": "01",
                "pageIdx": str(page),
                "rowsPerPage": "24",
                "searchTypeSort": "btn_thumb",
                "plusButtonFlag": "N",
                "isLoginCnt": "",
                "trackingCd": "Cat100000200010015_Small"
            }
            
            if page > 1:
                time.sleep(4.0)  # 지연시간을 4초로 상향하여 차단 완화
                
            retry_count = 5  # 재시도를 5회로 상향
            response = None
            while retry_count > 0:
                try:
                    response = session.get(url, params=params, headers=headers, impersonate="chrome120", timeout=25)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:
                        print(f"올리브영 {page}페이지 요청 실패 (429 Too Many Requests). 20초 대기 후 {retry_count}회 재시도 남음...")
                        time.sleep(20)  # 429 차단 회복을 위한 20초 대기
                    else:
                        print(f"올리브영 {page}페이지 요청 실패 (상태 코드: {response.status_code}). 8초 대기 후 {retry_count}회 재시도 남음...")
                        time.sleep(8)
                except Exception as e:
                    print(f"올리브영 {page}페이지 요청 에러: {e}. 8초 대기 후 {retry_count}회 재시도 남음...")
                    time.sleep(8)
                
                retry_count -= 1
                
            if response is None or response.status_code != 200:
                print(f"올리브영 {page}페이지 최종 수집 실패. 수집을 조기 종료하고 기존 데이터만 저장합니다.")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            prd_items = soup.select("ul.cate_prd_list > li")
            
            if not prd_items:
                print(f"올리브영 {page}페이지에 상품 목록이 존재하지 않습니다. 수집을 종료합니다.")
                break
                
            print(f"올리브영 {page}페이지에서 {len(prd_items)}개 상품 발견.")
            
            for item in prd_items:
                brand_el = item.select_one(".tx_brand")
                brand = brand_el.get_text(strip=True) if brand_el else "미지정"
                
                name_el = item.select_one(".tx_name")
                name = name_el.get_text(strip=True) if name_el else ""
                
                if not name:
                    continue
                
                price_el = item.select_one(".tx_cur")
                price_text = price_el.get_text(strip=True) if price_el else "0"
                price_num = int(re.sub(r"[^\d]", "", price_text)) if re.sub(r"[^\d]", "", price_text) else 0
                
                point_el = item.select_one(".prd_point_area")
                rating, review_count = parse_rating_and_reviews(point_el)
                
                formulation = classify_formulation(name)
                target_age = classify_age(name)
                
                soldout_el = item.select_one(".soldout") or item.select_one(".thumb_flag.soldout")
                sales_status = "품절" if soldout_el or "sold" in str(item).lower() else "판매중"
                
                product_data = {
                    "플랫폼": "올리브영",
                    "브랜드": brand,
                    "상품명": name,
                    "카테고리": "비타민",
                    "제형": formulation,
                    "가격": price_num,
                    "평점": rating,
                    "리뷰 수": review_count,
                    "후기 키워드": "",
                    "타깃 연령": target_age,
                    "판매상태": sales_status,
                    "수집일": "2026-06-20"
                }
                
                all_products.append(product_data)
                
            page += 1
            
    except Exception as e:
        print(f"올리브영 루프 중 중명세 에러 발생: {e}")
        
    if all_products:
        try:
            print(f"올리브영 데이터 저장 프로세스 시작. 총 수집 로우 수: {len(all_products)}개")
            df = pd.DataFrame(all_products)
            
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['상품명'], keep='first')
            after_dedup = len(df)
            print(f"올리브영 중복 상품 제거 완료: {before_dedup}개 -> {after_dedup}개 고유 상품")
            
            output_dir = os.path.join("testproj_2", "data")
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, "olive_vitamins.csv")
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"올리브영 상품 데이터 CSV 저장 완료: {output_path}")
        except Exception as save_err:
            print(f"올리브영 데이터 저장 중 오류 발생: {save_err}")
    else:
        print("올리브영 저장할 데이터가 없습니다.")

def collect_olive_probio():
    url = "https://www.oliveyoung.co.kr/store/display/getMCategoryList.do"
    
    session = requests.Session()
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": "https://www.oliveyoung.co.kr/store/main/main.do",
        "cache-control": "no-cache",
        "pragma": "no-cache"
    }
    
    print("올리브영 유산균 상품 데이터 수집 시작...")
    
    all_products = []
    page = 1
    max_pages = 100
    
    try:
        while page <= max_pages:
            print(f"올리브영 {page} 페이지 요청 중...")
            params = {
                "dispCatNo": "100000200010024",
                "fltDispCatNo": "",
                "prdSort": "01",
                "pageIdx": str(page),
                "rowsPerPage": "24",
                "searchTypeSort": "btn_thumb",
                "plusButtonFlag": "N",
                "isLoginCnt": "",
                "trackingCd": "Cat100000200010024_Small"
            }
            
            if page > 1:
                time.sleep(4.0)  # 지연시간을 4초로 상향하여 차단 완화
                
            retry_count = 5  # 재시도를 5회로 상향
            response = None
            while retry_count > 0:
                try:
                    response = session.get(url, params=params, headers=headers, impersonate="chrome120", timeout=25)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:
                        print(f"올리브영 {page}페이지 요청 실패 (429 Too Many Requests). 20초 대기 후 {retry_count}회 재시도 남음...")
                        time.sleep(20)  # 429 차단 회복을 위한 20초 대기
                    else:
                        print(f"올리브영 {page}페이지 요청 실패 (상태 코드: {response.status_code}). 8초 대기 후 {retry_count}회 재시도 남음...")
                        time.sleep(8)
                except Exception as e:
                    print(f"올리브영 {page}페이지 요청 에러: {e}. 8초 대기 후 {retry_count}회 재시도 남음...")
                    time.sleep(8)
                
                retry_count -= 1
                
            if response is None or response.status_code != 200:
                print(f"올리브영 {page}페이지 최종 수집 실패. 수집을 조기 종료하고 기존 데이터만 저장합니다.")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            prd_items = soup.select("ul.cate_prd_list > li")
            
            if not prd_items:
                print(f"올리브영 {page}페이지에 상품 목록이 존재하지 않습니다. 수집을 종료합니다.")
                break
                
            print(f"올리브영 {page}페이지에서 {len(prd_items)}개 상품 발견.")
            
            for item in prd_items:
                brand_el = item.select_one(".tx_brand")
                brand = brand_el.get_text(strip=True) if brand_el else "미지정"
                
                name_el = item.select_one(".tx_name")
                name = name_el.get_text(strip=True) if name_el else ""
                
                if not name:
                    continue
                
                price_el = item.select_one(".tx_cur")
                price_text = price_el.get_text(strip=True) if price_el else "0"
                price_num = int(re.sub(r"[^\d]", "", price_text)) if re.sub(r"[^\d]", "", price_text) else 0
                
                point_el = item.select_one(".prd_point_area")
                rating, review_count = parse_rating_and_reviews(point_el)
                
                formulation = classify_formulation(name)
                target_age = classify_age(name)
                
                soldout_el = item.select_one(".soldout") or item.select_one(".thumb_flag.soldout")
                sales_status = "품절" if soldout_el or "sold" in str(item).lower() else "판매중"
                
                product_data = {
                    "플랫폼": "올리브영",
                    "브랜드": brand,
                    "상품명": name,
                    "카테고리": "유산균",
                    "제형": formulation,
                    "가격": price_num,
                    "평점": rating,
                    "리뷰 수": review_count,
                    "후기 키워드": "",
                    "타깃 연령": target_age,
                    "판매상태": sales_status,
                    "수집일": "2026-06-20"
                }
                
                all_products.append(product_data)
                
            page += 1
            
    except Exception as e:
        print(f"올리브영 루프 중 중명세 에러 발생: {e}")
        
    if all_products:
        try:
            print(f"올리브영 데이터 저장 프로세스 시작. 총 수집 로우 수: {len(all_products)}개")
            df = pd.DataFrame(all_products)
            
            before_dedup = len(df)
            df = df.drop_duplicates(subset=['상품명'], keep='first')
            after_dedup = len(df)
            print(f"올리브영 중복 상품 제거 완료: {before_dedup}개 -> {after_dedup}개 고유 상품")
            
            output_dir = os.path.join("testproj_2", "data")
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, "olive_probio.csv")
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"올리브영 상품 데이터 CSV 저장 완료: {output_path}")
        except Exception as save_err:
            print(f"올리브영 데이터 저장 중 오류 발생: {save_err}")
    else:
        print("올리브영 저장할 데이터가 없습니다.")

if __name__ == "__main__":
    # 올리브영 유산균 데이터를 단독으로 수집하여 olive_probio.csv를 생성 및 업데이트합니다.
    collect_olive_probio()
