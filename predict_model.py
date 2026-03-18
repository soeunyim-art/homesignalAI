"""
HomeSignal AI - 동대문구 아파트 매매가 예측 모델
금리 + 전월세가 → 1~3개월 후 동별 매매가 Ridge 회귀 분석

실행 전 필수:
  1. supabase_views.sql 을 Supabase SQL Editor에서 실행
  2. pip install -r requirements.txt
"""

import os
import warnings
import requests
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")              # 화면 없는 환경에서도 PNG 저장
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split  # noqa: F401 (reserved for future use)
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings("ignore")
load_dotenv("homesignal.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 한글 폰트 (Windows)
plt.rcParams["font.family"]       = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ─────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────
def fetch_all(view: str) -> list[dict]:
    """Supabase REST API 페이지네이션 전체 조회"""
    url     = f"{SUPABASE_URL}/rest/v1/{view}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    rows, offset = [], 0
    while True:
        params = {"limit": "1000", "offset": str(offset)}
        resp   = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Supabase {resp.status_code}: {resp.text[:300]}")
        batch = resp.json()
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += len(batch)
    return rows


def load_data() -> pd.DataFrame:
    print("  v_model_features 로드 중...")
    rows = fetch_all("v_model_features")
    df   = pd.DataFrame(rows)

    num_cols = [
        "avg_price_10k", "median_price_10k", "avg_price_per_sqm", "avg_area",
        "trade_count",   "jeonse_count",     "avg_jeonse_10k",    "avg_jeonse_per_sqm",
        "wolse_count",   "avg_monthly_rent_10k",
        "rate_base",     "rate_cd",          "rate_bond3y",
        # 뉴스 피처 (없으면 0 으로 채움)
        "total_news",    "regulation_news",  "easing_news",
        "transport_news","redevelop_news",   "macro_sentiment",
        "local_news_count", "local_redevelop_count",
        "local_regulation_count", "local_transport_count",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = 0.0   # 뉴스 뷰 미생성 시 0으로 대체 (모델 실행 유지)

    df["deal_year"]  = df["deal_year"].astype(int)
    df["deal_month"] = df["deal_month"].astype(int)
    df["ym"] = pd.to_datetime(
        df["deal_year"].astype(str) + "-" + df["deal_month"].astype(str).str.zfill(2)
    )
    df = df.sort_values(["dong", "ym"]).reset_index(drop=True)
    print(f"  {len(df):,}행 로드 완료 (동: {df['dong'].nunique()}개, "
          f"기간: {df['ym'].min().strftime('%Y-%m')} ~ {df['ym'].max().strftime('%Y-%m')})")
    return df


# ─────────────────────────────────────────
# 2. Feature Engineering
# ─────────────────────────────────────────
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """동별 그룹으로 시계열 lag / 변화율 / 전세가율 피처 생성"""
    dfs = []
    for _, g in df.groupby("dong"):
        g = g.sort_values("ym").copy()

        # 전세 거래가 없는 달은 직전값으로 채움 (forward fill)
        # → 일부 동에서 최신 달 jeonse NULL로 인한 기준월 오래됨 방지
        for col in ["avg_jeonse_10k", "avg_jeonse_per_sqm", "jeonse_count"]:
            if col in g.columns:
                g[col] = g[col].ffill()

        # 뉴스 피처 결측치 처리
        # · 뉴스가 없는 달(데이터 수집 전 기간)은 0으로 채움
        # · macro_sentiment만 0.0 (중립) 기본값 사용
        for col in ["total_news", "regulation_news", "easing_news",
                    "transport_news", "redevelop_news",
                    "local_news_count", "local_redevelop_count",
                    "local_regulation_count", "local_transport_count"]:
            if col in g.columns:
                g[col] = g[col].fillna(0)
        if "macro_sentiment" in g.columns:
            g["macro_sentiment"] = g["macro_sentiment"].fillna(0.0)

        # Lag 1~3개월 (과거 가격 참조)
        for lag in [1, 2, 3]:
            g[f"price_lag{lag}"]  = g["avg_price_10k"].shift(lag)
            g[f"jeonse_lag{lag}"] = g["avg_jeonse_10k"].shift(lag)
            g[f"rbase_lag{lag}"]  = g["rate_base"].shift(lag)
            g[f"rcd_lag{lag}"]    = g["rate_cd"].shift(lag)
            g[f"rbond_lag{lag}"]  = g["rate_bond3y"].shift(lag)

        # 전월 대비 변화율 (%)
        g["price_mom"]   = g["avg_price_10k"].pct_change() * 100
        g["jeonse_mom"]  = g["avg_jeonse_10k"].pct_change() * 100
        g["rate_change"] = g["rate_base"].diff()

        # 전년 동월 대비 변화율 (YoY, %)
        g["price_yoy"]   = g["avg_price_10k"].pct_change(12) * 100
        g["jeonse_yoy"]  = g["avg_jeonse_10k"].pct_change(12) * 100

        # 전세가율 (전세가 / 매매가)  →  높을수록 매매가 저평가 신호
        g["jeonse_ratio"] = g["avg_jeonse_10k"] / g["avg_price_10k"].replace(0, np.nan)

        # 계절성 (월) - sin/cos 변환: 12월과 1월이 가까운 값이 되도록
        g["month_sin"] = np.sin(2 * np.pi * g["ym"].dt.month / 12)
        g["month_cos"] = np.cos(2 * np.pi * g["ym"].dt.month / 12)

        # 타겟: 1·3·6개월 후 매매가 변화율 (%)  ← 절대가 대신 변화율로 예측 (동별 가격 차이 제거)
        for h in HORIZONS:
            future = g["avg_price_10k"].shift(-h)
            g[f"target_{h}m"] = (future - g["avg_price_10k"]) / g["avg_price_10k"] * 100

        dfs.append(g)

    result = pd.concat(dfs, ignore_index=True)
    # inf 처리
    result = result.replace([np.inf, -np.inf], np.nan)
    return result


# 수치형 피처 목록
# 변경 이력:
#   - avg_price_10k 제거: 타겟(변화율) 계산에 현재가가 직접 쓰이므로 정보 누수
#   - rate_cd, rate_bond3y 제거: 기준금리와 거의 동일하게 움직이는 중복 피처
#   - month 제거 → month_sin/cos 추가: 12월-1월이 연속되도록 순환 인코딩
#   - 뉴스 피처 추가: SQL 뷰에서 1개월 lag로 이미 적용된 값
#     · 전국 거시(macro): total_news, regulation_news, easing_news,
#                         transport_news, redevelop_news, macro_sentiment
#     · 구별 로컬(local): local_news_count, local_redevelop_count,
#                         local_regulation_count, local_transport_count
NEWS_FEATURES = [
    # 전국 거시 뉴스 (5개 구 공통)
    "total_news",             # 전체 뉴스량 (시장 관심도 proxy)
    "regulation_news",        # 규제/긴축 뉴스 수 (악재)
    "easing_news",            # 완화/부양 뉴스 수 (호재)
    "transport_news",         # GTX/교통 뉴스 수
    "redevelop_news",         # 재개발/뉴타운 뉴스 수
    "macro_sentiment",        # 방향성 지수 (-1 ~ +1)
    # 구별 로컬 뉴스 (구 특화)
    "local_news_count",       # 해당 구 언급 뉴스 수
    "local_redevelop_count",  # 해당 구 재개발 뉴스 수
    "local_regulation_count", # 해당 구 규제 뉴스 수
    "local_transport_count",  # 해당 구 교통 뉴스 수
]

NUMERIC_FEATURES = [
    "avg_jeonse_10k",    "avg_jeonse_per_sqm",
    "rate_base",
    "trade_count",       "jeonse_count",
    "price_lag1",        "price_lag2",        "price_lag3",
    "jeonse_lag1",       "jeonse_lag2",       "jeonse_lag3",
    "rbase_lag1",        "rbase_lag2",        "rbase_lag3",
    "price_mom",         "jeonse_mom",        "rate_change",
    "price_yoy",         "jeonse_yoy",
    "jeonse_ratio",      "month_sin",         "month_cos",
] + NEWS_FEATURES

# 범주형 피처 (동 → OneHot)
CATEGORICAL_FEATURES = ["dong"]

# ── 동 → 구 매핑 (구 단위 집계 모델용) ──────────────────────────────
DONG_GU_MAP: dict[str, str] = {
    # 동대문구
    "회기동": "동대문구", "이문동": "동대문구", "용두동": "동대문구",
    "제기동": "동대문구", "전농동": "동대문구", "답십리동": "동대문구",
    "장안동": "동대문구", "청량리동": "동대문구", "신설동": "동대문구", "휘경동": "동대문구",
    # 성북구
    "길음동": "성북구", "동소문동": "성북구", "돈암동": "성북구",
    "안암동": "성북구", "보문동": "성북구", "정릉동": "성북구",
    "석관동": "성북구", "장위동": "성북구", "월곡동": "성북구", "종암동": "성북구",
    # 중랑구
    "면목동": "중랑구", "상봉동": "중랑구", "중화동": "중랑구",
    "묵동": "중랑구", "망우동": "중랑구", "신내동": "중랑구",
    # 강북구
    "번동": "강북구", "수유동": "강북구", "미아동": "강북구", "우이동": "강북구",
    # 도봉구
    "방학동": "도봉구", "창동": "도봉구", "도봉동": "도봉구", "쌍문동": "도봉구",
}

GU_NUMERIC_FEATURES = [
    "avg_jeonse_10k", "avg_jeonse_per_sqm",
    "rate_base",
    "trade_count",    "jeonse_count",
    "price_lag1",     "price_lag2",     "price_lag3",
    "jeonse_lag1",    "jeonse_lag2",    "jeonse_lag3",
    "rbase_lag1",     "rbase_lag2",     "rbase_lag3",
    "price_mom",      "jeonse_mom",     "rate_change",
    "price_yoy",      "jeonse_yoy",
    "jeonse_ratio",   "month_sin",      "month_cos",
]
GU_CATEGORICAL_FEATURES = ["gu"]

# 아파트 헤도닉 모델 피처
# - 아파트 고유 특성: area, floor, age
# - 시장 상황: jeonse_ratio, rate_base, lags, avg_jeonse_10k
APT_MARKET_FEATURES = [
    "jeonse_ratio", "rate_base",
    "rbase_lag1", "rbase_lag2", "rbase_lag3",
    "avg_jeonse_10k",
]
APT_NUMERIC_FEATURES = [
    "area", "floor", "age", "year_norm",
    "month_sin", "month_cos",
] + APT_MARKET_FEATURES
APT_CATEGORICAL_FEATURES = ["dong"]


# ─────────────────────────────────────────
# 3. 시각화 - 추이 차트
# ─────────────────────────────────────────
def plot_trends(df: pd.DataFrame):
    monthly = df.groupby("ym")[["avg_price_10k", "avg_jeonse_10k", "rate_base"]].mean()

    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    specs = [
        ("avg_price_10k",  "동대문구 평균 매매가 (만원)",   "steelblue"),
        ("avg_jeonse_10k", "동대문구 평균 전세가 (만원)",   "darkorange"),
        ("rate_base",      "기준금리 (%)",                   "crimson"),
    ]
    for ax, (col, label, color) in zip(axes, specs):
        ax.plot(monthly.index, monthly[col], color=color, lw=2)
        ax.set_title(label, fontsize=11)
        ax.grid(True, alpha=0.3)

    plt.suptitle("동대문구 아파트 가격 및 금리 추이 (2020~2026)", fontsize=13)
    plt.tight_layout()
    plt.savefig("price_trend.png", dpi=150, bbox_inches="tight")
    print("  → price_trend.png 저장")
    plt.close()


# ─────────────────────────────────────────
# 4. 상관관계 분석
# ─────────────────────────────────────────
def correlation_analysis(df: pd.DataFrame):
    print("\n[Step 1] 상관관계 분석")

    key_vars = [
        "avg_price_10k",   "avg_jeonse_10k",  "avg_jeonse_per_sqm",
        "rate_base",       "rate_cd",         "rate_bond3y",
        "price_lag1",      "jeonse_lag1",     "rbase_lag1",
        "jeonse_ratio",    "trade_count",
        # 뉴스 시그널
        "macro_sentiment", "regulation_news", "easing_news",
        "redevelop_news",  "transport_news",
        "local_redevelop_count", "local_news_count",
        "target_1m",       "target_2m",       "target_3m",
    ]
    key_vars = [c for c in key_vars if c in df.columns]
    sub  = df[key_vars].dropna()
    corr = sub.corr()

    # 1개월 후 매매가와의 상관계수 출력
    target_corr = (
        corr["target_1m"]
        .drop(["target_1m", "target_2m", "target_3m"], errors="ignore")
        .sort_values(ascending=False)
    )
    print("\n  [ 1개월 후 매매가 ]와의 상관계수:")
    print(f"  {'변수':<28} {'상관계수':>8}  막대")
    print("  " + "-" * 55)
    for feat, val in target_corr.items():
        import math
        if val is None or (isinstance(val, float) and math.isnan(val)):
            continue
        bar  = "#" * max(1, int(abs(val) * 20))
        sign = "+" if val >= 0 else "-"
        print(f"  {feat:<28} {sign}{abs(val):.3f}  {bar}")

    # 히트맵 저장
    fig, ax = plt.subplots(figsize=(13, 11))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f",
        cmap="RdYlGn", center=0, ax=ax,
        annot_kws={"size": 8}, linewidths=0.3,
    )
    ax.set_title("변수 간 상관관계 히트맵 (동대문구)", fontsize=14, pad=15)
    plt.tight_layout()
    plt.savefig("correlation_heatmap.png", dpi=150, bbox_inches="tight")
    print("\n  → correlation_heatmap.png 저장")
    plt.close()

    return target_corr


# ─────────────────────────────────────────
# 5. Ridge 회귀 모델
# ─────────────────────────────────────────
def _make_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("pre",   preprocessor),
        ("model", RidgeCV(alphas=[0.01, 0.1, 1, 5, 10, 50, 100, 500, 1000])),
    ])


