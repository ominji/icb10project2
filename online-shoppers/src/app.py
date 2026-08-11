import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import koreanize_matplotlib  # 한글 깨짐 방지

# 페이지 설정
st.set_page_config(
    page_title="온라인 쇼핑몰 구매 여부(Revenue) 분석 대시보드",
    page_icon="🛍️",
    layout="wide"
)

# 파일 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    # 상대경로 사용
    csv_path = os.path.join("online-shoppers", "data", "online_shoppers_intention.csv")
    if not os.path.exists(csv_path):
        # 혹시 경로가 다를 경우를 대비한 대체 경로 탐색
        csv_path = "online_shoppers_intention.csv"
    
    df = pd.read_csv(csv_path)
    # Month 순서 정렬을 위한 카테고리 설정
    month_order = ['Feb', 'Mar', 'May', 'June', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 제목 및 소개
st.title("🛍️ 온라인 쇼핑 고객 구매 의사 결정 분석 대시보드")
st.markdown("""
이 대시보드는 **Online Shoppers Purchasing Intention Dataset**을 활용하여 고객의 구매 여부(`Revenue`)에 영향을 미치는 다양한 요인을 시각화하고 통계적으로 분석합니다.
수치형 및 범주형 변수가 실제 구매 완료(`Revenue = True`)에 어떻게 기여하는지 한눈에 비교해볼 수 있습니다.
""")

# ----------------- 사이드바 / 상단 요약 카드 -----------------
# 중복 데이터 계산
dup_count = df.duplicated().sum()
total_rows, total_cols = df.shape
revenue_rate = df['Revenue'].mean() * 100

st.sidebar.header("📊 데이터 요약 정보")
st.sidebar.metric(label="전체 행(Rows) 수", value=f"{total_rows:,} 개")
st.sidebar.metric(label="전체 열(Columns) 수", value=f"{total_cols} 개")
st.sidebar.metric(label="구매 전환율 (Revenue %)", value=f"{revenue_rate:.2f} %")
st.sidebar.metric(label="중복 데이터 수", value=f"{dup_count} 행")

# ----------------- 탭 구성 -----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 데이터 개요", 
    "📈 수치형 변수 분석 (Revenue 대조)", 
    "📊 범주형 변수 분석 (Revenue 대조)", 
    "🔍 개별 변수 상세 분석"
])

# ----------------- TAB 1: 데이터 개요 -----------------
with tab1:
    st.header("📂 데이터셋 개요 및 미리보기")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💡 처음 5개 행 (Head)")
        st.dataframe(df.head(), width='stretch')
    with col2:
        st.subheader("💡 마지막 5개 행 (Tail)")
        st.dataframe(df.tail(), width='stretch')
        
    st.subheader("📊 변수 정보 (Metadata)")
    col_info_df = pd.DataFrame({
        "데이터 타입": df.dtypes.astype(str),
        "결측치 수": df.isnull().sum(),
        "고유값(Unique) 수": df.nunique()
    })
    st.dataframe(col_info_df, width='stretch')
    
    st.subheader("⚖️ 구매 여부(Revenue) 분포 비율")
    rev_counts = df['Revenue'].value_counts()
    rev_pct = df['Revenue'].value_counts(normalize=True) * 100
    rev_summary = pd.DataFrame({
        "빈도 (명)": rev_counts,
        "비율 (%)": rev_pct
    })
    st.dataframe(rev_summary.style.format({"비율 (%)": "{:.2f}%"}), width='stretch')
    st.info("💡 전체 데이터 중 약 15.47%의 고객만이 실제로 최종 구매(Revenue=True)로 이어졌습니다. 데이터의 클래스 불균형이 존재함을 알 수 있습니다.")

