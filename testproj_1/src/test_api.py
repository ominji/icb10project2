import urllib.request
import json

url = "http://openapi.foodsafetykorea.go.kr/api/be08162c9d464d6998a5/C003/json/1/5"

try:
    with urllib.request.urlopen(url) as response:
        if response.status == 200:
            data = json.loads(response.read().decode('utf-8'))
            print("API 응답 성공!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"API 호출 실패: 상태 코드 {response.status}")
except Exception as e:
    print(f"에러 발생: {e}")
