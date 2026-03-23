# HomeSignal AI — 서울 동북권 아파트 매매가 예측 플랫폼

> **v2.0 · 2026-03-13 개선 버전**
> 전월세가 + 금리 + 뉴스 시그널 → 1~3개월 후 동별 / 아파트별 매매가 예측
>
> **Full-Stack Platform:** Next.js 대시보드 + Python ML 파이프라인 + Supabase

---

## 주요 기능

### 대시보드
- **실시간 검색** - 구/동/아파트명으로 즉시 검색
- **인터랙티브 지도** - 서울 동북권 5개 구 시각화
- **KPI 티커** - 평균 매매가, 전세가율, 거래량, 금리 등 주요 지표
- **가격 예측 차트** - 1/2/3개월 후 예상 매매가 추이
- **뉴스 시그널** - 부동산 시장 영향 뉴스 실시간 피드
- **리스크 레이더** - 투자 위험도 시각화

### AI 예측
- **동별 예측** - Ridge 회귀 모델 (32개 피처)
- **아파트별 예측** - Gradient Boosting 헤도닉 모델
- **다중 기간** - 1/2/3개월 후 예측 (단기 트렌드 파악)
- **신뢰도 점수** - 모델 예측 신뢰도 제공

### 데이터 분석
- **5년 실거래 데이터** - 2020년부터 현재까지 누적
- **금리 연동** - 기준금리, CD금리, 국고채 3년 반영
- **뉴스 감성 분석** - 규제/완화/재개발/교통 키워드 추출
- **시계열 분석** - MoM/YoY 변화율, 계절성 분석

## 기술 스택

| 구분 | 기술 |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| **UI Components** | Radix UI, shadcn/ui, Framer Motion, Recharts |
| **Backend** | Python (scikit-learn, pandas), Next.js API Routes |
| **Database** | Supabase (PostgreSQL) |
| **Deployment** | Vercel |
| **ML** | Ridge Regression, Gradient Boosting (scikit-learn) |
| **Data Sources** | 국토교통부 API, 한국은행 ECOS API |

---

## 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/homesignalAI.git
cd homesignalAI

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 Supabase 정보 입력

# 3. 프론트엔드 설치 및 실행
npm install
npm run dev
# → http://localhost:3000

# 4. Python 환경 설정 (데이터 수집/예측용)
pip install -r requirements.txt
# homesignal.env 파일에 API 키 입력

# 5. 데이터 수집 및 모델 실행
python collect_data.py full
python predict_model.py
```

---

## 개선 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v1.0 | 2026-02-28 | MVP — 동대문구 단일 구, Ridge 회귀 |
| v1.5 | 2026-03-06 | 5개 구 확장, 헤도닉 GBM 모델 추가 |
| **v2.0** | **2026-03-13** | **뉴스 시그널 통합 (전국 거시 + 구별 로컬)** |
| **v2.1** | **2026-03-20** | **Next.js 웹 대시보드 추가, 5개 탭 구성** |

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

## 웹 대시보드 구조

```
[Frontend — Next.js App Router]
  app/page.tsx
    ├── HomeSearch        → 초기 검색 페이지 (구/동 선택)
    └── Dashboard         → 5개 탭 구성
        ├── Overview      → 종합 개요 (KPI, 지도, 가격 차트, 뉴스, 리스크)
        ├── Region        → 지역 분석 (구별 비교 테이블)
        ├── Price Trends  → 가격 동향 (시계열 차트)
        ├── Apt Search    → 아파트 검색 (개별 예측)
        └── AI Report     → AI 리포트 (시장 분석)

[API Routes]
  app/api/
    ├── predictions/route.ts       → GET /api/predictions (동별 예측)
    ├── predictions/apt/route.ts   → GET /api/predictions/apt (아파트별 예측)
    ├── news/route.ts              → GET /api/news (뉴스 시그널)
    └── trade-history/route.ts     → GET /api/trade-history (실거래 이력)

[Components]
  components/dashboard/
    ├── collapsible-sidebar.tsx    → 탭 네비게이션
    ├── home-search.tsx            → 검색 UI
    ├── map-area.tsx               → SVG 서울 지도
    ├── price-prediction-chart.tsx → Recharts 시계열 차트
    ├── news-sentiment-feed.tsx    → 뉴스 피드
    ├── gu-detail-sheet.tsx        → 구 상세 모달
    └── tabs/                      → 5개 탭 컴포넌트
