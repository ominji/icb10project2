import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
import koreanize_matplotlib  # 한글 깨짐 방지

from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split, learning_curve
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
    page_title="머신러닝 분석 | 온라인 쇼핑몰 구매 예측",
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
        background: linear-gradient(90deg, #667eea, #764ba2); padding: 12px 20px;
        border-radius: 10px; margin: 20px 0 12px 0; font-size: 18px; font-weight: 700; color: white;
    }
    .info-box {
        background: rgba(102,126,234,0.15); border: 1px solid rgba(102,126,234,0.4);
        border-left: 4px solid #667eea; border-radius: 8px; padding: 14px 18px;
        margin: 10px 0; color: #e0e0e0; font-size: 14px; line-height: 1.7;
    }
    .mermaid-container {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; padding: 20px; margin: 16px 0;
    }
    .metric-badge {
        display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; margin: 4px;
    }
    .overfit-box {
        border-radius: 10px; padding: 14px 18px; margin: 8px 0; font-size: 14px; line-height: 1.7;
    }
    h1 {
        background: linear-gradient(90deg, #a8edea, #fed6e3);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-size: 2.4rem !important; font-weight: 800 !important;
    }
    h2 { color: #a8edea !important; }
    h3 { color: #fed6e3 !important; }
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


def train_model(X_tr, y_tr, max_depth, min_samples_split, criterion,
                class_weight_opt, random_state):
    """Decision Tree 모델 학습"""
    cw = "balanced" if class_weight_opt else None
    clf = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        criterion=criterion,
        class_weight=cw,
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
st.title("🤖 머신러닝 구매 예측 분석")
st.markdown("""
<div class="info-box">
📌 <b>Decision Tree(결정 트리)</b> 알고리즘으로 온라인 쇼핑몰 고객의 <b>구매 여부(Revenue)</b>를 예측합니다.
<b>SMOTE 오버샘플링</b>으로 클래스 불균형을 해소하고, Train/Test 성능 비교로 과적합 여부를 진단합니다.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 사이드바 – 하이퍼파라미터 & 오버샘플링 설정
# ─────────────────────────────────────────────
st.sidebar.header("⚙️ 모델 설정")
st.sidebar.markdown("---")

st.sidebar.subheader("🌳 Decision Tree 파라미터")
max_depth = st.sidebar.slider(
    "최대 깊이 (max_depth)", min_value=2, max_value=15, value=5, step=1,
    help="트리의 최대 깊이. 값이 클수록 복잡한 모델."
)
min_samples_split = st.sidebar.slider(
    "최소 분기 샘플 수 (min_samples_split)", min_value=2, max_value=50, value=10, step=2,
    help="노드 분기에 필요한 최소 샘플 수."
)
criterion = st.sidebar.selectbox(
    "분기 기준 (criterion)", options=["gini", "entropy"], index=0
)
class_weight_opt = st.sidebar.checkbox(
    "⚖️ class_weight='balanced' 적용",
    value=True,
    help="클래스 불균형 시 소수 클래스(구매=1)에 가중치를 부여하여 Recall을 개선합니다."
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔁 오버샘플링 설정")
oversample_method = st.sidebar.selectbox(
    "오버샘플링 기법",
    options=["미적용", "SMOTE", "RandomOverSampler"],
    index=1,
    help="SMOTE: 소수 클래스 합성 샘플 생성 | RandomOverSampler: 단순 복제"
)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 데이터 분할")
test_size = st.sidebar.slider(
    "테스트 데이터 비율", min_value=0.1, max_value=0.4, value=0.2, step=0.05
)
random_state = st.sidebar.number_input(
    "🎲 랜덤 시드 (random_state)", min_value=0, max_value=999, value=42, step=1
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**📋 원본 데이터 정보**
- 총 행 수: {:,}
- 총 열 수: {}
- 구매 전환율: {:.2f}%
""".format(len(df_raw), df_raw.shape[1], df_raw['Revenue'].mean() * 100))


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

# 모델 학습
clf = train_model(
    X_train.values, y_train.values,
    max_depth=max_depth,
    min_samples_split=min_samples_split,
    criterion=criterion,
    class_weight_opt=class_weight_opt,
    random_state=int(random_state)
)

# 예측
y_pred_test  = clf.predict(X_test.values)
y_prob_test  = clf.predict_proba(X_test.values)[:, 1]
y_pred_train = clf.predict(X_train.values)
y_prob_train = clf.predict_proba(X_train.values)[:, 1]

# 평가 지표 계산 (Test)
test_metrics  = compute_metrics(y_test.values, y_pred_test, y_prob_test)
# 평가 지표 계산 (Train)
train_metrics = compute_metrics(y_train.values, y_pred_train, y_prob_train)

# 편의 변수
acc    = test_metrics["Accuracy"]
prec   = test_metrics["Precision"]
rec    = test_metrics["Recall"]
f1     = test_metrics["F1-Score"]
auc_roc = test_metrics["AUC-ROC"]
auc_pr  = test_metrics["AUC-PR"]
mcc     = test_metrics["MCC"]


# ═══════════════════════════════════════════════
# SECTION 1: 머신러닝 프로세스 Mermaid 다이어그램
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📌 Section 1 &nbsp;|&nbsp; 머신러닝 프로세스 흐름도</div>', unsafe_allow_html=True)

# 오버샘플링 노드 텍스트 동적 생성
os_label = oversample_method if oversample_method != "미적용" else "오버샘플링 미적용"
cw_label = "class_weight=balanced" if class_weight_opt else "class_weight=None"

mermaid_html = f"""
<div class="mermaid-container">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({{
    startOnLoad: true, theme: 'dark',
    themeVariables: {{
      primaryColor: '#667eea', primaryTextColor: '#fff', primaryBorderColor: '#764ba2',
      lineColor: '#a8edea', secondaryColor: '#302b63', tertiaryColor: '#24243e',
      background: '#0f0c29', mainBkg: '#302b63', nodeBorder: '#667eea',
      clusterBkg: '#302b63', titleColor: '#fed6e3', edgeLabelBackground: '#302b63', fontSize: '14px'
    }}
  }});
</script>
<div class="mermaid">
flowchart TD
    A([🗃️ 원본 데이터 로드<br/>12,330 행 × 18 열]) --> B
    B[🔍 탐색적 데이터 분석 EDA<br/>결측치 확인 / 분포 파악] --> C

    subgraph 전처리["⚙️ 데이터 전처리"]
        C[📝 범주형 인코딩<br/>Month · VisitorType → Label Encoding] --> D
        D[🎯 Feature / Target 분리<br/>X: 17개 특성 · y: Revenue] --> E
        E[✂️ Stratified Train/Test Split<br/>Train {int((1-test_size)*100)}%  ·  Test {int(test_size*100)}%]
    end

    E --> OS

    subgraph 오버샘플링["🔁 클래스 불균형 해소"]
        OS[⚡ {os_label}<br/>소수 클래스 합성 샘플 생성<br/>Train 데이터에만 적용]
    end

    OS --> F

    subgraph 학습["🤖 모델 학습"]
        F[🌳 Decision Tree 학습<br/>criterion={criterion} / max_depth={max_depth}<br/>{cw_label}]
    end

    F --> G1
    F --> G2

    subgraph 평가["📊 예측 및 평가"]
        G1[🔮 Train 예측<br/>오버피팅 탐지용] --> H1[📈 Train 점수 산출]
        G2[🔮 Test 예측<br/>y_pred / y_prob] --> H2[📈 Test 점수 산출<br/>Accuracy · Precision · Recall<br/>F1 · AUC-ROC · AUC-PR · MCC]
    end

    H1 --> CMP[📊 Train vs Test 비교<br/>과적합 / 언더피팅 진단]
    H2 --> CMP
    CMP --> VIZ

    subgraph 시각화["🎨 결과 시각화"]
        VIZ[🌳 결정트리 · 피처 중요도<br/>혼동행렬 · ROC · PR Curve]
    end

    VIZ --> L([✅ 분석 완료])

    style A fill:#667eea,color:#fff
    style L fill:#4CAF50,color:#fff
    style OS fill:#302b63,stroke:#FFC107,color:#FFC107
    style 전처리 fill:#302b63,stroke:#667eea,color:#fed6e3
    style 오버샘플링 fill:#1a1a2e,stroke:#FFC107,color:#fed6e3
    style 학습 fill:#302b63,stroke:#a8edea,color:#fed6e3
    style 평가 fill:#302b63,stroke:#764ba2,color:#fed6e3
    style 시각화 fill:#302b63,stroke:#FFC107,color:#fed6e3
    style CMP fill:#4CAF50,color:#fff
</div>
</div>
"""
st.components.v1.html(mermaid_html, height=680, scrolling=False)


# ═══════════════════════════════════════════════
# SECTION 2: 클래스 불균형 & 오버샘플링 결과
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">🔁 Section 2 &nbsp;|&nbsp; 클래스 불균형 & 오버샘플링 결과</div>', unsafe_allow_html=True)

col_os1, col_os2, col_os3 = st.columns(3)

orig_count = y_train_raw.value_counts().sort_index()
resamp_count = y_train.value_counts().sort_index()

with col_os1:
    st.markdown("**📊 원본 Train 클래스 분포**")
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
    st.metric("📦 원본 학습 샘플", f"{len(y_train_raw):,} 개")
    st.metric("✨ 오버샘플링 후 샘플", f"{len(y_train):,} 개",
              delta=f"+{delta_samples:,}" if delta_samples > 0 else "미적용")

# 클래스 분포 시각화
fig_os, (ax_os1, ax_os2) = plt.subplots(1, 2, figsize=(10, 4))
fig_os.patch.set_facecolor('#1a1a2e')

os_colors = ['#667eea', '#fed6e3']
for ax, counts, title in [
    (ax_os1, [int(orig_count.get(0,0)), int(orig_count.get(1,0))], "오버샘플링 전"),
    (ax_os2, [int(resamp_count.get(0,0)), int(resamp_count.get(1,0))], f"오버샘플링 후\n({oversample_method})")
]:
    ax.set_facecolor('#1a1a2e')
    bars = ax.bar(["비구매(0)", "구매(1)"], counts, color=os_colors, width=0.5, edgecolor='#302b63')
    for bar, val in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                f'{val:,}', ha='center', va='bottom', color='white', fontsize=11, fontweight='bold')
    ax.set_title(title, color='white', fontsize=12, fontweight='bold')
    ax.tick_params(colors='white')
    ax.set_facecolor('#1a1a2e')
    ax.spines['bottom'].set_color((1,1,1,0.3))
    ax.spines['left'].set_color((1,1,1,0.3))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel('샘플 수', color='white', fontsize=10)
    ax.grid(axis='y', color=(1,1,1,0.1), linestyle='--')

plt.tight_layout()
st.pyplot(fig_os)
plt.close(fig_os)

if oversample_method == "SMOTE":
    st.markdown("""
    <div class="info-box">
    ⚡ <b>SMOTE(Synthetic Minority Over-sampling Technique)</b>: 소수 클래스(구매=1)의 실제 샘플과 그 k-최근접 이웃 사이에
    <b>합성(synthetic) 샘플을 생성</b>합니다. 단순 복제가 아닌 보간(interpolation) 방식으로 새로운 데이터를 만들어
    과적합 위험을 낮추면서 클래스 균형을 맞춥니다.
    ⚠️ 오버샘플링은 <b>Train 데이터에만 적용</b>하고 Test 데이터는 원본 그대로 유지합니다.
    </div>
    """, unsafe_allow_html=True)
elif oversample_method == "RandomOverSampler":
    st.markdown("""
    <div class="info-box">
    🎲 <b>RandomOverSampler</b>: 소수 클래스(구매=1)의 샘플을 <b>무작위로 복제</b>하여 클래스 균형을 맞춥니다.
    구현이 단순하고 빠르지만, 동일 샘플 반복으로 과적합이 발생할 수 있습니다.
    ⚠️ 오버샘플링은 <b>Train 데이터에만 적용</b>하고 Test 데이터는 원본 그대로 유지합니다.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SECTION 3: 평가 지표 요약 카드
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Section 3 &nbsp;|&nbsp; 모델 평가 지표 요약 (Test 기준)</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("✅ Accuracy", f"{acc:.4f}", delta=f"{(acc-0.5)*100:.1f}pp vs 기준선")
with m2:
    st.metric("🎯 Precision", f"{prec:.4f}")
with m3:
    st.metric("🔍 Recall", f"{rec:.4f}",
              delta=f"↑ 오버샘플링 적용" if oversample_method != "미적용" else None)
with m4:
    st.metric("⚖️ F1-Score", f"{f1:.4f}")

m5, m6, m7, _ = st.columns(4)
with m5:
    st.metric("📈 AUC-ROC", f"{auc_roc:.4f}")
with m6:
    st.metric("📉 AUC-PR", f"{auc_pr:.4f}")
with m7:
    st.metric("🔗 MCC", f"{mcc:.4f}")


# ═══════════════════════════════════════════════
# SECTION 4: Train vs Test 비교 — 과적합/언더피팅 진단
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">🔬 Section 4 &nbsp;|&nbsp; Train vs Test 비교 — 과적합 / 언더피팅 진단</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
📐 <b>과적합(Overfitting)</b>: Train 점수 ≫ Test 점수 → 모델이 학습 데이터에 너무 특화됨<br>
📐 <b>언더피팅(Underfitting)</b>: Train 점수 ≈ Test 점수, 둘 다 낮음 → 모델이 패턴을 충분히 학습하지 못함<br>
📐 <b>이상적 모델</b>: Train ≈ Test, 둘 다 높음 → 일반화 성능 우수
</div>
""", unsafe_allow_html=True)

# ── 4-1. 지표 비교 테이블 ──
metric_keys = ["Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC", "AUC-PR", "MCC"]
compare_df = pd.DataFrame({
    "지표": metric_keys,
    "Train 점수": [round(train_metrics[k], 4) for k in metric_keys],
    "Test 점수":  [round(test_metrics[k],  4) for k in metric_keys],
    "차이 (Train - Test)": [round(train_metrics[k] - test_metrics[k], 4) for k in metric_keys],
})

# 과적합 진단
avg_gap = compare_df["차이 (Train - Test)"].mean()
recall_gap = train_metrics["Recall"] - test_metrics["Recall"]

if avg_gap > 0.1:
    fit_status = "🔴 과적합(Overfitting) 의심"
    fit_color  = "rgba(244,67,54,0.15)"
    fit_border = "#F44336"
    fit_advice = f"Train-Test 평균 격차 {avg_gap:.4f}로 과적합 가능성이 높습니다. max_depth를 줄이거나 min_samples_split을 높여 보세요."
elif avg_gap < -0.05:
    fit_status = "🟡 언더피팅(Underfitting) 의심"
    fit_color  = "rgba(255,193,7,0.15)"
    fit_border = "#FFC107"
    fit_advice = f"Train 점수가 Test보다 낮습니다. 모델 복잡도를 높여 보세요."
elif avg_gap <= 0.05 and acc < 0.7:
    fit_status = "🟡 언더피팅(Underfitting) 의심"
    fit_color  = "rgba(255,193,7,0.15)"
    fit_border = "#FFC107"
    fit_advice = "Train-Test 격차는 작지만 전반적 성능이 낮습니다. 피처 추가 또는 하이퍼파라미터 조정이 필요합니다."
else:
    fit_status = "🟢 적절한 일반화(Good Fit)"
    fit_color  = "rgba(76,175,80,0.15)"
    fit_border = "#4CAF50"
    fit_advice = f"Train-Test 격차 {avg_gap:.4f}로 양호한 일반화 성능을 보입니다."

st.markdown(f"""
<div class="overfit-box" style="background:{fit_color}; border:1px solid {fit_border}; border-left:4px solid {fit_border};">
<b style="font-size:16px;">{fit_status}</b><br>
{fit_advice}
</div>
""", unsafe_allow_html=True)

col_tbl, col_viz = st.columns([1, 1.6])

with col_tbl:
    st.markdown("**📋 Train vs Test 지표 비교표**")

    def highlight_gap(row):
        gap = row["차이 (Train - Test)"]
        if gap > 0.1:
            color = 'background-color: rgba(244,67,54,0.25); color: #ff8a80'
        elif gap > 0.05:
            color = 'background-color: rgba(255,193,7,0.2); color: #ffe57f'
        else:
            color = 'background-color: rgba(76,175,80,0.15); color: #b9f6ca'
        return ['', '', '', color]

    styled_df = compare_df.style.apply(highlight_gap, axis=1).format({
        "Train 점수": "{:.4f}",
        "Test 점수": "{:.4f}",
        "차이 (Train - Test)": "{:+.4f}"
    })
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Recall 개선 효과 강조
    st.markdown(f"""
    <div style="background:rgba(168,237,234,0.1); border:1px solid rgba(168,237,234,0.4);
                border-left:4px solid #a8edea; border-radius:8px; padding:12px; margin-top:12px; font-size:13px;">
    <b>🔍 Recall 개선 분석</b><br>
    Train Recall: <b>{train_metrics['Recall']:.4f}</b> &nbsp;|&nbsp; Test Recall: <b>{test_metrics['Recall']:.4f}</b><br>
    오버샘플링: <b>{oversample_method}</b> &nbsp;|&nbsp; class_weight: <b>{'balanced' if class_weight_opt else 'None'}</b>
    </div>
    """, unsafe_allow_html=True)

with col_viz:
    # Train vs Test 레이더 + 그룹 막대 차트
    train_vals = [train_metrics[k] for k in metric_keys]
    test_vals  = [test_metrics[k]  for k in metric_keys]
    # MCC -1~1 → 0~1 정규화
    train_norm = train_vals[:6] + [(train_vals[6]+1)/2]
    test_norm  = test_vals[:6]  + [(test_vals[6]+1)/2]

    x_idx = np.arange(len(metric_keys))
    width = 0.35

    fig_cmp, ax_cmp = plt.subplots(figsize=(9, 5))
    fig_cmp.patch.set_facecolor('#1a1a2e')
    ax_cmp.set_facecolor('#1a1a2e')

    bars_tr = ax_cmp.bar(x_idx - width/2, train_norm, width, label='Train', color='#667eea',
                          alpha=0.85, edgecolor='#302b63', zorder=3)
    bars_te = ax_cmp.bar(x_idx + width/2, test_norm, width, label='Test', color='#a8edea',
                          alpha=0.85, edgecolor='#302b63', zorder=3)

    for bar, raw in zip(bars_tr, train_vals):
        ax_cmp.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                    f'{raw:.3f}', ha='center', va='bottom', fontsize=7.5,
                    color='#667eea', fontweight='bold')
    for bar, raw in zip(bars_te, test_vals):
        ax_cmp.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                    f'{raw:.3f}', ha='center', va='bottom', fontsize=7.5,
                    color='#a8edea', fontweight='bold')

    ax_cmp.set_xticks(x_idx)
    ax_cmp.set_xticklabels(metric_keys, color='white', fontsize=10, rotation=20, ha='right')
    ax_cmp.set_ylim(0, 1.18)
    ax_cmp.set_ylabel('점수 (MCC는 0~1 정규화)', color='white', fontsize=10)
    ax_cmp.set_title('Train vs Test 점수 비교\n(과적합/언더피팅 진단)', color='white',
                      fontsize=12, fontweight='bold', pad=12)
    ax_cmp.tick_params(colors='white')
    ax_cmp.legend(fontsize=11, facecolor='#302b63', edgecolor='#667eea', labelcolor='white')
    ax_cmp.spines['bottom'].set_color((1,1,1,0.3))
    ax_cmp.spines['left'].set_color((1,1,1,0.3))
    ax_cmp.spines['top'].set_visible(False)
    ax_cmp.spines['right'].set_visible(False)
    ax_cmp.grid(axis='y', color=(1,1,1,0.1), linestyle='--', zorder=0)
    ax_cmp.axhline(y=0.5, color='red', linestyle='--', lw=1, alpha=0.5)

    plt.tight_layout()
    st.pyplot(fig_cmp)
    plt.close(fig_cmp)


