# 올리브영 상품 수집 테스트 2 (유산균) 프롬프트

이 파일은 올리브영 유산균 상품 데이터를 수집하기 위한 HTTP 요청 정보 및 테스트 설정을 기록하는 프롬프트 파일입니다.

## 1. HTTP 요청 정보
Request URL
https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=100000200010024&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=24&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=&trackingCd=Cat100000200010024_Small&amplitudePageGubun=&t_page=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EB%B4%80&t_click=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%ED%83%AD_%EC%A4%91%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&midCategory=%EC%9C%A0%EC%82%B0%EA%B5%A0&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd=&t_1st_category_type=%EB%8C%80_%EA%B1%B4%EA%B0%95%EC%8B%9D%ED%92%88&t_2nd_category_type=%EC%A4%91_%EC%9C%A0%EC%82%B0%EA%B5%A0
Request Method
GET
Status Code
200 OK
Remote Address
[64:ff9b::ac42:2da]:443
Referrer Policy
strict-origin-when-cross-origin

## 2. HTTP 헤더 정보
pragma
no-cache
priority
u=0, i
referer
https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=100000200010024&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=24&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=&trackingCd=Cat100000200010024_Small&amplitudePageGubun=&t_page=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EB%B4%80&t_click=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%ED%83%AD_%EC%A4%91%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&midCategory=%EC%9C%A0%EC%82%B0%EA%B5%A0&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd=&t_1st_category_type=%EB%8C%80_%EA%B1%B4%EA%B0%95%EC%8B%9D%ED%92%88&t_2nd_category_type=%EC%A4%91_%EC%9C%A0%EC%82%B0%EA%B5%A0
sec-ch-ua
"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"
sec-ch-ua-arch
"x86"
sec-ch-ua-bitness
"64"
sec-ch-ua-full-version
"149.0.7827.114"
sec-ch-ua-full-version-list
"Google Chrome";v="149.0.7827.114", "Chromium";v="149.0.7827.114", "Not)A;Brand";v="24.0.0.0"
sec-ch-ua-mobile
?0
sec-ch-ua-model
""
sec-ch-ua-platform
"Windows"
sec-ch-ua-platform-version
"19.0.0"
sec-fetch-dest
document
sec-fetch-mode
navigate
sec-fetch-site
same-origin
sec-fetch-user
?1
upgrade-insecure-requests
1
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36

## 3. Payload 정보
dispCatNo=100000200010024&fltDispCatNo=&prdSort=01&pageIdx=1&rowsPerPage=24&searchTypeSort=btn_thumb&plusButtonFlag=N&isLoginCnt=&trackingCd=Cat100000200010024_Small&amplitudePageGubun=&t_page=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EB%B4%80&t_click=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%ED%83%AD_%EC%A4%91%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&midCategory=%EC%9C%A0%EC%82%B0%EA%B5%A0&smallCategory=%EC%A0%84%EC%B2%B4&checkBrnds=&lastChkBrnd=&t_1st_category_type=%EB%8C%80_%EA%B1%B4%EA%B0%95%EC%8B%9D%ED%92%88&t_2nd_category_type=%EC%A4%91_%EC%9C%A0%EC%82%B0%EA%B5%A0

## 4. 응답 구조 예시 (Response JSON)
<!DOCTYPE html>
<html lang="ko">
	<head>
	<meta charset="utf-8">

## 5. 수집 및 저장 설정
- 한 페이지가 성공적으로 수집되는지 확인한 후 CSV 파일로 저장하도록 구성합니다.
