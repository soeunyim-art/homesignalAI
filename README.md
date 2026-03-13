# HomeSignal AI — 서울 동북권 아파트 매매가 예측 모델

> **v2.0 · 2026-03-13 개선 버전**
> 전월세가 + 금리 + 뉴스 시그널 → 1~3개월 후 동별 / 아파트별 매매가 예측

---

## 개선 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v1.0 | 2026-02-28 | MVP — 동대문구 단일 구, Ridge 회귀 |
| v1.5 | 2026-03-06 | 5개 구 확장, 헤도닉 GBM 모델 추가 |
| **v2.0** | **2026-03-13** | **뉴스 시그널 통합 (전국 거시 + 구별 로컬)** |

---

## 예측 대상 지역

서울 동북권 5개 구 · 전체 법정동

| 구 | 법정동코드 | 특징 |
|---|---|---|
| 동대문구 | 11230 | 이문·장안·답십리 재개발 |
| 성북구 | 11290 | 길음·장위 뉴타운 |
| 중랑구 | 11260 | 면목·신내 개발 |
| 강북구 | 11305 | 미아·수유 재정비 |
| 도봉구 | 11320 | 창동 GTX-C |

---

## 데이터 소스

| 소스 | 내용 | 수집 기간 |
|---|---|---|
| 국토교통부 실거래가 API | 아파트 매매 / 전월세 | 2020-01 ~ 현재 |
| 한국은행 ECOS API | 기준금리 / CD금리 / 국고채3년 | 2020-01 ~ 현재 |
| news_signals 테이블 | 부동산 뉴스 키워드 시그널 | 2026-02 ~ 현재 |

---

## 모델 구조

```
[데이터 수집]
  collect_data.py
    ├── 국토부 API → apt_trade, apt_rent (Supabase)
    └── ECOS API  → interest_rate (Supabase)

[피처 통합]
  supabase_views.sql
    ├── v_monthly_trade / v_monthly_jeonse / v_monthly_wolse
    ├── v_monthly_news_macro  ← (NEW v2.0) 전국 거시 뉴스 월별 집계
    ├── v_monthly_news_local  ← (NEW v2.0) 구별 로컬 뉴스 월별 집계
    └── v_model_features      ← 전체 통합 뷰 (1개월 lag JOIN)

[예측 모델]
  predict_model.py
    ├── Step 1: 상관관계 분석 → correlation_heatmap.png
    ├── Step 2: Ridge 회귀 (동별, 1/2/3개월 후) → importance_Xm.png
    ├── Step 3: 동별 향후 예측 → prediction_result.csv
    └── Step 4: 헤도닉 GBM (아파트별) → prediction_result_apt.csv
```

### 피처 목록 (v2.0 기준, 총 32개)

**기존 피처 (22개)**
- 전세가: `avg_jeonse_10k`, `avg_jeonse_per_sqm`
- 금리: `rate_base` + lag 1~3
- 시계열: 매매가/전세가 lag 1~3, MoM/YoY 변화율
- 파생: `jeonse_ratio` (전세가율), `month_sin/cos` (계절성)

**뉴스 피처 (10개, v2.0 신규)**
- 전국 거시: `total_news`, `regulation_news`, `easing_news`, `transport_news`, `redevelop_news`, `macro_sentiment`
- 구별 로컬: `local_news_count`, `local_redevelop_count`, `local_regulation_count`, `local_transport_count`

---

## 실행 방법

### 환경 설정

```bash
pip install -r requirements.txt
# homesignal.env 파일에 API 키 설정 (homesignal.env.example 참고)
```

### 1. 데이터 수집

```bash
# 최초 전체 수집 (2020-01 ~ 현재)
python collect_data.py full

# 월별 증분 업데이트
python collect_data.py update
```

### 2. SQL 뷰 생성

Supabase SQL Editor에서 순서대로 실행:

```
1. supabase_schema.sql  ← 테이블 생성 (최초 1회)
2. supabase_views.sql   ← 뷰 생성/업데이트
```

### 3. 예측 모델 실행

```bash
python predict_model.py
```

### 출력 파일

| 파일 | 내용 |
|---|---|
| `price_trend.png` | 매매가·전세가·금리 추이 차트 |
| `correlation_heatmap.png` | 변수 간 상관관계 히트맵 |
| `importance_1m/2m/3m.png` | 예측 변수 중요도 차트 |
| `actual_vs_pred.png` | 실제 vs 예측 정확도 차트 |
| `prediction_result.csv` | 동별 1~3개월 후 예측 결과 |
| `prediction_result_apt.csv` | 아파트별 1~3개월 후 헤도닉 예측 |

---

## Supabase 테이블 구조

```
apt_trade          - 아파트 매매 실거래가
apt_rent           - 전월세 실거래가
interest_rate      - 금리 (월별)
news_signals       - 뉴스 키워드 시그널
dongs              - 동 마스터 (gu_name 컬럼 필수)
apartments         - 아파트 마스터
predictions        - 동별 예측 결과 (자동 저장)
predictions_apt    - 아파트별 예측 결과 (자동 저장)
```

> `dongs` 테이블의 `gu_name` 컬럼을 채워야 구별 로컬 뉴스 피처가 활성화됩니다.

---

## 주의사항

- `homesignal.env`는 `.gitignore`에 포함되어 있으며 **절대 커밋하지 않습니다**
- 뉴스 피처는 **1개월 lag** 적용으로 정보 누수(look-ahead bias)를 방지합니다
- 뉴스 수집 기간(2026-02~) 이전 데이터는 뉴스 피처가 `0`으로 채워져 모델이 정상 작동합니다