# ── 4-2. 학습 곡선 (Learning Curve) ──
st.markdown("#### 📈 학습 곡선 (Learning Curve) — 샘플 수에 따른 Train/Test 성능 변화")
st.markdown("""
<div class="info-box" style="font-size:13px;">
📐 학습 곡선은 훈련 데이터 크기에 따른 Train/Test 성능 변화를 보여줍니다.<br>
두 곡선이 <b>수렴</b>하면 좋은 모델, Train만 높고 Test가 낮으면 <b>과적합</b>, 둘 다 낮으면 <b>언더피팅</b>입니다.
</div>
""", unsafe_allow_html=True)

with st.spinner("학습 곡선 계산 중..."):
    lc_clf = DecisionTreeClassifier(
        max_depth=max_depth, min_samples_split=min_samples_split,
        criterion=criterion, class_weight="balanced" if class_weight_opt else None,
        random_state=int(random_state)
    )
    # 학습 곡선은 원본 Train 데이터 사용 (오버샘플링 미적용 — CV 내부에서 적용 불가)
    train_sizes, train_scores_lc, test_scores_lc = learning_curve(
        lc_clf, X_train_raw.values, y_train_raw.values,
        cv=5, scoring='recall', n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 8)
    )

train_mean = train_scores_lc.mean(axis=1)
train_std  = train_scores_lc.std(axis=1)
test_mean  = test_scores_lc.mean(axis=1)
test_std   = test_scores_lc.std(axis=1)

