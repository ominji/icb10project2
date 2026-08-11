import os
import json
import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import koreanize_matplotlib

# 1. 페이지 설정
st.set_page_config(
    page_title="🍔 전국 버거지수(Burger Index) 대시보드",
    page_icon="🍔",
    layout="wide"
)

# 2. 경로 설정 (파일 위치 기준 상대경로 보장)
src_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(src_dir)
crosstab_path = os.path.join(project_dir, "data", "burger_crosstab.csv")
geojson_path = os.path.join(project_dir, "data", "skorea_municipalities.json")
draw_korea_path = os.path.join(project_dir, "data", "data_draw_korea.csv")
img_dir = os.path.join(project_dir, "images")

# 데이터 로드 헬퍼 함수
@st.cache_data
def load_data():
    df = pd.read_csv(crosstab_path, encoding="utf-8-sig")
    return df

@st.cache_data
def load_geojson():
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_draw_korea():
    df = pd.read_csv(draw_korea_path, index_col=0, encoding="utf-8")
    df["matching_name"] = df["광역시도"] + " " + df["행정구역"]
    return df

df_data = load_data()
geojson_data = load_geojson()
df_draw = load_draw_korea()

# 3. 사이드바 네비게이션 설정
st.sidebar.title("🍔 버거지수 대시보드")
st.sidebar.markdown("전국 4대 버거 브랜드 점포 분포를 통한 도시 발전 수준 분석")
page = st.sidebar.radio("페이지 선택", [
    "1) 기본 EDA", 
    "2) 버거지수 위치 산점도 (Folium)", 
    "3) 행정구역별 버거지수 (Choropleth)",
    "4) 버거지수 카토그램 (Block Map)"
])

# 4. 페이지별 렌더링
if page == "1) 기본 EDA":
    st.title("📊 전국 버거 브랜드 기본 EDA")
    st.markdown("전체 정제 완료된 고유 버거 매장(2,548개)과 시도시군구별 통계 자료입니다.")
    
    # 주요 통계 카드
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("총 매장 수", "2,548 개")
    with col2:
        st.metric("롯데리아 매장 수", f"{int(df_data['롯데리아'].sum())} 개")
    with col3:
        st.metric("맥도날드 매장 수", f"{int(df_data['맥도날드'].sum())} 개")
    with col4:
        st.metric("버거킹 매장 수", f"{int(df_data['버거킹'].sum())} 개")
    with col5:
        st.metric("KFC 매장 수", f"{int(df_data['KFC'].sum())} 개")
        
    st.markdown("---")
    
    # 탭을 활용해 시각화 차트 분할 노출
    tab1, tab2, tab3 = st.tabs(["📉 브랜드 빈도 & 분포", "🌡️ 상관관계 분석", "🏆 버거지수 상위 20개 지역"])
    
    with tab1:
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.subheader("브랜드별 총 빈도수")
            img_path1 = os.path.join(img_dir, "brand_counts.png")
            if os.path.exists(img_path1):
                st.image(img_path1, use_container_width=True)
            else:
                st.info("시각화 이미지를 찾을 수 없습니다.")
        with col_img2:
            st.subheader("지역별 매장 수 분포 (박스플롯 & 바이올린 플롯)")
            img_path2 = os.path.join(img_dir, "brand_distribution.png")
            if os.path.exists(img_path2):
                st.image(img_path2, use_container_width=True)
            else:
                st.info("시각화 이미지를 찾을 수 없습니다.")
                
    with tab2:
        col_img3, col_img4 = st.columns(2)
        with col_img3:
            st.subheader("브랜드 상관관계 히트맵")
            img_path3 = os.path.join(img_dir, "brand_heatmap.png")
            if os.path.exists(img_path3):
                st.image(img_path3, use_container_width=True)
            else:
                st.info("시각화 이미지를 찾을 수 없습니다.")
        with col_img4:
            st.subheader("브랜드 분포 상삼각 페어플롯")
            img_path4 = os.path.join(img_dir, "brand_pairplot_upper.png")
            if os.path.exists(img_path4):
                st.image(img_path4, use_container_width=True)
            else:
                st.info("시각화 이미지를 찾을 수 없습니다.")
                
    with tab3:
        st.subheader("🏆 버거지수 실질적 상위 20개 지역 (매장 합계 >= 5 이상)")
        df_rank = df_data[df_data["합계"] >= 5].sort_values(by="버거지수", ascending=False).head(20).copy()
        
        # 가독성 개선을 위한 테이블 출력
        st.dataframe(
            df_rank[["시도시군구명", "KFC", "롯데리아", "맥도날드", "버거킹", "합계", "버거지수", "위도_중간값", "경도_중간값"]].reset_index(drop=True),
            use_container_width=True
        )

