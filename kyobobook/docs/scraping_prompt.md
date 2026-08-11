# 교보문고 베스트셀러 데이터 스크래핑 명세 및 검증 결과

본 문서는 교보문고 베스트셀러 API의 분석 정보 및 수집 성공 여부를 기록한 문서입니다.

---

## 1) HTTP 요청정보
- **Request URL**: `https://store.kyobobook.co.kr/api/gw/best/v2/best-seller/online`
- **Request Method**: `GET`
- **Status Code**: `200 OK`
- **Remote Address**: `[64:ff9b::67b6:7e02]:443`
- **Referrer Policy**: `strict-origin-when-cross-origin`

---

## 2) HTTP 헤더정보
API 호출에 필요한 주요 요청 헤더(Header) 목록입니다.

```http
host: store.kyobobook.co.kr
referer: https://store.kyobobook.co.kr/category/domestic/33/best?page=1&per=50
sec-ch-ua: "Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "macOS"
sec-ch-ua-platform-version: "26.5.1"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36
x-api-gw-key: eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..i35xkkCOngvXqCRx.0CqToQel6sj5d0qOS2ftoDu37jRwb0vtQwMBd1e_G1ynl7KUrTrH_qPJnygVpkc0tExt4BUX_pJ4RepB5QsxWmKLjC8tEuMELKG8SvRLEVn6ambMnSmDaJ85mLbGtHcM-zFiDBzi.3y1-RnxGHFxeLNMK2dWZoQ
```

---

## 3) Payload 정보 (Query Parameters)
API에서 데이터를 필터링하고 페이지네이션을 처리하기 위해 사용하는 쿼리 파라미터 정보입니다.

| 파라미터명 | 값 | 설명 |
| :--- | :--- | :--- |
| `page` | `4` | 요청할 페이지 번호 |
| `per` | `20` | 페이지당 노출할 도서 수 |
| `saleCmdtClstCode` | `33` | 카테고리 코드 (33: 컴퓨터/IT) |
| `soldOutExcludeYn` | `N` | 품절 상품 제외 여부 (N: 포함) |
| `saleCmdtDsplDvsnCode` | `KOR` | 국내 도서 구분 코드 |
| `period` | `002` | 주기 설정 (002: 일간) |
| `dsplDvsnCode` | `001` | 전시 구분 코드 |
| `dsplTrgtDvsnCode` | `004` | 전시 대상 구분 코드 |

---

## 4) Response 데이터 일부 (JSON 구조)
서버가 반환하는 API 응답의 주요 필드 구조를 발췌한 결과입니다.

```json
{
  "data": {
    "bestSeller": [
      {
        "prstRnkn": 61,
        "frmrRnkn": 80,
        "ymw": "2026061020260616",
        "total": 0,
        "rowNum": 61,
        "product": {
          "productInfo": {
            "saleCmdtid": "S000219436120",
            "cmdtcode": "9791140717934",
            "cmdtName": "2026 시나공 정보처리기사 실기 총정리",
            "isbn": "1140717936",
            "rlseDate": "20260323",
            "pbcmName": "길벗",
            "chrcName": "길벗알앤디"
          },
          "priceInfo": {
            "saleCmdtPrce": 33000,
            "saleCmdtPrceDscnRate": 10.0,
            "saleCmdtSapr": 29700,
            "upntAcmlAmnt": 1650
          }
        }
      }
    ]
  }
}
```

---

## 5) 전체 페이지 수집 및 CSV 저장 결과 검증
파이썬 스크립트(`kyobobook/src/crawler.py`)를 가상환경에서 실행하여 1페이지부터 마지막 페이지(50페이지)까지 총 1,000개의 도서 데이터를 성공적으로 수집하여 CSV 파일로 저장하는 것을 확인했습니다.

### 5-1) 실행한 전체 수집 코드
`kyobobook/src/crawler.py` 파일로 아래의 Python 코드를 구현 및 실행하였습니다.