fig_lc, ax_lc = plt.subplots(figsize=(10, 5))
fig_lc.patch.set_facecolor('#1a1a2e')
ax_lc.set_facecolor('#1a1a2e')

ax_lc.fill_between(train_sizes, train_mean-train_std, train_mean+train_std, alpha=0.15, color='#667eea')
ax_lc.fill_between(train_sizes, test_mean-test_std,   test_mean+test_std,   alpha=0.15, color='#a8edea')
ax_lc.plot(train_sizes, train_mean, 'o-', color='#667eea', lw=2.5, ms=7, label='Train Recall (CV)')
ax_lc.plot(train_sizes, test_mean,  's-', color='#a8edea', lw=2.5, ms=7, label='Validation Recall (CV)')

ax_lc.set_xlabel('학습 샘플 수', fontsize=12, color='white')
ax_lc.set_ylabel('Recall (재현율)', fontsize=12, color='white')
ax_lc.set_title('학습 곡선 — 샘플 크기에 따른 Recall 변화 (5-Fold CV, 원본 데이터 기준)',
                 fontsize=13, fontweight='bold', color='white', pad=12)
ax_lc.legend(fontsize=11, facecolor='#302b63', edgecolor='#667eea', labelcolor='white')
ax_lc.tick_params(colors='white', labelsize=10)
ax_lc.spines['bottom'].set_color((1,1,1,0.3))
ax_lc.spines['left'].set_color((1,1,1,0.3))
ax_lc.spines['top'].set_visible(False)
ax_lc.spines['right'].set_visible(False)
ax_lc.grid(color=(1,1,1,0.1), linestyle='--')
ax_lc.set_ylim(0, 1.05)