elif page == "2) 버거지수 위치 산점도 (Folium)":
    st.title("📍 버거지수 위치 산점도 (Folium Map)")
    st.markdown("위경도 값에 기반해 지도상에 점을 배치하고, **버거지수가 높을수록** 더 크고 붉은 원으로 표현하였습니다.")
    
    # 필터 옵션
    min_stores = st.slider("최소 매장 수 합계 필터", min_value=1, max_value=20, value=3, step=1)
    df_map = df_data[(df_data["합계"] >= min_stores) & (df_data["버거지수"].notna()) & (~df_data["버거지수"].isin([np.inf, -np.inf]))].copy()
    
    st.caption(f"필터링된 행정구역 수: {len(df_map)}개")
    
    # Folium 지도 초기화 (대한민국 중심 좌표)
    m = folium.Map(location=[36.2, 127.8], zoom_start=7, tiles="OpenStreetMap")
    
    # 원 마커 추가
    for idx, row in df_map.iterrows():
        lat = row["위도_중간값"]
        lng = row["경도_중간값"]
        burger_index = row["버거지수"]
        
        # 반지름과 색상 스케일링 설정
        radius = float(burger_index * 6) if burger_index > 0 else 2
        
        # 버거지수가 높을수록 붉은색, 낮을수록 파란색에 가까운 형태 색상 지정
        if burger_index >= 2.0:
            color = "#ff0000"  # 빨강
        elif burger_index >= 1.0:
            color = "#ffaa00"  # 주황
        else:
            color = "#0000ff"  # 파랑
            
        tooltip_content = f"""
        <b>{row['시도시군구명']}</b><br>
        버거지수: {burger_index:.3f}<br>
        매장합계: {int(row['합계'])}개<br>
        [롯데리아: {int(row['롯데리아'])} | 맥도날드: {int(row['맥도날드'])} | 버거킹: {int(row['버거킹'])} | KFC: {int(row['KFC'])}]
        """
        
        folium.CircleMarker(
            location=[lat, lng],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            tooltip=folium.Tooltip(tooltip_content, sticky=True)
        ).add_to(m)
        
    st_folium(m, width=1000, height=700)

elif page == "3) 행정구역별 버거지수 (Choropleth)":
    st.title("🗺️ 행정구역별 버거지수 단계구분도 (Choropleth Map)")
    st.markdown("GeoJSON 정보를 바탕으로 시도시군구 행정구역별 버거지수 밀도를 시각화합니다.")
    
    # 필터 옵션
    min_stores_ch = st.slider("최소 매장 수 합계 필터", min_value=1, max_value=20, value=3, step=1, key="choropleth_filter")
    df_ch = df_data.copy()
    
    # 필터 적용 시 필터 이하 지역의 버거지수를 0으로 처리하거나 제외
    df_ch.loc[df_ch["합계"] < min_stores_ch, "버거지수"] = np.nan
    df_ch_clean = df_ch.dropna(subset=["버거지수"]).copy()
    df_ch_clean = df_ch_clean[~df_ch_clean["버거지수"].isin([np.inf, -np.inf])]
    
    # GeoJSON 매핑 함수
    def map_to_geojson_name(name):
        if "세종" in name:
            return "세종시"
        if "미추홀구" in name:
            return "남구"
        if "청주시 서원구" in name:
            return "청주시흥덕구"
        if "청주시 청원구" in name:
            return "청주시상당구"
        if "화성시" in name and ("동탄구" in name or "병점구" in name or "효행구" in name or "만세구" in name):
            return "화성시"
        parts = name.split()
        if len(parts) > 1:
            return "".join(parts[1:])
        return name

    df_ch_clean["geojson_name"] = df_ch_clean["시도시군구명"].apply(map_to_geojson_name)
    
    # Folium 지도 초기화
    m_ch = folium.Map(location=[36.2, 127.8], zoom_start=7)
    
    # Choropleth 추가
    folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=df_ch_clean,
        columns=["geojson_name", "버거지수"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="시군구별 버거지수",
        nan_fill_color="white",
        nan_fill_opacity=0.2
    ).add_to(m_ch)
    
    folium.LayerControl().add_to(m_ch)
    
    st_folium(m_ch, width=1000, height=700)

