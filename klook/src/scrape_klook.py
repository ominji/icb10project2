# -*- coding: utf-8 -*-
"""
Klook API 를 이용해 제품 정보를 수집하고 CSV 로 저장하는 스크립트.
요구 사항에 맞춰 `klook/data` 폴더 아래에 `klook_products.csv` 파일을 생성합니다.

사용 방법:
    python scrape_klook.py

필요 패키지: requests
이미 워크스페이스에 .venv 가 존재하므로, 해당 가상환경을 활성화한 뒤 실행하면 됩니다.
"""

import os
import csv
import json
import time
from urllib.parse import urlencode

import requests

# ----- 설정 ---------------------------------------------------------------
BASE_URL = "https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3"
# 기본 파라미터 (사용자 제공 내용과 동일)
COMMON_PARAMS = {
    "sort": "most_relevant",
    "tab_key": "0",
    "query": "대한민국",
    "size": "15",
    "search_scope": "main_search",
    "k_lang": "ko_KR",
    "k_currency": "KRW",
}

# 헤더 (사용자 제공 헤더 일부, 필요한 최소 헤더만 포함)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "x-klook-market": "global",
    "x-platform": "desktop",
    "x-requested-with": "XMLHttpRequest",
}

# 저장 경로 (워크스페이스 기준 상대경로)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "klook_products.csv")

def fetch_page(start: int):
    """주어진 start 값으로 한 페이지(15개) 데이터를 요청한다."""
    params = COMMON_PARAMS.copy()
    params["start"] = str(start)
    url = f"{BASE_URL}?{urlencode(params)}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()

def extract_items(json_resp):
    """응답 JSON 에서 실제 제품 데이터를 추출한다.
    현재 구조: result -> search_result -> cards[...].data
    """
    items = []
    try:
        cards = json_resp["result"]["search_result"]["cards"]
        for card in cards:
            data = card.get("data", {})
            items.append(data)
    except Exception as e:
        print(f"[WARN] 데이터 추출 중 오류: {e}")
    return items

def save_to_csv(items, write_header=False):
    """리스트 형태의 dict 를 CSV 로 저장한다.
    첫 번째 아이템의 키를 기준으로 헤더를 만든다.
    """
    if not items:
        return
    fieldnames = list(items[0].keys())
    mode = "w" if write_header else "a"
    with open(CSV_PATH, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for item in items:
            writer.writerow(item)

def main():
    # 최초 요청으로 전체 개수 파악
    first_resp = fetch_page(start=3)
    total = first_resp.get("result", {}).get("search_result", {}).get("total", 0)
    print(f"총 제품 수: {total}")

    # 첫 페이지 저장 (이미 받아온 데이터 활용)
    items = extract_items(first_resp)
    save_to_csv(items, write_header=True)
    fetched = len(items)

    # 이후 페이지 순회 (size=15 기준 start 값은 3, 18, 33, ...)
    start = 3 + 15
    while fetched < total:
        try:
            resp = fetch_page(start=start)
            page_items = extract_items(resp)
            if not page_items:
                break
            save_to_csv(page_items, write_header=False)
            fetched += len(page_items)
            print(f"{fetched}/{total} 수집 완료 (start={start})")
            start += 15
            time.sleep(0.5)  # API 부하 방지용 짧은 대기
        except Exception as e:
            print(f"[ERROR] 페이지 {start} 수집 실패: {e}")
            break
    print(f"CSV 저장 경로: {CSV_PATH}")

if __name__ == "__main__":
    main()