def train_model(df: pd.DataFrame, horizon: int):
    target = f"target_{horizon}m"
    needed = list(dict.fromkeys(
        NUMERIC_FEATURES + CATEGORICAL_FEATURES + [target, "ym", "trade_count"]
    ))
    sub    = df[needed].dropna().sort_values("ym").reset_index(drop=True)

    X   = sub[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y   = sub[target]

    # 시계열 7:3 고정 분할 (앞 70% 학습, 뒤 30% 평가)
    split = int(len(sub) * 0.7)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    train_start = sub["ym"].iloc[0].strftime("%Y-%m")
    train_end   = sub["ym"].iloc[split - 1].strftime("%Y-%m")
    test_start  = sub["ym"].iloc[split].strftime("%Y-%m")
    test_end    = sub["ym"].iloc[-1].strftime("%Y-%m")

    # 평가용 파이프라인: train으로만 학습 → test로 검증
    eval_pipe = _make_pipeline()
    eval_pipe.fit(X_train, y_train)
    y_pred  = eval_pipe.predict(X_test)
    mae_val = mean_absolute_error(y_test, y_pred)
    r2_val  = r2_score(y_test, y_pred)

    # 최종 파이프라인: 전체 데이터로 재학습 (예측에 사용)
    pipe = _make_pipeline()
    pipe.fit(X, y)

    best_alpha = pipe.named_steps["model"].alpha_
    print(f"\n  [{horizon}개월 후 예측]")
    print(f"    학습: {train_start} ~ {train_end} ({split}행)  "
          f"평가: {test_start} ~ {test_end} ({len(X_test)}행)")
    print(f"    최적 alpha: {best_alpha}")
    print(f"    MAE (test): {mae_val:.2f}%")
    print(f"    R²  (test): {r2_val:.3f}")

    return pipe, X, y, mae_val, r2_val


def _get_feature_names(pipe: Pipeline) -> list[str]:
    pre      = pipe.named_steps["pre"]
    cat_enc  = pre.named_transformers_["cat"]
    cat_names = list(cat_enc.get_feature_names_out(CATEGORICAL_FEATURES))
    return NUMERIC_FEATURES + cat_names


def plot_importance(pipe: Pipeline, horizon: int) -> pd.Series:
    feat_names = _get_feature_names(pipe)
    coef       = pipe.named_steps["model"].coef_
    importance = pd.Series(np.abs(coef), index=feat_names).sort_values(ascending=False)

    # 동 더미 제외한 실질 피처만
    real = importance[[f for f in importance.index if not f.startswith("dong_")]]

    # ── 그룹별 기여도 요약 ──────────────────────────
    groups = {
        "전세가 (현재)":  ["avg_jeonse_10k", "avg_jeonse_per_sqm"],
        "매매가 시차":    [f"price_lag{i}" for i in [1,2,3]],
        "전세가 시차":    [f"jeonse_lag{i}" for i in [1,2,3]],
        "금리 (현재)":   ["rate_base"],
        "금리 시차":      [f"rbase_lag{i}" for i in [1,2,3]],
        "변화율":         ["price_mom","jeonse_mom","rate_change","price_yoy","jeonse_yoy"],
        "전세가율·거래량": ["jeonse_ratio","trade_count","jeonse_count","month_sin","month_cos"],
    }
    print(f"\n  [{horizon}개월 후] 그룹별 변수 기여도:")
    group_score = {}
    for gname, cols in groups.items():
        score = real[[c for c in cols if c in real.index]].sum()
        group_score[gname] = score
    total = sum(group_score.values())
    for gname, score in sorted(group_score.items(), key=lambda x: -x[1]):
        pct = score / total * 100
        bar = "#" * max(1, int(pct / 3))
        print(f"    {gname:<18} {pct:5.1f}%  {bar}")

    print(f"\n  [{horizon}개월 후] 개별 변수 중요도 Top 10:")
    for rank, (feat, val) in enumerate(real.head(10).items(), 1):
        bar = "#" * max(1, int(val / real.max() * 20))
        print(f"    {rank:2}. {feat:<28} {bar}")

    # 차트 저장
    fig, ax = plt.subplots(figsize=(10, 6))
    real.head(15).sort_values().plot.barh(ax=ax, color="steelblue", edgecolor="white")
    ax.set_title(f"{horizon}개월 후 매매가 예측 - 변수 중요도 (Ridge)", fontsize=12)
    ax.set_xlabel("|표준화 Ridge 계수|")
    plt.tight_layout()
    plt.savefig(f"importance_{horizon}m.png", dpi=150, bbox_inches="tight")
    print(f"\n  → importance_{horizon}m.png 저장")
    plt.close()

    return real


# 예측 구간 및 클리핑 상한
HORIZONS    = [1, 3, 6]
CLIP_BOUNDS = {1: 10.0, 3: 15.0, 6: 25.0}


def calc_confidence(trade_count: float) -> int:
    """월 거래량 기반 신뢰도 점수 (0~100)
    - 20건 이상: 높음 (100점 상한)
    - 10건: 50점
    - 5건 이하: 낮음
    """
    return min(100, max(0, int(float(trade_count or 0) * 5)))


# ─────────────────────────────────────────
# 6. 향후 예측
# ─────────────────────────────────────────
def predict_next(df: pd.DataFrame, pipes: dict) -> pd.DataFrame:
    print("\n[Step 3] 향후 1~3개월 동별 매매가 예측")

    # 각 동의 최신 유효 row (NUMERIC_FEATURES 결측 없는 것)
    latest_rows = []
    for dong, g in df.sort_values("ym").groupby("dong"):
        valid = g.dropna(subset=NUMERIC_FEATURES)
        if len(valid) > 0:
            latest_rows.append(valid.iloc[-1])
    latest = pd.DataFrame(latest_rows).reset_index(drop=True)

    # 학습 때 실제로 사용한 컬럼을 파이프라인에서 직접 읽어옴
    feature_cols = list(pipes[1].named_steps["pre"].feature_names_in_)

    results = []
    dong_pct = {}   # 동별 예측 변화율 저장 (아파트별 예측에 재사용)
    for _, row in latest.iterrows():
        X_pred = pd.DataFrame([row[feature_cols]])
        current = row["avg_price_10k"]
        dong_name = row["dong"]
        confidence = calc_confidence(row.get("trade_count", 0))
        rec = {
            "동":          dong_name,
            "기준월":      row["ym"].strftime("%Y-%m"),
            "현재가(만원)": int(current),
            "신뢰도":      confidence,
        }
        pcts = {}
        for h in HORIZONS:
            try:
                pred_pct = float(pipes[h].predict(X_pred)[0])
                # 클리핑: 비현실적 극단값 제거
                pred_pct = float(np.clip(pred_pct, -CLIP_BOUNDS[h], CLIP_BOUNDS[h]))
                pred_price = current * (1 + pred_pct / 100)
                diff       = pred_price - current
                rec[f"{h}개월후_예측(만원)"] = f"{pred_price:,.0f}"
                rec[f"{h}개월후_변동(만원)"] = f"{diff:+,.0f}"
                rec[f"{h}개월후_변동(%)"]   = f"{pred_pct:+.2f}%"
                pcts[h] = pred_pct
            except Exception:
                rec[f"{h}개월후_예측(만원)"] = "N/A"
                rec[f"{h}개월후_변동(만원)"] = "N/A"
                rec[f"{h}개월후_변동(%)"]   = "N/A"
                pcts[h] = None
        dong_pct[dong_name] = pcts
        results.append(rec)

    pred_df = pd.DataFrame(results)

    # 터미널 출력
    print()
    print(pred_df.to_string(index=False))

    # CSV 저장 (동별)
    pred_df.to_csv("prediction_result.csv", index=False, encoding="utf-8-sig")
    print("\n  → prediction_result.csv 저장")

    # Supabase predictions 테이블에 저장 (동별)
    save_predictions_to_supabase(pred_df)

    return pred_df


def fetch_apt_current_prices() -> pd.DataFrame:
    """apt_trade에서 아파트별 최근 6개월 평균 거래가 조회"""
    print("\n  아파트별 최근 거래가 조회 중...")
    url     = f"{SUPABASE_URL}/rest/v1/apt_trade"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

    # 최근 6개월 데이터만 가져오기
    import datetime
    cutoff = (datetime.date.today().replace(day=1) - datetime.timedelta(days=180))
    cutoff_year  = cutoff.year
    cutoff_month = cutoff.month

    rows, offset = [], 0
    while True:
        params = {
            "select":     "dong,apt_name,area,deal_year,deal_month,price_10k",
            "deal_year":  f"gte.{cutoff_year}",
            "limit":      "1000",
            "offset":     str(offset),
        }
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  [WARN] apt_trade 조회 실패: {resp.status_code}")
            return None
        batch = resp.json()
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += len(batch)

    if not rows:
        return None

    apt = pd.DataFrame(rows)
    apt["deal_year"]  = pd.to_numeric(apt["deal_year"],  errors="coerce")
    apt["deal_month"] = pd.to_numeric(apt["deal_month"], errors="coerce")
    apt["price_10k"]  = pd.to_numeric(apt["price_10k"],  errors="coerce")
    apt["area"]       = pd.to_numeric(apt["area"],       errors="coerce").round(1)

    # cutoff 월 이후 필터
    apt = apt[(apt["deal_year"] > cutoff_year) |
              ((apt["deal_year"] == cutoff_year) & (apt["deal_month"] >= cutoff_month))]

    # 아파트별(동+이름+면적) 평균가 및 최신 거래월
    grp = apt.groupby(["dong", "apt_name", "area"]).agg(
        current_price_10k=("price_10k", "mean"),
        trade_count=("price_10k", "count"),
        last_year=("deal_year", "max"),
        last_month=("deal_month", "max"),
    ).reset_index()

    # 거래 2건 이상인 것만 (1건은 이상치 위험)
    grp = grp[grp["trade_count"] >= 2].copy()
    grp["current_price_10k"] = grp["current_price_10k"].round(0).astype(int)
    grp["base_ym"] = grp["last_year"].astype(int).astype(str) + "-" + \
                     grp["last_month"].astype(int).astype(str).str.zfill(2)

    print(f"  아파트 {len(grp):,}개 (거래 2건+ 기준)")
    return grp


def predict_apt_level(dong_pct: dict) -> pd.DataFrame:
    """동별 예측 변화율을 아파트별 현재가에 적용"""
    print("\n[Step 4] 아파트별 예측가 산출")

    apt = fetch_apt_current_prices()
    if apt is None or len(apt) == 0:
        print("  [WARN] 아파트 데이터 없음 - 아파트별 예측 건너뜀")
        return None

    results = []
    for _, row in apt.iterrows():
        dong = row["dong"]
        if dong not in dong_pct:
            continue
        pcts   = dong_pct[dong]
        cur    = row["current_price_10k"]
        rec = {
            "동":          dong,
            "아파트명":    row["apt_name"],
            "전용면적(㎡)": row["area"],
            "기준월":      row["base_ym"],
            "현재가(만원)": cur,
        }
        for h in HORIZONS:
            pct = pcts.get(h)
            if pct is not None:
                pred = int(cur * (1 + pct / 100))
                diff = pred - cur
                rec[f"{h}개월후_예측(만원)"] = pred
                rec[f"{h}개월후_변동(만원)"] = diff
                rec[f"{h}개월후_변동(%)"]   = round(pct, 2)
            else:
                rec[f"{h}개월후_예측(만원)"] = None
                rec[f"{h}개월후_변동(만원)"] = None
                rec[f"{h}개월후_변동(%)"]   = None
        results.append(rec)

    apt_df = pd.DataFrame(results).sort_values(["동", "아파트명", "전용면적(㎡)"]).reset_index(drop=True)
    print(f"  총 {len(apt_df):,}개 아파트 예측 완료")
    print()
    print(apt_df[["동","아파트명","전용면적(㎡)","현재가(만원)",
                  "1개월후_예측(만원)","1개월후_변동(%)"]].to_string(index=False))
    return apt_df


# ─────────────────────────────────────────
# 7. 아파트별 헤도닉 모델
# ─────────────────────────────────────────
def load_apt_transactions() -> pd.DataFrame:
    """apt_trade 전체 이력 로드 (헤도닉 모델 학습용)"""
    print("\n  apt_trade 전체 이력 로드 중...")
    rows = fetch_all("apt_trade")
    df   = pd.DataFrame(rows)
    for col in ["area", "floor", "build_year", "price_10k", "deal_year", "deal_month"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["area", "price_10k", "deal_year", "deal_month"])
    df = df[(df["price_10k"] > 0) & (df["area"] > 0)]
    df["ym"] = pd.to_datetime(
        df["deal_year"].astype(int).astype(str) + "-" +
        df["deal_month"].astype(int).astype(str).str.zfill(2)
    )
    df["age"]       = df["deal_year"] - df["build_year"].replace(0, np.nan)
    df["month_sin"] = np.sin(2 * np.pi * df["deal_month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["deal_month"] / 12)
    df["year_norm"] = (df["deal_year"] - 2020) / 5
    print(f"  {len(df):,}건 거래 이력 로드 완료")
    return df


def train_apt_hedonic_model(apt_df: pd.DataFrame, market_df: pd.DataFrame):
    """
    헤도닉 모델: 개별 거래가 = f(면적, 층수, 건물연령, 동, 시장상황, 시점)
    - 같은 동이라도 면적·층수·건물연령에 따라 예측가가 달라짐
    - GradientBoosting 사용: 비선형 관계(예: 면적↑ + 고층 = 프리미엄 증폭) 포착
    """
    print("\n[Step 4] 아파트 헤도닉 모델 학습")

    market_slim = market_df[["dong", "ym"] + APT_MARKET_FEATURES].dropna()
    merged = apt_df.merge(market_slim, on=["dong", "ym"], how="inner")

    needed = APT_NUMERIC_FEATURES + APT_CATEGORICAL_FEATURES + ["price_10k", "ym"]
    sub    = merged[needed].dropna().sort_values("ym").reset_index(drop=True)

    X = sub[APT_NUMERIC_FEATURES + APT_CATEGORICAL_FEATURES]
    y = sub["price_10k"]

    split       = int(len(sub) * 0.7)
    X_train     = X.iloc[:split];  X_test  = X.iloc[split:]
    y_train     = y.iloc[:split];  y_test  = y.iloc[split:]
    train_start = sub["ym"].iloc[0].strftime("%Y-%m")
    train_end   = sub["ym"].iloc[split - 1].strftime("%Y-%m")
    test_start  = sub["ym"].iloc[split].strftime("%Y-%m")
    test_end    = sub["ym"].iloc[-1].strftime("%Y-%m")

    def _make_apt_pipeline():
        pre = ColumnTransformer([
            ("num", StandardScaler(), APT_NUMERIC_FEATURES),
            ("cat", OneHotEncoder(drop="first", sparse_output=False,
                                  handle_unknown="ignore"), APT_CATEGORICAL_FEATURES),
        ])
        return Pipeline([
            ("pre",   pre),
            ("model", GradientBoostingRegressor(
                n_estimators=300, max_depth=4, learning_rate=0.05,
                subsample=0.8, random_state=42,
            )),
        ])

    # 평가
    eval_pipe = _make_apt_pipeline()
    eval_pipe.fit(X_train, y_train)
    y_pred = eval_pipe.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    r2     = r2_score(y_test, y_pred)
    print(f"    학습: {train_start} ~ {train_end} ({split:,}건)  "
          f"평가: {test_start} ~ {test_end} ({len(X_test):,}건)")
    print(f"    MAE: {mae:,.0f}만원  R²: {r2:.3f}")

    # 전체 재학습
    full_pipe = _make_apt_pipeline()
    full_pipe.fit(X, y)
    return full_pipe


def predict_apt_hedonic(
    apt_pipe, apt_df: pd.DataFrame, market_df: pd.DataFrame
) -> pd.DataFrame:
    """
    헤도닉 모델로 아파트별 1~3개월 후 예측가 산출
    - 각 아파트의 면적·층수·건물연령을 개별 반영
    - 미래 시장 상황: 현재 동별 최신 시장 데이터 사용 (1~3개월 내 근사)
    """
    print("\n[Step 5] 헤도닉 모델 아파트별 예측")

    # 동별 최신 시장 상황
    latest_market = {}
    for dong, g in market_df.sort_values("ym").groupby("dong"):
        valid = g.dropna(subset=APT_MARKET_FEATURES)
        if len(valid):
            latest_market[dong] = valid.iloc[-1]

    # 아파트별 대표 특성 (전체 이력에서 중앙값)
    apt_chars = (
        apt_df.groupby(["dong", "apt_name", "area"])
        .agg(
            median_floor=("floor", "median"),
            median_age=("age",   "median"),
        )
        .reset_index()
    )
    apt_chars["median_floor"] = apt_chars["median_floor"].fillna(5).round()
    apt_chars["median_age"]   = apt_chars["median_age"].fillna(15).round()

    # 최근 6개월 평균 거래가
    apt_recent = fetch_apt_current_prices()
    if apt_recent is None or len(apt_recent) == 0:
        print("  [WARN] 최근 거래 데이터 없음")
        return None

    apt_merged = apt_recent.merge(apt_chars, on=["dong", "apt_name", "area"], how="left")
    apt_merged["median_floor"] = apt_merged["median_floor"].fillna(5)
    apt_merged["median_age"]   = apt_merged["median_age"].fillna(15)

    import datetime
    today       = datetime.date.today()
    base_year   = today.year
    base_month  = today.month

    results = []
    for _, row in apt_merged.iterrows():
        dong = row["dong"]
        if dong not in latest_market:
            continue
        mkt = latest_market[dong]
        cur = row["current_price_10k"]

        rec = {
            "동":           dong,
            "아파트명":     row["apt_name"],
            "전용면적(㎡)": row["area"],
            "기준월":       row["base_ym"],
            "현재가(만원)": cur,
        }

        for h in HORIZONS:
            future_month = (base_month + h - 1) % 12 + 1
            future_year  = base_year + (base_month + h - 1) // 12

            feat = {
                "area":           float(row["area"]),
                "floor":          float(row["median_floor"]),
                "age":            float(row["median_age"]) + h / 12,
                "year_norm":      (future_year - 2020 + (future_month - 1) / 12) / 5,
                "month_sin":      np.sin(2 * np.pi * future_month / 12),
                "month_cos":      np.cos(2 * np.pi * future_month / 12),
                "jeonse_ratio":   float(mkt.get("jeonse_ratio",   0.6)),
                "rate_base":      float(mkt.get("rate_base",      3.0)),
                "rbase_lag1":     float(mkt.get("rbase_lag1",     3.0)),
                "rbase_lag2":     float(mkt.get("rbase_lag2",     3.0)),
                "rbase_lag3":     float(mkt.get("rbase_lag3",     3.0)),
                "avg_jeonse_10k": float(mkt.get("avg_jeonse_10k", 0)),
                "dong":           dong,
            }
            try:
                pred_price = int(apt_pipe.predict(pd.DataFrame([feat]))[0])
                diff       = pred_price - cur
                rec[f"{h}개월후_예측(만원)"] = pred_price
                rec[f"{h}개월후_변동(만원)"] = diff
                rec[f"{h}개월후_변동(%)"]   = round(diff / cur * 100, 2)
            except Exception:
                rec[f"{h}개월후_예측(만원)"] = None
                rec[f"{h}개월후_변동(만원)"] = None
                rec[f"{h}개월후_변동(%)"]   = None

        results.append(rec)

    apt_result = (
        pd.DataFrame(results)
        .sort_values(["동", "아파트명", "전용면적(㎡)"])
        .reset_index(drop=True)
    )
    print(f"  총 {len(apt_result):,}개 아파트 헤도닉 예측 완료")
    print()
    print(apt_result[["동", "아파트명", "전용면적(㎡)", "현재가(만원)",
                       "1개월후_예측(만원)", "1개월후_변동(%)"]].to_string(index=False))
    return apt_result


def save_apt_predictions_to_supabase(apt_df: pd.DataFrame):
    """아파트별 예측 결과를 Supabase predictions_apt 테이블에 upsert"""
    import json
    from datetime import date

    run_date = date.today().isoformat()
    rows = []
    for _, row in apt_df.iterrows():
        def to_int(val):
            try:   return int(val) if val is not None else None
            except: return None
        def to_float(val):
            try:   return float(val) if val is not None else None
            except: return None

        rows.append({
            "run_date":          run_date,
            "dong":              row["동"],
            "apt_name":          row["아파트명"],
            "area":              float(row["전용면적(㎡)"]),
            "base_ym":           row["기준월"],
            "current_price_10k": to_int(row["현재가(만원)"]),
            "pred_1m_10k":       to_int(row["1개월후_예측(만원)"]),
            "pred_3m_10k":       to_int(row["3개월후_예측(만원)"]),
            "pred_6m_10k":       to_int(row["6개월후_예측(만원)"]),
            "change_1m_pct":     to_float(row["1개월후_변동(%)"]),
            "change_3m_pct":     to_float(row["3개월후_변동(%)"]),
            "change_6m_pct":     to_float(row["6개월후_변동(%)"]),
        })

    url     = f"{SUPABASE_URL}/rest/v1/predictions_apt"
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates,return=representation",
    }
    resp = requests.post(url, headers=headers,
                         params={"on_conflict": "run_date,dong,apt_name,area"},
                         data=json.dumps(rows, ensure_ascii=False),
                         timeout=30)
    if resp.status_code in (200, 201):
        print(f"  → Supabase predictions_apt 저장 완료 ({len(rows)}개 아파트)")
    else:
        print(f"  [ERROR] predictions_apt 저장 실패 {resp.status_code}: {resp.text[:200]}")


# ─────────────────────────────────────────
# 구 단위 집계 모델
# ─────────────────────────────────────────
def build_gu_features(df: pd.DataFrame) -> pd.DataFrame:
    """동별 데이터를 구 단위로 집계하고 시계열 lag / 변화율 피처 생성"""
    d = df.copy()
    d["gu"] = d["dong"].map(DONG_GU_MAP)
    d = d.dropna(subset=["gu"])

    # 구·월별 집계 (거래량 가중 평균)
    def wavg(vals, weights):
        w = weights.clip(lower=1)
        return float(np.average(vals, weights=w)) if w.sum() > 0 else float(vals.mean())

    records = []
    for (gu, ym), g in d.groupby(["gu", "ym"]):
        records.append({
            "gu":                 gu,
            "ym":                 ym,
            "avg_price_10k":      wavg(g["avg_price_10k"],      g["trade_count"]),
            "avg_jeonse_10k":     wavg(g["avg_jeonse_10k"],     g["jeonse_count"].clip(lower=1)),
            "avg_jeonse_per_sqm": g["avg_jeonse_per_sqm"].mean(),
            "trade_count":        g["trade_count"].sum(),
            "jeonse_count":       g["jeonse_count"].sum(),
            "rate_base":          g["rate_base"].mean(),
        })
    gu_df = pd.DataFrame(records).sort_values(["gu", "ym"]).reset_index(drop=True)

    # gu별 lag·변화율·타겟 생성
    dfs = []
    for _, g in gu_df.groupby("gu"):
        g = g.sort_values("ym").copy()
        for lag in [1, 2, 3]:
            g[f"price_lag{lag}"]  = g["avg_price_10k"].shift(lag)
            g[f"jeonse_lag{lag}"] = g["avg_jeonse_10k"].shift(lag)
            g[f"rbase_lag{lag}"]  = g["rate_base"].shift(lag)
        g["price_mom"]    = g["avg_price_10k"].pct_change() * 100
        g["jeonse_mom"]   = g["avg_jeonse_10k"].pct_change() * 100
        g["rate_change"]  = g["rate_base"].diff()
        g["price_yoy"]    = g["avg_price_10k"].pct_change(12) * 100
        g["jeonse_yoy"]   = g["avg_jeonse_10k"].pct_change(12) * 100
        g["jeonse_ratio"] = g["avg_jeonse_10k"] / g["avg_price_10k"].replace(0, np.nan)
        g["month_sin"]    = np.sin(2 * np.pi * g["ym"].dt.month / 12)
        g["month_cos"]    = np.cos(2 * np.pi * g["ym"].dt.month / 12)
        for h in HORIZONS:
            future = g["avg_price_10k"].shift(-h)
            g[f"target_{h}m"] = (future - g["avg_price_10k"]) / g["avg_price_10k"] * 100
        dfs.append(g)

    result = pd.concat(dfs, ignore_index=True).replace([np.inf, -np.inf], np.nan)
    print(f"  구 단위 집계: {result['gu'].nunique()}개 구, {len(result):,}행")
    return result


def _make_gu_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), GU_NUMERIC_FEATURES),
        ("cat", OneHotEncoder(drop="first", sparse_output=False,
                              handle_unknown="ignore"), GU_CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("pre",   preprocessor),
        ("model", RidgeCV(alphas=[0.01, 0.1, 1, 5, 10, 50, 100, 500, 1000])),
    ])