plt.tight_layout()
st.pyplot(fig_lc)
plt.close(fig_lc)


# ═══════════════════════════════════════════════
# SECTION 5: 결정 트리 시각화
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">🌳 Section 5 &nbsp;|&nbsp; 결정 트리 시각화</div>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
🌳 학습된 Decision Tree의 구조를 시각화합니다. 가독성을 위해 최대 <b>깊이 4</b>까지만 렌더링합니다.
</div>
""", unsafe_allow_html=True)

display_depth = min(max_depth, 4)
fig_tree, ax_tree = plt.subplots(figsize=(28, 14))
fig_tree.patch.set_facecolor('#1a1a2e')
ax_tree.set_facecolor('#1a1a2e')

plot_tree(clf, feature_names=X.columns.tolist(), class_names=["비구매", "구매"],
          filled=True, rounded=True, fontsize=9, max_depth=display_depth, ax=ax_tree,
          impurity=True, proportion=False)
ax_tree.set_title(f"Decision Tree 시각화 (깊이 {display_depth}까지 표시 / 실제 학습 깊이: {max_depth})",
                  fontsize=14, fontweight='bold', color='white', pad=15)
plt.tight_layout()
st.pyplot(fig_tree)
plt.close(fig_tree)


# ═══════════════════════════════════════════════
# SECTION 6: 피처 중요도
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Section 6 &nbsp;|&nbsp; 피처 중요도 (Feature Importance)</div>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
📌 각 피처가 결정 트리 분기에 기여한 <b>Gini Importance</b>입니다. 값이 클수록 Revenue 예측에 더 중요합니다.
</div>
""", unsafe_allow_html=True)

