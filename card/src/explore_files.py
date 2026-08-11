import os

extract_dir = os.path.join("card", "data", "경기도 카드소비데이터_2025", "extracted")
files = os.listdir(extract_dir)

total_size = 0
for f in files:
    total_size += os.path.getsize(os.path.join(extract_dir, f))

print(f"전체 파일 수: {len(files)}개")
print(f"전체 파일 크기 합계: {total_size / (1024 * 1024 * 1024):.2f} GB")

# 실제 어떤 월(Month)의 데이터가 들어있는지 확인
months = set()
for f in files:
    # 파일명 예시: tbsh_gyeonggi_day_202503_안산.csv
    parts = f.split('_')
    for p in parts:
        if p.isdigit() and len(p) == 6:
            months.add(p)
            
print(f"포함된 월(Months): {sorted(list(months))}")