def train_gu_model(gu_df: pd.DataFrame, horizon: int):
    target = f"target_{horizon}m"
    needed = GU_NUMERIC_FEATURES + GU_CATEGORICAL_FEATURES + [target, "ym"]
    sub    = gu_df[needed].dropna().sort_values("ym").reset_index(drop=True)

    X = sub[GU_NUMERIC_FEATURES + GU_CATEGORICAL_FEATURES]
    y = sub[target]

    split       = int(len(sub) * 0.7)
    X_train     = X.iloc[:split];  X_test  = X.iloc[split:]
    y_train     = y.iloc[:split];  y_test  = y.iloc[split:]
    train_start = sub["ym"].iloc[0].strftime("%Y-%m")
    train_end   = sub["ym"].iloc[split - 1].strftime("%Y-%m")
    test_start  = sub["ym"].iloc[split].strftime("%Y-%m")
    test_end    = sub["ym"].iloc[-1].strftime("%Y-%m")

    eval_pipe = _make_gu_pipeline()
    eval_pipe.fit(X_train, y_train)
    y_pred  = eval_pipe.predict(X_test)
    mae_val = mean_absolute_error(y_test, y_pred)
    r2_val  = r2_score(y_test, y_pred)

    pipe = _make_gu_pipeline()
    pipe.fit(X, y)

    print(f"\n  [구 단위 {horizon}개월 후 예측]")
    print(f"    학습: {train_start} ~ {train_end} ({split}행)  "
          f"평가: {test_start} ~ {test_end} ({len(X_test)}행)")
    print(f"    최적 alpha: {pipe.named_steps['model'].alpha_}")
    print(f"    MAE (test): {mae_val:.2f}%")
    print(f"    R²  (test): {r2_val:.3f}")

    return pipe, mae_val, r2_val