```

---

## 실행 방법

### 환경 설정

#### Python 환경
```bash
pip install -r requirements.txt
# homesignal.env 파일에 API 키 설정 (.env.example 참고)
```

#### Next.js 환경
```bash
npm install
# 또는
pnpm install

# .env 파일 생성 (.env.example 참고)
```

**환경 변수 설정:**

**Frontend (`.env` or `.env.local`):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

**Python (`homesignal.env`):**
```bash
PUBLIC_DATA_API_KEY=your_public_data_api_key    # 공공데이터포털
ECOS_API_KEY=your_ecos_api_key                  # 한국은행 ECOS
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
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

### 4. 웹 대시보드 실행

```bash
# 개발 서버 시작
npm run dev
# → http://localhost:3000

# 프로덕션 빌드
npm run build
npm run start

# 린트 체크
npm run lint
```

### 5. 전체 워크플로우

**최초 설정 (1회):**
```bash
# 1. Python 패키지 설치
pip install -r requirements.txt

# 2. Node.js 패키지 설치
npm install

# 3. 환경 변수 설정
# .env.example 참고하여 .env 및 homesignal.env 생성

# 4. Supabase 스키마 생성
# Supabase SQL Editor에서 실행:
#   - supabase_schema.sql
#   - supabase_views.sql

# 5. 데이터 수집 (최초 전체)
python collect_data.py full

# 6. 모델 실행
python predict_model.py
```

**정기 업데이트 (월별):**
```bash
# 1. 데이터 증분 수집
python collect_data.py update

# 2. 예측 모델 재실행
python predict_model.py

# 3. 대시보드 자동 반영 (Supabase 연동)
# → http://localhost:3000 에서 최신 예측 확인
```

**월별 자동화 (선택):**
- `monthly_update.bat` 스크립트를 Windows 작업 스케줄러에 등록
- 매월 자동으로 데이터 수집 및 예측 수행 가능

### 출력 파일

**ML Pipeline 출력 (로컬 파일):**

| 파일 | 내용 |
|---|---|
| `price_trend.png` | 매매가·전세가·금리 추이 차트 |
| `correlation_heatmap.png` | 변수 간 상관관계 히트맵 |
| `importance_1m.png`, `importance_2m.png`, `importance_3m.png` | 예측 변수 중요도 차트 |
| `actual_vs_pred.png` | 실제 vs 예측 정확도 차트 |
| `prediction_result.csv` | 동별 1~3개월 후 예측 결과 |
| `prediction_result_apt.csv` | 아파트별 1~3개월 후 헤도닉 예측 |

**데이터베이스 저장:**
- `predictions` 테이블 - 동별 예측 (자동 upsert)
- `predictions_apt` 테이블 - 아파트별 예측 (자동 upsert)

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

## 프로젝트 구조

```
home_signal_ai/
├── app/                          # Next.js App Router
│   ├── page.tsx                  # 메인 대시보드 페이지
│   ├── layout.tsx                # 루트 레이아웃 (테마 프로바이더)
│   ├── globals.css               # 글로벌 스타일
│   └── api/                      # API Routes
│       ├── predictions/          # 예측 데이터 API
│       ├── news/                 # 뉴스 시그널 API
│       └── trade-history/        # 실거래 이력 API
├── components/
│   ├── dashboard/                # 대시보드 컴포넌트
│   │   ├── tabs/                 # 5개 탭 컴포넌트
│   │   └── *.tsx                 # UI 컴포넌트
│   └── ui/                       # shadcn/ui 재사용 컴포넌트
├── lib/
│   ├── supabase.ts               # Supabase 클라이언트 + 타입
│   └── utils.ts                  # 유틸리티 함수
├── collect_data.py               # 데이터 수집 파이프라인
├── predict_model.py              # ML 예측 파이프라인
├── supabase_schema.sql           # 데이터베이스 스키마
├── supabase_views.sql            # 피처 엔지니어링 뷰
├── requirements.txt              # Python 의존성
├── package.json                  # Node.js 의존성
├── monthly_update.bat            # 자동 업데이트 스크립트
├── .env.example                  # 환경 변수 템플릿
└── README.md                     # 프로젝트 문서
```

