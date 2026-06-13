import urllib.request
import json
import time
import os
import sys

# 표준 출력 인코딩을 UTF-8로 설정하여 윈도우 환경에서의 유니코드 출력 에러 방지
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "be08162c9d464d6998a5"
SERVICE_NAME = "C003"
BASE_URL = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{SERVICE_NAME}/json"

# 저장 경로 설정
DATA_DIR = os.path.join("testproj_1", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "food_safety_c003.json")

def fetch_data_chunk(start, end, max_retries=3):
    url = f"{BASE_URL}/{start}/{end}"
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    raw_data = response.read().decode('utf-8')
                    data = json.loads(raw_data)
                    return data
                else:
                    print(f"[경고] HTTP 상태 코드 {response.status} (시도 {attempt}/{max_retries})")
        except Exception as e:
            print(f"[오류] 데이터 요청 중 에러 발생: {e} (시도 {attempt}/{max_retries})")
        
        if attempt < max_retries:
            time.sleep(2 * attempt) # 지수 백오프 적용
            
    return None

def main():
    print("식약처 C003 API 데이터 수집을 시작합니다...")
    
    # 1. 첫 번째 호출로 전체 데이터 개수(total_count) 확인
    first_chunk = fetch_data_chunk(1, 1000)
    if not first_chunk or SERVICE_NAME not in first_chunk:
        print("[에러] 첫 번째 API 호출 실패 혹은 올바르지 않은 응답 구조입니다.")
        sys.exit(1)
        
    service_data = first_chunk[SERVICE_NAME]
    total_count_str = service_data.get("total_count")
    if not total_count_str:
        print("[에러] total_count 정보를 찾을 수 없습니다.")
        sys.exit(1)
        
    total_count = int(total_count_str)
    print(f"전체 데이터 개수: {total_count}개")
    
    all_rows = []
    
    # 첫 번째 청크에서 가져온 데이터 추가
    rows = service_data.get("row", [])
    all_rows.extend(rows)
    print(f"1 ~ {len(rows)} 데이터 수집 완료 (누적: {len(all_rows)}개)")
    
    # 2. 페이징 루프를 돌며 나머지 데이터 수집
    start_idx = 1001
    while start_idx <= total_count:
        end_idx = min(start_idx + 999, total_count)
        print(f"{start_idx} ~ {end_idx} 데이터 요청 중...", end="", flush=True)
        
        chunk = fetch_data_chunk(start_idx, end_idx)
        if chunk and SERVICE_NAME in chunk:
            rows = chunk[SERVICE_NAME].get("row", [])
            all_rows.extend(rows)
            print(f" 완료 (누적: {len(all_rows)}개)")
        else:
            print(f" 실패 (해당 구간 데이터 건너뜀)")
            
        start_idx += 1000
        time.sleep(0.5) # API 서버 부하 방지를 위한 대기 시간
        
    # 3. 수집 완료 데이터 저장
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"폴더 생성 완료: {DATA_DIR}")
        
    output_data = {
        "service_name": SERVICE_NAME,
        "total_count": len(all_rows),
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data": all_rows
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"모든 데이터 수집이 성공적으로 완료되었습니다!")
    print(f"저장 경로: {OUTPUT_FILE}")
    print(f"수집된 총 행 수: {len(all_rows)}개")

if __name__ == "__main__":
    main()
