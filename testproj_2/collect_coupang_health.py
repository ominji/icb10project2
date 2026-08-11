#!/usr/bin/env python3
"""coupang_health_prompt.md 에 정의된 단계에 따라 데이터를 수집하고 CSV 로 저장하는 스크립트.

1. 지정된 URL에 GET 요청을 수행하고 HTTP 요청/응답 정보를 기록합니다.
2. 요청 헤더와 페이로드(쿼리 파라미터)를 추출합니다.
3. 응답 본문의 일부를 저장합니다 (전체 HTML이 너무 커서 제한).
4. 페이지가 정상 수집됐는지 확인하고 결과를 CSV 파일에 저장합니다.

필요 패키지: requests
"""

import csv
import sys
from urllib.parse import urlparse, parse_qs

import requests

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------
URL = "https://www.coupang.com/np/campaigns/6585?page=3"
CSV_OUTPUT = "coupang_health_data.csv"

# ---------------------------------------------------------------------------
# 요청 수행
# ---------------------------------------------------------------------------
try:
    response = requests.get(URL, timeout=10)
except Exception as e:
    print(f"[오류] 요청 중 예외 발생: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 수집 데이터 준비
# ---------------------------------------------------------------------------
# 1) HTTP 요청 정보
request_info = {
    "method": response.request.method,
    "url": response.request.url,
    "status_code": response.status_code,
    "reason": response.reason,
    "remote_address": response.raw._connection.sock.getpeername() if hasattr(response.raw, "_connection") and hasattr(response.raw._connection, "sock") else "",
}

# 2) HTTP 헤더 정보
request_headers = response.request.headers
response_headers = response.headers

# 3) Payload 정보 (쿼리 파라미터)
parsed_url = urlparse(response.request.url)
query_params = parse_qs(parsed_url.query)
payload_info = {k: ",".join(v) for k, v in query_params.items()}

# 4) 응답 일부 (앞 500자)
response_snippet = response.text[:500].replace("\n", " ")

# ---------------------------------------------------------------------------
# CSV 저장
# ---------------------------------------------------------------------------
fieldnames = [
    "method",
    "url",
    "status_code",
    "reason",
    "remote_address",
    "request_headers",
    "response_headers",
    "payload",
    "response_snippet",
]

row = {
    "method": request_info["method"],
    "url": request_info["url"],
    "status_code": request_info["status_code"],
    "reason": request_info["reason"],
    "remote_address": request_info["remote_address"],
    "request_headers": dict(request_headers),
    "response_headers": dict(response_headers),
    "payload": payload_info,
    "response_snippet": response_snippet,
}

try:
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)
    print(f"[성공] 데이터가 '{CSV_OUTPUT}'에 저장되었습니다.")
except Exception as e:
    print(f"[오류] CSV 저장 중 예외 발생: {e}")
    sys.exit(1)
