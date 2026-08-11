import os
import requests
import pandas as pd
import time

def crawl_kyobo_bestseller_all():
    # 1) HTTP 요청 정보 설정
    url = "https://store.kyobobook.co.kr/api/gw/best/v2/best-seller/online"
    
    # 2) HTTP 헤더 정보
    headers = {
        "referer": "https://store.kyobobook.co.kr/category/domestic/33/best?page=1&per=50",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-api-gw-key": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..i35xkkCOngvXqCRx.0CqToQel6sj5d0qOS2ftoDu37jRwb0vtQwMBd1e_G1ynl7KUrTrH_qPJnygVpkc0tExt4BUX_pJ4RepB5QsxWmKLjC8tEuMELKG8SvRLEVn6ambMnSmDaJ85mLbGtHcM-zFiDBzi.3y1-RnxGHFxeLNMK2dWZoQ"
    }
    
    page = 1
    parsed_books = []
    
    print("교보문고 베스트셀러 전체 데이터 수집 시작...")
    
    while True:
        # 3) Payload 정보 (Query Parameters)
        params = {
            "page": page,
            "per": 20,
            "saleCmdtClstCode": "33",
            "soldOutExcludeYn": "N",
            "saleCmdtDsplDvsnCode": "KOR",
            "period": "002",
            "dsplDvsnCode": "001",
            "dsplTrgtDvsnCode": "004"
        }
        
        print(f"{page} 페이지 요청 중...")
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"{page} 페이지 요청 실패. 상태 코드: {response.status_code}")
                break
                
            data = response.json()
            best_seller_list = data.get("data", {}).get("bestSeller", [])
            
            # 수집된 도서 데이터가 없으면 마지막 페이지에 도달한 것이므로 루프 중단
            if not best_seller_list:
                print(f"더 이상 수집할 데이터가 없습니다. (마지막 페이지: {page - 1})")
                break
                
            for item in best_seller_list:
                rank = item.get("prstRnkn")
                product_info = item.get("product", {}).get("productInfo", {})
                price_info = item.get("product", {}).get("priceInfo", {})
                
                title = product_info.get("cmdtName")
                author = product_info.get("chrcName")
                publisher = product_info.get("pbcmName")
                release_date = product_info.get("rlseDate")
                isbn = product_info.get("cmdtcode")
                
                original_price = price_info.get("saleCmdtPrce")
                sale_price = price_info.get("saleCmdtSapr")
                discount_rate = price_info.get("saleCmdtPrceDscnRate")
                
                book_data = {
                    "순위": rank,
                    "도서명": title,
                    "저자": author,
                    "출판사": publisher,
                    "출판일": release_date,
                    "정가": original_price,
                    "할인가": sale_price,
                    "할인율": discount_rate,
                    "ISBN": isbn
                }
                parsed_books.append(book_data)
                
            print(f"{page} 페이지 수집 완료 (누적 도서 수: {len(parsed_books)}개)")
            page += 1
            
            # 서버 과부하 방지를 위한 지연(0.5초) 추가
            time.sleep(0.5)
            
        except Exception as e:
            print(f"오류 발생: {e}")
            break
            
    if not parsed_books:
        print("수집 완료된 데이터가 없습니다.")
        return
        
    # DataFrame 생성 및 CSV 저장
    df = pd.DataFrame(parsed_books)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 전체 수집 파일은 kyobo_bestseller_all.csv 로 저장
    output_path = os.path.join(output_dir, "kyobo_bestseller_all.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print("\n==================================================")
    print(f"수집 완료! 총 {page - 1}개 페이지에서 {len(df)}개의 도서 데이터를 수집했습니다.")
    print(f"저장 경로: {output_path}")
    print("==================================================")

if __name__ == "__main__":
    crawl_kyobo_bestseller_all()

