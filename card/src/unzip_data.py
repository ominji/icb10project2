import os
import zipfile
import re
from tqdm import tqdm

base_dir = os.path.join("card", "data", "경기도 카드소비데이터_2025")
extract_dir = os.path.join(base_dir, "extracted")

# 기존 추출 폴더 내 파일 삭제하여 데이터 꼬임 방지
if os.path.exists(extract_dir):
    for f in os.listdir(extract_dir):
        try:
            os.remove(os.path.join(extract_dir, f))
        except Exception:
            pass
os.makedirs(extract_dir, exist_ok=True)

zip_files = [f for f in os.listdir(base_dir) if f.endswith(".zip")]
print(f"압축 해제할 파일 수: {len(zip_files)}개")

for zip_file in tqdm(zip_files):
    # zip 파일명에서 연월 정보 추출 (예: 카드소비 데이터_202501.zip -> 202501)
    match_ym = re.search(r"(\d{6})", zip_file)
    if match_ym:
        ym = match_ym.group(1)
    else:
        ym = "unknown"
        
    zip_path = os.path.join(base_dir, zip_file)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            for name in namelist:
                # 한글 깨짐 방지 처리
                try:
                    decoded_name = name.encode('cp437').decode('euc-kr')
                except Exception:
                    decoded_name = name
                
                # 만약 디렉토리라면 생성하고 패스
                if decoded_name.endswith('/'):
                    continue
                
                # 파일명에 연월이 포함되어 있지 않은 경우 강제로 연월 삽입
                # 예: tbsh_gyeonggi_day_화성.csv -> tbsh_gyeonggi_day_202501_화성.csv
                file_basename = os.path.basename(decoded_name)
                
                if ym not in file_basename:
                    # 파일명에 연월이 없으면 삽입 처리
                    # 'day_' 뒤에 '202501_'를 삽입하거나, 맨 앞에 삽입
                    if "day_" in file_basename:
                        new_basename = file_basename.replace("day_", f"day_{ym}_")
                    else:
                        new_basename = f"{ym}_{file_basename}"
                else:
                    new_basename = file_basename
                
                target_path = os.path.join(extract_dir, new_basename)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                with open(target_path, "wb") as f_out:
                    f_out.write(zip_ref.read(name))
                        
    except Exception as e:
        print(f"\n{zip_file} 압축 해제 중 에러 발생: {e}")

print("모든 압축 파일 해제가 완료되었습니다.")
extracted_files = os.listdir(extract_dir)
print(f"추출된 파일 개수: {len(extracted_files)}개")
if extracted_files:
    print(f"추출된 파일 예시: {extracted_files[:10]}")
