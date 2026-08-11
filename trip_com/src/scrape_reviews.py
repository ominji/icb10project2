# trip_com/src/scrape_reviews.py
"""
호텔 리뷰 수집 스크립트

목표:
1. 첫 페이지에서 리뷰 제목, 내용, 별점이 정상적으로 추출되는지 확인
2. 확인이 성공하면 전체 페이지를 순회해 모든 리뷰를 수집
3. 결과를 CSV 파일로 저장 (trip_com/data/reviews.csv)

필요한 패키지:
- requests
- beautifulsoup4
- pandas (CSV 저장용)
- tqdm (진행 표시용, 선택 사항)

※ scrapling 라이브러리를 사용하려면 `pip install scrapling` 후 아래와 같이 사용 가능하지만,
   여기서는 일반적인 requests + BeautifulSoup 조합으로 구현했습니다.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import os
import sqlite3

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------
BASE_URL = "https://kr.trip.com/hotels/detail/"
# 대상 호텔 URL (쿼리 파라미터 포함)
HOTEL_URL = "https://kr.trip.com/hotels/detail/?cityEnName=Seoul&cityId=274&hotelId=58635410&checkIn=2026-06-22&checkOut=2026-06-23&adult=2&children=0&crn=1&ages=&curr=KRW&barcurr=KRW&hoteluniquekey=H4sIAAAAAAAA_-M6wcTFJMEkdZCJo3XuntdsQoxGBiv5La5mOR7-qhHTX1Tg4Nn6OnCHnGSRQwBPIQMYuDjMYJz08pf0RkbNmP5DXzOsHHYwMp1gbGtmWcD050OzwykWZo6XepdYDjFGVytlp1YqWZnoKJVkluSkKlkpvd7W8GoDCL3ZOeNNyw4lHaWU1OJkoASQlZibX5pXAmSbWloa6xkYAIVKEis8U8AGJCfmJJfmJJakhlQWAA0y01HKLHYuKcosCErNzSwpSQWqSkvMKU4FiQelFgNlksGCSn5AY4qgApn5eRDtBihiYYk5pakQNwAtdEuF2mFYG_uIhSk69hMLwy-gn1a5NrEydLEyTGJl4QB6dhcrR4iRc6CHka7hBdYNJ1ikFA0NDAyMTE2NzHUNEi0Tk40NknRNLE0NjE11DY1NDQ0szDR65y7_8c7YSPYUo5ShuamJpYWpubG5oaWhnqWFuXmeYXBOkkdOiQdjEJuloYWbi1uUDRezd1C4YMam-nlsPEX2UiCeIoynBeIZwniBsjtV9sYFuNpHwkSSWLPzdb2DMlaKFjA2MDJ1MXILMHowRjBWAHmMqxgZNjAy7mD8DwOMrxhB5gEA1rgozBECAAA&masterhotelid_tracelogid=100025527-0a9ac30b-495035-1351086&detailFilters=17%7C1%7E17%7E1*80%7C2%7C1%7E80%7E2*29%7C1%7E29%7E1%7C2&hotelType=normal&display=incavg&subStamp=714&isCT=true&isFlexible=F&locale=ko-KR"

# 저장 경로 (relative)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "reviews.csv")

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def fetch_page(url: str) -> str:
    """주어진 URL의 HTML을 반환한다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def parse_reviews(html: str) -> list:
    """HTML에서 리뷰 정보를 파싱한다.
    반환값은 딕셔너리 리스트이며, 각 딕셔너리는
    {
        "title": 리뷰 제목,
        "content": 리뷰 내용,
        "rating": 별점 (정수 1~5)
    } 형태이다.
    """
    soup = BeautifulSoup(html, "html.parser")
    reviews = []
    # Trip.com 리뷰는 보통 아래와 같은 구조를 가진다.
    # <div class="review-item"> ...
    #   <h3 class="review-title">제목</h3>
    #   <p class="review-content">내용</p>
    #   <span class="review-score">5.0</span>
    # 실제 클래스 이름은 사이트에 따라 달라질 수 있으니, 여러 패턴을 시도한다.
    for item in soup.select("div.review-item"):
        # 제목
        title_tag = item.select_one("h3.review-title, .review-title, .title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        # 내용
        content_tag = item.select_one("p.review-content, .review-content, .content")
        content = content_tag.get_text(strip=True) if content_tag else ""
        # 별점 (보통 0~5 사이의 실수)
        rating_tag = item.select_one("span.review-score, .review-score, .rating")
        rating_text = rating_tag.get_text(strip=True) if rating_tag else ""
        try:
            rating = float(rating_text)
        except ValueError:
            rating = None
        reviews.append({"title": title, "content": content, "rating": rating})
    return reviews


def get_total_pages(soup: BeautifulSoup) -> int:
    """페이지네이션 영역에서 전체 페이지 수를 추출한다.
    페이지 수를 찾지 못하면 1을 반환한다.
    """
    # 일반적으로 페이지 번호는 <a class="page-number"> 형태이다.
    page_links = soup.select("a.page-number, .page-number")
    page_numbers = []
    for link in page_links:
        try:
            num = int(link.get_text(strip=True))
            page_numbers.append(num)
        except ValueError:
            continue
    return max(page_numbers) if page_numbers else 1

# ---------------------------------------------------------------------------
# Main Logic
# ---------------------------------------------------------------------------

def main():
    # 1️⃣ 첫 페이지 요청 및 파싱 (검증 단계)
    print("[1] 첫 페이지 로드 중…")
    first_html = fetch_page(HOTEL_URL)
    first_soup = BeautifulSoup(first_html, "html.parser")
    first_reviews = parse_reviews(first_html)
    if not first_reviews:
        print("⚠️ 첫 페이지에서 리뷰를 찾지 못했습니다. 페이지 구조를 확인해 주세요.")
        return
    print(f"✅ 첫 페이지에서 리뷰 {len(first_reviews)}개 추출")
    # 샘플 출력
    print("--- 샘플 리뷰 ---")
    sample = first_reviews[0]
    print(f"제목: {sample['title']}")
    print(f"내용: {sample['content'][:100]}...")
    print(f"별점: {sample['rating']}")
    print("-------------------")

    # 2️⃣ 전체 페이지 수 확인
    total_pages = get_total_pages(first_soup)
    print(f"전체 페이지 수: {total_pages}")

    # 3️⃣ 전체 리뷰 수집 (첫 페이지 포함)
    all_reviews = []
    for page in tqdm(range(1, total_pages + 1), desc="리뷰 수집 중"):
        if page == 1:
            page_html = first_html
        else:
            # 페이지 번호는 쿼리 파라미터 `page` 혹은 `offset` 로 전달되는 경우가 많다.
            # 여기서는 `page` 파라미터를 붙여 재요청한다.
            paged_url = HOTEL_URL + f"&page={page}"
            page_html = fetch_page(paged_url)
        page_reviews = parse_reviews(page_html)
        all_reviews.extend(page_reviews)

    # 4️⃣ 데이터프레임 변환 및 저장
    # SQLite DB 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    db_path = os.path.join(OUTPUT_DIR, "reviews.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # 테이블 생성 (이미 존재하면 무시)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        rating REAL
    )
    """)
    # 데이터 삽입
    cur.executemany(
        "INSERT INTO reviews (title, content, rating) VALUES (?, ?, ?)",
        [(r["title"], r["content"], r["rating"]) for r in all_reviews]
    )
    conn.commit()
    conn.close()
    print(f"💾 전체 {len(all_reviews)}개의 리뷰가 {db_path} 로 저장되었습니다.")

if __name__ == "__main__":
    main()
