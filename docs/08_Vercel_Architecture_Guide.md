# HomeSignal AI — Vercel 배포 아키텍처 가이드

**문서 버전:** 1.0  
**최종 수정일:** 2026-03-09  
**목적:** Python FastAPI 백엔드와 Next.js 프론트엔드의 Vercel Serverless 배포 아키텍처 상세 가이드

---

## 목차

1. [아키텍처 개요](#1-아키텍처-개요)
2. [배포 구조](#2-배포-구조)
3. [백엔드 배포 설정](#3-백엔드-배포-설정)
4. [프론트엔드 배포 설정](#4-프론트엔드-배포-설정)
5. [환경 변수 설정](#5-환경-변수-설정)
6. [CORS 설정](#6-cors-설정)
7. [제한사항 및 대응](#7-제한사항-및-대응)
8. [배포 워크플로우](#8-배포-워크플로우)
9. [트러블슈팅](#9-트러블슈팅)

---

## 1. 아키텍처 개요

### 1.1 전체 시스템 구성

```
┌─────────────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                                 │
│                   (https://homesignal-ai.vercel.app)                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Vercel Edge Network                          │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐    │
│  │  Frontend Project       │    │  Backend Project            │    │
│  │  (Next.js 15)           │    │  (FastAPI Python)           │    │
│  │                         │    │                             │    │
│  │  - Static SSG pages     │    │  - Serverless Function      │    │
│  │  - API routes           │    │  - api/index.py → app       │    │
│  │  - CDN cached assets    │    │  - 500MB bundle limit       │    │
│  └────────┬────────────────┘    └────────┬────────────────────┘    │
└───────────┼──────────────────────────────┼──────────────────────────┘
            │                              │
            │ NEXT_PUBLIC_API_URL          │
            └──────────────►───────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Supabase │    │ OpenAI   │    │ Redis    │
    │ PostgreSQL│   │   API    │    │ (Optional)│
    │ + pgvector│   │          │    │          │
    └──────────┘    └──────────┘    └──────────┘
```

### 1.2 배포 전략

| 레이어 | 플랫폼 | 배포 방식 | 도메인 |
|--------|--------|----------|--------|
| **Frontend** | Vercel | Next.js App Router (SSG/SSR) | `homesignal-ai-frontend.vercel.app` |
| **Backend** | Vercel | Python Serverless Function | `homesignal-ai-backend.vercel.app` |
| **Database** | Supabase | Managed PostgreSQL + pgvector | `yietqoikdaqpwmmvamtv.supabase.co` |
| **ML Service** | Railway/Render (향후) | Prophet + LightGBM 추론 서버 | TBD |
| **Crawler** | GitHub Actions | Cron 스케줄 실행 | - |

---

## 2. 배포 구조

### 2.1 두 개의 Vercel 프로젝트

HomeSignal AI는 **백엔드와 프론트엔드를 별도 Vercel 프로젝트**로 배포합니다.

#### 백엔드 프로젝트

- **Root Directory:** `./` (프로젝트 루트)
- **Framework Preset:** Other
- **Build Command:** (없음, Python 자동 빌드)
- **Output Directory:** (없음)
- **Install Command:** `pip install -r requirements.txt`

#### 프론트엔드 프로젝트

- **Root Directory:** `frontend`
- **Framework Preset:** Next.js
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`

### 2.2 디렉터리 구조

```
home_signal_ai/
├── api/
│   └── index.py              # Vercel Python 진입점
├── src/
│   ├── main.py               # FastAPI app
│   ├── forecast/
│   ├── chat/
│   ├── news/
│   └── shared/
├── frontend/                 # 별도 Vercel 프로젝트
│   ├── app/
│   ├── components/
│   ├── lib/
│   │   └── api-client.ts     # 백엔드 API 호출
│   └── package.json
├── vercel.json               # 백엔드 설정
├── requirements.txt          # Python 의존성 (ML 제외)
└── .vercelignore            # 백엔드 배포 시 제외 파일
```

---

## 3. 백엔드 배포 설정

### 3.1 vercel.json

**파일:** `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.12"
  }
}
```

**설명:**
- `builds`: Python 런타임으로 `api/index.py` 빌드
- `routes`: 모든 요청을 `api/index.py`로 라우팅
- `env`: Python 3.12 사용

### 3.2 api/index.py

**파일:** `api/index.py`

```python
"""
Vercel Serverless Function Entry Point
"""
from src.main import app
```

Vercel Python 런타임은 `app` 객체를 찾아 ASGI 서버로 실행합니다.

### 3.3 requirements.txt

**파일:** `requirements.txt`

```txt
# Core dependencies (ML 제외 - 500MB 제한)
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0
pydantic-settings>=2.0
supabase>=2.0
httpx>=0.26.0
openai>=1.10.0
anthropic>=0.18.0
pyyaml>=6.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
```

**제외된 의존성:**
- `prophet`, `lightgbm`, `pandas`, `numpy` (ML 라이브러리)
- 이유: 500MB 번들 크기 제한

### 3.4 .vercelignore

**파일:** `.vercelignore`

```
# Frontend (백엔드 배포 시 불필요)
frontend/

# Test files
tests/
*.test.py

# ML artifacts
*.pkl
*.joblib
models/

# Development
.venv/
__pycache__/
.env
```

---

## 4. 프론트엔드 배포 설정

### 4.1 package.json

**파일:** `frontend/package.json`

```json
{
  "name": "homesignal-ai-frontend",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "15.1.6",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.17.0",
    "recharts": "^2.10.0"
  }
}
```

### 4.2 API 클라이언트

**파일:** `frontend/lib/api-client.ts`

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getForecast(params: ForecastParams) {
  const res = await fetch(`${API_BASE_URL}/api/v1/forecast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return res.json()
}
```

---

## 5. 환경 변수 설정

### 5.1 백엔드 환경 변수 (Vercel Dashboard)

**Settings → Environment Variables:**

| 변수 | 환경 | 값 예시 | 설명 |
|------|------|---------|------|
| `SUPABASE_URL` | All | `https://yietqoikdaqpwmmvamtv.supabase.co` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | All | `eyJhbGci...` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | All | `eyJhbGci...` | Supabase service_role key |
| `OPENAI_API_KEY` | All | `sk-...` | OpenAI API 키 |
| `ANTHROPIC_API_KEY` | All (선택) | `sk-ant-...` | Anthropic API 키 |
| `AI_PROVIDER` | All | `openai` | AI 제공자 |
| `APP_ENV` | Production | `production` | 앱 환경 |
| `DEBUG` | Production | `false` | 디버그 모드 |
| `ALLOWED_ORIGINS` | Production | `https://homesignal-ai-frontend.vercel.app` | CORS 허용 오리진 |
| `REDIS_URL` | All (선택) | `redis://...` | Redis 캐시 |

**중요:**
- 모든 환경 변수는 **Production, Preview, Development** 체크박스 모두 선택
- `ALLOWED_ORIGINS`는 쉼표로 여러 도메인 구분 가능

### 5.2 프론트엔드 환경 변수 (Vercel Dashboard)

| 변수 | 환경 | 값 예시 | 설명 |
|------|------|---------|------|
| `NEXT_PUBLIC_API_URL` | All | `https://homesignal-ai-backend.vercel.app` | 백엔드 API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | All (선택) | `https://yietqoikdaqpwmmvamtv.supabase.co` | Supabase 직접 접근 시 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | All (선택) | `eyJhbGci...` | Supabase anon key |

**주의:**
- `NEXT_PUBLIC_*` 접두사는 브라우저에 노출됨
- `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` 등 비밀키는 절대 프론트에 설정하지 않음

### 5.3 로컬 개발 환경

**백엔드:** `.env` 파일

```bash
SUPABASE_URL=https://yietqoikdaqpwmmvamtv.supabase.co
SUPABASE_KEY=eyJhbGci...
OPENAI_API_KEY=sk-...
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
```

**프론트엔드:** `frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 6. CORS 설정

### 6.1 CORS 동작 원리

```
Browser (https://frontend.vercel.app)
    │
    ├─► Preflight: OPTIONS /api/v1/forecast
    │   Header: Origin: https://frontend.vercel.app
    │
    ▼
Backend (https://backend.vercel.app)
    │
    ├─► CORS Middleware 검증
    │   - Origin이 ALLOWED_ORIGINS에 포함?
    │   - Yes → Access-Control-Allow-Origin 헤더 추가
    │   - No → 403 Forbidden
    │
    ▼
Browser
    │
    └─► Actual Request: POST /api/v1/forecast
```

### 6.2 Settings 구현

**파일:** `src/config/settings.py`

```python
class Settings(BaseSettings):
    # ...
    allowed_origins: list[str] = []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """쉼표 구분 문자열을 리스트로 파싱"""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v or []
```

### 6.3 main.py CORS 미들웨어

**파일:** `src/main.py`

```python
# CORS 설정
cors_origins = ["*"] if settings.debug else settings.allowed_origins

if not settings.debug and not cors_origins:
    logger.warning(
        "프로덕션 환경에서 ALLOWED_ORIGINS가 설정되지 않았습니다. "
        "프론트엔드에서 API 호출이 차단될 수 있습니다."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.4 CORS 검증

**로컬 테스트:**

```bash
# 백엔드 실행
uv run uvicorn src.main:app --reload

# 프론트엔드 실행
cd frontend
npm run dev

# 브라우저에서 http://localhost:3000 접속
# Network 탭에서 CORS 헤더 확인
```

**프로덕션 테스트:**

```bash
curl -i -X OPTIONS https://backend.vercel.app/api/v1/forecast \
  -H "Origin: https://frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST"

# 응답 헤더에 Access-Control-Allow-Origin 확인
```

---

## 7. 제한사항 및 대응

### 7.1 Vercel Function 제한

| 항목 | Hobby Plan | Pro Plan | 대응 방안 |
|------|-----------|----------|----------|
| **번들 크기** | 500MB | 500MB | ML 라이브러리 제외, .vercelignore 활용 |
| **실행 시간** | 10초 | 60초 | Chat/예측 로직 최적화, 타임아웃 처리 |
| **메모리** | 1024MB | 3008MB | 메모리 집약적 작업 최소화 |
| **Cold Start** | 1~3초 | 1~3초 | lifespan 이벤트로 초기화 최적화 |
| **동시 실행** | 1000 | 1000 | 충분 (일반 트래픽) |

### 7.2 ML 예측 전략

#### 현재 (Phase 1): Mock 예측

```python
# src/forecast/service.py
async def get_forecast(region, period, horizon):
    # Mock 데이터 반환
    return MockDataRepository().get_houses_time_series(...)
```

#### 단기 (Phase 2): Supabase 조회

```python
# 배치 스크립트로 사전 예측 실행 → predictions 테이블 저장
# API는 조회만 수행
async def get_forecast(region, period, horizon):
    predictions = await repo.get_latest_predictions(region, period, horizon)
    return predictions
```

#### 중기 (Phase 3): 별도 ML 서비스

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Vercel API   │─────►│ Railway ML   │─────►│ Supabase     │
│ (FastAPI)    │ HTTP │ (Prophet+LGB)│ 조회 │ (Features)   │
└──────────────┘      └──────────────┘      └──────────────┘
```

Railway/Render에서 ML 추론 서버 운영:
- Prophet + LightGBM 로드
- `/predict` 엔드포인트 제공
- Vercel API가 ML 서비스 호출

#### 장기 (Phase 4): 배치 예측

```
GitHub Actions (Cron)
    │
    ├─► 1. ML Feature 조회 (Supabase)
    ├─► 2. Prophet + LightGBM 예측
    ├─► 3. predictions 테이블 저장
    └─► 4. Vercel API는 조회만 수행
```

### 7.3 데이터 수집 파이프라인

Vercel Serverless는 **장시간 실행 작업에 부적합**합니다.

**권장 방안:**

#### GitHub Actions (권장)

```yaml
# .github/workflows/news-crawler.yml
name: News Crawler
on:
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시 (UTC)
  workflow_dispatch:

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --extra crawler
      - run: uv run python -m src.crawler.cli crawl
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - run: uv run python scripts/generate_embeddings.py
```

#### 별도 서버 (대안)

Railway/Render에서 Cron job 실행:
```bash
0 2 * * * cd /app && uv run python -m src.crawler.cli crawl
```

---

## 8. 배포 워크플로우

### 8.1 초기 배포 (CLI)

#### 백엔드

```bash
cd d:\Ai_project\home_signal_ai

# 프리뷰 배포
vercel

# 프로덕션 배포
vercel --prod
```

프롬프트:
- Set up and deploy? **Y**
- Which scope? **선택**
- Link to existing project? **N**
- Project name? **homesignal-ai-backend**
- In which directory? **./**
- Override settings? **N**

#### 프론트엔드

```bash
cd d:\Ai_project\home_signal_ai\frontend

# 프리뷰 배포
vercel

# 프로덕션 배포
vercel --prod
```

프롬프트:
- Project name? **homesignal-ai-frontend**
- In which directory? **./**

### 8.2 Git 연동 배포 (권장)

#### Step 1: GitHub 저장소 푸시

```bash
git add .
git commit -m "feat: Vercel 배포 설정 추가"
git push origin main
```

#### Step 2: Vercel Dashboard 설정

1. [Vercel Dashboard](https://vercel.com/dashboard) 접속
2. **Add New... → Project** 클릭
3. GitHub 저장소 선택

**백엔드 프로젝트:**
- Project Name: `homesignal-ai-backend`
- Root Directory: `./` (루트)
- Framework Preset: Other
- 환경 변수 설정 (5.1 참조)

**프론트엔드 프로젝트:**
- Project Name: `homesignal-ai-frontend`
- Root Directory: `frontend`
- Framework Preset: Next.js
- 환경 변수 설정 (5.2 참조)

#### Step 3: 자동 배포

- `main` 브랜치 푸시 → 프로덕션 배포
- PR 생성 → 프리뷰 배포

### 8.3 배포 후 확인

```bash
# 백엔드 헬스체크
curl https://homesignal-ai-backend.vercel.app/health

# 프론트엔드 접속
open https://homesignal-ai-frontend.vercel.app
```

---

## 9. 트러블슈팅

### 9.1 CORS 에러

**증상:**
```
Access to fetch at 'https://backend.vercel.app/api/v1/forecast'
from origin 'https://frontend.vercel.app' has been blocked by CORS policy
```

**원인:**
- `ALLOWED_ORIGINS` 환경 변수 미설정
- 프론트엔드 도메인이 CORS 허용 목록에 없음

**해결:**
1. Vercel Dashboard → Backend Project → Settings → Environment Variables
2. `ALLOWED_ORIGINS` 추가: `https://homesignal-ai-frontend.vercel.app`
3. **Redeploy** 클릭 (환경 변수 변경 후 재배포 필수)

### 9.2 500 Internal Server Error

**증상:**
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "내부 서버 오류가 발생했습니다."
  }
}
```

**원인:**
- 환경 변수 누락 (`SUPABASE_URL`, `OPENAI_API_KEY` 등)
- Python 의존성 설치 실패

**해결:**
1. Vercel Dashboard → Deployments → 최신 배포 클릭
2. **Function Logs** 탭에서 에러 로그 확인
3. 환경 변수 재확인 후 Redeploy

### 9.3 Build Failed (번들 크기 초과)

**증상:**
```
Error: Function size exceeds 500MB limit
```

**원인:**
- ML 라이브러리(Prophet, LightGBM) 포함
- 불필요한 파일 포함

**해결:**
1. `requirements.txt`에서 ML 라이브러리 제거
2. `.vercelignore`에 `frontend/`, `tests/`, `models/` 추가
3. 재배포

### 9.4 Function Timeout

**증상:**
```
Error: Function execution timed out (10s)
```

**원인:**
- Chat API가 AI API 호출 시간 초과
- 데이터베이스 쿼리 느림

**해결:**
1. `settings.ai_api_timeout` 조정 (최대 8초)
2. Supabase 쿼리 최적화 (인덱스, RPC 함수)
3. Pro Plan 업그레이드 (60초 제한)

### 9.5 Cold Start 지연

**증상:**
- 첫 요청 시 3~5초 지연

**원인:**
- Vercel Function이 idle 상태에서 재시작

**해결:**
- `lifespan` 이벤트에서 초기화 최소화
- Vercel Pro Plan의 "Keep Functions Warm" 기능 사용
- 프론트엔드에서 로딩 UI 표시

---

## 10. 성능 최적화

### 10.1 응답 시간 목표

| API | 목표 | Cold Start | Warm |
|-----|------|-----------|------|
| `/health` | 100ms | 1.5s | 50ms |
| `/api/v1/forecast` | 1.5s | 3s | 1s |
| `/api/v1/chat` | 2.0s | 4s | 1.5s |
| `/api/v1/news/insights` | 1.0s | 2.5s | 500ms |

### 10.2 최적화 전략

#### 캐싱

```python
# Redis 캐싱 (향후)
@cache(ttl=3600)
async def get_forecast(region, period, horizon):
    # ...
```

#### RPC 함수 활용

```python
# Python 루프 집계 대신 DB 레벨 집계
result = db.rpc("aggregate_houses_time_series", {
    "p_region": region,
    "p_period_type": period,
})
```

#### 병렬 처리

```python
# RAG 검색과 예측을 병렬 실행
forecast_task = asyncio.create_task(get_forecast(...))
news_task = asyncio.create_task(vector_db.search(...))
forecast, news = await asyncio.gather(forecast_task, news_task)
```

---

## 11. 모니터링 및 로깅

### 11.1 Vercel Analytics

**활성화:**
1. Vercel Dashboard → Project → Analytics
2. Web Analytics 활성화

**지표:**
- 페이지 뷰
- API 호출 수
- 응답 시간
- 에러율

### 11.2 Function Logs

**실시간 로그:**
1. Vercel Dashboard → Deployments → 배포 선택
2. **Function Logs** 탭

**로그 레벨:**
- `DEBUG=false` (프로덕션): INFO 이상만 출력
- `DEBUG=true` (개발): DEBUG 포함 모든 로그

### 11.3 에러 추적 (권장)

**Sentry 연동:**

```bash
pip install sentry-sdk[fastapi]
```

```python
# src/main.py
import sentry_sdk

if settings.app_env == "production":
    sentry_sdk.init(
        dsn="https://...",
        environment=settings.app_env,
    )
```

---

## 12. 보안 체크리스트

### 12.1 배포 전 확인

- [ ] `DEBUG=false` (프로덕션)
- [ ] `ALLOWED_ORIGINS` 설정 (프론트엔드 도메인만)
- [ ] API 키는 백엔드 환경변수에만 저장
- [ ] `SUPABASE_SERVICE_ROLE_KEY`는 절대 프론트엔드에 노출 금지
- [ ] `.env` 파일은 `.gitignore`에 포함
- [ ] Supabase RLS 정책 활성화

### 12.2 프로덕션 설정

**src/main.py:**
```python
app = FastAPI(
    title="HomeSignal AI",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,  # 프로덕션에서 비활성화
    redoc_url="/redoc" if settings.debug else None,
)
```

**CORS:**
```python
allow_origins=settings.allowed_origins  # ["*"] 금지
```

---

## 13. 배포 체크리스트

### 13.1 백엔드 배포

- [ ] `vercel.json` 설정 확인
- [ ] `requirements.txt` ML 라이브러리 제외 확인
- [ ] `.vercelignore`에 `frontend/`, `tests/` 포함
- [ ] 환경 변수 설정 (All environments)
- [ ] `vercel --prod` 실행
- [ ] `/health` 엔드포인트 200 응답 확인
- [ ] `/api/v1/forecast` Mock 응답 확인

### 13.2 프론트엔드 배포

- [ ] `NEXT_PUBLIC_API_URL` 설정 (백엔드 도메인)
- [ ] `npm run build` 로컬 빌드 테스트
- [ ] `vercel --prod` 실행
- [ ] 홈페이지 로딩 확인
- [ ] API 호출 성공 확인 (Network 탭)

### 13.3 통합 테스트

- [ ] 프론트엔드에서 Forecast API 호출 → 차트 렌더링
- [ ] 프론트엔드에서 Chat API 호출 → 응답 표시
- [ ] 프론트엔드에서 News API 호출 → 인사이트 표시
- [ ] CORS 에러 없음
- [ ] 응답 시간 <2초

---

## 14. 다음 단계

### 14.1 ML 서비스 분리

1. Railway/Render에 ML 추론 서버 배포
2. Prophet + LightGBM 모델 로드
3. Vercel API에서 ML 서비스 호출

### 14.2 데이터 수집 자동화

1. GitHub Actions Cron job 설정
2. 뉴스 크롤링 + 임베딩 생성
3. Supabase에 자동 저장

### 14.3 캐싱 구현

1. Vercel KV 또는 Upstash Redis 연동
2. Forecast/Chat 응답 캐싱
3. TTL 설정 (1시간/30분)

---

## 부록 A: Vercel CLI 명령어

```bash
# 로그인
vercel login

# 프리뷰 배포
vercel

# 프로덕션 배포
vercel --prod

# 로컬 개발 (Vercel 환경 시뮬레이션)
vercel dev

# 환경 변수 추가
vercel env add SUPABASE_URL production

# 환경 변수 조회
vercel env ls

# 프로젝트 정보
vercel inspect

# 로그 확인
vercel logs
```

---

## 부록 B: 환경별 설정 비교

| 설정 | Development | Preview | Production |
|------|-------------|---------|------------|
| `APP_ENV` | `development` | `staging` | `production` |
| `DEBUG` | `true` | `false` | `false` |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | `https://*.vercel.app` | `https://homesignal-ai-frontend.vercel.app` |
| Swagger Docs | 활성화 | 비활성화 | 비활성화 |
| 로그 레벨 | DEBUG | INFO | INFO |
| CORS | `["*"]` | 설정된 오리진 | 설정된 오리진 |

---

## 참고 자료

- [Vercel FastAPI Documentation](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Supabase Dashboard](https://supabase.com/dashboard)

---

**문서 작성자:** DevOps Specialist  
**검토자:** Backend/Frontend 담당자  
**최종 업데이트:** 2026-03-09
