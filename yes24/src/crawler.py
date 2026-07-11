import os
import time
import json
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

def clean_number(text):
    if not text:
        return 0
    cleaned = re.sub(r'[^\d]', '', text)
    return int(cleaned) if cleaned else 0

def clean_float(text):
    if not text:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', text)
    return float(cleaned) if cleaned else 0.0

def scrape_yes24_bestsellers(test_mode=False):
    base_url = "https://www.yes24.com/product/category/BestSellerContents"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Referer": "https://www.yes24.com/product/category/bestseller?categoryNumber=001001003&pageNumber=1&pageSize=24",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    params = {
        "categoryNumber": "001001003",
        "sumGb": "06",
        "sex": "A",
        "age": "255",
        "goodsTp": "0",
        "addOptionTp": "0",
        "excludeTp": "2",
        "pageSize": "24",
        "goodsStatGb": "06",
        "eBookTp": "0",
        "bestType": "YES24_BESTSELLER",
        "type": "",
        "saleYear": "0",
        "saleMonth": "0",
        "weekNo": "0",
        "saleDts": "",
        "viewMode": "",
        "freeYn": ""
    }
    
    all_books = []
    page = 1
    
    print("Yes24 베스트셀러 데이터 수집을 시작합니다...")
    if test_mode:
        print("[!] 테스트 모드가 활성화되었습니다. (1페이지만 수집하고 결과를 확인합니다.)")
    
    while True:
        params["pageNumber"] = str(page)
        print(f"[페이지 {page}] 수집 중...")
        
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            if response.status_code != 200:
                print(f"[오류] 페이지 {page} 요청 실패 (상태 코드: {response.status_code})")
                break
                
            soup = BeautifulSoup(response.text, "lxml")
            li_elements = soup.select("li")
            
            # 실제 도서 아이템인지 확인 (data-goods-no가 있는 li만 필터링)
            book_lis = [li for li in li_elements if li.has_attr("data-goods-no")]
            
            if not book_lis:
                print(f"[완료] 더 이상 수집할 도서 데이터가 없습니다. (마지막 페이지: {page-1})")
                break
                
            print(f"[페이지 {page}] {len(book_lis)}개의 도서가 발견되었습니다.")
            
            for li in book_lis:
                book_data = {}
                
                # 기본 ID 및 속성
                book_data["goods_no"] = li.get("data-goods-no", "").strip()
                book_data["statgb"] = li.get("data-statgb", "").strip()
                
                # 순위 (Rank)
                rank_el = li.select_one("em.ico.rank")
                book_data["rank"] = rank_el.get_text(strip=True) if rank_el else ""
                
                # 도서명 (Title)
                title_el = li.select_one("a.gd_name")
                book_data["title"] = title_el.get_text(strip=True) if title_el else ""
                
                # 부제목 (Subtitle)
                subtitle_el = li.select_one("span.gd_nameE")
                book_data["subtitle"] = subtitle_el.get_text(strip=True) if subtitle_el else ""
                
                # 특징 (Features)
                feature_els = li.select("span.gd_feature span.feature")
                book_data["features"] = "|".join([f.get_text(strip=True) for f in feature_els]) if feature_els else ""
                
                # 저자, 출판사, 출판일
                auth_el = li.select_one("span.info_auth")
                book_data["author_html"] = auth_el.get_text(strip=True).replace(" 저", "") if auth_el else ""
                
                pub_el = li.select_one("span.info_pub")
                book_data["publisher_html"] = pub_el.get_text(strip=True) if pub_el else ""
                
                date_el = li.select_one("span.info_date")
                book_data["publish_date"] = date_el.get_text(strip=True) if date_el else ""
                
                # 가격 정보
                sale_rate_el = li.select_one("span.txt_sale em.num")
                book_data["discount_rate"] = sale_rate_el.get_text(strip=True) if sale_rate_el else ""
                
                # 평점 및 수치
                sale_num_el = li.select_one("span.saleNum")
                if sale_num_el:
                    sale_index_text = sale_num_el.get_text(strip=True)
                    book_data["sale_index"] = clean_number(sale_index_text)
                else:
                    book_data["sale_index"] = 0
                    
                review_el = li.select_one("span.rating_rvCount a em.txC_blue")
                book_data["review_count"] = clean_number(review_el.get_text(strip=True)) if review_el else 0
                
                rating_el = li.select_one("span.rating_grade em.yes_b")
                book_data["rating"] = clean_float(rating_el.get_text(strip=True)) if rating_el else 0.0
                
                # 배송 정보
                deli_el = li.select_one("div.info_deli")
                book_data["delivery_info"] = deli_el.get_text(" ", strip=True) if deli_el else ""
                
                # 구매 혜택 (Benefit)
                benefit_el = li.select_one("dl.info_present dd a")
                book_data["benefit"] = benefit_el.get_text(strip=True) if benefit_el else ""
                
                # 태그 (Tags)
                tag_els = li.select("div.info_tag span.tag a")
                book_data["tags"] = "|".join([t.get_text(strip=True) for t in tag_els]) if tag_els else ""
                
                # 관련 상품 (Related Goods)
                rel_el = li.select_one("div.info_relG")
                book_data["related_goods"] = rel_el.get_text(" ", strip=True).replace("관련상품 :", "").strip() if rel_el else ""
                
                # 이미지 URL
                img_el = li.select_one("img.lazy")
                if img_el:
                    book_data["image_url"] = img_el.get("data-original") or img_el.get("src") or ""
                else:
                    book_data["image_url"] = ""
                
                # ORD_GOODS_OPT JSON 데이터 파싱
                opt_input = li.select_one("input[name='ORD_GOODS_OPT']")
                if opt_input and opt_input.get("value"):
                    try:
                        opt_val = opt_input.get("value")
                        opt_json = json.loads(opt_val)
                        
                        book_data["goods_sort_no"] = opt_json.get("goodsSortNo", "")
                        book_data["goods_sort_nm"] = opt_json.get("goodsSortNm", "")
                        book_data["author_json"] = opt_json.get("goodsAuth", "").replace(" 저", "").replace("<", "").replace(">", "").strip()
                        book_data["original_price"] = int(opt_json.get("shopPrice", 0))
                        book_data["sale_price"] = int(opt_json.get("salePrice", 0))
                        book_data["discount_price"] = int(opt_json.get("discountShopPrice", 0))
                    except Exception as je:
                        print(f"[경고] JSON 파싱 에러 (도서번호: {book_data['goods_no']}): {je}")
                        book_data["goods_sort_no"] = ""
                        book_data["goods_sort_nm"] = ""
                        book_data["author_json"] = ""
                        book_data["original_price"] = 0
                        book_data["sale_price"] = 0
                        book_data["discount_price"] = 0
                else:
                    book_data["goods_sort_no"] = ""
                    book_data["goods_sort_nm"] = ""
                    book_data["author_json"] = ""
                    book_data["original_price"] = 0
                    book_data["sale_price"] = 0
                    book_data["discount_price"] = 0
                
                # 저자와 가격 정리
                book_data["author"] = book_data["author_json"] if book_data["author_json"] else book_data["author_html"]
                
                # HTML 백업 가격 정리
                html_orig_price = clean_number(li.select_one("span.txt_num.dash em.yes_m").get_text(strip=True) if li.select_one("span.txt_num.dash em.yes_m") else "")
                html_sale_price = clean_number(li.select_one("strong.txt_num em.yes_b").get_text(strip=True) if li.select_one("strong.txt_num em.yes_b") else "")
                
                book_data["original_price"] = book_data["original_price"] if book_data["original_price"] > 0 else html_orig_price
                book_data["sale_price"] = book_data["sale_price"] if book_data["sale_price"] > 0 else html_sale_price
                
                # 임시 컬럼 삭제
                book_data.pop("author_html", None)
                book_data.pop("author_json", None)
                
                all_books.append(book_data)
            
            if test_mode:
                print("[!] 테스트 모드가 완료되어 페이지 1 수집 후 종료합니다.")
                break
                
            # 수집 속도 조절 및 다음 페이지
            time.sleep(1.2)
            page += 1
            
        except Exception as e:
            print(f"[오류] 페이지 {page} 수집 중 예외 발생: {e}")
            break
            
    # 데이터프레임 변환 및 저장
    if all_books:
        df = pd.DataFrame(all_books)
        
        # 순서 재정리
        columns_order = [
            "rank", "goods_no", "title", "subtitle", "author", "publisher_html", "publish_date",
            "original_price", "sale_price", "discount_rate", "discount_price", "sale_index",
            "rating", "review_count", "delivery_info", "benefit", "tags", "features",
            "goods_sort_no", "goods_sort_nm", "related_goods", "image_url"
        ]
        
        # 존재하지 않는 컬럼이 있을 수 있으므로 필터링
        columns_order = [c for c in columns_order if c in df.columns]
        df = df[columns_order]
        
        # 컬럼명 리네임
        if "publisher_html" in df.columns:
            df.rename(columns={"publisher_html": "publisher"}, inplace=True)
        
        if test_mode:
            print("\n=== [테스트 수집 데이터 샘플 (상위 3개)] ===")
            print(df[["rank", "title", "author", "sale_price"]].head(3))
            print("======================================\n")
            return True, df
        else:
            os.makedirs("yes24/data", exist_ok=True)
            csv_path = "yes24/data/yes24_bestsellers_001001003.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"\n[성공] 총 {len(df)}개의 도서 데이터를 수집하여 '{csv_path}'에 저장했습니다.")
            return True, df
    else:
        print("[실패] 수집된 도서 데이터가 없습니다.")
        return False, None

if __name__ == "__main__":
    # 1단계: 테스트 수집 실행
    success, test_df = scrape_yes24_bestsellers(test_mode=True)
    
    if success and test_df is not None and len(test_df) > 0:
        print("\n[알림] 1페이지 테스트 수집이 정상적으로 성공하였습니다.")
        print("[알림] 이어서 전체 페이지 수집을 진행합니다...\n")
        time.sleep(1.0)
        # 2단계: 전체 페이지 수집 실행
        scrape_yes24_bestsellers(test_mode=False)
    else:
        print("[오류] 1페이지 테스트 수집에 실패하여 전체 수집을 진행하지 않습니다.")
