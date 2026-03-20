<<<<<<< HEAD
# HomeSignal AI

동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스

## 프로젝트 개요

HomeSignal AI는 **Prophet + LightGBM 앙상블 모델**과 **RAG 기반 챗봇**을 결합하여 동대문구 부동산 시장을 분석하는 AI 서비스입니다.

### 핵심 기능

1. **시계열 예측**: 실거래가, 뉴스 키워드, 정책 이벤트를 통합한 가격 예측
2. **RAG 챗봇**: Vector DB 기반 부동산 정보 상담 (4단계 Query Planner Agent)
3. **뉴스 분석**: 키워드 빈도 및 감성 시그널 분석 (8개 카테고리, 95개 키워드)

### 주요 특징

- **Mock-First 개발**: 외부 서비스 없이도 전체 API 실행 가능
- **Repository 패턴**: 데이터 접근 추상화로 Mock/Production 전환 자동화
- **Query Planner Agent**: 복잡한 질문을 4단계로 분해 및 실행 (Intent → Decompose → Plan → Execute)
- **Hybrid Keyword Extraction**: KoNLPy + TF-IDF 결합 방식
- **Ensemble Forecasting**: Prophet + LightGBM 앙상블 (60:40 비율)
- **Rise Point Detection**: MA Crossover, Rate Threshold, Consecutive Rise 알고리즘

---

## 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
uv sync --extra ml --extra dev --extra crawler

# .env 파일 생성
cp .env.example .env
# SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY 등 설정
```

### 2. 데이터베이스 설정

Supabase SQL Editor에서 마이그레이션 실행:

```bash
# 1. 기본 테이블 (houses_data, news_signals, predictions)
migrations/001_setup_pgvector.sql

# 2. ML Feature 테이블 (ml_training_features, policy_events)
migrations/004_create_ml_features_tables.sql
```

### 3. 데이터 수집

```bash
# 뉴스 크롤링
uv run python -m src.crawler.cli crawl -q "GTX-C 청량리" "동대문구 재개발"

# 임베딩 생성
uv run python scripts/generate_embeddings.py

# 정책 이벤트 수집
uv run python scripts/collect_policy_events.py
```

### 4. ML Feature 생성 및 모델 학습

```bash
# Feature 생성 (실거래가 + 뉴스 + 이벤트 + 계절성 통합)
uv run python scripts/generate_ml_features.py

# 모델 학습 (Prophet + LightGBM)
uv run python scripts/train_forecast_model.py
```

### 5. API 서버 실행

```bash
# 로컬 개발 (src/main.py)
uv run uvicorn src.main:app --reload

# Mock 모드 (외부 서비스 없이 실행)
export SUPABASE_URL="placeholder"  # 또는 빈 문자열
uv run uvicorn src.main:app --reload
```

API 문서: http://localhost:8000/docs

**참고**: Vercel 배포 시에는 `api/index.py`가 진입점으로 사용됩니다 (serverless 함수)

### 6. 진단 및 검증 (선택사항)

```bash
# 데이터베이스 스키마 검사
uv run python scripts/inspect_db_schema.py

# Supabase 연결 테스트
uv run python scripts/check_supabase.py

# 데이터 무결성 검증
uv run python scripts/validate_data_integrity.py --check-rpc

# Vercel 환경변수 검증
uv run python scripts/check_vercel_env.py
```

---

## Mock 모드 (외부 서비스 없이 개발)

외부 서비스 없이 API를 실행할 수 있습니다:

```bash
# Mock 모드 활성화
export SUPABASE_URL="placeholder"  # 또는 빈 문자열
export SUPABASE_KEY=""
export OPENAI_API_KEY=""