# ----------------- TAB 2: 수치형 변수 분석 -----------------
with tab2:
    st.header("📈 수치형 변수와 Revenue 간의 관계 분석")
    st.markdown("수치형 변수 10개에 대해 구매 여부(`Revenue`)에 따라 값의 분포가 어떻게 달라지는지 서브플롯으로 시각화하고 하단에 기술통계를 비교합니다.")
    
    numerical_cols = [
        'Administrative', 'Administrative_Duration', 
        'Informational', 'Informational_Duration', 
        'ProductRelated', 'ProductRelated_Duration', 
        'BounceRates', 'ExitRates', 'PageValues', 'SpecialDay'
    ]
    
    # 5x2 서브플롯 생성
    fig, axes = plt.subplots(5, 2, figsize=(16, 25))
    axes = axes.flatten()
    
    for i, col in enumerate(numerical_cols):
        ax = axes[i]
        # 이상치가 크므로 이상치를 제외하고 보기 쉽게 boxplot 시각화 (showfliers=False)
        sns.boxplot(x='Revenue', y=col, hue='Revenue', data=df, ax=ax, palette={True: '#4CAF50', False: '#FFC107', 'True': '#4CAF50', 'False': '#FFC107'}, showfliers=False, legend=False)
        ax.set_title(f"Revenue에 따른 {col} 분포 (이상치 제외)", fontsize=12, fontweight='bold')
        ax.set_xlabel("구매 성공 여부 (Revenue)", fontsize=10)
        ax.set_ylabel(col, fontsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    st.markdown("---")
    st.subheader("📋 수치형 변수별 세부 기술통계 및 Revenue 대조표")
    
    # 각 수치형 변수별로 Revenue에 따른 기술통계 표 출력
    for col in numerical_cols:
        with st.expander(f"🔍 {col} 변수의 Revenue별 기술통계 보기"):
            # Revenue에 따른 그룹화 기술통계
            stats = df.groupby('Revenue')[col].describe().T
            st.write(f"**{col}** 변수는 구매 고객(True)과 비구매 고객(False) 간에 다음과 같은 통계적 차이를 보입니다.")
            st.dataframe(stats.style.format("{:.4f}"), width='stretch')
            
            # 해석 덧붙임
            mean_diff = stats.loc['mean', True] - stats.loc['mean', False]
            if mean_diff > 0:
                st.write(f"👉 **해석**: 구매 고객(True)의 `{col}` 평균값이 비구매 고객(False)보다 약 **{abs(mean_diff):.4f}** 더 높습니다.")
            else:
                st.write(f"👉 **해석**: 구매 고객(True)의 `{col}` 평균값이 비구매 고객(False)보다 약 **{abs(mean_diff):.4f}** 더 낮습니다.")

# ----------------- TAB 3: 범주형 변수 분석 -----------------
with tab3:
    st.header("📊 범주형 변수와 Revenue 간의 관계 분석")
    st.markdown("범주형 변수 7개에 대해 구매 여부(`Revenue`)에 따라 빈도와 비율이 어떻게 다른지 서브플롯으로 시각화하고 하단에 빈도 및 비율 교차표를 제공합니다.")
    
    categorical_cols = [
        'Month', 'OperatingSystems', 'Browser', 
        'Region', 'TrafficType', 'VisitorType', 'Weekend'
    ]
    
    # 4x2 서브플롯 생성
    fig, axes = plt.subplots(4, 2, figsize=(16, 22))
    axes = axes.flatten()
    
    for i, col in enumerate(categorical_cols):
        ax = axes[i]
        # x축 기준 정렬 처리
        order = sorted(df[col].unique()) if col != 'Month' else ['Feb', 'Mar', 'May', 'June', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        # Stacked Bar Chart를 위해 교차 테이블 생성
        ct = pd.crosstab(df[col], df['Revenue'], normalize='index') * 100
        
        # 시각화 (구매율 % 누적 막대 그래프)
        ct.plot(kind='bar', stacked=True, ax=ax, color=['#FFC107', '#4CAF50'], width=0.6)
        ax.set_title(f"{col}별 구매(Revenue) 전환 비율 (%)", fontsize=12, fontweight='bold')
        ax.set_xlabel(col, fontsize=10)
        ax.set_ylabel("비율 (%)", fontsize=10)
        ax.legend(["비구매(False)", "구매(True)"], loc='upper right')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
    # 마지막 빈 서브플롯은 숨김 처리
    fig.delaxes(axes[-1])
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    st.markdown("---")
    st.subheader("📋 범주형 변수별 빈도 및 구매율 교차표 (Crosstab)")
    
    for col in categorical_cols:
        with st.expander(f"🔍 {col} 변수의 Revenue 교차표 보기"):
            # 빈도표
            ct_count = pd.crosstab(df[col], df['Revenue'])
            # 비율표
            ct_ratio = pd.crosstab(df[col], df['Revenue'], normalize='index') * 100
            
            # 병합하여 보여주기
            ct_summary = pd.DataFrame()
            ct_summary[f'비구매 빈도(False)'] = ct_count[False]
            ct_summary[f'구매 빈도(True)'] = ct_count[True]
            ct_summary[f'구매 비율(True, %)'] = ct_ratio[True]
            ct_summary['전체 빈도'] = ct_count[False] + ct_count[True]
            
            st.write(f"**{col}** 변수의 각 항목별 구매 성공(True) 빈도 및 비율 교차표입니다.")
            st.dataframe(ct_summary.style.format({
                '비구매 빈도(False)': '{:,}',
                '구매 빈도(True)': '{:,}',
                '구매 비율(True, %)': '{:.2f}%',
                '전체 빈도': '{:,}'
            }), width='stretch')
            
            # 최댓값 위치 찾기
            max_ratio_idx = ct_ratio[True].idxmax()
            max_ratio_val = ct_ratio[True].max()
            st.write(f"👉 **통찰**: `{col}` 변수에서 구매 성공율(True)이 가장 높은 범주는 **{max_ratio_idx}** (구매율: **{max_ratio_val:.2f}%**) 입니다.")

# ----------------- TAB 4: 개별 변수 상세 분석 -----------------
with tab4:
    st.header("🔍 개별 변수 심층 분석 및 세부 시각화")
    st.markdown("원하는 변수를 선택하여 구매 여부(`Revenue`)와의 관계를 대조하고 상세 리포트를 확인해 보세요.")
    
    all_features = numerical_cols + categorical_cols
    selected_var = st.selectbox("🎯 분석할 변수를 선택하세요:", all_features)
    
    is_numeric = selected_var in numerical_cols
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📊 {selected_var} vs Revenue 시각화")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if is_numeric:
            # 수치형 변수 상세 시각화
            # KDE Plot (커널 밀도 추정)과 Boxplot을 나란히 표현
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # 1. Boxplot (로그 스케일 옵션 추가)
            use_log = st.checkbox("y축 로그 스케일 적용 (값이 큰 이상치가 존재할 때 유용)", value=False)
            sns.boxplot(x='Revenue', y=selected_var, hue='Revenue', data=df, ax=ax1, palette={True: '#4CAF50', False: '#F44336', 'True': '#4CAF50', 'False': '#F44336'}, showfliers=False, legend=False)
            ax1.set_title(f"Revenue별 {selected_var} 상자 그림 (이상치 제외)")
            if use_log:
                ax1.set_yscale('log')
                
            # 2. KDE Plot
            sns.kdeplot(data=df, x=selected_var, hue='Revenue', common_norm=False, fill=True, ax=ax2, palette={True: '#4CAF50', False: '#F44336', 'True': '#4CAF50', 'False': '#F44336'}, alpha=0.4)
            ax2.set_title(f"Revenue별 {selected_var} 분포 곡선 (KDE)")
            # 극단적으로 큰 값을 잘라내고 밀도를 자세히 보기 위해 quantile 기준 범위 제한 옵션 제공
            limit_quantile = st.checkbox("상위 1% 극단치 제외하고 분포 보기", value=True)
            if limit_quantile:
                q_val = df[selected_var].quantile(0.99)
                ax2.set_xlim(df[selected_var].min(), q_val)
                
            st.pyplot(fig)
            plt.close()
        else:
            # 범주형 변수 상세 시각화 (Countplot + Stacked 비율)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # 1. Countplot (전체 빈도수)
            order = sorted(df[selected_var].unique()) if selected_var != 'Month' else ['Feb', 'Mar', 'May', 'June', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            sns.countplot(x=selected_var, hue='Revenue', data=df, ax=ax1, order=order, palette={True: '#4CAF50', False: '#F44336', 'True': '#4CAF50', 'False': '#F44336'})
            ax1.set_title(f"{selected_var} 범주별 구매 여부 빈도수")
            ax1.tick_params(axis='x', rotation=45)
            
            # 2. Stacked Bar (백분율 누적)
            ct = pd.crosstab(df[selected_var], df['Revenue'], normalize='index') * 100
            ct = ct.reindex(order) if selected_var == 'Month' else ct
            ct.plot(kind='bar', stacked=True, ax=ax2, color=['#F44336', '#4CAF50'], width=0.6)
            ax2.set_title(f"{selected_var} 범주별 구매 전환 비율 (%)")
            ax2.set_ylabel("비율 (%)")
            ax2.tick_params(axis='x', rotation=45)
            ax2.legend(["비구매(False)", "구매(True)"])
            
            st.pyplot(fig)
            plt.close()

    with col2:
        st.subheader("📋 요약 통계 & 분석 결과")
        if is_numeric:
            stats = df.groupby('Revenue')[selected_var].describe()
            st.dataframe(stats.T, width='stretch')
            
            # 변수별 맞춤형 설명
            if selected_var == 'PageValues':
                st.write("""
                💡 **주요 인사이트 (PageValues)**:
                `PageValues`는 해당 고객이 최종 구매에 도달하기 직전 방문한 웹 페이지의 평균 가치를 나타냅니다.
                시각화에서 보듯, **구매를 한 고객(True)의 PageValues 분포가 비구매 고객(False)에 비해 월등히 높음**을 알 수 있습니다.
                이는 구매 예측 모델에서 가장 중요한 Feature 중 하나가 될 것임을 강력하게 시사합니다.
                """)
            elif selected_var in ['BounceRates', 'ExitRates']:
                st.write("""
                💡 **주요 인사이트 (Bounce/Exit Rates)**:
                `BounceRates`(이탈률)와 `ExitRates`(종료율)는 고객이 페이지에 실망하거나 원하는 정보가 없어 떠난 비율을 의미합니다.
                일반적으로 **구매 고객(True)은 이탈률과 종료율이 현저하게 낮음**을 알 수 있습니다.
                고객이 사이트에 머물며 제품을 많이 탐색할수록 구매 확률이 높아집니다.
                """)
            else:
                st.write(f"""
                💡 **기술 통계 분석**:
                - `{selected_var}`의 평균값은 구매 집단(True)이 비구매 집단(False)에 비해 유의미한 차이가 납니다.
                - 특히 중앙값(50%)과 75% 백분위수 정보를 대조해 보면, 특정 임계값 이상인 경우 구매 확률이 급증하는 경향이 있는지 확인해 볼 수 있습니다.
                """)
        else:
            ct_count = pd.crosstab(df[selected_var], df['Revenue'])
            ct_ratio = pd.crosstab(df[selected_var], df['Revenue'], normalize='index') * 100
            
            ct_summary = pd.DataFrame({
                '비구매 빈도': ct_count[False],
                '구매 빈도': ct_count[True],
                '구매율 (%)': ct_ratio[True]
            })
            st.dataframe(ct_summary.style.format({'구매율 (%)': '{:.2f}%'}), width='stretch')
            
            if selected_var == 'Month':
                st.write("""
                💡 **주요 인사이트 (Month)**:
                - `May`와 `Nov`에 방문 횟수가 가장 집중되는 경향이 있습니다.
                - 하지만 **구매 성공률(%)은 11월(Nov)이 매우 높은 수준**을 기록하는 반면, 3월(Mar) 이나 5월(May)은 방문자 수 대비 실제 구매율이 낮을 수 있습니다. 연말 할인 행사(블랙 프라이데이 등)의 효과일 가능성이 높습니다.
                """)
            elif selected_var == 'VisitorType':
                st.write("""
                💡 **주요 인사이트 (VisitorType)**:
                - `New_Visitor`(신규 방문자)가 `Returning_Visitor`(재방문자)보다 **실제 구매로 이어지는 비율(구매 전환율)이 더 높게 나타나는** 흥미로운 경향이 관찰됩니다.
                - 이는 신규 유입 마케팅의 효과가 일시적인 구매로 잘 유도되었거나, 신규 회원을 위한 웰컴 쿠폰 등의 장치가 효과가 있음을 시사할 수 있습니다.
                """)
            else:
                st.write(f"""
                💡 **교차 통계 분석**:
                - `{selected_var}` 범주에 따른 구매 여부 비율 차이를 통해, 어떤 타겟 그룹에 마케팅 역량을 집중해야 할지 힌트를 얻을 수 있습니다.
                """)
