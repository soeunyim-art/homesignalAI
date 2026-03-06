# HomeSignal AI — 인수인계서 (Handover Document)

**문서 버전:** 1.1  
**최종 수정일:** 2026-02-28  
**프로젝트:** 동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스  
**대상:** 후임 개발자, DB 담당자, 기획자, 디자이너  
**참조 룰:** [moduler box](https://github.com/Siyeolryu/Ai_study/tree/main/moduler%20box) — 모듈형 인수인계 구조

---

## 목차

1. [프로젝트 한눈에 보기](#1-프로젝트-한눈에-보기)
2. [역할별 인수인계 요약](#2-역할별-인수인계-요약)
3. [2026-02-28 완료 내역 및 나머지 개발](#3-2026-02-28-완료-내역-및-나머지-개발)
4. [후임 개발자 인수인계](#4-후임-개발자-인수인계)
5. [DB 담당자 인수인계](#5-db-담당자-인수인계)
6. [기획자 인수인계](#6-기획자-인수인계)
7. [디자이너 인수인계](#7-디자이너-인수인계)
8. [공통 참고사항](#8-공통-참고사항)

---

## 1. 프로젝트 한눈에 보기

### 1.1 프로젝트 정의

**HomeSignal AI**는 서울 동대문구를 대상으로 한 부동산 시장 분석 서비스입니다.  
**시계열 가격 예측 엔진**과 **RAG(검색 증강 생성) AI 챗봇**을 결합하여, 단순 수치 예측을 넘어 **"왜 오르는가(이슈, 정책, 뉴스)"**에 대한 근거를 함께 제공합니다.

### 1.2 현재 완성도

```
■■■■■□□□□□  약 45% 완성
```

| 영역 | 완성도 | 상세 |
|------|--------|------|
| 기획·설계 문서 | ✅ 100% | PRD, 아키텍처, ML 파이프라인, RAG 전략, 배포 가이드 |
| 백엔드 API 골격 | ✅ 100% | FastAPI 라우터/서비스/스키마 전체 구조 완성 |
| DB 스키마 설계 | ✅ 100% | 4개 테이블 SQL DDL 완성 |
| **Supabase 연동** | ✅ **설정 완료** | 2026-02-28 .env, DataRepository, 프론트 클라이언트 |
| 데이터 수집 | ⬜ 0% | 국토교통부 API, 뉴스 크롤러 미구현 |
| ML 모델 | ⬜ 0% | Prophet, LightGBM 학습 코드 미구현 |
| Vector DB·AI API·Redis | ⬜ 0% | 실제 연결 미완 |
| 프론트엔드 | ⚠️ 30% | design/ 기반 Mock, Supabase 클라이언트 준비됨 |
| 테스트 | ⬜ 0% | 단위/통합 테스트 미작성 |

### 1.3 시스템 구성도 (간략)

```
사용자 (프론트엔드)
       │
       ▼
 ┌─────────────────────────────────────────────┐
 │          FastAPI 백엔드 서버                   │
 │                                               │
 │  /api/v1/forecast  ← 시계열 예측              │
 │  /api/v1/chat      ← RAG 챗봇                │
 │  /api/v1/news      ← 뉴스 인사이트            │
 │                                               │
 │  [Redis 캐시] [Fallback 로직]                 │
 └──────┬──────────┬──────────┬─────────────────┘
        │          │          │
        ▼          ▼          ▼
   Supabase   Vector DB    AI API
  (PostgreSQL)  (RAG용)   (GPT-4o/Claude)
        ▲
        │
  데이터 수집 파이프라인
  (국토교통부 API + 뉴스 크롤링)
```

---

## 2. 역할별 인수인계 요약

| 역할 | 핵심 인수인계 내용 | 최우선 해야 할 일 |
|------|-------------------|-------------------|
| **후임 개발자** | 백엔드 코드 전체, Mock→실제 데이터 교체, ML 모델 개발 | Mock 데이터를 실제 데이터로 교체 |
| **DB 담당자** | Supabase 스키마, Vector DB 인터페이스, 데이터 파이프라인 | Supabase에 테이블 생성 및 데이터 적재 |
| **기획자** | PRD, 성공 지표, 로드맵, 사용자 시나리오 | 미구현 기능 우선순위 재정립 |
| **디자이너** | API 응답 구조, 사용자 흐름, 톤앤매너 | 프론트엔드 UI/UX 설계 |

---

## 3. 2026-02-28 완료 내역 및 나머지 개발

### [Box A] 2026-02-28 당일 완료

| # | 작업 | 담당 영역 | 산출물 |
|---|------|-----------|--------|
| 1 | Supabase 백엔드 연동 | 백엔드 | `.env` SUPABASE_URL, SUPABASE_KEY |
| 2 | DataRepository 자동 전환 | 백엔드 | placeholder → Mock, 실제 URL → SupabaseDataRepository |
| 3 | 프론트 Supabase 클라이언트 | 프론트 | `design/.../lib/supabase.ts`, @supabase/supabase-js |
| 4 | 프론트 환경변수 | 프론트 | `.env.local`, `.env.example` |
| 5 | DATABASE_URL 옵션 | 설정 | `settings.py`, PostgreSQL 직접 연결 |
| 6 | pyiceberg 의존성 | 패키지 | supabase storage3 호환 |
| 7 | GitHub 푸시 대상 지정 | - | https://github.com/soeunyim-art/homesignalAI |

### [Box B] 나머지 개발 — 백엔드

| # | 작업 | 우선순위 | 의존성 |
|---|------|----------|--------|
| 1 | 국토교통부 실거래가 API 연동 | P0 | 없음 |
| 2 | 구글 뉴스 크롤러 | P0 | 없음 |
| 3 | Supabase 테이블 생성 및 데이터 적재 | P0 | DB 담당자 |
| 4 | Prophet + LightGBM 모델 학습 | P0 | 1 |
| 5 | Forecast API Mock → 실제 DB 조회 | P0 | 3, 4 |
| 6 | Vector DB 실제 연동 | P1 | DB 담당자 |
| 7 | AI API 실제 연동·비용 모니터링 | P1 | OpenAI/Anthropic 키 |
| 8 | Redis 캐싱 성능 테스트 | P2 | Redis 서버 |
| 9 | pyiceberg 미설치 환경 대응 | P2 | Windows 등 |

### [Box C] 나머지 개발 — 프론트엔드

| # | 작업 | 우선순위 | 의존성 |
|---|------|----------|--------|
| 1 | `lib/data.ts` Mock 제거, API 호출 | P0 | 백엔드 /api/v1/forecast |
| 2 | 예측·챗봇·뉴스 API 연동 | P0 | 1 |
| 3 | 에러·Fallback·로딩 UI | P0 | 1 |
| 4 | NEXT_PUBLIC_API_URL 설정 | P0 | 백엔드 URL |
| 5 | Vercel 배포 (선택) | P2 | 1~4 |

### [Box D] 나머지 개발 — DB·인프라

| # | 작업 | 담당 | 상세 |
|---|------|------|------|
| 1 | `db_Schema(Sql)_mokdb.md` DDL 실행 | DB | 4개 테이블, pgvector |
| 2 | RLS 정책 설정 | DB | anon key 보안 |
| 3 | houses_data 초기 데이터 적재 | DB | 국토교통부 데이터 |
| 4 | CORS 프론트 도메인 추가 | 백엔드 | Vercel, localhost |

### [Box E] 나머지 개발 — 테스트·배포

| # | 작업 | 상태 |
|---|------|------|
| 1 | 단위 테스트 (pytest) | ⬜ 미착수 |
| 2 | 통합 테스트 (E2E) | ⬜ 미착수 |
| 3 | 성능 테스트 (2.0초 목표) | ⬜ 미착수 |
| 4 | Git push (soeunyim-art/homesignalAI) | ⬜ 예정 |
| 5 | Docker·스테이징 배포 | ⬜ 미착수 |

---

## 4. 후임 개발자 인수인계

### 4.1 즉시 확인할 사항

#### 1) 개발 환경 세팅
```bash
# Python 3.11+ 필수
python --version

# uv 설치 (패키지 매니저)
pip install uv

# 의존성 설치
uv sync

# 환경변수 설정
cp .env.example .env
# .env 파일에 실제 API 키 입력

# 개발 서버 실행
uv run uvicorn src.main:app --reload

# 브라우저에서 확인
# http://127.0.0.1:8000/docs → Swagger UI
```

#### 2) Git 초기화 (최우선)
```bash
git init
git add .
git commit -m "Initial commit: HomeSignal AI backend skeleton"
```

#### 3) 프로젝트 이해를 위한 문서 읽기 순서
1. `docs/01_PRD_HomeSignalAI.md` — 왜 만드는가 (비즈니스 목표)
2. `docs/02_Architecture_Design.md` — 어떻게 만드는가 (기술 구조)
3. `docs/06_Development_Journal.md` — 지금까지 무엇이 완성되었는가
4. `CLAUDE.md` — 개발 명령어 및 구조 요약
5. 나머지 설계 문서 (03, 04, 05)

### 4.2 코드베이스 핵심 이해

#### 앱 엔트리포인트 (`src/main.py`)
- FastAPI 앱 생성, CORS 설정, 전역 예외 핸들러 등록
- 3개 도메인 라우터(`forecast`, `chat`, `news`)를 `/api/v1` 프리픽스로 등록
- `lifespan` 함수로 앱 시작/종료 로그 관리
- `debug` 모드에서만 `/docs`, `/redoc` 활성화

#### 환경변수 (`src/config/settings.py`)
- `pydantic-settings` 기반, `.env` 파일 자동 로드
- `ai_provider`로 OpenAI/Anthropic 전환 가능
- `cache_ttl_forecast`(1시간), `cache_ttl_chat`(30분) TTL 설정
- `lru_cache` 데코레이터로 싱글톤 패턴 적용

#### 도메인 구조 (3개 도메인 동일 패턴)
```
domain/
├── router.py    → FastAPI 라우터 (엔드포인트 정의, 의존성 주입)
├── service.py   → 비즈니스 로직 (핵심 로직 여기에)
├── schemas.py   → Pydantic 스키마 (요청/응답 검증)
└── __init__.py  → 외부 공개 인터페이스
```

#### 공유 모듈 (`src/shared/`)
| 파일 | 역할 | 현재 상태 |
|------|------|-----------|
| `database.py` | Supabase 클라이언트 싱글톤 | 클라이언트 생성만 구현 |
| `ai_client.py` | OpenAI/Anthropic 통합 API 클라이언트 | ✅ 완전 구현 |
| `cache.py` | Redis 캐싱 (SHA-256 키, TTL) | ✅ 완전 구현 |
| `vector_db.py` | Vector DB 인터페이스 + Mock | ⚠️ Mock 상태 |
| `exceptions.py` | 커스텀 예외 계층 (5종) | ✅ 완전 구현 |

### 4.3 Mock 데이터 → 실제 데이터 교체 가이드

#### 우선순위 1: 시계열 예측 (`forecast/service.py`)

**현재 상태:** `_run_forecast()` 메서드가 하드코딩된 Mock 데이터 반환

**교체 방법:**
1. ML 의존성 설치: `uv sync --extra ml`
2. Prophet + LightGBM 모델 학습 코드 작성 (별도 모듈 또는 `forecast/models/`)
3. 학습된 모델 파일(.pkl) 로드 후 `_run_forecast()`에서 실제 예측 수행
4. `_get_news_weights()`에서 Supabase `news_signals` 테이블 쿼리

**참고 설계서:** `docs/03_AI_Model_Pipeline.md`

```python
# forecast/service.py 내 교체 대상 메서드:
async def _run_forecast(self, request: ForecastRequest) -> list[ForecastPoint]:
    # TODO: Prophet + LightGBM 앙상블 모델 연동
    # 현재는 Mock 데이터 반환
    ...

async def _get_news_weights(self, region: str) -> list[NewsWeightSummary]:
    # TODO: Supabase 뉴스 테이블에서 실제 데이터 조회
    ...
```

#### 우선순위 2: Vector DB 연동 (`shared/vector_db.py`)

**현재 상태:** `MockVectorDB` 클래스가 하드코딩된 2개의 뉴스 청크 반환

**교체 방법:**
1. Vector DB 담당자와 인터페이스 합의 (이미 `VectorDBInterface` ABC 정의됨)
2. `VectorDBInterface`를 구현하는 실제 클라이언트 클래스 작성
3. `get_vector_db()` 함수에서 Mock 대신 실제 구현체 반환

**인터페이스 규약:**
```python
class VectorDBInterface(ABC):
    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[DocumentChunk]:
        ...
    async def upsert(self, documents: list[dict], embeddings: list[list[float]]) -> bool:
        ...
```

#### 우선순위 3: 뉴스 분석 (`news/service.py`)

**현재 상태:** `_analyze_keywords()` 메서드가 Mock 딕셔너리 반환

**교체 방법:**
1. Supabase `news_signals` 테이블에서 키워드 빈도 집계 쿼리 작성
2. 감성 분석은 NLP 라이브러리 또는 AI API 활용
3. 크롤러 모듈 신규 작성 필요 (구글 뉴스 키워드 수집)

### 4.4 향후 개발 로드맵 (개발자 관점)

```
Phase 4: 데이터 수집 파이프라인
 ├── 국토교통부 실거래가 API 연동
 ├── 구글 뉴스 크롤러 구현
 └── 데이터 전처리 + Supabase 적재

Phase 5: ML 모델 개발
 ├── Prophet 베이스라인 모델 학습
 ├── LightGBM 뉴스 가중치 모델 학습
 ├── Ensemble 결합 로직
 └── RMSE/MAE/MAPE 평가

Phase 6: 외부 서비스 실제 연동
 ├── Supabase CRUD 로직 (houses_data 조회 등)
 ├── Redis 캐싱 연결 및 성능 테스트
 ├── AI API 실제 호출 + 비용 모니터링
 └── Vector DB 교체 (Mock → 실제)

Phase 7: 테스트 및 품질 보증
 ├── 단위 테스트 (pytest)
 ├── 통합 테스트 (E2E)
 ├── 성능 테스트 (2.0초 목표)
 └── 보안 점검 (XSS, CSRF, Prompt Injection)

Phase 8: 배포
 ├── Docker 컨테이너화
 ├── 스테이징 환경 배포
 └── 프로덕션 배포 + 롤백 계획
```

### 4.5 코드 컨벤션 및 주의사항

- **린트:** `ruff` 사용 (line-length: 88, Python 3.11 타겟)
- **타입 체크:** `mypy` strict mode
- **임포트 규칙:** ruff가 isort 대체 (`select = ["E", "F", "I", "N", "W", "UP"]`)
- **비동기 우선:** 모든 서비스 메서드는 `async def`로 작성
- **예외 처리:** `HomeSignalError` 계층 사용, AI 오류는 반드시 `AIAPIError`로 래핑
- **프롬프트 변경:** `prompts/v{n}.py` 새 파일 생성 → `__init__.py` import 전환

---

## 5. DB 담당자 인수인계

### 5.1 현재 상태 (DB)
- DB 스키마 SQL DDL이 `db_Schema(Sql)_mokdb.md` 파일에 정의되어 있습니다.
- **Supabase에 실제 테이블은 아직 생성되지 않았습니다.**

### 5.2 테이블 구조 상세

#### 테이블 1: `houses_data` (부동산 실거래 데이터)
```sql
create table houses_data (
    id uuid default gen_random_uuid() primary key,
    complex_name text not null,          -- 아파트 단지명
    dong_name text,                      -- 법정동 (동대문구 세부 동)
    price numeric,                       -- 실거래가
    bedrooms float,                      -- 침실 수
    bathrooms float,                     -- 욕실 수
    sqft_living int,                     -- 전용면적
    sqft_lot int,                        -- 대지면적
    floors float,                        -- 층수
    waterfront int,                      -- 수변 조망 여부
    view int,                            -- 조망권 등급
    condition int,                       -- 건물 상태
    sqft_above int,                      -- 지상층 면적
    sqft_basement int,                   -- 지하층 면적
    yr_built int,                        -- 준공 연도
    yr_renovated int,                    -- 리모델링 연도
    contract_date timestamp with time zone default now(),
    created_at timestamp with time zone default now()
);
```

**데이터 소스:** 국토교통부 실거래가 API + Kaggle data.csv 형식 참고  
**시계열 기준 컬럼:** `contract_date`  
**인덱스 권장:** `contract_date`, `dong_name`, `complex_name`

#### 테이블 2: `news_signals` (뉴스/정책 데이터)
```sql
create table news_signals (
    id uuid default gen_random_uuid() primary key,
    title text not null,
    content text,
    url text,
    keywords text[],                     -- 핵심 키워드 배열
    embedding vector(1536),              -- OpenAI text-embedding-3-small 규격
    published_at timestamp with time zone,
    created_at timestamp with time zone default now()
);
```

**핵심:** `embedding` 컬럼은 `pgvector` 확장 필요 (`create extension if not exists vector`)  
**키워드 예시:** GTX, 재개발, 청량리, 이문휘경뉴타운, 금리, 분양  
**인덱스 권장:** `published_at`, `keywords` (GIN), `embedding` (ivfflat 또는 hnsw)

#### 테이블 3: `ai_predictions` (모델 예측 결과)
```sql
create table ai_predictions (
    id uuid default gen_random_uuid() primary key,
    model_version text,                  -- 모델 버전 (예: "v1.0-prophet-lgbm")
    target_date date not null,           -- 예측 대상 일자
    predicted_price numeric,             -- 예측 가격
    confidence_score float,              -- 신뢰도 (0~1)
    features_used jsonb,                 -- 예측에 사용된 변수 가중치
    created_at timestamp with time zone default now()
);
```

**용도:** 모델 예측 이력 저장, 모델 버전 간 성능 비교  
**`features_used` 예시:**
```json
{
  "gtx_keyword_freq": 45,
  "redevelopment_freq": 32,
  "interest_rate": 3.5,
  "ma_5week": 104.2,
  "ma_20week": 101.8
}
```

#### 테이블 4: `user_interactions` (대화 로그 및 피드백)
```sql
create table user_interactions (
    id uuid default gen_random_uuid() primary key,
    user_query text,
    ai_response text,
    feedback_is_positive boolean,        -- 좋아요(true)/싫어요(false)/미응답(null)
    latency_ms int,                      -- 응답 속도 (밀리초)
    created_at timestamp with time zone default now()
);
```

**용도:** 사용자 행동 분석, AI 응답 품질 모니터링, 프롬프트 최적화 근거 데이터

### 5.3 DB 담당자가 해야 할 일

| 순서 | 작업 | 상세 |
|------|------|------|
| 1 | **Supabase 프로젝트 생성** | PostgreSQL 인스턴스 확보 |
| 2 | **pgvector 확장 활성화** | `create extension if not exists vector;` |
| 3 | **4개 테이블 생성** | `db_Schema(Sql)_mokdb.md`의 SQL 실행 |
| 4 | **인덱스 생성** | 위 권장 인덱스 적용 |
| 5 | **RLS(Row Level Security) 정책** | Supabase 보안 정책 설정 |
| 6 | **초기 데이터 적재** | 국토교통부 API 데이터 Import |
| 7 | **Vector DB 연동 협의** | `VectorDBInterface` 인터페이스에 맞는 구현체 제공 |

### 5.4 백엔드와의 연동 지점

| 백엔드 코드 위치 | DB 연동 내용 |
|------------------|-------------|
| `src/shared/database.py` | Supabase 클라이언트 생성 (URL + Key 환경변수) |
| `src/forecast/service.py` | `houses_data` 조회 → 시계열 모델 입력 |
| `src/forecast/service.py` | `news_signals` 조회 → 뉴스 가중치 계산 |
| `src/news/service.py` | `news_signals` 키워드 분석 쿼리 |
| `src/chat/service.py` | `user_interactions` 대화 로그 저장 |
| `src/shared/vector_db.py` | `news_signals.embedding` 벡터 유사도 검색 |

### 5.5 Vector DB 인터페이스 규약

DB 담당자가 Vector DB 구현 시, 백엔드의 `VectorDBInterface` ABC를 준수해야 합니다:

```python
@dataclass
class DocumentChunk:
    content: str       # 문서 본문
    source: str        # 출처 (예: "한국경제 2024-12-01")
    score: float       # 유사도 점수 (0~1)
    metadata: dict | None = None

class VectorDBInterface(ABC):
    async def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[DocumentChunk]:
        """유사도 검색 - 사용자 질의와 가장 관련 있는 문서 top_k개 반환"""
        ...

    async def upsert(self, documents: list[dict], embeddings: list[list[float]]) -> bool:
        """문서 임베딩 저장/갱신"""
        ...
```

**임베딩 규격:** OpenAI `text-embedding-3-small` (1536차원)

---

## 6. 기획자 인수인계

### 6.1 기획 문서 현황

| 문서 | 파일명 | 핵심 내용 |
|------|--------|-----------|
| **PRD** | `docs/01_PRD_HomeSignalAI.md` | 프로젝트 목표, 타겟 사용자, 기능 정의, 성공 지표 |
| **아키텍처** | `docs/02_Architecture_Design.md` | 시스템 구성도, API 설계, 데이터 모델 |
| **AI 파이프라인** | `docs/03_AI_Model_Pipeline.md` | 시계열 모델, 피처 엔지니어링, 평가 프로세스 |
| **RAG 전략** | `docs/04_Prompt_RAG_Strategy.md` | 프롬프트 설계, RAG 검색 로직, Fallback |
| **배포 운영** | `docs/05_Deployment_Operation.md` | 출시 전략, 모니터링 지표, 운영 사이클 |

### 5.2 기능 우선순위 재확인

PRD에 정의된 기능 분류:

#### Must Have (필수)
| 기능 | 구현 상태 | 비고 |
|------|-----------|------|
| 시계열 예측 엔진 | ⚠️ API 골격만 | ML 모델 학습 미완 |
| RAG 기반 챗봇 | ⚠️ API 골격만 | Vector DB Mock |
| 백엔드 API | ✅ 골격 완성 | 실제 데이터 연동 필요 |

#### Should Have (주요)
| 기능 | 구현 상태 | 비고 |
|------|-----------|------|
| 뉴스 크롤링 + 이슈 분석 | ⚠️ API 골격만 | 크롤러 미구현 |
| Fallback 처리 | ✅ 완성 | AI 장애 시 수치만 반환 |

#### Nice to Have (부가)
| 기능 | 구현 상태 | 비고 |
|------|-----------|------|
| 사용자 피드백 수집 | ⬜ 미착수 | DB 스키마만 설계 |
| 뉴스 감성 분석 | ⬜ 미착수 | 설계만 완료 |

### 6.3 성공 지표 (KPI)

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 예측 정확도 | RMSE 최소화 | 실제 실거래가 vs 예측가 비교 |
| 응답 속도 | 2.0초 이내 | `user_interactions.latency_ms` 모니터링 |
| 답변 신뢰성 | 근거 출처 포함률 100% | AI 응답에 `sources` 배열 포함 여부 |
| 사용자 만족도 | 긍정 피드백 70% 이상 | `feedback_is_positive` 비율 |

### 6.4 사용자 시나리오 (User Flow)

#### 시나리오 1: 가격 예측 조회
```
1. 사용자가 "동대문구" 또는 세부 동(청량리동, 이문동) 선택
2. 예측 기간 선택 (주간/월간, 1~12개월)
3. 시스템이 시계열 예측 결과 + 뉴스 가중치 표시
4. 차트로 예측 추세(상승/하락/보합), 신뢰구간 시각화
```

#### 시나리오 2: AI 챗봇 질의
```
1. 사용자가 자유 형식 질문 입력
   예: "동대문구 아파트 가격이 오를까요?"
2. 로딩 상태 표시
3. AI가 시계열 예측 + 뉴스 분석 결합 답변 생성
4. 답변에 참고 출처(뉴스 링크, 데이터 소스) 포함
5. 사용자가 좋아요/싫어요 피드백 제공
```

#### 시나리오 3: 뉴스 인사이트 조회
```
1. 사용자가 키워드(GTX, 재개발 등) 및 기간 선택
2. 시스템이 키워드별 빈도, 트렌드, 감성 점수 표시
3. 대표 뉴스 헤드라인 목록 제공
```

### 6.5 기획자가 해야 할 일

1. **미구현 기능의 우선순위 재정립** — 현재 PRD 기준으로 팀 리소스에 맞게 조정
2. **사용자 리서치** — 실제 동대문구 투자자/실거주자 대상 니즈 검증
3. **프론트엔드 기능 명세** — 디자이너와 협업하여 화면 단위 기능 정의
4. **릴리스 계획 수립** — 소프트 런칭 → 하드 런칭 일정 수립
5. **AI 응답 품질 기준 수립** — 정상/모호/악의적 입력에 대한 기대 응답 정의

---

## 6. 디자이너 인수인계

### 7.1 현재 프론트엔드 상태
**프론트엔드는 전혀 구현되지 않았습니다.** 백엔드 API만 존재하며, 디자이너가 UI/UX를 설계하고 프론트엔드 개발자와 협업하여 구현해야 합니다.

### 6.2 설계 시 참고할 API 응답 구조

#### 시계열 예측 응답 구조
```json
{
  "region": "동대문구",
  "period": "month",
  "trend": "상승",
  "confidence": 0.85,
  "forecast": [
    {
      "date": "2026-03-29",
      "value": 105.5,
      "lower_bound": 103.5,
      "upper_bound": 107.5
    },
    {
      "date": "2026-04-28",
      "value": 106.0,
      "lower_bound": 104.0,
      "upper_bound": 108.0
    }
  ],
  "news_weights": [
    { "keyword": "GTX", "frequency": 45, "impact_score": 0.8 },
    { "keyword": "재개발", "frequency": 32, "impact_score": 0.6 }
  ],
  "model_version": "v1.0"
}
```

**디자인 포인트:**
- `trend`(상승/하락/보합)를 색상으로 구분 (예: 빨강/파랑/회색)
- `forecast` 배열을 **꺾은선 차트**로 시각화 (upper/lower bound = 신뢰구간 영역)
- `news_weights`를 **바 차트** 또는 **태그 클라우드**로 표현
- `confidence` 수치를 **게이지** 또는 **퍼센트 바**로 시각화

#### RAG 챗봇 응답 구조
```json
{
  "answer": "동대문구 아파트 시장은 GTX-C 호재와 재개발 사업 진행에 힘입어...",
  "sources": [
    {
      "title": "GTX-C 청량리역 개통 예정으로 동대문구 부동산...",
      "source": "한국경제 2024-12-01",
      "relevance_score": 0.92
    }
  ],
  "forecast_summary": {
    "trend": "상승",
    "confidence": 0.85,
    "next_month_prediction": 105.5
  },
  "session_id": null,
  "fallback": false
}
```

**디자인 포인트:**
- `answer`는 **마크다운 렌더링** 필요 (볼드, 리스트 등)
- `sources`는 답변 아래 **출처 카드** 형태로 표시 (클릭 시 원문 이동)
- `fallback=true` 시 별도 **경고 배너** 표시 ("AI 해설이 일시적으로 불가합니다")
- 채팅 인터페이스는 좋아요/싫어요 **피드백 버튼** 포함

#### 뉴스 인사이트 응답 구조
```json
{
  "region": "동대문구",
  "period": "month",
  "analysis_date": "2026-02-27",
  "total_articles": 135,
  "insights": [
    {
      "keyword": "GTX",
      "frequency": 45,
      "trend": "상승",
      "sentiment_score": 0.72,
      "sample_headlines": [
        "GTX-C 청량리역 2028년 개통 확정",
        "GTX 호재에 동대문구 아파트 거래량 증가"
      ]
    }
  ],
  "top_issues": [
    "청량리: 52건 (유지)",
    "GTX: 45건 (상승)",
    "재개발: 38건 (상승)"
  ]
}
```

**디자인 포인트:**
- `insights`를 **키워드 카드** 형태로 표시
- `sentiment_score`를 **컬러 바** 또는 **이모지**로 시각화 (-1~1)
- `sample_headlines`는 접기/펼치기(Accordion) UI
- `top_issues`를 **대시보드 상단 요약 카드**로 배치

### 7.3 톤앤매너 가이드

| 항목 | 가이드 |
|------|--------|
| **서비스 페르소나** | 신뢰감 있는 부동산 전문가 |
| **어조** | 객관적, 데이터 기반, 전문적이되 쉽게 |
| **필수 표기** | "본 데이터는 참고용이며, 투자 결정의 근거로 사용하지 마세요" |
| **타겟 연령층** | 30~50대 부동산 투자자/실거주자 |
| **컬러 방향성** | 신뢰감(블루 계열) + 부동산(따뜻한 톤 포인트) |

### 7.4 디자이너가 해야 할 일

| 순서 | 작업 | 비고 |
|------|------|------|
| 1 | **정보 구조(IA) 설계** | 메인 > 예측 / 챗봇 / 뉴스 인사이트 |
| 2 | **와이어프레임** | 핵심 3개 화면 + 에러/Fallback 상태 |
| 3 | **UI 디자인 시스템** | 컬러, 타이포, 컴포넌트 규격 |
| 4 | **차트 시각화 설계** | 시계열 꺾은선, 신뢰구간, 키워드 빈도 |
| 5 | **챗봇 인터페이스** | 메시지 버블, 로딩 상태, 피드백 UI |
| 6 | **반응형 설계** | 모바일 우선 또는 데스크톱 우선 결정 |
| 7 | **에러 상태 디자인** | Fallback, 네트워크 오류, 빈 데이터 |

### 7.5 주요 화면 구성 제안

```
┌─────────────────────────────────────────┐
│               HomeSignal AI              │
├─────────────────────────────────────────┤
│                                          │
│  [대시보드]  [예측]  [챗봇]  [뉴스]      │
│                                          │
├─────────────────────────────────────────┤
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  시세 요약 카드                     │  │
│  │  동대문구 | 상승 | 신뢰도 85%      │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  예측 차트 (꺾은선 + 신뢰구간)     │  │
│  │  ~~~~~~~~~~~~                      │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  주요 이슈 키워드                   │  │
│  │  [GTX 45건] [재개발 32건] [...]   │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  AI 챗봇                           │  │
│  │  "동대문구 아파트 가격이 오를까요?" │  │
│  │  ─────────────────────────────    │  │
│  │  GTX-C 호재와 재개발 사업 진행에    │  │
│  │  힘입어 상승 가능성이 높습니다...   │  │
│  │  [출처 1] [출처 2]                 │  │
│  │  [👍 도움이 됐어요] [👎 아쉬워요]  │  │
│  └───────────────────────────────────┘  │
│                                          │
└─────────────────────────────────────────┘
```

---

## 8. 공통 참고사항

### 7.1 프로젝트 문서 인덱스

| # | 문서 | 파일 경로 | 대상 |
|---|------|-----------|------|
| 1 | PRD (제품 요구사항) | `docs/01_PRD_HomeSignalAI.md` | 전원 필독 |
| 2 | 아키텍처 설계서 | `docs/02_Architecture_Design.md` | 개발자, DB |
| 3 | AI 모델 파이프라인 | `docs/03_AI_Model_Pipeline.md` | 개발자 |
| 4 | 프롬프트/RAG 전략 | `docs/04_Prompt_RAG_Strategy.md` | 개발자, 기획 |
| 5 | 배포/운영 가이드 | `docs/05_Deployment_Operation.md` | 전원 |
| 6 | 개발일지 | `docs/06_Development_Journal.md` | 전원 |
| 7 | 인수인계서 (본 문서) | `docs/07_Handover_Document.md` | 전원 필독 |
| 8 | 업무분장 및 역할 정의 | `docs/09_Organization_Roles.md` | 전원 필독 |
| 9 | 프론트엔드·Supabase 연동 인수인계 | `docs/10_Frontend_Supabase_Integration_Handover.md` | 프로젝트 총괄, 개발1 |
| 10 | DB 스키마 | `db_Schema(Sql)_mokdb.md` | DB 담당자 |
| 11 | Cursor/Claude 가이드 | `.cursorrules`, `CLAUDE.md` | 개발자 |

### 8.2 환경변수 목록

| 변수명 | 설명 | 예시 | 필수 |
|--------|------|------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL | `https://xxx.supabase.co` | ✅ |
| `SUPABASE_KEY` | Supabase anon key | `eyJ...` | ✅ |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` | AI_PROVIDER가 openai일 때 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | `sk-ant-...` | AI_PROVIDER가 anthropic일 때 |
| `AI_PROVIDER` | AI 제공자 | `openai` 또는 `anthropic` | 기본값: openai |
| `REDIS_URL` | Redis 연결 URL | `redis://localhost:6379/0` | 기본값 제공됨 |
| `APP_ENV` | 앱 환경 | `development` / `staging` / `production` | 기본값: development |
| `DEBUG` | 디버그 모드 | `true` / `false` | 기본값: true |

### 8.3 커뮤니케이션 및 협업 포인트

| 관계 | 협의 필요 사항 |
|------|---------------|
| **개발자 ↔ DB** | Supabase 연결 정보 공유, 테이블 스키마 확정, Vector DB 인터페이스 합의 |
| **개발자 ↔ 기획** | API 응답 구조 변경 시 공유, 새 기능 추가 시 PRD 업데이트 |
| **개발자 ↔ 디자이너** | API 응답 구조 전달, 에러/로딩 상태 정의, 챗봇 UX 협의 |
| **기획 ↔ 디자이너** | 사용자 시나리오 기반 화면 설계, 톤앤매너 가이드 |
| **DB ↔ 기획** | 데이터 수집 범위 확정, 분석 대상 키워드 목록 합의 |

### 8.4 리스크 사항

| 리스크 | 영향 | 대응 방안 |
|--------|------|-----------|
| AI API 비용 초과 | 서비스 중단 | 캐싱 강화, 저가 모델 전환, 일일 호출 상한 설정 |
| 국토교통부 API 변경 | 데이터 수집 중단 | 크롤링 대안, API 모니터링 |
| 뉴스 크롤링 차단 | 뉴스 데이터 부재 | RSS 피드 대안, 뉴스 API 서비스 검토 |
| 예측 모델 성능 부족 | 서비스 신뢰도 하락 | 지속적 모델 재학습, 평가 지표 모니터링 |
| Prompt Injection | 부적절한 응답 | 시스템 프롬프트 방어, 입력 필터링 |

### 8.5 용어 사전 (Glossary)

| 용어 | 설명 |
|------|------|
| **RAG** | Retrieval-Augmented Generation. 외부 문서를 검색하여 AI 답변의 근거로 활용하는 기법 |
| **시계열 예측** | 과거 시간 순서 데이터를 기반으로 미래 값을 예측하는 통계/ML 기법 |
| **Prophet** | Facebook(Meta)이 개발한 시계열 예측 라이브러리. 트렌드와 계절성 분석에 특화 |
| **LightGBM** | Microsoft의 그래디언트 부스팅 프레임워크. 빠른 학습 속도와 높은 정확도 |
| **Ensemble** | 여러 모델의 예측 결과를 결합하여 더 정확한 예측을 만드는 기법 |
| **Vector DB** | 텍스트를 숫자 벡터로 변환(임베딩)하여 의미 기반 유사도 검색을 지원하는 DB |
| **Embedding** | 텍스트를 수백~수천 차원의 숫자 벡터로 변환한 것 (의미가 유사하면 벡터도 가까움) |
| **Fallback** | 주 서비스(AI API) 장애 시 대안 응답을 제공하는 예외 처리 전략 |
| **TTL** | Time To Live. 캐시 데이터의 유효 기간 |
| **RMSE/MAE/MAPE** | 예측 모델의 오차를 측정하는 지표들 |
| **pgvector** | PostgreSQL에서 벡터 데이터를 저장하고 유사도 검색을 지원하는 확장 |
| **Supabase** | Firebase의 오픈소스 대안. PostgreSQL 기반 BaaS(Backend as a Service) |
| **GTX** | 수도권광역급행철도. 동대문구(청량리)에 GTX-C 노선 예정 |

---

## 부록: 빠른 시작 체크리스트 (Quick Start)

### 후임 개발자
- [ ] Python 3.11+, uv 설치
- [ ] `uv sync` 실행
- [ ] `.env` 파일 생성 및 API 키 입력
- [ ] `uv run uvicorn src.main:app --reload` 서버 실행 확인
- [ ] `http://localhost:8000/docs` Swagger UI 확인
- [ ] `git init && git add . && git commit` Git 초기화
- [ ] `docs/01_PRD_HomeSignalAI.md` 읽기
- [ ] `docs/06_Development_Journal.md` 읽기

### DB 담당자
- [ ] Supabase 프로젝트 생성
- [ ] `db_Schema(Sql)_mokdb.md`의 SQL 실행
- [ ] `.env`에 `SUPABASE_URL`, `SUPABASE_KEY` 공유
- [ ] Vector DB 인터페이스(`shared/vector_db.py`) 검토
- [ ] 개발자와 쿼리 패턴 협의

### 기획자
- [ ] `docs/01_PRD_HomeSignalAI.md` 정독
- [ ] 미구현 기능 우선순위 재정립
- [ ] 사용자 시나리오 기반 화면 기획서 작성
- [ ] 성공 지표(KPI) 측정 방안 구체화

### 디자이너
- [ ] `docs/01_PRD_HomeSignalAI.md` 정독 (서비스 목표 이해)
- [ ] 본 문서 [Section 7 디자이너 인수인계](#7-디자이너-인수인계) 숙지
- [ ] API 응답 구조 기반 화면 설계
- [ ] 정보 구조(IA) → 와이어프레임 → UI 디자인 순서 진행

---

*본 인수인계서는 2026-02-28 기준으로 작성되었습니다.*  
*문의사항이 있으면 개발일지(`06_Development_Journal.md`)와 관련 설계 문서를 우선 참고해 주세요.*
