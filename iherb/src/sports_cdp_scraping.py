import urllib.request
import json
import asyncio
import websockets
import os
import sys
import sqlite3
import time
from bs4 import BeautifulSoup
import pandas as pd

# 인코딩 설정 (윈도우 콘솔 한글 깨짐 방지)
sys.stdout.reconfigure(encoding='utf-8')

# DB 파일 경로 및 CSV 백업 경로 (상대 경로 사용)
DB_PATH = "iherb/data/sports_products.db"
CSV_PATH = "iherb/data/sports_products_1_10.csv"

def init_db(db_path=DB_PATH):
    """
    SQLite 데이터베이스 및 테이블을 초기화합니다.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # sports_products 테이블 생성 (productId를 PK로 하여 중복 방지)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sports_products (
            productId TEXT PRIMARY KEY,
            brandName TEXT,
            displayName TEXT,
            discountPrice INTEGER,
            position INTEGER,
            rating REAL,
            reviewCount INTEGER,
            imageUrl TEXT,
            collectedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"데이터베이스 초기화 완료: {db_path}")

def save_to_db(products, db_path=DB_PATH):
    """
    수집한 상품 리스트를 SQLite DB에 저장(INSERT OR REPLACE)합니다.
    """
    if not products:
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    for p in products:
        try:
            # discountPrice, position, reviewCount 등은 데이터 형식을 숫자로 변환하여 저장
            price = int(p["discountPrice"]) if p["discountPrice"].isdigit() else None
            pos = int(p["position"]) if p["position"].isdigit() else None
            rating = float(p["rating"]) if p["rating"] else None
            reviews = int(p["reviewCount"]) if p["reviewCount"].isdigit() else None

            cursor.execute("""
                INSERT OR REPLACE INTO sports_products 
                (productId, brandName, displayName, discountPrice, position, rating, reviewCount, imageUrl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["productId"],
                p["brandName"],
                p["displayName"],
                p["discountPrice"],
                pos,
                rating,
                reviews,
                p["imageUrl"]
            ))
            inserted_count += 1
        except Exception as e:
            print(f"DB 저장 중 에러 발생 (상품 ID {p.get('productId')}): {e}")

    conn.commit()
    conn.close()
    return inserted_count

async def fetch_html_via_cdp(page):
    """
    원격 디버깅 포트(9222)에 접속하여 지정된 페이지의 Ajax HTML을 가져옵니다.
    """
    try:
        req = urllib.request.Request("http://127.0.0.1:9222/json")
        with urllib.request.urlopen(req) as response:
            tabs = json.loads(response.read().decode())
    except Exception as e:
        print("디버깅 포트 조회 실패. 크롬이 9222 포트로 켜져 있는지 확인하세요:", e)
        return None

    # iHerb sports 카테고리 탭 찾기
    target_tab = None
    for tab in tabs:
        if tab.get("type") == "page" and "sports" in tab.get("url", ""):
            target_tab = tab
            break

    if not target_tab:
        for tab in tabs:
            if tab.get("type") == "page":
                target_tab = tab
                break

    if not target_tab:
        print("활성화된 브라우저 페이지 탭을 찾을 수 없습니다.")
        return None

    ws_url = target_tab.get("webSocketDebuggerUrl")

    async with websockets.connect(ws_url) as websocket:
        # fetch 스크립트 실행 (헤더 모사 포함)
        js_code = f"""
        fetch('https://kr.iherb.com/c/sports?p={page}&isAjax=true', {{
            headers: {{
                'x-requested-with': 'XMLHttpRequest'
            }}
        }}).then(r => r.text())
        """

        payload = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": js_code,
                "awaitPromise": True,
                "returnByValue": True
            }
        }

        await websocket.send(json.dumps(payload))
        response_str = await websocket.recv()
        response_json = json.loads(response_str)
        
        result = response_json.get("result", {}).get("result", {})
        if "value" in result:
            return result["value"]
        else:
            print(f"{page}페이지 에러 발생:", result.get("description", "알 수 없는 오류"))
            return None

def parse_html(html_content):
    """
    HTML 콘텐츠에서 상품 리스트 정보를 추출합니다.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "lxml")
    product_cells = soup.select("div.product-cell-container")
    products = []
    
    for cell in product_cells:
        link_tag = cell.select_one("a.absolute-link.product-link")
        if not link_tag:
            continue

        product_id = link_tag.get("data-product-id", "").strip()
        brand = link_tag.get("data-ga-brand-name", "").strip()
        price_val = link_tag.get("data-ga-discount-price", "").strip()
        title = link_tag.get("title", "").strip()
        position = link_tag.get("data-ga-product-position", "").strip()

        # 이미지
        img_tag = cell.select_one("img")
        image_url = img_tag.get("src", "").strip() if img_tag else ""

        # 평점 및 리뷰 수 추출
        rating_tag = cell.select_one("div.rating a.stars")
        rating_text = rating_tag.get("title", "").strip() if rating_tag else ""
        
        rating_val = ""
        review_count = ""
        if rating_text:
            if "/" in rating_text:
                rating_val = rating_text.split("/")[0].strip()
            if "-" in rating_text:
                review_part = rating_text.split("-")[1].strip()
                review_count = review_part.replace("구매후기", "").replace(",", "").strip()

        products.append({
            "productId": product_id,
            "brandName": brand,
            "displayName": title,
            "discountPrice": price_val,
            "position": position,
            "rating": rating_val,
            "reviewCount": review_count,
            "imageUrl": image_url
        })

    return products

def export_db_to_csv(db_path=DB_PATH, csv_path=CSV_PATH):
    """
    최종 저장 완료된 SQLite DB 데이터를 확인용 CSV로 내보냅니다.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM sports_products ORDER BY collectedAt DESC", conn)
    conn.close()
    
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"최종 DB 데이터를 CSV로 백업 완료: {csv_path} (총 {len(df)}개 행)")

def main():
    init_db()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    total_inserted = 0
    print("1페이지부터 10페이지까지의 수집 작업을 시작합니다...")
    
    for page in range(1, 11):
        print(f"\n--- {page} 페이지 수집 중 ---")
        try:
            # 1. HTML 데이터 수집
            html_content = loop.run_until_complete(fetch_html_via_cdp(page))
            if not html_content:
                print(f"{page} 페이지의 HTML 데이터를 가져오지 못했습니다. 건너뜁니다.")
                continue
            
            # 2. 데이터 파싱
            products = parse_html(html_content)
            print(f"파싱 완료: {len(products)}개의 상품 데이터를 추출했습니다.")
            
            if not products:
                print(f"{page} 페이지에 추출된 상품 데이터가 없습니다.")
                continue
                
            # 3. SQLite DB 저장 (매 페이지마다 즉시 커밋)
            saved_count = save_to_db(products)
            total_inserted += saved_count
            print(f"SQLite DB에 {saved_count}개 상품 저장 완료 (누적: {total_inserted}개)")
            
        except Exception as e:
            print(f"{page} 페이지 작업 중 예외 발생: {e}")
            
        # 서버 부하 및 레이트 리밋 완화를 위한 대기 시간 추가
        time.sleep(1.5)
        
    print("\n==========================================")
    print("수집 완료! 최종 데이터 통계를 조회합니다.")
    # 최종 DB 데이터 CSV 변환 및 통계 출력
    export_db_to_csv()
    print("==========================================")

if __name__ == "__main__":
    main()
