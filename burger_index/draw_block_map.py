import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import koreanize_matplotlib

# 1. 경로 설정
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
draw_korea_path = os.path.join(base_dir, "data_draw_korea.csv")
burger_path = os.path.join(base_dir, "burger.csv")

# 2. 데이터 로드
df_draw = pd.read_csv(draw_korea_path, index_col=0, encoding="utf-8")
df_draw["matching_name"] = df_draw["광역시도"] + " " + df_draw["행정구역"]

df_burger = pd.read_csv(burger_path, encoding="utf-8-sig", low_memory=False)

# 3. 데이터 통합 (광역시도 및 시군구 앞자리 단어로 병합)
sido_mapping = {
    "강원특별자치도": "강원도",
    "제주특별자치도": "제주특별자치도",
    "서울특별시": "서울특별시",
    "부산광역시": "부산광역시",
    "대구광역시": "대구광역시",
    "인천광역시": "인천광역시",
    "광주광역시": "광주광역시",
    "대전광역시": "대전광역시",
    "울산광역시": "울산광역시",
    "세종특별자치시": "세종특별자치시",
    "경기도": "경기도",
    "충청북도": "충청북도",
    "충청남도": "충청남도",
    "전북특별자치도": "전라북도",
    "전라북도": "전라북도",
    "전라남도": "전라남도",
    "경상북도": "경상북도",
    "경상남도": "경상남도"
}

def get_matching_name(row):
    sido = str(row["시도명"]).strip()
    sigungu = str(row["시군구명"]).strip()
    if "세종" in sido:
        return "세종특별자치시 세종시"
    std_sido = sido_mapping.get(sido, sido)
    std_sigungu = sigungu.split()[0]
    if std_sido == "인천광역시" and std_sigungu == "미추홀구":
        std_sigungu = "남구"
    return f"{std_sido} {std_sigungu}"

df_burger["matching_name"] = df_burger.apply(get_matching_name, axis=1)

# 브랜드 점포 수 집계
pivot = pd.crosstab(df_burger["matching_name"], df_burger["brand"]).reset_index()
for brand in ["버거킹", "맥도날드", "KFC", "롯데리아"]:
    if brand not in pivot.columns:
        pivot[brand] = 0

# 버거지수 계산 (롯데리아 = 0이면 NaN)
numerator = pivot["버거킹"] + pivot["맥도날드"] + pivot["KFC"]
denominator = pivot["롯데리아"]
pivot["버거지수"] = np.where(denominator > 0, np.round(numerator / denominator, 3), np.nan)

# draw_korea 데이터프레임에 버거지수 병합
df_map = df_draw.merge(pivot[["matching_name", "버거지수", "KFC", "롯데리아", "맥도날드", "버거킹"]], on="matching_name", how="left")

# 4. 블록맵 그리드 시각화 (Matplotlib)
fig, ax = plt.subplots(figsize=(8, 11))

# 컬러맵 설정 (버거지수에 따른 채우기 색상)
cmap = plt.cm.get_cmap("YlOrRd")
# 버거지수의 최댓값을 구하되, NaN은 제외
vmax = df_map["버거지수"].max() if not df_map["버거지수"].isna().all() else 3.0
norm = plt.Normalize(vmin=0, vmax=3.0)  # 일반적인 버거지수 범위인 0 ~ 3으로 노멀라이즈 고정

# 행정구역 경계선 그리기용 라인 리스트 (시각적 경계 그룹화)
# 광역시도 경계를 굵은 선으로 표현하여 지도의 입체감 형성
BORDER_LINES = [
    [(3, 2), (3, 3), (2, 3), (2, 4), (1, 4), (1, 5), (0, 5), (0, 7), (1, 7), (1, 9), (3, 9), (3, 10), (3, 11), (4, 11), (4, 12)], # 경기도 외곽
    [(12, 1), (12, 2), (11, 2), (11, 3), (10, 3), (10, 4), (9, 4), (9, 5), (10, 5), (10, 6), (11, 6), (11, 7), (12, 7)], # 강원도 경계
]

for idx, row in df_map.iterrows():
    x = row["x"]
    y = row["y"]
    val = row["버거지수"]
    short_name = row["shortName"]
    
    # 롯데리아가 0개이거나 매칭 데이터가 없으면 회색(#e0e0e0)
    if pd.isna(val):
        color = "#e0e0e0"
        text_color = "#7f7f7f"
    else:
        color = cmap(norm(val))
        # 색이 너무 어두우면 글씨를 흰색으로, 밝으면 검은색으로 처리
        text_color = "white" if norm(val) > 0.6 else "black"
        
    # 블록 사각형 추가
    rect = patches.Rectangle(
        (x - 0.5, y - 0.5), 1, 1,
        facecolor=color, edgecolor="#ffffff", linewidth=1.5
    )
    ax.add_patch(rect)
    
    # 블록 내부 이름 텍스트 표기
    # 세 글자 이상인 경우 가독성을 위해 줄바꿈 처리
    if len(short_name) >= 3 and not short_name.endswith(")"):
        display_name = short_name[:2] + "\n" + short_name[2:]
    else:
        display_name = short_name
        
    ax.text(
        x, y, display_name,
        ha="center", va="center",
        fontsize=9, color=text_color, fontweight="semibold"
    )

# 축 눈금 제거 및 형태 조정
ax.set_xlim(-0.5, 13.5)
ax.set_ylim(-0.5, 25.5)
ax.invert_yaxis()  # 북쪽이 위로 가게 y축 반전
ax.axis("off")

# 컬러바 추가
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.02, shrink=0.7)
cbar.set_label("버거지수", fontsize=11, fontweight="bold", labelpad=8)

plt.title("대한민국 버거지수(Burger Index) 카토그램 블록맵", fontsize=15, fontweight="bold", pad=20)

# 저장 및 출력
images_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "images"))
os.makedirs(images_dir, exist_ok=True)
plot_path = os.path.join(images_dir, "brand_block_map.png")
plt.savefig(plot_path, bbox_inches="tight", dpi=300)
plt.close()

print(f"카토그램 블록맵 이미지 저장 완료: {plot_path}")
