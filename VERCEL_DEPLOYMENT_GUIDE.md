# Vercel 배포 가이드

## 준비 사항

### 1. Vercel CLI 설치

```bash
npm i -g vercel
```

### 2. Vercel 로그인

```bash
vercel login
```

---

## 백엔드 배포

### Step 1: 프리뷰 배포

```bash
cd d:\Ai_project\home_signal_ai
vercel
```

프롬프트에 따라:
- Set up and deploy? **Y**
- Which scope? **선택**
- Link to existing project? **N**
- Project name? **homesignal-ai-backend** (또는 원하는 이름)
- In which directory? **./** (현재 디렉토리)
- Override settings? **N**

### Step 2: 환경 변수 설정

Vercel Dashboard에서 설정:
https://vercel.com/dashboard

**Settings → Environment Variables:**

```env
# Supabase
SUPABASE_URL=https://yietqoikdaqpwmmvamtv.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpZXRxb2lrZGFxcHdtbXZhbXR2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMjMyNjksImV4cCI6MjA4NzU5OTI2OX0.cnGFGUsn05TpVIvZyk6Sn6jEUdkTPzqc9YHOLnPr6NY
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpZXRxb2lrZGFxcHdtbXZhbXR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjAyMzI2OSwiZXhwIjoyMDg3NTk5MjY5fQ.F4HvWwUiFMysGP06DW45v5RbxG7UoW38q8JI2z1MIDM

# AI API (나중에 설정)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# App Config
APP_ENV=production
DEBUG=false
AI_PROVIDER=openai

# Cache (Optional - Vercel KV 또는 Upstash Redis)
REDIS_URL=
```

**중요:** 모든 환경 변수는 **Production, Preview, Development** 모두에 체크

**CLI로 환경변수 설정:**
```bash
# 필수 환경변수 설정
vercel env add SUPABASE_URL production
vercel env add SUPABASE_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add OPENAI_API_KEY production
vercel env add APP_ENV production
vercel env add DEBUG production

# 환경변수 확인
vercel env ls

# 로컬에서 환경변수 테스트
vercel env pull .env.vercel
```

### Step 3: 프로덕션 배포

```bash
vercel --prod
```

### Step 4: 배포 확인

```bash
# Health check
curl https://your-backend.vercel.app/health

# Forecast API 테스트
curl -X POST https://your-backend.vercel.app/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{"region": "청량리동", "period": "week", "horizon": 12}'
```

---

## 프론트엔드 배포

### Step 1: 의존성 설치

```bash
cd frontend
npm install
```

### Step 2: 로컬 테스트

```bash
npm run dev
```

http://localhost:3000 접속 확인

### Step 3: 프리뷰 배포

```bash
vercel
```

프롬프트에 따라:
- Set up and deploy? **Y**
- Which scope? **선택**
- Link to existing project? **N**
- Project name? **homesignal-ai-frontend** (또는 원하는 이름)
- In which directory? **./** (frontend 디렉토리)
- Override settings? **N**

### Step 4: 환경 변수 설정

Vercel Dashboard에서 설정:

```env
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
NEXT_PUBLIC_SUPABASE_URL=https://yietqoikdaqpwmmvamtv.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlpZXRxb2lrZGFxcHdtbXZhbXR2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIwMjMyNjksImV4cCI6MjA4NzU5OTI2OX0.cnGFGUsn05TpVIvZyk6Sn6jEUdkTPzqc9YHOLnPr6NY
```

### Step 5: 프로덕션 배포

```bash
vercel --prod
```

### Step 6: 배포 확인

브라우저에서 접속:
- 홈: `https://your-frontend.vercel.app`
- Forecast: `https://your-frontend.vercel.app/forecast`
- Chat: `https://your-frontend.vercel.app/chat`
- News: `https://your-frontend.vercel.app/news`

---

## CORS 설정 (중요)

백엔드 배포 후 **반드시** 프론트엔드 도메인을 CORS에 추가해야 합니다.

### Step 1: 백엔드 환경 변수 추가

**Vercel Dashboard → Backend Project → Settings → Environment Variables:**

```env
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

**여러 도메인 허용 (쉼표 구분):**
```env
ALLOWED_ORIGINS=https://homesignal-ai-frontend.vercel.app,https://custom-domain.com
```

**Preview 배포 포함:**
```env
ALLOWED_ORIGINS=https://homesignal-ai-frontend.vercel.app,https://*.vercel.app
```

### Step 2: 재배포

환경 변수 추가 후 **반드시 Redeploy** 클릭:
1. Vercel Dashboard → Deployments
2. 최신 배포의 **⋯** 메뉴 → **Redeploy**

### Step 3: CORS 동작 확인

**브라우저 개발자 도구 (Network 탭):**
```
Request URL: https://backend.vercel.app/api/v1/forecast
Request Method: POST
Origin: https://frontend.vercel.app

Response Headers:
  Access-Control-Allow-Origin: https://frontend.vercel.app
  Access-Control-Allow-Credentials: true
```

**CORS 에러 발생 시:**
```
Access to fetch at 'https://backend.vercel.app/api/v1/forecast'
from origin 'https://frontend.vercel.app' has been blocked by CORS policy
```

→ `ALLOWED_ORIGINS` 재확인 후 Redeploy

### CORS 설정 구현 (이미 완료)

**src/config/settings.py:**
```python
class Settings(BaseSettings):
    # CORS 설정
    allowed_origins: list[str] = []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v or []
```

**src/main.py:**
```python
cors_origins = ["*"] if settings.debug else settings.allowed_origins

if not settings.debug and not cors_origins:
    logger.warning("프로덕션 환경에서 ALLOWED_ORIGINS가 설정되지 않았습니다.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### CORS 테스트 명령어

```bash
# Preflight 요청 테스트
curl -i -X OPTIONS https://backend.vercel.app/api/v1/forecast \
  -H "Origin: https://frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

# 응답 헤더 확인
# Access-Control-Allow-Origin: https://frontend.vercel.app
# Access-Control-Allow-Methods: *
# Access-Control-Allow-Headers: *
```

---

## 문제 해결

### 1. 환경변수 누락 오류 (ValidationError) ⭐ 가장 흔한 오류

**증상:**
```
pydantic_core._pydantic_core.ValidationError:
2 validation errors for Settings
supabase_url
  Field required [type=missing, input_value={}, input_type=dict]
supabase_key
  Field required [type=missing, input_value={}, input_type=dict]
```

**원인:** Vercel 환경변수 미설정

**해결 (3단계):**

**Step 1: Vercel CLI로 환경변수 설정**
```bash
vercel env add SUPABASE_URL production
vercel env add SUPABASE_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add OPENAI_API_KEY production
vercel env add APP_ENV production
vercel env add DEBUG production

# 환경변수 확인
vercel env ls
```

**Step 2: 또는 Vercel Dashboard 사용**
1. https://vercel.com/dashboard 접속
2. 프로젝트 선택 → **Settings** → **Environment Variables**
3. 필수 환경변수 추가 (아래 참조)
4. **Production, Preview, Development** 모두 체크

**필수 환경변수:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
OPENAI_API_KEY=sk-...
APP_ENV=production
DEBUG=false
```

**Step 3: 재배포**
```bash
vercel --prod
```

**검증:**
```bash
# Health check
curl https://your-backend.vercel.app/health

# 예상 응답: {"status": "ok"}
```

---

### 2. 백엔드 배포 실패

**증상:** Build failed 또는 Function size exceeded

**해결:**
- `requirements.txt`에 ML 라이브러리(Prophet, LightGBM) 포함 여부 확인
- `.vercelignore`에 불필요한 파일 추가
- `vercel.json`의 Python 버전 확인 (3.12)

### 3. 프론트엔드 빌드 실패

**증상:** Type errors 또는 Module not found

**해결:**
```bash
cd frontend
npm install
npm run build  # 로컬에서 빌드 테스트
```

### 4. API 호출 실패 (CORS)

**증상:** Network error 또는 CORS policy error

**해결:**
- 백엔드 환경 변수에 `ALLOWED_ORIGINS` 추가
- 프론트엔드 `.env.local`의 `NEXT_PUBLIC_API_URL` 확인

### 5. 환경 변수 미적용

**증상:** 500 Internal Server Error

**해결:**
- Vercel Dashboard에서 환경 변수 재확인
- **Redeploy** 버튼 클릭 (환경 변수 변경 후 재배포 필요)

### 6. Import Time Error (Module-level 초기화 문제)

**증상:** 모듈 임포트 시점에 에러 발생

**원인:** `settings.py`의 module-level에서 Settings 객체를 즉시 생성

**해결:** 이미 적용됨 (2026-03-13 수정)
- Settings에 기본값 추가
- Production 환경 검증 로직 추가
- Mock mode 자동 활성화 (placeholder URL)

---

## 배포 후 체크리스트

### 백엔드

- [ ] `/health` 엔드포인트 응답 200
- [ ] `/api/v1/forecast` Mock 데이터 반환
- [ ] `/api/v1/chat` Mock 응답 반환
- [ ] `/api/v1/news/insights` 키워드 분석 작동
- [ ] Supabase 연결 확인 (테이블 조회)

### 프론트엔드

- [ ] 홈페이지 로딩
- [ ] 네비게이션 작동
- [ ] Forecast 페이지 차트 렌더링
- [ ] Chat 페이지 메시지 전송
- [ ] News 페이지 키워드 분석

### 통합

- [ ] 프론트엔드 → 백엔드 API 호출 성공
- [ ] CORS 정상 작동
- [ ] 응답 시간 <2초
- [ ] 모바일 반응형 확인

---

## 다음 단계

### 1. OpenAI API 키 설정

```bash
# Vercel Dashboard에서 환경 변수 추가
OPENAI_API_KEY=sk-...

# 임베딩 생성 (로컬에서 실행)
uv run python scripts/generate_embeddings.py
```

### 2. 실제 데이터 수집

```bash
# 뉴스 크롤링 (더 많은 데이터)
uv run python -m src.crawler.cli crawl \
  -q "GTX-C 청량리" "동대문구 재개발" "이문휘경뉴타운" \
  --max-results 500 \
  --date-range 90
```

### 3. ML 모델 구현

- Prophet 모델 학습 스크립트
- LightGBM 모델 학습 스크립트
- 모델 파일 Supabase Storage 저장
- ForecastService Mock → 실제 모델 교체

### 4. 모니터링 설정

- Vercel Analytics 활성화
- Sentry 에러 추적
- 성능 모니터링 (응답 시간, 에러율)

---

## 참고 링크

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel FastAPI Docs](https://vercel.com/docs/frameworks/backend/fastapi)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Supabase Dashboard](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv)