elif page == "4) 버거지수 카토그램 (Block Map)":
    st.title("🧱 버거지수 카토그램 블록맵 (Cartogram)")
    st.markdown("행정구역 경계를 직사각형 블록으로 단순화하여 균등한 면적으로 버거지수 밀도를 비교합니다.")
    
    # 필터 옵션
    min_stores_bm = st.slider("최소 매장 수 합계 필터", min_value=1, max_value=20, value=3, step=1, key="block_map_filter")
    
    # 원본 점포 데이터 로드 후 그룹 매핑
    df_burger_raw = pd.read_csv(os.path.join(project_dir, "data", "burger.csv"), encoding="utf-8-sig", low_memory=False)
    
    sido_mapping_bm = {
        "강원특별자치도": "강원도", "제주특별자치도": "제주특별자치도", "서울특별시": "서울특별시",
        "부산광역시": "부산광역시", "대구광역시": "대구광역시", "인천광역시": "인천광역시",
        "광주광역시": "광주광역시", "대전광역시": "대전광역시", "울산광역시": "울산광역시",
        "세종특별자치시": "세종특별자치시", "경기도": "경기도", "충청북도": "충청북도",
        "충청남도": "충청남도", "전북특별자치도": "전라북도", "전라북도": "전라북도",
        "전라남도": "전라남도", "경상북도": "경상북도", "경상남도": "경상남도"
    }

    def get_matching_name_bm(row):
        sido = str(row["시도명"]).strip()
        sigungu = str(row["시군구명"]).strip()
        if "세종" in sido:
            return "세종특별자치시 세종시"
        std_sido = sido_mapping_bm.get(sido, sido)
        std_sigungu = sigungu.split()[0]
        if std_sido == "인천광역시" and std_sigungu == "미추홀구":
            std_sigungu = "남구"
        return f"{std_sido} {std_sigungu}"

    df_burger_raw["matching_name"] = df_burger_raw.apply(get_matching_name_bm, axis=1)

    # 브랜드 점포 수 통합 집계
    pivot_bm = pd.crosstab(df_burger_raw["matching_name"], df_burger_raw["brand"]).reset_index()
    for brand in ["버거킹", "맥도날드", "KFC", "롯데리아"]:
        if brand not in pivot_bm.columns:
            pivot_bm[brand] = 0
            
    # 합계 계산
    pivot_bm["합계"] = pivot_bm["KFC"] + pivot_bm["롯데리아"] + pivot_bm["맥도날드"] + pivot_bm["버거킹"]
    
    # 필터 적용: 매장 수가 필터 기준 미만인 경우 버거지수 계산에서 제외
    numerator_bm = pivot_bm["버거킹"] + pivot_bm["맥도날드"] + pivot_bm["KFC"]
    denominator_bm = pivot_bm["롯데리아"]
    
    pivot_bm["버거지수"] = np.where(
        (denominator_bm > 0) & (pivot_bm["합계"] >= min_stores_bm),
        np.round(numerator_bm / denominator_bm, 3),
        np.nan
    )
    
    # 블록맵용 데이터프레임과 병합
    df_bm_map = df_draw.merge(pivot_bm[["matching_name", "버거지수", "합계"]], on="matching_name", how="left")
    
    # 블록맵 시각화 생성
    fig, ax = plt.subplots(figsize=(8, 11))
    
    cmap = plt.colormaps.get_cmap("YlOrRd")
    norm = plt.Normalize(vmin=0, vmax=3.0)
    
    for idx, row in df_bm_map.iterrows():
        x = row["x"]
        y = row["y"]
        val = row["버거지수"]
        short_name = row["shortName"]
        
        if pd.isna(val):
            color = "#e0e0e0"
            text_color = "#7f7f7f"
        else:
            color = cmap(norm(val))
            text_color = "white" if norm(val) > 0.6 else "black"
            
        rect = patches.Rectangle(
            (x - 0.5, y - 0.5), 1, 1,
            facecolor=color, edgecolor="#ffffff", linewidth=1.5
        )
        ax.add_patch(rect)
        
        # 3글자 이상인 경우 줄바꿈
        if len(short_name) >= 3 and not short_name.endswith(")"):
            display_name = short_name[:2] + "\n" + short_name[2:]
        else:
            display_name = short_name
            
        ax.text(
            x, y, display_name,
            ha="center", va="center",
            fontsize=9, color=text_color, fontweight="semibold"
        )
        
    ax.set_xlim(-0.5, 13.5)
    ax.set_ylim(-0.5, 25.5)
    ax.invert_yaxis()
    ax.axis("off")
    
    # 컬러바 추가
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.02, shrink=0.7)
    cbar.set_label(f"버거지수 (최소 매장 {min_stores_bm}개 이상)", fontsize=11, fontweight="bold", labelpad=8)
    
    # 스트림릿에 표시
    st.pyplot(fig)