def save_metrics(dong_metrics: dict, gu_metrics: dict):
    """모델 성능 지표를 metrics.json으로 저장"""
    import json
    from datetime import date

    out = {
        "run_date": date.today().strftime("%Y-%m-%d"),
        "note": "MAE: 예측 변화율의 평균절대오차(%), R²: 분산 설명력(1=완벽, 0=무의미)",
        "dong_level": {
            f"ridge_{h}m": {
                "r2":      round(dong_metrics[h]["r2"],  3),
                "mae_pct": round(dong_metrics[h]["mae"], 2),
                "note":    "동 단위, 노이즈 필터링(trade>=5, |target|<=15%) 적용",
            }
            for h in HORIZONS
        },
        "gu_level": {
            f"ridge_{h}m": {
                "r2":      round(gu_metrics[h]["r2"],  3),
                "mae_pct": round(gu_metrics[h]["mae"], 2),
                "note":    "구 단위 거래량 가중 집계, 노이즈 적음",
            }
            for h in HORIZONS
        },
    }
    with open("metrics.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("  → metrics.json 저장")


def save_predictions_to_supabase(pred_df: pd.DataFrame):
    """예측 결과를 Supabase predictions 테이블에 upsert"""
    import json
    from datetime import date

    run_date = date.today().isoformat()
    rows = []
    for _, row in pred_df.iterrows():
        def to_int(val):
            try:
                return int(str(val).replace(",", "").replace("+", ""))
            except Exception:
                return None

        def to_float(val):
            try:
                return float(str(val).replace("%", "").replace("+", ""))
            except Exception:
                return None

        rows.append({
            "run_date":           run_date,
            "dong":               row["동"],
            "base_ym":            row["기준월"],
            "current_price_10k":  to_int(row["현재가(만원)"]),
            "pred_1m_10k":        to_int(row["1개월후_예측(만원)"]),
            "pred_3m_10k":        to_int(row["3개월후_예측(만원)"]),
            "pred_6m_10k":        to_int(row["6개월후_예측(만원)"]),
            "change_1m_pct":      to_float(row["1개월후_변동(%)"]),
            "change_3m_pct":      to_float(row["3개월후_변동(%)"]),
            "change_6m_pct":      to_float(row["6개월후_변동(%)"]),
            "confidence_score":   to_int(row.get("신뢰도", 50)),
        })

    url     = f"{SUPABASE_URL}/rest/v1/predictions"
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates,return=representation",
    }
    resp = requests.post(url, headers=headers,
                         params={"on_conflict": "run_date,dong"},
                         data=json.dumps(rows, ensure_ascii=False),
                         timeout=30)
    if resp.status_code in (200, 201):
        print(f"  → Supabase predictions 테이블 저장 완료 ({len(rows)}개 동)")
    else:
        print(f"  [ERROR] Supabase 저장 실패 {resp.status_code}: {resp.text[:200]}")


