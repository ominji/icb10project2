import matplotlib.pyplot as plt
import koreanize_matplotlib
import os

# 디렉토리 설정
image_dir = os.path.join("card", "images")
os.makedirs(image_dir, exist_ok=True)

# 1. [데이터 1] 전국 신용카드 월별 대표 업종 데이터 정의
months_1 = [
    "22/08", "22/09", "22/10", "22/11", "22/12", 
    "23/01", "23/02", "23/03", "23/04", "23/05", 
    "23/06", "23/07", "23/08"
]
sectors_1 = [
    "숙박", "건강보조식품", "의복/직물", "기타운송수단", "국산자동차신품",
    "건강보조식품", "항공사", "서적/문구", "국산자동차신품", "면세점",
    "항공사", "여행사/임대", "숙박"
]
indices_1 = [1.40, 1.32, 1.30, 1.25, 1.15, 1.25, 1.13, 1.21, 1.07, 1.21, 1.16, 1.25, 1.30]
mom_changes_1 = ["-", "+32.2%", "+35.5%", "+2.6%", "+6.5%", "+35.8%", "+7.6%", "+27.4%", "-10.6%", "+13.2%", "+3.1%", "+12.4%", "+30.3%"]

# 2. [데이터 2] 경기도 카드 월별 대표 업종 데이터 정의
months_2 = [
    "25/01", "25/02", "25/03", "25/04", "25/05", "25/06",
    "25/07", "25/08", "25/09", "25/10", "25/11", "25/12"
]
sectors_2 = [
    "학문/교육", "학문/교육", "미디어/통신", "여가/오락", "여가/오락", "여가/오락",
    "여가/오락", "여가/오락", "미디어/통신", "공연/전시", "공연/전시", "생활서비스"
]
indices_2 = [1.01, 1.03, 1.13, 1.01, 1.12, 1.07, 1.10, 1.12, 1.12, 1.51, 1.19, 1.12]
mom_changes_2 = ["-", "+2.3%", "+10.1%", "+1.3%", "+11.1%", "-4.9%", "+3.3%", "+1.6%", "+13.4%", "+57.9%", "-21.0%", "+5.6%"]

# --- 시각화 1: 전국 월별 대표 업종 지수 ---
plt.figure(figsize=(12, 6))
bars_1 = plt.bar(months_1, indices_1, color='#1f77b4', alpha=0.85, edgecolor='black', linewidth=0.7)
plt.axhline(1.0, color='red', linestyle='--', linewidth=1, label="전체 기간 평균선 (1.0)")
plt.ylim(0, 1.7)
plt.title("전국 신용카드 월별 대표 업종 및 지수 (평균 대비 배수)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=8)
plt.ylabel("평균 대비 매출 배수 (배)", fontsize=11, labelpad=8)
plt.legend(loc='upper right')
plt.grid(True, linestyle=':', alpha=0.6, axis='y')

# 각 막대 위에 텍스트 추가
for bar, sector, idx, mom in zip(bars_1, sectors_1, indices_1, mom_changes_1):
    yval = bar.get_height()
    # 텍스트 배치
    label_text = f"{sector}\n{idx:.2f}배\n({mom})"
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.03, label_text, 
             ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50')

plt.tight_layout()
plt.savefig(os.path.join(image_dir, "representative_sectors_national.png"), dpi=150)
plt.close()

# --- 시각화 2: 경기도 월별 대표 업종 지수 ---
plt.figure(figsize=(12, 6))
bars_2 = plt.bar(months_2, indices_2, color='#2ca02c', alpha=0.85, edgecolor='black', linewidth=0.7)
plt.axhline(1.0, color='red', linestyle='--', linewidth=1, label="전체 기간 평균선 (1.0)")
plt.ylim(0, 1.8)
plt.title("경기도 신용카드 월별 대표 업종 및 지수 (평균 대비 배수)", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("연월", fontsize=11, labelpad=8)
plt.ylabel("평균 대비 매출 배수 (배)", fontsize=11, labelpad=8)
plt.legend(loc='upper right')
plt.grid(True, linestyle=':', alpha=0.6, axis='y')

# 각 막대 위에 텍스트 추가
for bar, sector, idx, mom in zip(bars_2, sectors_2, indices_2, mom_changes_2):
    yval = bar.get_height()
    # 텍스트 배치
    label_text = f"{sector}\n{idx:.2f}배\n({mom})"
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.03, label_text, 
             ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50')

plt.tight_layout()
plt.savefig(os.path.join(image_dir, "representative_sectors_gyeonggi.png"), dpi=150)
plt.close()

print("월별 대표 업종 시각화 이미지 2개가 성공적으로 생성되었습니다.")