# API 실행 (자동으로 Mock 구현 사용)
uv run uvicorn src.main:app --reload
```

**자동 Mock 전환 조건:**
- `SUPABASE_URL`이 "placeholder" 포함 또는 빈 문자열
- Supabase 라이브러리 없음
- 명시적 `use_mock=True` 파라미터

**Mock 구현:**
- `MockSupabaseClient` - 하드코딩된 시계열 데이터 반환
- `MockVectorDB` - 시뮬레이션된 벡터 검색 결과
- `MockDataRepository` - 샘플 뉴스 시그널 및 키워드 빈도

---

## 프로젝트 구조

```
homesignal-ai/
├── api/
│   └── index.py           # Vercel 서버리스 진입점
├── src/
│   ├── main.py            # FastAPI 앱 정의 (로컬 개발용)
│   ├── forecast/          # 시계열 예측
│   │   ├── service.py     # Prophet + LightGBM 앙상블
│   │   ├── model_loader.py # 모델 로드 유틸
│   │   └── rise_point_detector.py
│   ├── chat/              # RAG 챗봇
│   │   ├── service.py
│   │   ├── planner/       # Query Planner Agent (4-stage)
│   │   └── extractors/    # 하이브리드 키워드 추출
│   ├── news/              # 뉴스 분석
│   ├── crawler/           # Google News 크롤러
│   ├── ingest/            # 데이터 수집 API (JWT 인증)
│   └── shared/            # 공통 모듈
│       ├── database.py    # Supabase 클라이언트 (Mock 지원)
│       ├── data_repository.py  # Repository 패턴
│       ├── ai_client.py   # AI API 추상화
│       ├── vector_db.py   # Vector DB (Mock 지원)
│       ├── mcp_client.py  # MCP 프로토콜 클라이언트
│       └── embedding.py   # 임베딩 생성
├── scripts/
│   ├── generate_ml_features.py    # ML Feature 생성
│   ├── train_forecast_model.py    # 모델 학습
│   ├── collect_policy_events.py   # 정책 이벤트 수집
│   ├── generate_embeddings.py     # 벡터 임베딩 생성
│   ├── split_train_test_data.py   # 학습/테스트 분할
│   ├── setup_vercel_env.py        # Vercel 환경변수 설정
│   └── check_*.py         # 진단 스크립트
├── migrations/            # Supabase SQL 마이그레이션
│   ├── 001_setup_pgvector.sql
│   ├── 004_create_ml_features_tables.sql
│   └── 006_add_rpc_methods.sql
├── config/
│   ├── keywords.yaml              # 뉴스 키워드 (8 카테고리, 95개)
│   ├── policy_events.yaml         # 정책 이벤트 정의
│   └── rise_point_config.yaml     # 가격 상승점 탐지 설정
├── models/                        # 학습된 모델 저장
│   ├── prophet_청량리동_week_v1.pkl
│   └── lightgbm_청량리동_week_v1.pkl
├── tests/                         # 테스트 (async 지원)
│   ├── conftest.py        # 공통 fixtures
│   ├── test_planner.py    # Query Planner 테스트
│   ├── test_ml_features.py
│   └── crawler/           # 크롤러 테스트
├── frontend/                      # Next.js 프론트엔드
│   ├── app/                       # 다크모드 UI
│   ├── components/                # 공통 컴포넌트
│   └── styles/                    # 디자인 토큰
└── docs/                          # 문서
```

---

## 핵심 문서

| 문서 | 내용 |
|------|------|
| **[CLAUDE.md](CLAUDE.md)** | **완전한 개발 가이드 (명령어, 아키텍처, 트러블슈팅)** ⭐ |
| [docs/01_PRD_HomeSignalAI.md](docs/01_PRD_HomeSignalAI.md) | 요구사항 정의 |
| [docs/02_Architecture_Design.md](docs/02_Architecture_Design.md) | 시스템 아키텍처 설계 |
| [docs/03_AI_Model_Pipeline.md](docs/03_AI_Model_Pipeline.md) | ML 파이프라인 |
| [docs/04_Prompt_RAG_Strategy.md](docs/04_Prompt_RAG_Strategy.md) | RAG 로직, 프롬프트 템플릿 |
| [docs/06_Rise_Point_Keyword_Extraction.md](docs/06_Rise_Point_Keyword_Extraction.md) | 가격 상승점 탐지 전략 |
| **[docs/07_API_Contract_Rules.md](docs/07_API_Contract_Rules.md)** | **DB/Backend/Frontend 공통 규칙 (SSOT)** ⭐ |
| [docs/08_Vercel_Architecture_Guide.md](docs/08_Vercel_Architecture_Guide.md) | Vercel 배포 아키텍처 가이드 |
| [docs/12_Vector_DB_Setup_Guide.md](docs/12_Vector_DB_Setup_Guide.md) | Vector DB (pgvector) 설정 |
| [docs/13_Database_Schema_and_Relationships.md](docs/13_Database_Schema_and_Relationships.md) | 데이터베이스 스키마 및 RPC 함수 |
| [docs/ML_Feature_통합_테이블_가이드.md](docs/ML_Feature_통합_테이블_가이드.md) | ML Feature 테이블 구조 및 생성 |
| [docs/VERCEL_ENV_SETUP.md](docs/VERCEL_ENV_SETUP.md) | Vercel 환경변수 설정 가이드 |

---

## 기술 스택

### Backend
- **Framework**: FastAPI (비동기 아키텍처)
- **Database**: Supabase (PostgreSQL + pgvector)
- **ML**: Prophet, LightGBM, scikit-learn
- **AI**: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **Cache**: Redis
- **Integration**: MCP (Model Context Protocol) 지원
- **Deployment**: Vercel Serverless Functions

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS (다크모드)
- **Charts**: Recharts
- **State**: React Query

---

## 아키텍처 하이라이트

### Query Planner Agent (4단계)

복잡한 사용자 질문을 체계적으로 처리:

1. **IntentClassifier**: 질문 유형 분류 (forecast, comparison, news_analysis, general)
2. **QueryDecomposer**: 복잡한 질문을 하위 질문으로 분해
3. **PlanGenerator**: 실행 계획 생성 (데이터 소스, 순서, 의존성)
4. **PlanExecutor**: 계획 실행 및 AI 응답 합성

**예시**: "청량리와 이문동 중 어디가 더 오를까?"
→ ["청량리 예측", "이문동 예측", "비교 분석"] 3개 하위 질문으로 분해

### Mock-First 아키텍처

Factory 패턴을 통한 자동 Mock 전환:
- `get_supabase_client()` → `MockSupabaseClient` or `SupabaseClient`
- `get_data_repository()` → `MockDataRepository` or `SupabaseDataRepository`
- `get_vector_db()` → `MockVectorDB` or `SupabaseVectorDB`

**장점**: 외부 서비스 없이도 전체 API 개발 및 테스트 가능

### Repository 패턴

모든 데이터 접근은 `DataRepositoryInterface`를 통해 이루어짐:
- 비즈니스 로직과 데이터 소스 분리
- Mock/Production 구현 쉽게 전환
- 테스트 용이성 향상

---

## ML 파이프라인

### 1. Feature 통합

**ml_training_features** 테이블에 다음을 통합:
- 실거래가 집계 (avg_price, transaction_count)
- 뉴스 키워드 빈도 (8개 카테고리)
- 정책 이벤트 더미 (5개 타입)
- 계절성 더미 (개학/이사/결혼)
- 이동평균 (5주, 20주)

### 2. 모델 학습

- **Prophet**: 트렌드, 계절성, Regressor (뉴스, 이벤트)
- **LightGBM**: 모든 Feature 학습 (뉴스 가중치)
- **Ensemble**: Prophet 60% + LightGBM 40%

### 3. 예측 서빙

- 학습된 모델 로드 (models/)
- 최신 Feature 조회 (ml_training_features)
- 앙상블 예측 실행
- 신뢰구간 포함 응답

---

## 개발 워크플로우

### 신규 Feature 추가
1. `migrations/004_create_ml_features_tables.sql`에 컬럼 추가
2. `scripts/generate_ml_features.py`에 생성 로직 추가
3. `scripts/train_forecast_model.py`에 Feature 매핑 추가
4. 재학습 및 평가

### 신규 정책 이벤트 추가
1. `config/policy_events.yaml`에 이벤트 추가
2. `uv run python scripts/collect_policy_events.py` 실행
3. Feature 재생성 및 모델 재학습

### 코드 품질 관리

```bash
# 코드 포맷팅
uv run ruff format src/