# ─────────────────────────────────────────
# 7. 예측 정확도 시각화 (전체 기간 Actual vs Predicted)
# ─────────────────────────────────────────
def plot_actual_vs_pred(df: pd.DataFrame, pipes: dict):
    target = "target_1m"
    # 학습 때 실제로 사용한 컬럼을 파이프라인에서 직접 읽어옴
    feature_cols = list(pipes[1].named_steps["pre"].feature_names_in_)
    # avg_price_10k / ym 이 이미 feature_cols 에 있을 수 있으므로 중복 제거
    extra = [c for c in [target, "ym", "avg_price_10k"] if c not in feature_cols]
    needed = feature_cols + extra
    sub    = df[needed].dropna()
    X      = sub[feature_cols]
    y_pct  = sub[target]                                         # 실제 변화율 (%)
    ym     = sub["ym"]
    base   = sub["avg_price_10k"]

    pred_pct   = pipes[1].predict(X)
    y_actual   = base * (1 + y_pct / 100)                       # 실제 미래가
    y_predicted = base * (1 + pred_pct / 100)                   # 예측 미래가

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(ym, y_actual,    label="실제 1개월 후 매매가", color="steelblue", lw=1.5, alpha=0.8)
    ax.plot(ym, y_predicted, label="예측 1개월 후 매매가", color="tomato",    lw=1.5, linestyle="--", alpha=0.8)
    ax.set_title("동대문구 전체 - 실제 vs 예측 매매가 (1개월 후)", fontsize=12)
    ax.set_ylabel("평균 매매가 (만원)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("actual_vs_pred.png", dpi=150, bbox_inches="tight")
    print("  → actual_vs_pred.png 저장")
    plt.close()


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main():
    print("=" * 55)
    print("HomeSignal AI - 동대문구 아파트 매매가 예측 모델")
    print("=" * 55)

    # Step 0: 데이터 준비
    print("\n[Step 0] 데이터 준비")
    raw = load_data()
    df  = build_features(raw)
    print(f"  피처 생성 완료: {len(df):,}행")

    plot_trends(df)

    # Step 1: 상관관계 분석
    target_corr = correlation_analysis(df)

    # Step 2: 동 단위 Ridge 모델 학습
    print("\n[Step 2] 동 단위 Ridge 회귀 모델 학습 (노이즈 필터링 적용)")
    pipes = {}
    dong_metrics = {}
    for h in HORIZONS:
        pipe, X, y, mae_val, r2_val = train_model(df, h)
        plot_importance(pipe, h)
        pipes[h] = pipe
        dong_metrics[h] = {"mae": mae_val, "r2": r2_val}

    # Actual vs Predicted 차트
    plot_actual_vs_pred(df, pipes)

    # Step 2b: 구 단위 Ridge 모델 학습
    print("\n[Step 2b] 구 단위 Ridge 회귀 모델 학습 (거래량 가중 집계)")
    gu_df = build_gu_features(df)
    gu_pipes = {}
    gu_metrics = {}
    for h in HORIZONS:
        gu_pipe, mae_val, r2_val = train_gu_model(gu_df, h)
        gu_pipes[h] = gu_pipe
        gu_metrics[h] = {"mae": mae_val, "r2": r2_val}

    # 성능 비교 요약
    print("\n  ── 모델 성능 비교 ──────────────────────────────────")
    print(f"  {'구간':<10} {'동 단위 R²':>10} {'동 단위 MAE':>12} {'구 단위 R²':>10} {'구 단위 MAE':>12}")
    print("  " + "-" * 58)
    for h in HORIZONS:
        print(f"  {h}개월 후   "
              f"  {dong_metrics[h]['r2']:>8.3f}   {dong_metrics[h]['mae']:>9.2f}%"
              f"  {gu_metrics[h]['r2']:>8.3f}   {gu_metrics[h]['mae']:>9.2f}%")

    # metrics.json 저장
    save_metrics(dong_metrics, gu_metrics)

    # Step 3: 동별 향후 예측
    pred_df = predict_next(df, pipes)

    # Step 4~5: 아파트별 헤도닉 예측
    apt_transactions = load_apt_transactions()
    apt_pipe         = train_apt_hedonic_model(apt_transactions, df)
    apt_df           = predict_apt_hedonic(apt_pipe, apt_transactions, df)
    if apt_df is not None:
        apt_df.to_csv("prediction_result_apt.csv", index=False, encoding="utf-8-sig")
        print("\n  → prediction_result_apt.csv 저장")
        save_apt_predictions_to_supabase(apt_df)

    print("\n" + "=" * 55)
    print("완료!  생성된 파일:")
    print("  price_trend.png           - 가격·금리 추이")
    print("  correlation_heatmap.png   - 상관관계 히트맵")
    print("  importance_1m/2m/3m.png   - 변수 중요도 차트")
    print("  actual_vs_pred.png        - 예측 정확도 차트")
    print("  prediction_result.csv     - 동별 1~3개월 예측 결과")
    print("  prediction_result_apt.csv - 아파트별 1~3개월 헤도닉 예측")
    print("  metrics.json              - 동·구 단위 모델 R²/MAE 지표")
    print("=" * 55)


if __name__ == "__main__":
    main()