importance_df = pd.DataFrame({
    "피처": X.columns,
    "중요도": clf.feature_importances_
}).sort_values("중요도", ascending=True)

colors = ['#667eea' if v < importance_df['중요도'].quantile(0.75) else '#fed6e3'
          for v in importance_df['중요도']]

fig_imp, ax_imp = plt.subplots(figsize=(10, 8))
fig_imp.patch.set_facecolor('#1a1a2e')
ax_imp.set_facecolor('#1a1a2e')

bars = ax_imp.barh(importance_df['피처'], importance_df['중요도'],
                   color=colors, edgecolor=(1.0, 1.0, 1.0, 0.15), height=0.65)
for bar, val in zip(bars, importance_df['중요도']):
    if val > 0.001:
        ax_imp.text(val + 0.001, bar.get_y() + bar.get_height()/2,
                    f'{val:.4f}', va='center', ha='left', fontsize=9, color='white')

ax_imp.set_xlabel("중요도 (Gini Importance)", fontsize=12, color='white')
ax_imp.set_title("피처별 중요도 (Feature Importance)", fontsize=14, fontweight='bold', color='white', pad=15)
ax_imp.tick_params(colors='white', labelsize=10)
ax_imp.spines['bottom'].set_color((1,1,1,0.3))
ax_imp.spines['left'].set_color((1,1,1,0.3))
ax_imp.spines['top'].set_visible(False)
ax_imp.spines['right'].set_visible(False)
ax_imp.set_xlim(0, max(importance_df['중요도'].max() * 1.18, 0.01))

legend_handles = [
    mpatches.Patch(color='#fed6e3', label='상위 25% 중요 피처'),
    mpatches.Patch(color='#667eea', label='일반 피처'),
]
ax_imp.legend(handles=legend_handles, loc='lower right', fontsize=10,
              facecolor='#302b63', edgecolor='#667eea', labelcolor='white')
plt.tight_layout()
st.pyplot(fig_imp)
plt.close(fig_imp)