# 린트 체크
uv run ruff check src/

# 타입 체크
uv run mypy src/

# 전체 품질 체크
uv run ruff check src/ && uv run mypy src/ && uv run pytest
```

---

## 테스트

```bash
# 전체 테스트
uv run pytest

# 특정 모듈 테스트
uv run pytest tests/test_ml_features.py -v
uv run pytest tests/test_planner.py -v
uv run pytest tests/crawler/ -v

# 키워드로 테스트 필터링
uv run pytest -k "planner" -v

# 커버리지 리포트
uv run pytest --cov=src tests/

# HTML 커버리지 리포트
uv run pytest --cov=src --cov-report=html tests/
```

**주요 테스트 파일:**
- `test_planner.py` - Query Planner Agent (4단계 파이프라인)
- `test_ml_features.py` - ML Feature 생성 및 통합
- `test_rise_point_detector.py` - 가격 상승점 탐지 알고리즘
- `test_rpc_methods.py` - Database RPC 함수 검증
- `crawler/*.py` - 크롤러 컴포넌트 (rate limiter, keyword extractor)

**참고**: 모든 async 테스트는 `pytest.ini_options.asyncio_mode = "auto"`로 자동 처리

---

## 배포

### Backend (Vercel Serverless)
```bash
vercel --prod
```

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

자세한 내용: [VERCEL_DEPLOYMENT_GUIDE.md](VERCEL_DEPLOYMENT_GUIDE.md)

---

## 문제 해결

### 일반적인 문제

**의존성 설치 실패**
```bash
# 모든 선택적 의존성 포함 설치
uv sync --extra ml --extra dev --extra crawler --extra nlp
```

**데이터베이스 연결 실패**
```bash
# Mock 모드로 전환
export SUPABASE_URL="placeholder"

# 또는 .env 파일 확인
cat .env | grep SUPABASE
```

**Vercel ValidationError**
```bash
# 환경변수 자동 설정
uv run python scripts/setup_vercel_env.py --environment production

# 수동 설정
vercel env add SUPABASE_URL production
vercel env add SUPABASE_KEY production

# 재배포
vercel --prod --force
```

**테스트 실패**
```bash
# pytest-asyncio 확인
uv sync --extra test

# 단일 테스트 실행
uv run pytest tests/test_planner.py -v
```

자세한 내용: [CLAUDE.md](CLAUDE.md) - 전체 개발 가이드 참조

---

## 빠른 참조

### 핵심 상수
- **대상 지역**: 청량리동, 이문동, 회기동, 휘경동
- **임베딩 차원**: 1536 (OpenAI text-embedding-3-small)
- **앙상블 비율**: Prophet 60% + LightGBM 40%
- **뉴스 카테고리**: transport_gtx, redevelopment, supply, policy, school, environment, finance, event

### 주요 엔드포인트
- `GET/POST /api/v1/forecast` - 가격 예측
- `POST /api/v1/chat` - RAG 챗봇
- `GET /api/v1/news/insights` - 뉴스 분석
- `POST /api/v1/ingest/*` - 데이터 수집 (JWT 인증 필요)

---

## 라이선스

MIT License

---

## 기여

HomeSignal AI는 동대문구 부동산 시장 분석을 위한 오픈소스 프로젝트입니다.
=======
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
>>>>>>> web
