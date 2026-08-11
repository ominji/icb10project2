1) HTTP 요청정보
Request URL
https://www.klook.com/v1/cardinfocenterservicesrv/search/platform/complete_search_v3?sort=most_relevant&tab_key=0&start=3&query=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&size=15&search_scope=main_search&k_lang=ko_KR&k_currency=KRW
Request Method
GET
Status Code
200 OK
Remote Address
104.18.31.170:443
Referrer Policy
strict-origin-when-cross-origin


2) HTTP 헤더정보
Accept-language
ko_KR
baggage
sentry-environment=production,sentry-release=web_ssr-platform_20260623_7acde2fb,sentry-public_key=919ae3dd598137e1aa2a88c31e161bb3,sentry-trace_id=f58bdd1f067f452e9a7de0055c9a2c4f,sentry-transaction=SearchResult,sentry-sampled=false,sentry-sample_rand=0.5150356711438143,sentry-sample_rate=0
cache-control
no-cache


3) Payload 정보
sort=most_relevant&tab_key=0&start=3&query=%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD&size=15&search_scope=main_search&k_lang=ko_KR&k_currency=KRW


4) 응답의 일부를 Response 에서 일부를 복사해서 넣어주기 (전체는 토큰 수 제한으로 어렵습니다.)
{
    "success": true,
    "error": {
        "code": "",
        "message": ""
    },
    "result": {
        "search_result": {
            "total": 1000,
            "cards": [
                {
                    "data": {


5) 한페이지가 성공적으로 수집되는지 확인하고 csv 파일로 저장할 것 