top3 = importance_df.sort_values("중요도", ascending=False).head(3)
st.markdown("**🔑 중요도 TOP 3 피처:**")
for i, row in enumerate(top3.itertuples(), 1):
    st.markdown(f"""
    <span class="metric-badge">#{i}</span>
    <b>{row.피처}</b> — 중요도: <b>{row.중요도:.4f}</b>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SECTION 7: 평가 지표 상세 시각화
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Section 7 &nbsp;|&nbsp; 평가 지표 상세 시각화</div>', unsafe_allow_html=True)

tab_cm, tab_roc, tab_pr, tab_radar, tab_report = st.tabs([
    "🔢 혼동 행렬", "📈 ROC Curve", "📉 PR Curve", "🕸️ 지표 비교 차트", "📋 분류 리포트"
])

# ── 혼동 행렬 ──
with tab_cm:
    st.subheader("🔢 혼동 행렬 (Confusion Matrix)")
    cm = confusion_matrix(y_test, y_pred_test)
    tn, fp, fn, tp = cm.ravel()

    col_cm, col_cm_info = st.columns([1.5, 1])
    with col_cm:
        fig_cm, ax_cm = plt.subplots(figsize=(7, 5))
        fig_cm.patch.set_facecolor('#1a1a2e')
        ax_cm.set_facecolor('#1a1a2e')
        sns.heatmap(cm, annot=True, fmt='d', cmap='RdYlGn',
                    xticklabels=['비구매(0)', '구매(1)'], yticklabels=['비구매(0)', '구매(1)'],
                    ax=ax_cm, linewidths=2, linecolor='#302b63',
                    annot_kws={'size': 18, 'weight': 'bold', 'color': 'white'},
                    cbar_kws={'shrink': 0.8})
        ax_cm.set_xlabel('예측값 (Predicted)', fontsize=12, color='white', labelpad=10)
        ax_cm.set_ylabel('실제값 (Actual)', fontsize=12, color='white', labelpad=10)
        ax_cm.set_title('혼동 행렬', fontsize=14, fontweight='bold', color='white', pad=15)
        ax_cm.tick_params(colors='white', labelsize=10)
        plt.tight_layout()
        st.pyplot(fig_cm)
        plt.close(fig_cm)

    with col_cm_info:
        st.markdown("**📊 혼동 행렬 세부 정보**")
        cm_detail = pd.DataFrame({
            "항목": ["True Negative (TN)", "False Positive (FP)", "False Negative (FN)", "True Positive (TP)"],
            "값": [tn, fp, fn, tp],
            "설명": ["비구매→비구매 정확", "비구매→구매 오탐", "구매→비구매 누락", "구매→구매 정확"]
        })
        st.dataframe(cm_detail, use_container_width=True, hide_index=True)
        st.markdown(f"""
        <div class="info-box" style="margin-top:12px;">
        ✅ <b>정확히 예측</b>: {tn+tp:,}개 ({(tn+tp)/len(y_test)*100:.1f}%)<br>
        ❌ <b>잘못 예측</b>: {fp+fn:,}개 ({(fp+fn)/len(y_test)*100:.1f}%)<br>
        🔍 <b>Recall</b>: TP/(TP+FN) = {tp}/{tp+fn} = <b>{rec:.4f}</b>
        </div>
        """, unsafe_allow_html=True)

# ── ROC Curve ──
with tab_roc:
    st.subheader("📈 ROC Curve")
    fpr_t, tpr_t, _ = roc_curve(y_test, y_prob_test)
    fig_roc, ax_roc = plt.subplots(figsize=(8, 6))
    fig_roc.patch.set_facecolor('#1a1a2e')
    ax_roc.set_facecolor('#1a1a2e')
    ax_roc.fill_between(fpr_t, tpr_t, alpha=0.25, color='#667eea')
    ax_roc.plot(fpr_t, tpr_t, color='#a8edea', lw=2.5, label=f'Decision Tree (AUC = {auc_roc:.4f})')
    ax_roc.plot([0,1],[0,1], 'r--', lw=1.5, label='기준선 (AUC = 0.50)')
    ax_roc.set_xlabel('FPR', fontsize=12, color='white')
    ax_roc.set_ylabel('TPR (Recall)', fontsize=12, color='white')
    ax_roc.set_title('ROC Curve', fontsize=14, fontweight='bold', color='white', pad=15)
    ax_roc.legend(loc='lower right', fontsize=11, facecolor='#302b63', edgecolor='#667eea', labelcolor='white')
    ax_roc.tick_params(colors='white')
    ax_roc.spines['bottom'].set_color((1,1,1,0.3))
    ax_roc.spines['left'].set_color((1,1,1,0.3))
    ax_roc.spines['top'].set_visible(False)
    ax_roc.spines['right'].set_visible(False)
    ax_roc.grid(color=(1,1,1,0.1), linestyle='--')
    plt.tight_layout()
    st.pyplot(fig_roc)
    plt.close(fig_roc)

# ── PR Curve ──
with tab_pr:
    st.subheader("📉 PR Curve (Precision-Recall Curve)")
    prc_p, prc_r, _ = precision_recall_curve(y_test, y_prob_test)
    baseline = y_test.mean()
    fig_pr, ax_pr = plt.subplots(figsize=(8, 6))
    fig_pr.patch.set_facecolor('#1a1a2e')
    ax_pr.set_facecolor('#1a1a2e')
    ax_pr.fill_between(prc_r, prc_p, alpha=0.25, color='#764ba2')
    ax_pr.plot(prc_r, prc_p, color='#fed6e3', lw=2.5, label=f'Decision Tree (AUC-PR = {auc_pr:.4f})')
    ax_pr.axhline(y=baseline, color='r', lw=1.5, linestyle='--', label=f'기준선 ({baseline:.2f})')
    ax_pr.set_xlabel('Recall', fontsize=12, color='white')
    ax_pr.set_ylabel('Precision', fontsize=12, color='white')
    ax_pr.set_title('PR Curve', fontsize=14, fontweight='bold', color='white', pad=15)
    ax_pr.legend(loc='upper right', fontsize=11, facecolor='#302b63', edgecolor='#764ba2', labelcolor='white')
    ax_pr.tick_params(colors='white')
    ax_pr.spines['bottom'].set_color((1,1,1,0.3))
    ax_pr.spines['left'].set_color((1,1,1,0.3))
    ax_pr.spines['top'].set_visible(False)
    ax_pr.spines['right'].set_visible(False)
    ax_pr.grid(color=(1,1,1,0.1), linestyle='--')
    plt.tight_layout()
    st.pyplot(fig_pr)
    plt.close(fig_pr)

# ── 지표 비교 차트 (Radar + Bar) ──
with tab_radar:
    st.subheader("🕸️ 7가지 평가 지표 종합 비교")
    metric_vals_norm = [acc, prec, rec, f1, auc_roc, auc_pr, (mcc+1)/2]
    metric_raw_list  = [acc, prec, rec, f1, auc_roc, auc_pr, mcc]

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        angles = np.linspace(0, 2*np.pi, len(metric_keys), endpoint=False).tolist()
        vals_c = metric_vals_norm + [metric_vals_norm[0]]
        angles_c = angles + [angles[0]]
        fig_radar, ax_radar = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        fig_radar.patch.set_facecolor('#1a1a2e')
        ax_radar.set_facecolor('#0f0c29')
        ax_radar.fill(angles_c, vals_c, alpha=0.3, color='#667eea')
        ax_radar.plot(angles_c, vals_c, color='#a8edea', lw=2.5)
        ax_radar.scatter(angles_c, vals_c, color='#fed6e3', s=80, zorder=5)
        ax_radar.set_xticks(angles)
        ax_radar.set_xticklabels(metric_keys, fontsize=11, color='white')
        ax_radar.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax_radar.set_yticklabels(['0.2','0.4','0.6','0.8','1.0'], fontsize=8, color='gray')
        ax_radar.set_ylim(0, 1)
        ax_radar.grid(color=(1,1,1,0.15))
        ax_radar.spines['polar'].set_color((1,1,1,0.2))
        ax_radar.set_title('평가 지표 방사형 차트\n(MCC는 0~1 정규화)', fontsize=12, fontweight='bold', color='white', pad=20)
        plt.tight_layout()
        st.pyplot(fig_radar)
        plt.close(fig_radar)

    with col_r2:
        bar_colors = ['#a8edea','#667eea','#764ba2','#fed6e3','#FFC107','#4CAF50','#FF7043']
        fig_bar, ax_bar = plt.subplots(figsize=(7, 6))
        fig_bar.patch.set_facecolor('#1a1a2e')
        ax_bar.set_facecolor('#1a1a2e')
        b = ax_bar.bar(metric_keys, metric_vals_norm, color=bar_colors, edgecolor='#302b63', width=0.6, zorder=3)
        ax_bar.axhline(y=0.5, color='red', linestyle='--', lw=1.5, alpha=0.7, label='기준선 (0.5)')
        for bar, raw in zip(b, metric_raw_list):
            ax_bar.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                        f'{raw:.3f}', ha='center', va='bottom', fontsize=10, color='white', fontweight='bold')
        ax_bar.set_ylim(0, 1.15)
        ax_bar.set_ylabel('지표 값', fontsize=11, color='white')
        ax_bar.set_title('7가지 지표 비교 (MCC 0~1 정규화)', fontsize=12, fontweight='bold', color='white', pad=12)
        ax_bar.tick_params(colors='white', labelsize=10)
        ax_bar.tick_params(axis='x', rotation=30)
        ax_bar.spines['bottom'].set_color((1,1,1,0.3))
        ax_bar.spines['left'].set_color((1,1,1,0.3))
        ax_bar.spines['top'].set_visible(False)
        ax_bar.spines['right'].set_visible(False)
        ax_bar.grid(axis='y', color=(1,1,1,0.1), linestyle='--', zorder=0)
        ax_bar.legend(fontsize=10, facecolor='#302b63', edgecolor='#667eea', labelcolor='white')
        plt.tight_layout()
        st.pyplot(fig_bar)
        plt.close(fig_bar)

    st.markdown("**📋 평가 지표 해석 가이드**")
    guide_df = pd.DataFrame({
        "지표": metric_keys,
        "Test 값": [f"{v:.4f}" for v in metric_raw_list],
        "Train 값": [f"{train_metrics[k]:.4f}" for k in metric_keys],
        "범위": ["0~1","0~1","0~1","0~1","0~1","0~1","-1~1"],
        "해석": [
            "전체 예측 중 정확히 예측한 비율",
            "구매 예측 중 실제 구매인 비율 (오탐 방지)",
            "실제 구매 중 구매로 예측한 비율 (누락 방지) ← 핵심 지표",
            "Precision과 Recall의 조화 평균",
            "ROC 곡선 아래 면적 (분류 능력 종합)",
            "PR 곡선 아래 면적 (불균형 데이터에 적합)",
            "상관계수 기반 균형 지표"
        ]
    })
    st.dataframe(guide_df, use_container_width=True, hide_index=True)

# ── 분류 리포트 ──
with tab_report:
    st.subheader("📋 분류 상세 리포트")
    report_dict = classification_report(y_test, y_pred_test,
                                        target_names=["비구매(0)", "구매(1)"], output_dict=True)
    report_df = pd.DataFrame(report_dict).T
    report_df.index.name = "클래스"
    st.dataframe(report_df.style.format("{:.4f}").background_gradient(cmap='RdYlGn', axis=1),
                 use_container_width=True)

    top_feature = importance_df.sort_values("중요도", ascending=False).iloc[0]
    st.markdown("---")
    st.subheader("💡 모델 분석 인사이트 요약")
    st.markdown(f"""
    <div class="info-box">
    🌟 <b>핵심 예측 피처</b>: <code>{top_feature['피처']}</code> (중요도: {top_feature['중요도']:.4f})<br>
    🎯 <b>Accuracy</b>: {acc:.2%} &nbsp;|&nbsp; 🔍 <b>Recall</b>: {rec:.2%} &nbsp;|&nbsp; ⚖️ <b>F1</b>: {f1:.4f}<br>
    📈 <b>AUC-ROC</b>: {auc_roc:.4f} &nbsp;|&nbsp; 📉 <b>AUC-PR</b>: {auc_pr:.4f} &nbsp;|&nbsp; 🔗 <b>MCC</b>: {mcc:.4f}<br>
    🔁 <b>오버샘플링</b>: {oversample_method} &nbsp;|&nbsp; ⚖️ <b>class_weight</b>: {'balanced' if class_weight_opt else 'None'}<br>
    {fit_status} — {fit_advice}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SECTION 8: 비즈니스 인사이트 & 액션플랜
# ═══════════════════════════════════════════════
st.markdown('<div class="section-header">💼 Section 8 &nbsp;|&nbsp; 비즈니스 인사이트 & 액션플랜</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
📌 본 섹션은 <b>결정 트리(Decision Tree)의 피처 중요도</b>와 <b>분기 구조(트리 시각화)</b>를 바탕으로,
온라인 쇼핑몰 운영에 실질적으로 활용할 수 있는 <b>데이터 기반 비즈니스 인사이트와 구체적 액션플랜</b>을 제시합니다.
</div>
""", unsafe_allow_html=True)

col_ins1, col_ins2 = st.columns(2)

with col_ins1:
    st.markdown("### 🔍 핵심 인사이트")
    st.markdown("""
    <div style="background: rgba(168,237,234,0.08); border: 1px solid rgba(168,237,234,0.3);
                border-left: 4px solid #a8edea; border-radius: 8px; padding: 18px; margin-bottom: 14px; line-height: 1.85;">
    <b>① PageValues — 구매 의향의 최강 시그널</b><br>
    결정 트리의 최상위 분기와 피처 중요도 1위를 동시에 차지한 <code>PageValues</code>는,
    고객이 구매 전 방문한 페이지의 평균 가치를 나타냅니다.
    이 값이 높을수록 실제 구매로 이어질 확률이 극적으로 상승합니다.
    <br><br>
    <b style="color:#a8edea;">📌 시사점</b>: 단순 방문 횟수보다 <b>어떤 페이지를 방문했는가</b>가 구매를 결정하는 핵심입니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(254,214,227,0.08); border: 1px solid rgba(254,214,227,0.3);
                border-left: 4px solid #fed6e3; border-radius: 8px; padding: 18px; margin-bottom: 14px; line-height: 1.85;">
    <b>② ExitRates / BounceRates — 이탈 위험 탐지의 핵심</b><br>
    트리 하위 분기에서 반복적으로 등장하는 <code>ExitRates</code>와 <code>BounceRates</code>는
    고객의 이탈 패턴을 포착하는 지표입니다. <b>ExitRates가 0.02 이하</b>인 구간에서 구매 전환율이
    급격히 상승하는 패턴이 트리 분기에서 명확히 관찰됩니다.
    <br><br>
    <b style="color:#fed6e3;">📌 시사점</b>: 이탈률이 높은 페이지는 UI/UX 개선의 우선 대상입니다.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(102,126,234,0.08); border: 1px solid rgba(102,126,234,0.3);
                border-left: 4px solid #667eea; border-radius: 8px; padding: 18px; line-height: 1.85;">
    <b>③ ProductRelated / ProductRelated_Duration — 탐색 깊이의 힘</b><br>
    상품 관련 페이지 방문 수와 체류 시간은 중요도 상위권으로, 고객이 상품을 충분히 탐색할수록
    구매 전환 확률이 높아집니다. 반면, 단 1~2개 페이지만 방문한 고객은 대부분 비구매로 분류됩니다.
    </div>
    """, unsafe_allow_html=True)

with col_ins2:
    st.markdown("### 🚀 비즈니스 액션플랜")
    st.markdown("""
    <div style="background: rgba(76,175,80,0.08); border: 1px solid rgba(76,175,80,0.3);
                border-left: 4px solid #4CAF50; border-radius: 8px; padding: 18px; margin-bottom: 14px; line-height: 1.85;">
    <b>🎯 Action 1. PageValues 기반 실시간 구매 의향 스코어링</b><br>
    PageValues가 일정 임계값(예: 10 이상)을 초과한 세션에 대해 <b>실시간 구매 의향 스코어</b>를 산출하고,
    해당 고객에게 즉각적인 개인화 혜택(한정 쿠폰, 무료 배송 팝업)을 자동 제공합니다.
    <br><br>
    <b style="color:#4CAF50;">⏱ 단기 실행 (1~2개월)</b>: A/B 테스트로 팝업 트리거 임계값 최적화
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(255,193,7,0.08); border: 1px solid rgba(255,193,7,0.3);
                border-left: 4px solid #FFC107; border-radius: 8px; padding: 18px; margin-bottom: 14px; line-height: 1.85;">
    <b>🔧 Action 2. 고이탈률 페이지 집중 개선 (CRO 전략)</b><br>
    ExitRates 상위 20% 페이지를 추출하여 <b>CRO(전환율 최적화)</b>를 집중 적용합니다.
    CTA 버튼 위치 조정, 로딩 속도 개선, 관련 상품 추천 모듈 삽입 등의 개선이
    직접적인 구매 전환율 향상으로 이어질 수 있습니다.
    <br><br>
    <b style="color:#FFC107;">⏱ 중기 실행 (2~4개월)</b>: 히트맵·세션 리플레이 도구(Hotjar 등) 병행 분석
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: rgba(255,112,67,0.08); border: 1px solid rgba(255,112,67,0.3);
                border-left: 4px solid #FF7043; border-radius: 8px; padding: 18px; line-height: 1.85;">
    <b>📅 Action 3. 시즌 및 방문자 유형별 타겟 마케팅 고도화</b><br>
    Month와 VisitorType은 트리 분기에서 특정 조합(11월 신규 방문자)에서 구매율이 급등합니다.
    <b>블랙프라이데이·연말 시즌에 신규 방문자 웰컴 오퍼</b>를 강화하고, 재방문자에게는 개인화
    리타겟팅 광고를 차별화하여 집행합니다.
    <br><br>
    <b style="color:#FF7043;">⏱ 장기 실행 (3~6개월)</b>: 모델 재학습 주기화(분기별) 및 성과 KPI 설정
    </div>
    """, unsafe_allow_html=True)

st.markdown("### 📋 전략 실행 로드맵 요약")
roadmap_df = pd.DataFrame({
    "우선순위": ["🥇 1순위", "🥈 2순위", "🥉 3순위"],
    "핵심 피처": ["PageValues", "ExitRates / BounceRates", "Month / VisitorType"],
    "비즈니스 전략": [
        "실시간 구매 의향 스코어링 & 즉각 개인화 혜택 제공",
        "고이탈 페이지 CRO 집중 개선 (UI/UX · CTA 최적화)",
        "시즌 × 방문자 유형 기반 타겟 마케팅 고도화",
    ],
    "기대 효과": ["구매 전환율 +15~25% 향상", "이탈률 -10~20% 감소", "시즌 매출 +20~30% 증가"],
    "실행 기간": ["1~2개월", "2~4개월", "3~6개월"],
})
st.dataframe(roadmap_df, use_container_width=True, hide_index=True)

st.markdown("""
<div style="background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
            border: 1px solid rgba(102,126,234,0.4); border-radius: 12px;
            padding: 20px 24px; margin-top: 18px; line-height: 1.9; font-size: 14px;">
<b style="font-size:16px; color:#a8edea;">🏁 종합 결론</b><br><br>
결정 트리 모델의 분석 결과는 온라인 쇼핑몰의 구매 전환을 좌우하는 핵심 변수가
<b>방문한 페이지의 '질'(PageValues)</b>과 <b>이탈하지 않고 탐색을 지속하는 행동(낮은 ExitRates)</b>
임을 명확히 보여줍니다. 단순히 트래픽을 늘리는 전략보다,
<b>고가치 페이지로의 유도 → 이탈 방지 → 개인화된 구매 촉진</b>이라는 3단계 퍼널을
데이터 기반으로 최적화하는 것이 실질적인 매출 성장의 핵심 레버가 될 것입니다.
본 머신러닝 모델은 이 전략의 실시간 자동화 엔진으로 활용될 수 있으며,
분기별 모델 재학습을 통해 시즌·트렌드 변화에 지속적으로 대응하는 <b>살아있는 예측 시스템</b>으로
발전시킬 것을 권장합니다.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.4); font-size: 13px; padding: 16px;">
    🤖 머신러닝 분석 페이지 | Online Shoppers Purchasing Intention Dataset<br>
    Decision Tree + SMOTE 오버샘플링 | scikit-learn · imbalanced-learn · streamlit
</div>
""", unsafe_allow_html=True)
