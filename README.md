# HomeSignal AI

동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스

## 프로젝트 개요

HomeSignal AI는 **Prophet + LightGBM 앙상블 모델**과 **RAG 기반 챗봇**을 결합하여 동대문구 부동산 시장을 분석하는 AI 서비스입니다.

### 핵심 기능

1. **시계열 예측**: 실거래가, 뉴스 키워드, 정책 이벤트를 통합한 가격 예측
2. **RAG 챗봇**: Vector DB 기반 부동산 정보 상담
3. **뉴스 분석**: 키워드 빈도 및 감성 시그널 분석

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
uv run uvicorn src.main:app --reload
```

API 문서: http://localhost:8000/docs

---

## 프로젝트 구조

```
homesignal-ai/
├── src/
│   ├── forecast/          # 시계열 예측
│   │   ├── service.py     # Prophet + LightGBM 앙상블
│   │   ├── model_loader.py # 모델 로드 유틸
│   │   └── rise_point_detector.py
│   ├── chat/              # RAG 챗봇
│   │   ├── service.py
│   │   ├── planner/       # Query Planner Agent
│   │   └── extractors/    # 하이브리드 키워드 추출
│   ├── news/              # 뉴스 분석
│   ├── crawler/           # Google News 크롤러
│   ├── ingest/            # 데이터 수집 API
│   └── shared/            # 공통 모듈
├── scripts/
│   ├── generate_ml_features.py    # ML Feature 생성
│   ├── train_forecast_model.py    # 모델 학습
│   ├── collect_policy_events.py   # 정책 이벤트 수집
│   └── generate_embeddings.py     # 벡터 임베딩 생성
├── migrations/
│   ├── 001_setup_pgvector.sql
│   └── 004_create_ml_features_tables.sql
├── config/
│   ├── keywords.yaml              # 뉴스 키워드 정의
│   ├── policy_events.yaml         # 정책 이벤트 정의
│   └── rise_point_config.yaml
├── models/                        # 학습된 모델 저장
│   ├── prophet_청량리동_week_v1.pkl
│   └── lightgbm_청량리동_week_v1.pkl
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
| [CLAUDE.md](CLAUDE.md) | 개발 가이드 (명령어, 아키텍처) |
| [docs/01_PRD_HomeSignalAI.md](docs/01_PRD_HomeSignalAI.md) | 요구사항 정의 |
| [docs/02_Architecture_Design.md](docs/02_Architecture_Design.md) | 시스템 아키텍처 설계 |
| [docs/03_AI_Model_Pipeline.md](docs/03_AI_Model_Pipeline.md) | ML 파이프라인 |
| **[docs/07_API_Contract_Rules.md](docs/07_API_Contract_Rules.md)** | **DB/Backend/Frontend 공통 규칙** ⭐ |
| [docs/ML_Feature_통합_테이블_가이드.md](docs/ML_Feature_통합_테이블_가이드.md) | Feature 테이블 가이드 |
| [docs/12_Vector_DB_Setup_Guide.md](docs/12_Vector_DB_Setup_Guide.md) | Vector DB 설정 |
| [VERCEL_DEPLOYMENT_GUIDE.md](VERCEL_DEPLOYMENT_GUIDE.md) | Vercel 배포 가이드 |

---

## 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL + pgvector)
- **ML**: Prophet, LightGBM, scikit-learn
- **AI**: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **Cache**: Redis

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS (다크모드)
- **Charts**: Recharts
- **State**: React Query

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

---

## 테스트

```bash
# 전체 테스트
uv run pytest

# ML Feature 테스트
uv run pytest tests/test_ml_features.py -v

# 커버리지 리포트
uv run pytest --cov=src tests/
```

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

## 라이선스

MIT License

---

## 기여

HomeSignal AI는 동대문구 부동산 시장 분석을 위한 오픈소스 프로젝트입니다.
