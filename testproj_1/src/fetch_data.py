# -*- coding: utf-8 -*-
import os
import requests
import json
from dotenv import load_dotenv

# .env 파일 로드 (상대경로 적용)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def fetch_food_safety_data(service_id="C003", start_idx=1, end_idx=10):
    """
    식품안전나라 OpenAPI로부터 데이터를 가져옵니다.
    """
    api_key = os.getenv("FOOD_SAFETY_API_KEY")
    api_url = os.getenv("FOOD_SAFETY_API_URL")

    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("[오류] .env 파일에 올바른 FOOD_SAFETY_API_KEY를 입력해 주세요.")
        return None

    # 요청 URL 조립
    # 구조: http://openapi.foodsafetykorea.go.kr/api/<인증키>/<서비스명>/<반환타입>/<요청시작위치>/<요청종료위치>
    url = f"{api_url}/{api_key}/{service_id}/json/{start_idx}/{end_idx}"
    
    print(f"[정보] API 요청 중: {url.replace(api_key, '***')}") # API 키 마스킹 처리하여 출력
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 정상 응답 코드 확인
        if service_id in data:
            result_code = data[service_id].get("RESULT", {}).get("CODE")
            if result_code == "INFO-000":
                print("[성공] 데이터를 정상적으로 수신했습니다.")
                return data
            else:
                print(f"[경고] API 오류 발생: {data[service_id].get('RESULT', {}).get('MSG')}")
        else:
            print("[오류] 응답 데이터 형식이 올바르지 않습니다.")
            
    except requests.exceptions.RequestException as e:
        print(f"[오류] 네트워크 에러 발생: {e}")
        
    return None

if __name__ == "__main__":
    # 데이터 수집 및 로컬 저장 예제
    data = fetch_food_safety_data(service_id="C003", start_idx=1, end_idx=10)
    
    if data:
        output_path = os.path.join(os.path.dirname(__file__), "..", "data", "health_functional_food_fetched.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[성공] 수집된 데이터가 {output_path} 에 저장되었습니다.")