```python
import os
import requests
import pandas as pd
import time

def crawl_kyobo_bestseller_all():
    url = "https://store.kyobobook.co.kr/api/gw/best/v2/best-seller/online"
    headers = {
        "referer": "https://store.kyobobook.co.kr/category/domestic/33/best?page=1&per=50",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "x-api-gw-key": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..i35xkkCOngvXqCRx.0CqToQel6sj5d0qOS2ftoDu37jRwb0vtQwMBd1e_G1ynl7KUrTrH_qPJnygVpkc0tExt4BUX_pJ4RepB5QsxWmKLjC8tEuMELKG8SvRLEVn6ambMnSmDaJ85mLbGtHcM-zFiDBzi.3y1-RnxGHFxeLNMK2dWZoQ"
    }
    
    page = 1
    parsed_books = []
    
    print("교보문고 베스트셀러 전체 데이터 수집 시작...")
    
    while True:
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
            
            # 더 이상 데이터가 없는 경우 종료
            if not best_seller_list:
                print(f"더 이상 수집할 데이터가 없습니다. (마지막 페이지: {page - 1})")
                break
                
            for item in best_seller_list:
                rank = item.get("prstRnkn")
                product_info = item.get("product", {}).get("productInfo", {})
                price_info = item.get("product", {}).get("priceInfo", {})
                
                book_data = {
                    "순위": rank,
                    "도서명": product_info.get("cmdtName"),
                    "저자": product_info.get("chrcName"),
                    "출판사": product_info.get("pbcmName"),
                    "출판일": product_info.get("rlseDate"),
                    "정가": price_info.get("saleCmdtPrce"),
                    "할인가": price_info.get("saleCmdtSapr"),
                    "할인율": price_info.get("saleCmdtPrceDscnRate"),
                    "ISBN": product_info.get("cmdtcode")
                }
                parsed_books.append(book_data)
                
            print(f"{page} 페이지 수집 완료 (누적 도서 수: {len(parsed_books)}개)")
            page += 1
            time.sleep(0.5) # 서버 부하 방지
            
        except Exception as e:
            print(f"오류 발생: {e}")
            break
            
    if not parsed_books:
        print("수집 완료된 데이터가 없습니다.")
        return
        
    df = pd.DataFrame(parsed_books)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "kyobo_bestseller_all.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"성공적으로 {len(df)}개의 도서 데이터를 수집했습니다.")

if __name__ == "__main__":
    crawl_kyobo_bestseller_all()
```

### 5-2) 수집 완료 및 저장 정보
- **저장된 CSV 파일 경로**: [kyobobook/data/kyobo_bestseller_all.csv](file:///c:/Users/user1/Desktop/icb10proj2/kyobobook/data/kyobo_bestseller_all.csv)
- **최종 수집 건수**: 1,000개 (1 ~ 50 페이지 완료)

### 5-3) 수집 완료 데이터 미리보기 (마지막 5개 행, 996위 ~ 1000위)
수집된 CSV 파일의 마지막 부분 내용입니다. 한글 깨짐 없이 정상적으로 저장된 것을 확인하였습니다.

| 순위 | 도서명 | 저자 | 출판사 | 출판일 | 정가 | 할인가 | 할인율 | ISBN |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 996 | 2026 백발백중 ITQ 한글2020 | 한정수 외 | 성안당 | 20260121 | 19000 | 17100 | 10.0 | 9788931583731 |
| 997 | 스마트폰과 함께하는 일상 디지털여행 활용편 | 오정화 외 | 북인스토리 | 20260121 | 18000 | 16200 | 10.0 | 9791124221044 |
| 998 | 2026 케이렙 KcLep에 의한 Point 전산회계 2급 | 이성노 | 경영과회계 | 20260120 | 21000 | 18900 | 10.0 | 9791194085874 |
| 999 | 디지털복지사 3급 1 | 이종구 외 | 디지털콘텐츠그룹 | 20260120 | 20000 | 18000 | 10.0 | 9791194642428 |
| 1000 | 디지털복지사 3급 3 | 이정화 외 | 디지털콘텐츠그룹 | 20260120 | 18000 | 16200 | 10.0 | 9791194642442 |