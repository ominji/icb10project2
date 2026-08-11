import os
import zipfile

base_dir = os.path.join("card", "data", "경기도 카드소비데이터_2025")
extract_dir = os.path.join(base_dir, "extracted")

target_zips = ["카드소비 데이터_202501.zip", "카드소비 데이터_202502.zip"]

for tz in target_zips:
    zip_path = os.path.join(base_dir, tz)
    if not os.path.exists(zip_path):
        print(f"파일 없음: {zip_path}")
        # 공백 문제 등 파일명 다를 수 있으니 유연하게 매칭
        all_files = os.listdir(base_dir)
        matched = [f for f in all_files if "202501" in f or "202502" in f]
        print(f"매칭되는 후보 파일들: {matched}")
        if matched:
            zip_path = os.path.join(base_dir, matched[0])
            print(f"후보 파일로 대체 시도: {zip_path}")
            
    try:
        print(f"압축 해제 시도: {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            print(f"내부 파일 개수: {len(namelist)}개")
            for name in namelist:
                try:
                    decoded_name = name.encode('cp437').decode('euc-kr')
                except Exception:
                    decoded_name = name
                
                target_path = os.path.join(extract_dir, decoded_name)
                print(f"추출 경로: {target_path}")
                if name.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f_out:
                        f_out.write(zip_ref.read(name))
        print("압축 해제 성공!")
    except Exception as e:
        print(f"에러 발생: {e}")
