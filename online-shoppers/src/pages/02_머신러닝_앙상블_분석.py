import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
import koreanize_matplotlib  # 한글 깨짐 방지

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, matthews_corrcoef,
    confusion_matrix, roc_curve, precision_recall_curve, classification_report
)
from imblearn.over_sampling import SMOTE, RandomOverSampler

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="앙상블 머신러닝 분석 | 온라인 쇼핑몰 구매 예측",
    page_icon="🤖",
    layout="wide"
)

# ─────────────────────────────────────────────
# 사용자 정의 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #f0f0f0; }
    [data-testid="stSidebar"] { background: rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px; padding: 16px; backdrop-filter: blur(10px);
    }
    .section-header {
        background: linear-gradient(90deg, #3a7bd5, #3a6073); padding: 12px 20px;
        border-radius: 10px; margin: 20px 0 12px 0; font-size: 18px; font-weight: 700; color: white;
    }
    .info-box {
        background: rgba(58,123,213,0.15); border: 1px solid rgba(58,123,213,0.4);
        border-left: 4px solid #3a7bd5; border-radius: 8px; padding: 14px 18px;
        margin: 10px 0; color: #e0e0e0; font-size: 14px; line-height: 1.7;
    }
    .mermaid-container {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; padding: 20px; margin: 16px 0;
    }
    .metric-badge {
        display: inline-block; background: linear-gradient(135deg, #3a7bd5, #3a6073);
        color: white; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; margin: 4px;
    }
    .overfit-box {
        border-radius: 10px; padding: 14px 18px; margin: 8px 0; font-size: 14px; line-height: 1.7;
    }
    h1 {
        background: linear-gradient(90deg, #a1c4fd, #c2e9fb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-size: 2.4rem !important; font-weight: 800 !important;
    }
    h2 { color: #a1c4fd !important; }
    h3 { color: #c2e9fb !important; }
    [data-testid="stTabs"] button { font-weight: 600; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    candidates = [
        os.path.join("online-shoppers", "data", "online_shoppers_intention.csv"),
        os.path.join("..", "data", "online_shoppers_intention.csv"),
        os.path.join("online_shoppers_intention.csv"),
    ]
    df = None
    for path in candidates:
        if os.path.exists(path):
            df = pd.read_csv(path)
            break
    if df is None:
        raise FileNotFoundError("데이터 파일을 찾을 수 없습니다.")
    return df

@st.cache_data
def preprocess_data(df):
    df_ml = df.copy()
    df_ml['Revenue'] = df_ml['Revenue'].astype(int)
    cat_cols = ['Month', 'VisitorType']
    for col in cat_cols:
        le = LabelEncoder()
        df_ml[col] = le.fit_transform(df_ml[col].astype(str))
    df_ml['Weekend'] = df_ml['Weekend'].astype(int)
    X = df_ml.drop(columns=['Revenue'])
    y = df_ml['Revenue']
    return X, y, df_ml

def apply_oversampling(X_train, y_train, method, random_state):
    """오버샘플링 적용"""
    if method == "SMOTE":
        sampler = SMOTE(random_state=random_state, k_neighbors=5)
    elif method == "RandomOverSampler":
        sampler = RandomOverSampler(random_state=random_state)
    else:
        return X_train, y_train  # 미적용
    X_res, y_res = sampler.fit_resample(X_train, y_train)
    return X_res, y_res

def train_rf_model(X_tr, y_tr, n_estimators, max_depth, min_samples_split, class_weight_opt, random_state):
    """Random Forest 모델 학습"""
    cw = "balanced" if class_weight_opt else None
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        class_weight=cw,
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_tr, y_tr)
    return clf

def train_gb_model(X_tr, y_tr, learning_rate, n_estimators, max_depth, random_state):
    """Gradient Boosting 모델 학습"""
    clf = GradientBoostingClassifier(
        learning_rate=learning_rate,
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state
    )
    clf.fit(X_tr, y_tr)
    return clf

def compute_metrics(y_true, y_pred, y_prob):
    return {
        "Accuracy":  accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall":    recall_score(y_true, y_pred, zero_division=0),
        "F1-Score":  f1_score(y_true, y_pred, zero_division=0),
        "AUC-ROC":  roc_auc_score(y_true, y_prob),
        "AUC-PR":   average_precision_score(y_true, y_prob),
        "MCC":      matthews_corrcoef(y_true, y_pred),
    }

# ─────────────────────────────────────────────
# 데이터 로드 실행
# ─────────────────────────────────────────────
try:
    df_raw = load_data()
except FileNotFoundError as e:
    st.error(f"❌ {e}")
    st.stop()

X, y, df_ml = preprocess_data(df_raw)

# ─────────────────────────────────────────────
# 페이지 제목
# ─────────────────────────────────────────────
st.title("🤖 앙상블 모델 구매 예측 분석")
st.markdown("""
<div class="info-box">
📌 대표적인 앙상블 알고리즘인 <b>랜덤 포레스트(Random Forest)</b>와 <b>그레이디언트 부스팅(Gradient Boosting)</b>을 사용하여 온라인 쇼핑몰 고객의 <b>구매 여부(Revenue)</b>를 예측합니다.<br>
배깅(Bagging)과 부스팅(Boosting)의 아키텍처 차이에 따른 학습 결과를 상세히 대조하고, 비즈니스에 바로 적용할 수 있는 전략적 퍼널 최적화 안을 수립합니다.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 사이드바 – 하이퍼파라미터 & 오버샘플링 설정
# ─────────────────────────────────────────────
st.sidebar.header("⚙️ 모델 설정 및 조율")
st.sidebar.markdown("---")

# 공통 설정
st.sidebar.subheader("🔁 데이터 처리 설정")
oversample_method = st.sidebar.selectbox(
    "오버샘플링 기법 선택",
    options=["미적용", "SMOTE", "RandomOverSampler"],
    index=1,
    help="소수 클래스의 가치를 재조정하여 모델의 재현율(Recall)을 향상시킵니다."
)
test_size = st.sidebar.slider(
    "테스트 데이터 비율", min_value=0.1, max_value=0.4, value=0.2, step=0.05
)
random_state = st.sidebar.number_input(
    "🎲 랜덤 시드 (random_state)", min_value=0, max_value=999, value=42, step=1
)

st.sidebar.markdown("---")

# 1. Random Forest 하이퍼파라미터
st.sidebar.subheader("🌲 Random Forest 파라미터")
rf_n_estimators = st.sidebar.slider(
    "RF 트리 개수 (n_estimators)", min_value=10, max_value=200, value=100, step=10,
    help="의사결정나무의 총 개수입니다."
)
rf_max_depth = st.sidebar.slider(
    "RF 최대 깊이 (max_depth)", min_value=2, max_value=15, value=8, step=1,
    help="개별 트리의 최대 깊이입니다."
)
rf_min_samples_split = st.sidebar.slider(
    "RF 최소 분할 샘플 수", min_value=2, max_value=50, value=10, step=2,
    help="노드가 자식 노드로 분할되기 위해 가지고 있어야 할 최소 샘플 수입니다."
)
rf_class_weight_opt = st.sidebar.checkbox(
    "⚖️ RF class_weight='balanced' 적용",
    value=True,
    help="소수 클래스(구매 완료=1)에 높은 가중치를 실어 Recall을 개선합니다."
)

st.sidebar.markdown("---")

# 2. Gradient Boosting 하이퍼파라미터
st.sidebar.subheader("⚡ Gradient Boosting 파라미터")
gb_learning_rate = st.sidebar.slider(
    "GB 학습률 (learning_rate)", min_value=0.01, max_value=0.3, value=0.1, step=0.01,
    help="이전 트리의 오차를 얼마나 강하게 보정할지 결정하는 단계 크기입니다."
)
gb_n_estimators = st.sidebar.slider(
    "GB 트리 개수 (n_estimators)", min_value=10, max_value=200, value=100, step=10,
    help="순차적으로 생성할 부스팅 트리 개수입니다."
)
gb_max_depth = st.sidebar.slider(
    "GB 최대 깊이 (max_depth)", min_value=2, max_value=10, value=4, step=1,
    help="부스팅에서 개별 트리의 최대 깊이(보통 3~5가 추천됩니다)."
)

# ─────────────────────────────────────────────
# Train/Test Split → 오버샘플링 → 모델 학습
# ─────────────────────────────────────────────
X_train_raw, X_test, y_train_raw, y_test = train_test_split(
    X, y, test_size=test_size, random_state=int(random_state), stratify=y
)

# 오버샘플링 (train에만 적용)
if oversample_method != "미적용":
    X_train, y_train = apply_oversampling(
        X_train_raw.values, y_train_raw.values, oversample_method, int(random_state)
    )
    X_train = pd.DataFrame(X_train, columns=X.columns)
    y_train = pd.Series(y_train, name='Revenue')
else:
    X_train, y_train = X_train_raw, y_train_raw

# 1. Random Forest 학습 및 예측
with st.spinner("🌲 Random Forest 모델 학습 중..."):
    rf_clf = train_rf_model(
        X_train.values, y_train.values,
        n_estimators=rf_n_estimators,
        max_depth=rf_max_depth,
        min_samples_split=rf_min_samples_split,
        class_weight_opt=rf_class_weight_opt,
        random_state=int(random_state)
    )
    rf_pred_test = rf_clf.predict(X_test.values)
    rf_prob_test = rf_clf.predict_proba(X_test.values)[:, 1]
    rf_pred_train = rf_clf.predict(X_train.values)
    rf_prob_train = rf_clf.predict_proba(X_train.values)[:, 1]
    
    rf_metrics_test = compute_metrics(y_test.values, rf_pred_test, rf_prob_test)
    rf_metrics_train = compute_metrics(y_train.values, rf_pred_train, rf_prob_train)

# 2. Gradient Boosting 학습 및 예측
with st.spinner("⚡ Gradient Boosting 모델 학습 중..."):
    gb_clf = train_gb_model(
        X_train.values, y_train.values,
        learning_rate=gb_learning_rate,
        n_estimators=gb_n_estimators,
        max_depth=gb_max_depth,
        random_state=int(random_state)
    )
    gb_pred_test = gb_clf.predict(X_test.values)
    gb_prob_test = gb_clf.predict_proba(X_test.values)[:, 1]
    gb_pred_train = gb_clf.predict(X_train.values)
    gb_prob_train = gb_clf.predict_proba(X_train.values)[:, 1]
    
    gb_metrics_test = compute_metrics(y_test.values, gb_pred_test, gb_prob_test)
    gb_metrics_train = compute_metrics(y_train.values, gb_pred_train, gb_prob_train)


# ═══════════════════════════════════════════════
# SECTION 1: 앙상블 머신러닝 프로세스 Mermaid 흐름도
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📌 Section 1 &nbsp;|&nbsp; 앙상블 머신러닝 파이프라인 흐름도</div>', unsafe_allow_html=True)

os_label = oversample_method if oversample_method != "미적용" else "오버샘플링 미적용"
rf_cw_label = "class_weight=balanced" if rf_class_weight_opt else "class_weight=None"

mermaid_html = f"""
<div class="mermaid-container">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({{
    startOnLoad: true, theme: 'dark',
    themeVariables: {{
      primaryColor: '#3a7bd5', primaryTextColor: '#fff', primaryBorderColor: '#3a6073',
      lineColor: '#a1c4fd', secondaryColor: '#302b63', tertiaryColor: '#24243e',
      background: '#0f0c29', mainBkg: '#302b63', nodeBorder: '#3a7bd5',
      clusterBkg: '#302b63', titleColor: '#c2e9fb', edgeLabelBackground: '#302b63', fontSize: '14px'
    }}
  }});
</script>
<div class="mermaid">
flowchart TD
    A([🗃️ 원본 데이터 로드<br/>12,330 세션 × 18 특성]) --> B
    B[⚙️ 카테고리/불리언 인코딩<br/>Month · VisitorType · Weekend] --> C
    C[✂️ 데이터 분할<br/>Train {int((1-test_size)*100)}% · Test {int(test_size*100)}%] --> OS
    
    subgraph 밸런싱["⚖️ 클래스 밸런싱 (학습 데이터 전용)"]
        OS[🔁 {os_label}<br/>소수 샘플 가중 튜닝]
    end
    
    OS --> M1
    OS --> M2
    
    subgraph RF["🌲 Random Forest (배깅)"]
        M1[🌳 다수 의사결정나무 병렬 학습<br/>n_estimators={rf_n_estimators} · max_depth={rf_max_depth}<br/>{rf_cw_label}]
    end
    
    subgraph GB["⚡ Gradient Boosting (부스팅)"]
        M2[📈 잔차 기반 순차 오차 보정<br/>learning_rate={gb_learning_rate} · n_estimators={gb_n_estimators}<br/>max_depth={gb_max_depth}]
    end
    
    M1 --> E1
    M2 --> E2
    
    subgraph 분석["📊 평가 및 비교 시각화"]
        E1[🔮 RF 예측 평가 지표] --> VIZ
        E2[🔮 GB 예측 평가 지표] --> VIZ
        VIZ[🎨 성능 대조 분석<br/>ROC/PR Curves · Feature Importance 대조]
    end
    
    VIZ --> OUT([✅ 최적 앙상블 전략 수립])
    
    style A fill:#3a7bd5,color:#fff
    style OUT fill:#4CAF50,color:#fff
    style RF fill:#1a3c40,stroke:#3a7bd5,color:#fff
    style GB fill:#3c2a21,stroke:#FFC107,color:#fff
    style 분석 fill:#222831,stroke:#a1c4fd,color:#fff
</div>
</div>
"""
st.components.v1.html(mermaid_html, height=600, scrolling=False)


# ═══════════════════════════════════════════════
# SECTION 2: 오버샘플링 분포 정보
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">🔁 Section 2 &nbsp;|&nbsp; 클래스 불균형 & 오버샘플링 튜닝</div>', unsafe_allow_html=True)

col_os1, col_os2, col_os3 = st.columns(3)
orig_count = y_train_raw.value_counts().sort_index()
resamp_count = y_train.value_counts().sort_index()

with col_os1:
    st.markdown("**📊 원본 학습 세트 클래스 분포**")
    orig_df = pd.DataFrame({
        "클래스": ["비구매(0)", "구매(1)"],
        "샘플 수": [int(orig_count.get(0, 0)), int(orig_count.get(1, 0))],
        "비율": [
            f"{orig_count.get(0,0)/len(y_train_raw)*100:.1f}%",
            f"{orig_count.get(1,0)/len(y_train_raw)*100:.1f}%"
        ]
    })
    st.dataframe(orig_df, use_container_width=True, hide_index=True)

with col_os2:
    st.markdown(f"**🔄 오버샘플링 후 분포 ({oversample_method})**")
    res_df = pd.DataFrame({
        "클래스": ["비구매(0)", "구매(1)"],
        "샘플 수": [int(resamp_count.get(0, 0)), int(resamp_count.get(1, 0))],
        "비율": [
            f"{resamp_count.get(0,0)/len(y_train)*100:.1f}%",
            f"{resamp_count.get(1,0)/len(y_train)*100:.1f}%"
        ]
    })
    st.dataframe(res_df, use_container_width=True, hide_index=True)

with col_os3:
    delta_samples = len(y_train) - len(y_train_raw)
    st.metric("📦 원본 학습 데이터 개수", f"{len(y_train_raw):,} 개")
    st.metric("✨ 전처리 후 학습 데이터 개수", f"{len(y_train):,} 개",
              delta=f"+{delta_samples:,}" if delta_samples > 0 else "변동 없음")

# ═══════════════════════════════════════════════
# SECTION 3: 두 모델의 평가 지표 대조
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Section 3 &nbsp;|&nbsp; 앙상블 모델별 예측 성능 직접 비교 (Test 데이터 기준)</div>', unsafe_allow_html=True)
st.markdown("배깅 대표인 **Random Forest**와 부스팅 대표인 **Gradient Boosting**의 최종 분류 성적을 주요 성능 지표 단위로 1대1 대조합니다.")

m_cols = st.columns(7)
metrics_keys = ["Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC", "AUC-PR", "MCC"]

for idx, metric_key in enumerate(metrics_keys):
    with m_cols[idx]:
        val_rf = rf_metrics_test[metric_key]
        val_gb = gb_metrics_test[metric_key]
        diff = val_gb - val_rf
        
        # 더 나은 모델 구분 표시
        status_arrow = "🔺 GB 우세" if diff > 0 else "🔻 RF 우세" if diff < 0 else "동률"
        
        st.markdown(f"""
        <div style="text-align: center; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; background: rgba(255,255,255,0.02);">
            <div style="font-size: 13px; color: #a1c4fd; font-weight: bold; margin-bottom: 6px;">{metric_key}</div>
            <div style="font-size: 11px; color: #aaa;">🌲 RF: <b>{val_rf:.4f}</b></div>
            <div style="font-size: 11px; color: #aaa;">⚡ GB: <b>{val_gb:.4f}</b></div>
            <div style="font-size: 12px; margin-top: 8px; font-weight: bold; color: {'#4CAF50' if diff > 0 else '#FF7043' if diff < 0 else '#fff'}">
                {status_arrow}<br>({abs(diff):.4f})
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SECTION 4: 과적합(Overfitting) 자가 진단
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">🔬 Section 4 &nbsp;|&nbsp; 모델별 과적합 / 언더피팅 진단</div>', unsafe_allow_html=True)

col_fit_rf, col_fit_gb = st.columns(2)

def diagnose_overfitting(train_metrics, test_metrics, model_name):
    avg_gap = train_metrics["F1-Score"] - test_metrics["F1-Score"]
    test_acc = test_metrics["Accuracy"]
    
    if avg_gap > 0.12:
        return {
            "status": "🔴 과적합(Overfitting) 강함",
            "color": "rgba(244,67,54,0.15)",
            "border": "#F44336",
            "advice": f"Train과 Test의 F1-Score 격차가 {avg_gap:.4f}로 큽니다. 모델의 복잡도를 완화해야 합니다. 트리 깊이(max_depth)를 줄이거나 최소 분할 샘플 수(min_samples_split)를 올리세요."
        }
    elif avg_gap > 0.05:
        return {
            "status": "🟡 약한 과적합 경향",
            "color": "rgba(255,193,7,0.15)",
            "border": "#FFC107",
            "advice": f"일반적인 수준의 편차가 존재합니다(격차: {avg_gap:.4f}). 과적합을 더 줄이려면 규제 매개변수를 세밀하게 조율해 볼 수 있습니다."
        }
    elif avg_gap < -0.05 or (avg_gap <= 0.05 and test_acc < 0.75):
        return {
            "status": "🟡 언더피팅(Underfitting) 의심",
            "color": "rgba(255,193,7,0.15)",
            "border": "#FFC107",
            "advice": "학습 점수와 평가 점수가 모두 낮거나 격차가 마이너스입니다. 모델이 패턴을 학습하기에 용량이 부족할 수 있으므로, 트리 개수나 깊이를 넓혀 보세요."
        }
    else:
        return {
            "status": "🟢 최적의 일반화 성능 (Good Fit)",
            "color": "rgba(76,175,80,0.15)",
            "border": "#4CAF50",
            "advice": f"Train-Test 격차 {avg_gap:.4f}로 매우 안정적인 모델 일반화 경향을 확인했습니다."
        }

diag_rf = diagnose_overfitting(rf_metrics_train, rf_metrics_test, "Random Forest")
diag_gb = diagnose_overfitting(gb_metrics_train, gb_metrics_test, "Gradient Boosting")

with col_fit_rf:
    st.markdown("#### 🌲 Random Forest 과적합 판단")
    st.markdown(f"""
    <div class="overfit-box" style="background:{diag_rf['color']}; border:1px solid {diag_rf['border']}; border-left:4px solid {diag_rf['border']};">
        <b style="font-size:16px;">{diag_rf['status']}</b><br>
        {diag_rf['advice']}
    </div>
    """, unsafe_allow_html=True)
    
    # RF 비교 테이블
    rf_compare = pd.DataFrame({
        "평가 지표": metrics_keys,
        "Train": [rf_metrics_train[k] for k in metrics_keys],
        "Test": [rf_metrics_test[k] for k in metrics_keys]
    })
    rf_compare["격차"] = rf_compare["Train"] - rf_compare["Test"]
    st.dataframe(rf_compare.style.format({
        "Train": "{:.4f}",
        "Test": "{:.4f}",
        "격차": "{:+.4f}"
    }), use_container_width=True, hide_index=True)

with col_fit_gb:
    st.markdown("#### ⚡ Gradient Boosting 과적합 판단")
    st.markdown(f"""
    <div class="overfit-box" style="background:{diag_gb['color']}; border:1px solid {diag_gb['border']}; border-left:4px solid {diag_gb['border']};">
        <b style="font-size:16px;">{diag_gb['status']}</b><br>
        {diag_gb['advice']}
    </div>
    """, unsafe_allow_html=True)
    
    # GB 비교 테이블
    gb_compare = pd.DataFrame({
        "평가 지표": metrics_keys,
        "Train": [gb_metrics_train[k] for k in metrics_keys],
        "Test": [gb_metrics_test[k] for k in metrics_keys]
    })
    gb_compare["격차"] = gb_compare["Train"] - gb_compare["Test"]
    st.dataframe(gb_compare.style.format({
        "Train": "{:.4f}",
        "Test": "{:.4f}",
        "격차": "{:+.4f}"
    }), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# Train vs Test 시각화 비교 그래프
# ─────────────────────────────────────────────
st.markdown("#### 📊 알고리즘별 Train/Test 성능 대조 차트")
fig_bar, (ax_bar1, ax_bar2) = plt.subplots(1, 2, figsize=(15, 5))
fig_bar.patch.set_facecolor('#1a1a2e')

x_idx = np.arange(len(metrics_keys))
width = 0.35

# RF 차트 그리기
ax_bar1.set_facecolor('#1a1a2e')
ax_bar1.bar(x_idx - width/2, [rf_metrics_train[k] for k in metrics_keys], width, label='Train', color='#3a7bd5', alpha=0.85, edgecolor='#0f0c29')
ax_bar1.bar(x_idx + width/2, [rf_metrics_test[k] for k in metrics_keys], width, label='Test', color='#a1c4fd', alpha=0.85, edgecolor='#0f0c29')
ax_bar1.set_xticks(x_idx)
ax_bar1.set_xticklabels(metrics_keys, color='white', rotation=15)
ax_bar1.set_ylim(0, 1.15)
ax_bar1.set_title('🌲 Random Forest - Train vs Test', color='white', fontsize=12, fontweight='bold')
ax_bar1.tick_params(colors='white')
ax_bar1.legend(facecolor='#302b63', edgecolor='#3a7bd5', labelcolor='white')
ax_bar1.spines['bottom'].set_color((1,1,1,0.2))
ax_bar1.spines['left'].set_color((1,1,1,0.2))
ax_bar1.spines['top'].set_visible(False)
ax_bar1.spines['right'].set_visible(False)
ax_bar1.grid(axis='y', color=(1,1,1,0.1), linestyle='--')

# GB 차트 그리기
ax_bar2.set_facecolor('#1a1a2e')
ax_bar2.bar(x_idx - width/2, [gb_metrics_train[k] for k in metrics_keys], width, label='Train', color='#ff7043', alpha=0.85, edgecolor='#0f0c29')
ax_bar2.bar(x_idx + width/2, [gb_metrics_test[k] for k in metrics_keys], width, label='Test', color='#ffab91', alpha=0.85, edgecolor='#0f0c29')
ax_bar2.set_xticks(x_idx)
ax_bar2.set_xticklabels(metrics_keys, color='white', rotation=15)
ax_bar2.set_ylim(0, 1.15)
ax_bar2.set_title('⚡ Gradient Boosting - Train vs Test', color='white', fontsize=12, fontweight='bold')
ax_bar2.tick_params(colors='white')
ax_bar2.legend(facecolor='#302b63', edgecolor='#ff7043', labelcolor='white')
ax_bar2.spines['bottom'].set_color((1,1,1,0.2))
ax_bar2.spines['left'].set_color((1,1,1,0.2))
ax_bar2.spines['top'].set_visible(False)
ax_bar2.spines['right'].set_visible(False)
ax_bar2.grid(axis='y', color=(1,1,1,0.1), linestyle='--')

plt.tight_layout()
st.pyplot(fig_bar)
plt.close(fig_bar)


# ═══════════════════════════════════════════════
# SECTION 5: ROC 및 PR 곡선 성능 대조
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Section 5 &nbsp;|&nbsp; ROC 및 PR 곡선 통합 성능 비교</div>', unsafe_allow_html=True)
st.markdown("하나의 그래프 캔버스 상에서 두 모델의 분류 임계값 변화에 따른 변동 양상을 정밀 대조합니다.")

col_curve1, col_curve2 = st.columns(2)

# 계산
fpr_rf, tpr_rf, _ = roc_curve(y_test, rf_prob_test)
fpr_gb, tpr_gb, _ = roc_curve(y_test, gb_prob_test)

prec_rf, rec_rf, _ = precision_recall_curve(y_test, rf_prob_test)
prec_gb, rec_gb, _ = precision_recall_curve(y_test, gb_prob_test)

baseline = y_test.mean()

with col_curve1:
    st.subheader("📈 ROC Curve (수신자 판단 특성 곡선)")
    fig_roc, ax_roc = plt.subplots(figsize=(8, 6))
    fig_roc.patch.set_facecolor('#1a1a2e')
    ax_roc.set_facecolor('#1a1a2e')
    
    ax_roc.plot(fpr_rf, tpr_rf, color='#a1c4fd', lw=2.5, label=f'🌲 Random Forest (AUC = {rf_metrics_test["AUC-ROC"]:.4f})')
    ax_roc.plot(fpr_gb, tpr_gb, color='#ff7043', lw=2.5, label=f'⚡ Gradient Boosting (AUC = {gb_metrics_test["AUC-ROC"]:.4f})')
    ax_roc.plot([0,1], [0,1], 'r--', lw=1.5, label='기준 무작위 선 (AUC = 0.50)')
    
    ax_roc.set_xlabel('False Positive Rate (FPR)', color='white')
    ax_roc.set_ylabel('True Positive Rate (Recall)', color='white')
    ax_roc.tick_params(colors='white')
    ax_roc.legend(facecolor='#302b63', edgecolor='white', labelcolor='white')
    ax_roc.grid(color=(1,1,1,0.1), linestyle='--')
    ax_roc.spines['bottom'].set_color((1,1,1,0.2))
    ax_roc.spines['left'].set_color((1,1,1,0.2))
    ax_roc.spines['top'].set_visible(False)
    ax_roc.spines['right'].set_visible(False)
    st.pyplot(fig_roc)
    plt.close(fig_roc)

with col_curve2:
    st.subheader("📉 Precision-Recall Curve (정밀도-재현율 곡선)")
    fig_pr, ax_pr = plt.subplots(figsize=(8, 6))
    fig_pr.patch.set_facecolor('#1a1a2e')
    ax_pr.set_facecolor('#1a1a2e')
    
    ax_pr.plot(rec_rf, prec_rf, color='#a1c4fd', lw=2.5, label=f'🌲 Random Forest (AP = {rf_metrics_test["AUC-PR"]:.4f})')
    ax_pr.plot(rec_gb, prec_gb, color='#ff7043', lw=2.5, label=f'⚡ Gradient Boosting (AP = {gb_metrics_test["AUC-PR"]:.4f})')
    ax_pr.axhline(y=baseline, color='r', lw=1.5, linestyle='--', label=f'기준선 (양성 비율 = {baseline:.2f})')
    
    ax_pr.set_xlabel('Recall (재현율)', color='white')
    ax_pr.set_ylabel('Precision (정밀도)', color='white')
    ax_pr.tick_params(colors='white')
    ax_pr.legend(facecolor='#302b63', edgecolor='white', labelcolor='white')
    ax_pr.grid(color=(1,1,1,0.1), linestyle='--')
    ax_pr.spines['bottom'].set_color((1,1,1,0.2))
    ax_pr.spines['left'].set_color((1,1,1,0.2))
    ax_pr.spines['top'].set_visible(False)
    ax_pr.spines['right'].set_visible(False)
    st.pyplot(fig_pr)
    plt.close(fig_pr)


# ═══════════════════════════════════════════════
# SECTION 6: 피처 중요도 비교
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Section 6 &nbsp;|&nbsp; 피처 중요도 대조 분석 (Feature Importance Comparison)</div>', unsafe_allow_html=True)
st.markdown("두 모델이 구매 결정 예측에 기여하는 각 웹 방문 피처의 가치를 다르게 해석하는지 중요도 정렬로 파악합니다.")

# 데이터프레임 생성
feat_imp_df = pd.DataFrame({
    "피처": X.columns,
    "Random Forest": rf_clf.feature_importances_,
    "Gradient Boosting": gb_clf.feature_importances_
})

# RF 기준으로 정렬
feat_imp_df_sorted = feat_imp_df.sort_values(by="Random Forest", ascending=True)

fig_imp, (ax_imp1, ax_imp2) = plt.subplots(1, 2, figsize=(15, 8))
fig_imp.patch.set_facecolor('#1a1a2e')

# 1. RF 피처 중요도 그리기
ax_imp1.set_facecolor('#1a1a2e')
bars_rf = ax_imp1.barh(feat_imp_df_sorted["피처"], feat_imp_df_sorted["Random Forest"], color='#3a7bd5', height=0.6, edgecolor=(1,1,1,0.1))
for bar in bars_rf:
    width = bar.get_width()
    if width > 0.005:
        ax_imp1.text(width + 0.002, bar.get_y() + bar.get_height()/2, f"{width:.4f}", va='center', ha='left', color='white', fontsize=8)
ax_imp1.set_title("🌲 Random Forest 피처 중요도", color='white', fontweight='bold', fontsize=12)
ax_imp1.tick_params(colors='white')
ax_imp1.spines['top'].set_visible(False)
ax_imp1.spines['right'].set_visible(False)
ax_imp1.spines['left'].set_color((1,1,1,0.2))
ax_imp1.spines['bottom'].set_color((1,1,1,0.2))
ax_imp1.grid(axis='x', color=(1,1,1,0.05), linestyle='--')

# 2. GB 피처 중요도 그리기 (같은 순서로 배치하여 비교를 편하게 처리)
ax_imp2.set_facecolor('#1a1a2e')
bars_gb = ax_imp2.barh(feat_imp_df_sorted["피처"], feat_imp_df_sorted["Gradient Boosting"], color='#ff7043', height=0.6, edgecolor=(1,1,1,0.1))
for bar in bars_gb:
    width = bar.get_width()
    if width > 0.005:
        ax_imp2.text(width + 0.002, bar.get_y() + bar.get_height()/2, f"{width:.4f}", va='center', ha='left', color='white', fontsize=8)
ax_imp2.set_title("⚡ Gradient Boosting 피처 중요도", color='white', fontweight='bold', fontsize=12)
ax_imp2.tick_params(colors='white')
ax_imp2.spines['top'].set_visible(False)
ax_imp2.spines['right'].set_visible(False)
ax_imp2.spines['left'].set_color((1,1,1,0.2))
ax_imp2.spines['bottom'].set_color((1,1,1,0.2))
ax_imp2.grid(axis='x', color=(1,1,1,0.05), linestyle='--')

plt.tight_layout()
st.pyplot(fig_imp)
plt.close(fig_imp)

# 피처 중요도 분석 요약 
top3_rf = feat_imp_df.sort_values(by="Random Forest", ascending=False).head(3)
top3_gb = feat_imp_df.sort_values(by="Gradient Boosting", ascending=False).head(3)

col_top1, col_top2 = st.columns(2)
with col_top1:
    st.markdown("**🌲 Random Forest 중요 피처 TOP 3**")
    for idx, (i, row) in enumerate(top3_rf.iterrows(), 1):
        st.markdown(f"<span class='metric-badge'>#{idx}</span> <b>{row['피처']}</b> ({row['Random Forest']:.4f})", unsafe_allow_html=True)
with col_top2:
    st.markdown("**⚡ Gradient Boosting 중요 피처 TOP 3**")
    for idx, (i, row) in enumerate(top3_gb.iterrows(), 1):
        st.markdown(f"<span class='metric-badge'>#{idx}</span> <b>{row['피처']}</b> ({row['Gradient Boosting']:.4f})", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
💡 <b>앙상블 모델 비교 피처 인사이트</b>:<br>
두 모델 모두 고객이 전환 직전 거친 페이지 가치를 나타내는 <b>PageValues</b>를 압도적으로 중요한 지표로 채택했습니다. 
하지만 <b>Gradient Boosting</b>은 <b>ExitRates, ProductRelated_Duration</b>과 같이 고객의 실시간 세션 행동 특성에 더 가중치를 싣는 양상을 띱니다. 
반면 <b>Random Forest</b>는 배깅 특유의 피처 무작위 선택 메커니즘 덕분에 <b>Month</b>나 <b>Administrative_Duration</b> 등의 변수들도 골고루 중요도에 반영하여 오버피팅을 방지하는 다각화된 시각을 보여줍니다.
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SECTION 7: 모델 상세 분류 성능 (혼동행렬 및 분류 리포트)
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📋 Section 7 &nbsp;|&nbsp; 세부 오차 분석 및 분류 리포트</div>', unsafe_allow_html=True)

tab_cm_rf, tab_cm_gb, tab_rep_rf, tab_rep_gb = st.tabs([
    "🌲 Random Forest 혼동 행렬", "⚡ Gradient Boosting 혼동 행렬",
    "🌲 Random Forest 상세 리포트", "⚡ Gradient Boosting 상세 리포트"
])

with tab_cm_rf:
    cm_rf = confusion_matrix(y_test, rf_pred_test)
    tn, fp, fn, tp = cm_rf.ravel()
    
    col_cm1, col_cm2 = st.columns([1.5, 1])
    with col_cm1:
        fig_cm, ax_cm = plt.subplots(figsize=(7, 5))
        fig_cm.patch.set_facecolor('#1a1a2e')
        ax_cm.set_facecolor('#1a1a2e')
        sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['비구매(0)', '구매(1)'], yticklabels=['비구매(0)', '구매(1)'],
                    ax=ax_cm, linewidths=2, linecolor='#0f0c29',
                    annot_kws={'size': 18, 'weight': 'bold', 'color': 'white'})
        ax_cm.set_xlabel('예측값 (Predicted)', color='white')
        ax_cm.set_ylabel('실제값 (Actual)', color='white')
        ax_cm.set_title('Random Forest 혼동 행렬', color='white', fontweight='bold')
        ax_cm.tick_params(colors='white')
        st.pyplot(fig_cm)
        plt.close(fig_cm)
    with col_cm2:
        st.markdown("**📊 Random Forest 오차 분석 요약**")
        st.write(f"- 실제 구매 전환(1) 세션 {tp+fn}개 중 **{tp}개** 분류 성공 (재현율: **{rf_metrics_test['Recall']:.4f}**)")
        st.write(f"- 구매 완료로 잘못 분류한 오탐 세션: **{fp}개** (정밀도: **{rf_metrics_test['Precision']:.4f}**)")
        st.write(f"- 실제 구매를 찾아내지 못한 누락 세션: **{fn}개**")

with tab_cm_gb:
    cm_gb = confusion_matrix(y_test, gb_pred_test)
    tn, fp, fn, tp = cm_gb.ravel()
    
    col_cm1, col_cm2 = st.columns([1.5, 1])
    with col_cm1:
        fig_cm, ax_cm = plt.subplots(figsize=(7, 5))
        fig_cm.patch.set_facecolor('#1a1a2e')
        ax_cm.set_facecolor('#1a1a2e')
        sns.heatmap(cm_gb, annot=True, fmt='d', cmap='Oranges',
                    xticklabels=['비구매(0)', '구매(1)'], yticklabels=['비구매(0)', '구매(1)'],
                    ax=ax_cm, linewidths=2, linecolor='#0f0c29',
                    annot_kws={'size': 18, 'weight': 'bold', 'color': 'white'})
        ax_cm.set_xlabel('예측값 (Predicted)', color='white')
        ax_cm.set_ylabel('실제값 (Actual)', color='white')
        ax_cm.set_title('Gradient Boosting 혼동 행렬', color='white', fontweight='bold')
        ax_cm.tick_params(colors='white')
        st.pyplot(fig_cm)
        plt.close(fig_cm)
    with col_cm2:
        st.markdown("**📊 Gradient Boosting 오차 분석 요약**")
        st.write(f"- 실제 구매 전환(1) 세션 {tp+fn}개 중 **{tp}개** 분류 성공 (재현율: **{gb_metrics_test['Recall']:.4f}**)")
        st.write(f"- 구매 완료로 잘못 분류한 오탐 세션: **{fp}개** (정밀도: **{gb_metrics_test['Precision']:.4f}**)")
        st.write(f"- 실제 구매를 찾아내지 못한 누락 세션: **{fn}개**")

with tab_rep_rf:
    st.subheader("🌲 Random Forest Classification Report")
    rep_rf = classification_report(y_test, rf_pred_test, target_names=["비구매(0)", "구매(1)"], output_dict=True)
    st.dataframe(pd.DataFrame(rep_rf).T.style.format("{:.4f}").background_gradient(cmap='Blues'), use_container_width=True)

with tab_rep_gb:
    st.subheader("⚡ Gradient Boosting Classification Report")
    rep_gb = classification_report(y_test, gb_pred_test, target_names=["비구매(0)", "구매(1)"], output_dict=True)
    st.dataframe(pd.DataFrame(rep_gb).T.style.format("{:.4f}").background_gradient(cmap='Oranges'), use_container_width=True)


# ═══════════════════════════════════════════════
# SECTION 8: 비즈니스 통찰 및 실행 전략 로드맵
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">💼 Section 8 &nbsp;|&nbsp; 고도화 앙상블 분석 기반 비즈니스 인사이트</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
📌 단일 의사결정나무 모델을 뛰어넘는 <b>앙상블(Random Forest, Gradient Boosting) 분류 모델</b>의 피처 중요도와 의사결정 패턴을 바탕으로, 쇼핑몰 실무에 바로 대입 가능한 정교한 타겟 마케팅 및 전환 전략을 제안합니다.
</div>
""", unsafe_allow_html=True)

col_plan1, col_plan2 = st.columns(2)

with col_plan1:
    st.markdown("### 🎯 행동 패턴 기반 개인화 혜택")
    st.markdown("""
    <div style="background: rgba(58,123,213,0.08); border: 1px solid rgba(58,123,213,0.3);
                border-left: 4px solid #3a7bd5; border-radius: 8px; padding: 18px; margin-bottom: 14px; line-height: 1.85;">
    <b>① PageValues 연동 실시간 구매 가능성 탐지</b><br>
    가장 기여도가 큰 <code>PageValues</code> 지표를 실시간 마케팅 엔진에 올립니다. 세션 진행 중 고객의 방문 페이지 조합에 따라 예측 모델이 실시간 점수를 판독하고, 구매 가능 영역(임계값 초과) 진입 시 즉각 무료배송 등의 맞춤형 혜택 팝업을 트리거합니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(255,112,67,0.08); border: 1px solid rgba(255,112,67,0.3);
                border-left: 4px solid #ff7043; border-radius: 8px; padding: 18px; line-height: 1.85;">
    <b>② 이탈 방어 CRO(Conversion Rate Optimization) 고도화</b><br>
    Gradient Boosting 모델의 판단 근거에서 <code>ExitRates</code>의 미세한 움직임이 구매 실패 분류에 핵심 영향을 미침을 보였습니다. 
    이탈률이 비정상적으로 치솟는 장바구니/옵션 선택 페이지의 레이아웃을 A/B 테스트로 단순화하여 사용자의 이탈 행동 저항선을 무너뜨리는 작업이 시급합니다.
    </div>
    """, unsafe_allow_html=True)

with col_plan2:
    st.markdown("### 🚀 마케팅 실행 우선순위 로드맵")
    st.markdown("""
    <div style="background: rgba(76,175,80,0.08); border: 1px solid rgba(76,175,80,0.3);
                border-left: 4px solid #4CAF50; border-radius: 8px; padding: 18px; margin-bottom: 14px; line-height: 1.85;">
    <b>🥇 단기 플랜 (1개월 이내) — 실시간 팝업 스코어링 시스템 구축</b><br>
    Random Forest 및 Gradient Boosting의 예측 API를 연동하여 실시간 고객 세션 점수가 70점을 넘어선 대상자에게 한정 수량 쿠폰을 동적으로 전달해 결제를 완료하도록 유도합니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(255,193,7,0.08); border: 1px solid rgba(255,193,7,0.3);
                border-left: 4px solid #FFC107; border-radius: 8px; padding: 18px; line-height: 1.85;">
    <b>🥈 중기 플랜 (2~3개월) — 고이탈 단계 이탈 제어 리타겟팅</b><br>
    두 모델의 중요도에서 <code>ExitRates</code>와 <code>BounceRates</code>가 공통으로 검증되었습니다. 사용자가 이탈 결정을 내린 직후 인스타그램, 페이스북 리타겟팅 배너를 통해 장바구니에 담은 물건의 품절 임박 경고 문구를 전달해 재유입을 견인합니다.
    </div>
    """, unsafe_allow_html=True)

# 종합 비교 요약 표
st.markdown("### 📊 전략 수립 로드맵 요약")
roadmap_df = pd.DataFrame({
    "구분": ["실시간 개인화", "웹 퍼널 UX 개선", "시즌 및 유형 집중 오퍼"],
    "핵심 감지 피처": ["PageValues", "ExitRates / BounceRates", "Month / VisitorType"],
    "분석 적용 알고리즘": ["Gradient Boosting (정밀 세션 예측)", "Random Forest (일반화 변수 확인)", "앙상블 통합 모델 (가중 튜닝)"],
    "실무 액션 플랜": [
        "PageValues 상승 고객 대상 실시간 타겟 팝업 쿠폰 발행",
        "상위 이탈 구간 UX 단일화 및 불필요 동선 단축 (A/B Test)",
        "연말(11, 12월) 신규/재방문자 맞춤 프로모션 자동화 기획"
    ],
    "목표 KPI": ["구매 전환율 20% 상승", "평균 이탈률 15% 감축", "광고 투자 대비 수익률(ROAS) 30% 증가"]
})
st.dataframe(roadmap_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.4); font-size: 13px; padding: 16px;">
    🤖 앙상블 머신러닝 분석 페이지 | Online Shoppers Purchasing Intention Dataset<br>
    Random Forest & Gradient Boosting + SMOTE | scikit-learn · imbalanced-learn · streamlit
</div>
""", unsafe_allow_html=True)
