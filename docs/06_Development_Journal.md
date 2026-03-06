# HomeSignal AI — 개발일지 (Development Journal)

**문서 버전:** 1.1  
**최종 수정일:** 2026-02-28  
**프로젝트:** 동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스  
**대상 독자:** 후임 개발자, DB 담당자, 기획자, 디자이너  
**참조 룰:** [moduler box](https://github.com/Siyeolryu/Ai_study/tree/main/moduler%20box) — 모듈형·체크리스트 기반 기록

---

## [Box 0] 2026-02-28 개발일지 (당일 완료)

### 완료 작업 체크리스트

| # | 작업 | 산출물 | 상태 |
|---|------|--------|------|
| 1 | Supabase 백엔드 연동 설정 | `.env` SUPABASE_URL, SUPABASE_KEY | ✅ |
| 2 | DataRepository 실제 DB 전환 로직 | `src/shared/data_repository.py` | ✅ |
| 3 | 프론트엔드 Supabase 클라이언트 | `design/.../lib/supabase.ts` | ✅ |
| 4 | 프론트엔드 환경변수 | `.env.local`, `.env.example` | ✅ |
| 5 | 설정 확장 (DATABASE_URL) | `src/config/settings.py` | ✅ |
| 6 | pyiceberg 의존성 추가 | `pyproject.toml` | ✅ |
| 7 | Supabase 연결 테스트 스크립트 | `scripts/test_supabase.py` | ✅ |
| 8 | 인수인계서 §6 연동 내역 | `docs/10_Frontend_Supabase_Integration_Handover.md` | ✅ |

### 상세 변경 내역

| 모듈 | 변경 파일 | 변경 내용 |
|------|-----------|-----------|
| 백엔드 env | `.env` | `SUPABASE_URL`, `SUPABASE_KEY` 실제 프로젝트 값 설정 |
| 백엔드 env | `.env.example` | `DATABASE_URL` 옵션 추가 |
| 데이터 계층 | `src/shared/data_repository.py` | placeholder 감지 시 Mock, 아니면 SupabaseDataRepository 사용 |
| 설정 | `src/config/settings.py` | `database_url` 선택 필드 추가 |
| 패키지 | `pyproject.toml` | `pyiceberg` 의존성 (supabase storage3 호환) |
| 프론트엔드 | `design/.../lib/supabase.ts` | createClient 기반 Supabase 클라이언트 |
| 프론트엔드 | `design/.../.env.local` | NEXT_PUBLIC_SUPABASE_URL, ANON_KEY |
| 문서 | `docs/10_...Handover.md` | §6 Supabase 연동 적용 내역 추가 |

### GitHub 업로드 정보

- **저장소:** https://github.com/soeunyim-art/homesignalAI  
- **상태:** 아직 push 미실행 (예정)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 정의
**HomeSignal AI**는 서울 동대문구 부동산 시장의 **시계열 가격 예측**과 **RAG(Retrieval-Augmented Generation) 기반 AI 챗봇**을 결합한 지능형 부동산 분석 서비스입니다.

### 1.2 핵심 가치
단순히 "가격이 오를까?"에 대한 답변이 아니라, **"어떤 이슈(GTX, 재개발, 정책) 때문에 오를 가능성이 높은가?"**에 대한 **근거 중심의 답변**을 제공하는 것이 이 프로젝트의 핵심입니다.

### 1.3 타겟 사용자
- 동대문구 지역 **부동산 투자자**
- **실거주 희망자**
- 동대문구 시장 동향에 관심 있는 일반 사용자

---

## 2. 기술 스택 요약

| 구분 | 기술 | 비고 |
|------|------|------|
| **언어** | Python 3.11+ | 타입 힌트 적극 활용 |
| **웹 프레임워크** | FastAPI | 비동기 아키텍처, 자동 API 문서 생성 |
| **패키지 매니저** | uv | pip 대비 10~100배 빠른 의존성 관리 |
| **데이터베이스** | Supabase (PostgreSQL) | 실거래가, 뉴스, 예측 결과, 대화 로그 저장 |
| **벡터 DB** | 별도 담당자 영역 | RAG용 문서 임베딩 및 유사도 검색 |
| **캐싱** | Redis | 응답 속도 최적화 (목표 2.0초 이내) |
| **AI API** | OpenAI GPT-4o / Claude 3.5 Sonnet | 환경변수로 Provider 전환 가능 |
| **ML 모델** | Prophet + LightGBM (Ensemble) | 시계열 예측 (현재 Mock 단계) |
| **린트/포맷** | Ruff | Python 린트 + 포맷 통합 |
| **타입 체크** | mypy (strict mode) | 정적 타입 검사 |
| **테스트** | pytest + pytest-asyncio | 비동기 테스트 지원 |

---

## 3. 프로젝트 디렉토리 구조

```
home_signal_ai/
├── .cursorrules                      # Cursor AI 개발 지침
├── .cursor/
│   └── rules/
│       └── homesignal-ai-master.mdc  # Cursor 마스터 룰
├── .env.example                      # 환경변수 템플릿
├── CLAUDE.md                         # Claude Code 개발 가이드
├── pyproject.toml                    # 프로젝트 메타 + 의존성 + 도구 설정
├── db_Schema(Sql)_mokdb.md           # DB 스키마 (SQL) 정의서
│
├── docs/                             # 기획·설계 문서
│   ├── 01_PRD_HomeSignalAI.md        # 제품 요구사항 명세서 (PRD)
│   ├── 02_Architecture_Design.md     # 아키텍처 설계서
│   ├── 03_AI_Model_Pipeline.md       # AI/ML 파이프라인 설계서
│   ├── 04_Prompt_RAG_Strategy.md     # 프롬프트 및 RAG 전략서
│   ├── 05_Deployment_Operation.md    # 배포 및 운영 가이드
│   ├── 06_Development_Journal.md     # 개발일지 (본 문서)
│   └── 07_Handover_Document.md       # 인수인계서
│
└── src/                              # 소스코드
    ├── __init__.py
    ├── main.py                       # FastAPI 앱 엔트리포인트
    │
    ├── config/                       # 설정 모듈
    │   ├── __init__.py
    │   └── settings.py               # Pydantic Settings (환경변수)
    │
    ├── forecast/                     # 시계열 예측 도메인
    │   ├── __init__.py
    │   ├── router.py                 # GET/POST /api/v1/forecast
    │   ├── service.py                # 예측 비즈니스 로직
    │   └── schemas.py                # 요청/응답 Pydantic 스키마
    │
    ├── chat/                         # RAG 챗봇 도메인
    │   ├── __init__.py
    │   ├── router.py                 # POST /api/v1/chat
    │   ├── service.py                # RAG 파이프라인 (핵심 로직)
    │   ├── fallback.py               # AI API 장애 시 Fallback 처리
    │   ├── schemas.py                # 요청/응답 Pydantic 스키마
    │   └── prompts/
    │       ├── __init__.py
    │       └── v1.py                 # 시스템 프롬프트 v1 + 컨텍스트 빌더
    │
    ├── news/                         # 뉴스 분석 도메인
    │   ├── __init__.py
    │   ├── router.py                 # GET /api/v1/news/insights
    │   ├── service.py                # 뉴스 키워드 분석 로직
    │   └── schemas.py                # 요청/응답 Pydantic 스키마
    │
    └── shared/                       # 공통 모듈
        ├── __init__.py
        ├── database.py               # Supabase 클라이언트 (싱글톤)
        ├── ai_client.py              # OpenAI/Anthropic 통합 클라이언트
        ├── cache.py                  # Redis 캐싱 클라이언트
        ├── vector_db.py              # Vector DB 인터페이스 + Mock
        └── exceptions.py             # 커스텀 예외 클래스 계층
```

---

## 4. 개발 진행 내역 (Phase별)

### Phase 1: 기획 및 설계 (완료)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| 문제 정의 및 가설 설정 | PRD 문서 | ✅ 완료 |
| 상세 요구사항 확정 | `01_PRD_HomeSignalAI.md` | ✅ 완료 |
| 시스템 아키텍처 설계 | `02_Architecture_Design.md` | ✅ 완료 |
| AI/ML 파이프라인 설계 | `03_AI_Model_Pipeline.md` | ✅ 완료 |
| 프롬프트 및 RAG 전략 수립 | `04_Prompt_RAG_Strategy.md` | ✅ 완료 |
| 배포/운영 가이드 작성 | `05_Deployment_Operation.md` | ✅ 완료 |

### Phase 2: 백엔드 API 골격 구축 (완료)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| FastAPI 앱 초기화 + uv 세팅 | `main.py`, `pyproject.toml` | ✅ 완료 |
| 환경변수 관리 (Pydantic Settings) | `config/settings.py`, `.env.example` | ✅ 완료 |
| 도메인별 라우터/스키마/서비스 분리 | `forecast/`, `chat/`, `news/` | ✅ 완료 |
| 공유 모듈 설계 | `shared/` (DB, AI, Cache, VectorDB, 예외) | ✅ 완료 |
| 시계열 예측 API (Mock) | `GET/POST /api/v1/forecast` | ✅ 완료 |
| RAG 챗봇 API (Mock) | `POST /api/v1/chat` | ✅ 완료 |
| 뉴스 인사이트 API (Mock) | `GET /api/v1/news/insights` | ✅ 완료 |
| Fallback 로직 구현 | `chat/fallback.py` | ✅ 완료 |
| 프롬프트 버전 관리 체계 수립 | `chat/prompts/v1.py` | ✅ 완료 |
| CORS, 헬스체크, 전역 예외 핸들러 | `main.py` | ✅ 완료 |

### Phase 3: DB 스키마 설계 (완료)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| Supabase 테이블 스키마 설계 | `db_Schema(Sql)_mokdb.md` | ✅ 완료 |
| Vector 확장 활성화 (pgvector) | SQL DDL | ✅ 완료 |

### Phase 4: 데이터 수집 파이프라인 (미착수)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| 국토교통부 실거래가 API 연동 | 데이터 수집 스크립트 | ⬜ 미착수 |
| 구글 뉴스 크롤링 모듈 | 뉴스 크롤러 | ⬜ 미착수 |
| 데이터 전처리 파이프라인 | ETL 스크립트 | ⬜ 미착수 |

### Phase 5: ML 모델 개발 (미착수)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| Prophet 베이스라인 모델 | 학습 스크립트 | ⬜ 미착수 |
| LightGBM 뉴스 가중치 모델 | 학습 스크립트 | ⬜ 미착수 |
| Ensemble 결합 | 예측 모듈 | ⬜ 미착수 |
| 모델 평가 (RMSE, MAE, MAPE) | 평가 리포트 | ⬜ 미착수 |

### Phase 6: 외부 서비스 연동 (진행 중)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| Supabase 실제 연동 | DB CRUD 로직, DataRepository | ✅ 2026-02-28 설정 완료 |
| Vector DB 실제 연동 | RAG 검색 로직 | ⬜ 미착수 |
| AI API 실제 연동 | 테스트 완료 | ⬜ 미착수 |
| Redis 캐싱 실제 연동 | 성능 테스트 | ⬜ 미착수 |

### Phase 7: 테스트 및 배포 (미착수)
| 작업 | 산출물 | 상태 |
|------|--------|------|
| 단위 테스트 작성 | `tests/` | ⬜ 미착수 |
| 통합 테스트 | E2E 시나리오 | ⬜ 미착수 |
| 성능 테스트 (2.0초 목표) | 부하 테스트 결과 | ⬜ 미착수 |
| 스테이징/프로덕션 배포 | 배포 스크립트 | ⬜ 미착수 |

---

## 5. API 엔드포인트 현황

### 5.1 구현 완료 API

| Method | Endpoint | 설명 | 구현 상태 |
|--------|----------|------|-----------|
| `GET` | `/` | 루트 (API 안내) | ✅ 실제 동작 |
| `GET` | `/health` | 헬스체크 | ✅ 실제 동작 |
| `GET` | `/api/v1/forecast` | 시계열 예측 조회 | ⚠️ Mock 데이터 |
| `POST` | `/api/v1/forecast` | 시계열 예측 조회 (POST) | ⚠️ Mock 데이터 |
| `POST` | `/api/v1/chat` | RAG 챗봇 질의 | ⚠️ Mock 데이터 |
| `GET` | `/api/v1/news/insights` | 뉴스 키워드 인사이트 | ⚠️ Mock 데이터 |
| `GET` | `/docs` | Swagger UI (개발 모드) | ✅ 자동 생성 |
| `GET` | `/redoc` | ReDoc (개발 모드) | ✅ 자동 생성 |

> **중요:** 모든 도메인 API는 골격(라우터-서비스-스키마)은 완성되어 있으나, 내부 비즈니스 로직은 **Mock 데이터**를 반환합니다. 실제 데이터 연동은 Phase 4~6에서 수행해야 합니다.

### 5.2 API 파라미터 상세

#### `/api/v1/forecast`
- `region` (str): 예측 대상 지역 — 기본값 "동대문구"
- `period` (str): 예측 기간 단위 — "week" 또는 "month"
- `horizon` (int, 1~12): 예측 기간 수
- `include_news_weight` (bool): 뉴스 가중치 포함 여부

#### `/api/v1/chat`
- `message` (str, 필수): 사용자 질문 (최대 2000자)
- `session_id` (str, 선택): 세션 ID
- `region` (str): 질문 대상 지역 — 기본값 "동대문구"

#### `/api/v1/news/insights`
- `period` (str): 분석 기간 — "week", "month", "quarter"
- `keywords` (list[str]): 분석 대상 키워드 — 기본값 ["GTX", "재개발", "청량리"]
- `region` (str): 분석 대상 지역 — 기본값 "동대문구"

---

## 6. 주요 설계 결정 기록 (ADR: Architecture Decision Records)

### ADR-001: 패키지 매니저로 uv 선택
- **결정:** pip 대신 uv 사용
- **이유:** 의존성 설치 속도 10~100배 향상, `pyproject.toml` 네이티브 지원
- **영향:** `uv sync` 명령어로 의존성 설치, `uv run` 명령어로 실행

### ADR-002: 도메인 기반 패키지 구조
- **결정:** `forecast/`, `chat/`, `news/` 도메인 단위로 코드 분리
- **이유:** 기능별 독립적인 개발·테스트·유지보수 가능
- **영향:** 각 도메인은 `router.py` + `service.py` + `schemas.py` 구조

### ADR-003: AI Provider 추상화
- **결정:** OpenAI와 Anthropic을 단일 `AIClient` 클래스로 통합
- **이유:** 환경변수 하나(`AI_PROVIDER`)로 Provider 전환 가능, 비용·품질에 따라 유연하게 대응
- **영향:** `settings.ai_provider`가 "openai" 또는 "anthropic"일 때 자동 분기

### ADR-004: Vector DB 인터페이스 추상화
- **결정:** `VectorDBInterface` ABC를 정의하고, 현재는 `MockVectorDB` 사용
- **이유:** Vector DB 담당자가 별도 존재하며, 인터페이스만 합의하면 독립 개발 가능
- **영향:** `search(query, top_k)` → `list[DocumentChunk]` 인터페이스 준수 시 즉시 교체 가능

### ADR-005: Fallback 전략
- **결정:** AI API 오류 시 시계열 수치 데이터만이라도 반환
- **이유:** 사용자에게 "아무것도 안 보여주는 것"보다 수치 데이터라도 제공하는 것이 UX상 유리
- **영향:** `AIAPIError` 발생 시 `create_fallback_response()` 호출, `fallback=true` 플래그 포함

### ADR-006: 프롬프트 버전 관리
- **결정:** `prompts/v1.py`, `v2.py` 형태로 Git 추적 가능한 코드 기반 관리
- **이유:** A/B 테스트, 롤백, 이력 추적이 용이
- **영향:** 새 프롬프트 작성 시 `prompts/v{n}.py` 생성 후 `__init__.py`에서 import 전환

### ADR-007: 캐싱 전략
- **결정:** SHA-256 해시 기반 캐시 키 생성 + TTL 기반 만료
- **이유:** 동일 요청에 대한 비용 절감 및 응답 속도 최적화
- **영향:** 시계열 예측 TTL=1시간, 챗봇 TTL=30분, Fallback 응답은 캐시하지 않음

---

## 7. DB 스키마 설계 현황

Supabase(PostgreSQL) 기반 4개 테이블 설계 완료:

| 테이블 | 용도 | 주요 컬럼 |
|--------|------|-----------|
| `houses_data` | 부동산 실거래 및 물리적 속성 | complex_name, dong_name, price, sqft_living, yr_built, contract_date |
| `news_signals` | RAG용 뉴스 및 정책 데이터 | title, content, keywords[], embedding(vector 1536), published_at |
| `ai_predictions` | 시계열 모델 예측 결과 | model_version, target_date, predicted_price, confidence_score, features_used(jsonb) |
| `user_interactions` | 챗봇 대화 로그 및 피드백 | user_query, ai_response, feedback_is_positive, latency_ms |

> pgvector 확장 활성화(`create extension if not exists vector`)로 뉴스 임베딩 벡터 검색 지원

---

## 8. 미해결 사항 및 기술 부채 (Tech Debt)

### 8.1 즉시 해결 필요 (High Priority)
| # | 항목 | 위치 | 설명 |
|---|------|------|------|
| 1 | 국토교통부 API 연동 | `forecast/service.py` | `_run_forecast()`가 Mock 데이터 반환 중 |
| 2 | 구글 뉴스 크롤러 구현 | 신규 모듈 필요 | 데이터 수집 파이프라인 자체가 없음 |
| 3 | Vector DB 실제 연동 | `shared/vector_db.py` | `MockVectorDB` → 실제 구현체 교체 |
| 4 | ML 모델 학습 코드 | 신규 모듈 필요 | Prophet + LightGBM 파이프라인 전무 |

### 8.2 중기 해결 (Medium Priority)
| # | 항목 | 위치 | 설명 |
|---|------|------|------|
| 5 | Redis 연결 안정성 | `shared/cache.py` | Redis 미연결 시 graceful degradation 보완 |
| 6 | 뉴스 감성 분석 | `news/service.py` | Mock 데이터 → 실제 NLP 분석 교체 |
| 7 | 단위/통합 테스트 | `tests/` | 테스트 코드 전무 |
| 8 | Git 저장소 초기화 | 프로젝트 루트 | soeunyim-art/homesignalAI 푸시 예정 |

### 8.3 장기 개선 (Low Priority)
| # | 항목 | 설명 |
|---|------|------|
| 9 | SSE/WebSocket 스트리밍 | AI 응답 실시간 스트리밍 |
| 10 | 사용자 피드백 수집 UI | 좋아요/싫어요 피드백 시스템 |
| 11 | Rate Limiting | API 호출 제한 미들웨어 |
| 12 | A/B 테스트 프레임워크 | 프롬프트 버전별 성능 비교 |

---

## 9. 개발 환경 실행 가이드

### 9.1 사전 요구사항
- Python 3.11 이상
- uv 패키지 매니저 (`pip install uv` 또는 공식 설치)
- Redis 서버 (캐싱, 없어도 동작은 가능하나 캐싱 비활성화)
- Supabase 프로젝트 (DB 연동 시 필요)

### 9.2 설치 및 실행

```bash
# 1. 의존성 설치
uv sync

# ML 의존성도 설치하려면:
uv sync --extra ml

# 개발 도구까지:
uv sync --extra dev

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 실제 API 키 입력

# 3. 개발 서버 실행
uv run uvicorn src.main:app --reload

# 4. API 문서 확인
# http://127.0.0.1:8000/docs (Swagger UI)
# http://127.0.0.1:8000/redoc (ReDoc)
```

### 9.3 주요 명령어

```bash
# 린트 검사
uv run ruff check src/

# 린트 자동 수정
uv run ruff check src/ --fix

# 타입 체크
uv run mypy src/

# 테스트 실행
uv run pytest
```

---

## 10. 의존성 목록

### 10.1 프로덕션 의존성
| 패키지 | 버전 | 용도 |
|--------|------|------|
| fastapi | ≥0.109.0 | 웹 프레임워크 |
| uvicorn[standard] | ≥0.27.0 | ASGI 서버 |
| pydantic | ≥2.0 | 데이터 검증/직렬화 |
| pydantic-settings | ≥2.0 | 환경변수 관리 |
| supabase | ≥2.0 | Supabase 클라이언트 |
| redis | ≥5.0 | Redis 비동기 클라이언트 |
| httpx | ≥0.26.0 | HTTP 클라이언트 |
| openai | ≥1.10.0 | OpenAI API 클라이언트 |
| anthropic | ≥0.18.0 | Anthropic API 클라이언트 |

### 10.2 개발 의존성 (optional: dev)
| 패키지 | 버전 | 용도 |
|--------|------|------|
| pytest | ≥8.0 | 테스트 프레임워크 |
| pytest-asyncio | ≥0.23 | 비동기 테스트 |
| ruff | ≥0.2 | 린트 + 포맷 |
| mypy | ≥1.8 | 정적 타입 검사 |

### 10.3 ML 의존성 (optional: ml)
| 패키지 | 버전 | 용도 |
|--------|------|------|
| prophet | ≥1.1 | 시계열 예측 (베이스라인) |
| lightgbm | ≥4.0 | 그래디언트 부스팅 (뉴스 가중치) |
| pandas | ≥2.0 | 데이터 처리 |
| numpy | ≥1.26 | 수치 연산 |
| scikit-learn | ≥1.4 | 전처리, 평가 지표 |

---

## 11. 알려진 이슈 및 주의사항

1. **Git 미초기화:** 현재 프로젝트 폴더가 Git 저장소가 아닙니다. `git init` 후 초기 커밋이 필요합니다.
2. **환경변수 필수:** `.env` 파일이 없으면 `settings.py` 로딩 시 `ValidationError`가 발생합니다. 반드시 `.env.example`을 복사하여 설정하세요.
3. **Mock 데이터 의존:** 모든 도메인 서비스가 Mock 데이터를 반환합니다. 실제 데이터 연동 전까지 API 응답값은 하드코딩된 값입니다.
4. **Redis 미연결 시:** 캐시 조회/저장 실패 시 warning 로그만 남기고 무시합니다 (graceful degradation). 하지만 `get_cache_client()` 호출 시 Redis 연결 자체가 실패하면 에러가 발생할 수 있습니다.
5. **Python 버전:** `pyproject.toml`에 Python 3.11+ 명시. `str | None` 등 union 타입 문법이 3.10+ 필수입니다.

---

*본 개발일지는 2026-02-28 기준으로 작성되었으며, 이후 변경사항은 후임자가 업데이트해 주시기 바랍니다.*
