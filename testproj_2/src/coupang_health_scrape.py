'''Coupang 건강기능식품 데이터 수집 스크립트

- Playwright를 사용해 동적 페이지를 로드하고, 제품 리스트를 파싱합니다.
- 페이지가 정상적으로 로드되면 전체 페이지를 순회합니다.
- 수집된 데이터를 SQLite DB (data/health_products.db) 에 저장합니다.
'''

import asyncio
import os
import sqlite3
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://www.coupang.com/np/campaigns/6585"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(OUTPUT_DIR, "health_products.db")

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def init_db():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            rating REAL,
            review_count INTEGER,
            url TEXT
        )
        """
    )
    conn.commit()
    conn.close()

async def fetch_page(page, page_num: int):
    url = f"{BASE_URL}?page={page_num}"
    await page.goto(url, wait_until="networkidle")
    # 쿠팡은 스크립트 로딩이 있기에 잠시 대기
    await page.wait_for_timeout(2000)
    return await page.content()

def parse_products(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for prod in soup.select("li.search-product"):
        name_tag = prod.select_one("div.name")
        price_tag = prod.select_one("strong.price-value")
        rating_tag = prod.select_one("em.rating")
        review_tag = prod.select_one("span.rating-total-count")
        link_tag = prod.select_one("a.search-product-link")
        name = name_tag.get_text(strip=True) if name_tag else ""
        price = price_tag.get_text(strip=True) if price_tag else ""
        rating = None
        if rating_tag:
            rating_text = rating_tag.get_text(strip=True).replace(',', '.')
            try:
                rating = float(rating_text)
            except ValueError:
                rating = None
        review_count = 0
        if review_tag:
            rc = review_tag.get_text(strip=True).replace('(', '').replace(')', '')
            try:
                review_count = int(rc)
            except ValueError:
                review_count = 0
        url = f"https://www.coupang.com{link_tag['href']}" if link_tag and link_tag.has_attr('href') else ""
        items.append({"name": name, "price": price, "rating": rating, "review_count": review_count, "url": url})
    return items

async def main():
    init_db()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # 첫 페이지 검증
        first_html = await fetch_page(page, 1)
        products = parse_products(first_html)
        if not products:
            print("[WARN] Failed to find products on first page. Check page structure.")
            await browser.close()
            return
        print(f"[INFO] 첫 페이지에서 제품 {len(products)}개 추출")
        # 전체 페이지 수 추출 (예: 페이지네이션 마지막 번호)
        soup = BeautifulSoup(first_html, "html.parser")
        pages = [int(a.get_text()) for a in soup.select("a[data-page-number]") if a.get_text().isdigit()]
        total_pages = max(pages) if pages else 1
        print(f"[INFO] 전체 페이지 수: {total_pages}")
        all_products = []
        for pn in range(1, total_pages + 1):
            html = await fetch_page(page, pn) if pn != 1 else first_html
            all_products.extend(parse_products(html))
            print(f"[INFO] 페이지 {pn}/{total_pages} 수집 완료 (현재 총 {len(all_products)}개)")
        await browser.close()
        # CSV 파일 저장
        csv_path = os.path.join(OUTPUT_DIR, "health_products.csv")
        df = pd.DataFrame(all_products)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[SUCCESS] 전체 {len(all_products)}개의 제품이 {csv_path} 로 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())