---

## 주의사항

**보안:**
- `homesignal.env` 및 `.env` 파일은 `.gitignore`에 포함되어 있으며 **절대 커밋하지 않습니다**
- API 키는 `.env.example`을 참고하여 별도로 설정해야 합니다

**데이터 특성:**
- 뉴스 피처는 **1개월 lag** 적용으로 정보 누수(look-ahead bias)를 방지합니다
- 뉴스 수집 기간(2026-02~) 이전 데이터는 뉴스 피처가 `0`으로 채워져 모델이 정상 작동합니다
- `dongs` 테이블의 `gu_name` 컬럼을 채워야 구별 로컬 뉴스 피처가 활성화됩니다

**API 제약:**
- 공공데이터포털 API는 호출 제한이 있어 `collect_data.py`는 요청 간 1초 지연 포함
- 대용량 데이터 수집 시 시간이 소요될 수 있습니다 (최초 수집: 약 30분~1시간)

**개발 환경:**
- Python ML 스크립트는 Windows 환경에서 "Malgun Gothic" 폰트 사용 (다른 OS에서는 폰트 조정 필요)
- TypeScript strict 모드 활성화되어 있으나 빌드 에러는 무시 설정 (`next.config.mjs`)

---

## 트러블슈팅

### 프론트엔드

**문제: `npm run dev` 실행 시 Supabase 연결 오류**
```bash
# 해결: .env 파일 확인
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

**문제: 빌드 시 TypeScript 에러**
```bash
# 해결: next.config.mjs 에서 ignoreBuildErrors: true 설정됨
# 개발 중 타입 에러는 IDE에서 확인하고 수정 권장
```

**문제: 대시보드에 예측 데이터가 표시되지 않음**
```bash
# 해결 순서:
# 1. python predict_model.py 실행했는지 확인
# 2. Supabase predictions 테이블에 데이터가 있는지 확인
# 3. API 엔드포인트 테스트: http://localhost:3000/api/predictions
```

### 백엔드 (Python)

**문제: `collect_data.py` 실행 시 API 키 에러**
```bash
# 해결: homesignal.env 파일에 API 키 설정
PUBLIC_DATA_API_KEY=your_key
ECOS_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

**문제: `predict_model.py` 실행 시 뷰를 찾을 수 없음**
```bash
# 해결: Supabase SQL Editor에서 순서대로 실행
# 1. supabase_schema.sql
# 2. supabase_views.sql
```

**문제: 한글 폰트 렌더링 오류 (macOS/Linux)**
```python
# 해결: predict_model.py 상단 수정
# Windows: "Malgun Gothic"
# macOS: "AppleGothic" 또는 "Arial Unicode MS"
# Linux: "NanumGothic" 설치 후 설정
plt.rcParams["font.family"] = "AppleGothic"  # macOS
```

**문제: 데이터 수집이 너무 느림**
```bash
# 원인: 공공데이터포털 API 제약 (요청당 1초 지연)
# 해결: collect_data.py update (증분 업데이트) 사용
# 최초 full 수집은 30분~1시간 소요 (정상)
```

### 데이터베이스

**문제: 로컬 뉴스 피처가 활성화되지 않음**
```sql
-- 해결: dongs 테이블의 gu_name 컬럼 채우기
UPDATE dongs SET gu_name = '동대문구' WHERE dong_name LIKE '%동대문구%';
UPDATE dongs SET gu_name = '성북구' WHERE dong_name LIKE '%성북구%';
-- (나머지 구도 동일하게 업데이트)
```

---

## 문서

- **CLAUDE.md** - Claude Code (AI 개발 도구)를 위한 상세 개발 가이드
- **README.md** - 프로젝트 개요 및 실행 가이드 (이 문서)
- **작업일지_*.md** - 개발 과정 기록
- **모델링_종합보고서.md** - ML 모델 성능 분석 보고서

---

## 기여

이슈 및 풀 리퀘스트는 언제나 환영합니다.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 실제 부동산 투자 결정에 사용 시 주의가 필요합니다.
