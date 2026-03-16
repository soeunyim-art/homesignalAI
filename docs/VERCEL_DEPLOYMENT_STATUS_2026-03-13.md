# Vercel 배포 상태 확인 결과

**확인 일시:** 2026-03-13
**배포 URL:** https://homesignal-ai.vercel.app
**상태:** ⚠️ 배포 완료, 서버 오류 발생 (500)

---

## 📊 배포 상태 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| **GitHub 푸시** | ✅ 완료 | 최신 커밋: 2ddb27d |
| **Vercel 배포** | ✅ 완료 | URL 활성화 |
| **서버 응답** | ❌ 500 오류 | 내부 서버 오류 |
| **환경변수 설정** | ⚠️ 확인 필요 | Dashboard에서 확인 필요 |

---

## 🔴 발견된 문제

### HTTP 500 Internal Server Error

```bash
# 테스트 결과
$ curl https://homesignal-ai.vercel.app/health
❌ 500 Internal Server Error

$ curl https://homesignal-ai.vercel.app/
❌ 500 Internal Server Error
```

**의미:**
- 배포는 성공했지만 서버 실행 중 오류 발생
- Python 코드 또는 환경변수 문제 가능성

---

## 🔍 가능한 원인 분석

### 1. 환경변수 미설정 (가장 가능성 높음) ⚠️

**증상:**
```python
# src/config/settings.py에서 검증 실패
if v == "https://placeholder.supabase.co":
    if os.environ.get("APP_ENV") == "production":
        raise ValueError("Production 환경에서 placeholder 사용 불가")
```

**해결 방법:**
1. Vercel Dashboard → Settings → Environment Variables 확인
2. 필수 환경변수 7개 모두 설정되었는지 확인
3. 재배포 (Redeploy) 실행

---

### 2. Python Import 오류

**가능한 원인:**
- `api/index.py`에서 `from src.main import app` 실패
- Dependencies 설치 문제
- Python 버전 불일치

**해결 방법:**
- Vercel 빌드 로그 확인

---

### 3. Dependencies 설치 실패

**가능한 원인:**
- `requirements.txt`의 패키지 설치 실패
- 패키지 버전 충돌
- 빌드 크기 초과 (500MB)

**해결 방법:**
- Vercel 빌드 로그에서 "pip install" 섹션 확인

---

## 🛠️ 즉시 조치 사항

### Step 1: Vercel Dashboard 로그 확인 (필수)

1. https://vercel.com/dashboard 접속
2. 프로젝트 선택 (homesignal-ai)
3. **Deployments** 탭 클릭
4. 최신 배포 클릭
5. **Build Logs** 탭에서 에러 확인
6. **Runtime Logs** 탭에서 실행 오류 확인

**주요 확인 사항:**
- ❌ Build Failed? → Dependencies 문제
- ❌ Import Error? → Python path 문제
- ❌ ValidationError? → 환경변수 문제

---

### Step 2: 환경변수 확인 및 설정

Vercel Dashboard에서:
1. **Settings** → **Environment Variables**
2. 아래 7개 환경변수 모두 있는지 확인:

**필수 환경변수:**
```
✅ SUPABASE_URL
✅ SUPABASE_KEY
✅ SUPABASE_SERVICE_ROLE_KEY
✅ APP_ENV
✅ DEBUG
✅ AI_PROVIDER
⚪ OPENAI_API_KEY (선택)
```

**없으면:** VERCEL_ENV_SETUP_GUIDE.md 참조하여 추가

---

### Step 3: 재배포 실행

환경변수 추가/수정 후:
1. **Deployments** 탭
2. 최신 배포의 **⋯** 메뉴
3. **Redeploy** 클릭
4. 배포 완료 대기 (1-3분)

---

## 📋 환경변수 체크리스트

### Vercel Dashboard에서 확인

- [ ] SUPABASE_URL = `https://yietqoikdaqpwmmvamtv.supabase.co`
- [ ] SUPABASE_KEY = `eyJhbGciOiJI...` (긴 문자열)
- [ ] SUPABASE_SERVICE_ROLE_KEY = `eyJhbGciOiJI...` (긴 문자열)
- [ ] APP_ENV
  - [ ] Production = `production`
  - [ ] Preview = `preview`
  - [ ] Development = `development`
- [ ] DEBUG
  - [ ] Production = `false`
  - [ ] Preview = `false`
  - [ ] Development = `true`
- [ ] AI_PROVIDER = `openai`
- [ ] OPENAI_API_KEY = `sk-...` (선택사항)

---

## 🔧 문제별 해결 방법

### 문제 1: "ValidationError: Production에서 placeholder 사용 불가"

**로그 예시:**
```
ValueError: Production 환경에서 placeholder Supabase URL을 사용할 수 없습니다
```

**원인:** 환경변수 미설정

**해결:**
1. Vercel Dashboard → Environment Variables
2. SUPABASE_URL, SUPABASE_KEY 추가
3. Redeploy

---

### 문제 2: "ModuleNotFoundError: No module named 'src'"

**로그 예시:**
```
ModuleNotFoundError: No module named 'src'
```

**원인:** Python path 문제

**해결:**
1. `api/index.py` 파일 확인 (이미 수정됨)
2. `pyproject.toml`의 `[project.scripts]` 확인 (이미 추가됨)
3. Redeploy

---

### 문제 3: Dependencies 설치 실패

**로그 예시:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**원인:** requirements.txt 패키지 문제

**해결:**
1. 로컬에서 테스트: `pip install -r requirements.txt`
2. 문제 패키지 버전 조정
3. Git 커밋 및 푸시

---

## 📊 Vercel 로그 분석 가이드

### Build Logs에서 확인할 것

```bash
# 1. Python 버전
> Installing Python 3.12...
✅ Python 설치 성공

# 2. Dependencies 설치
> Installing dependencies from requirements.txt...
✅ pip install 성공

# 3. Build 완료
> Build completed
✅ 빌드 성공
```

### Runtime Logs에서 확인할 것

```bash
# 1. 앱 시작
> Starting application...
✅ FastAPI 앱 시작

# 2. Import 성공
> Importing src.main...
❌ 여기서 오류 발생 시 Python path 문제

# 3. 환경변수 검증
> Validating settings...
❌ 여기서 오류 발생 시 환경변수 문제
```

---

## 🎯 예상 해결 시나리오

### 시나리오 1: 환경변수 미설정 (90% 확률)

**단계:**
1. ✅ Vercel Dashboard에서 환경변수 7개 추가
2. ✅ Redeploy 실행
3. ✅ 3분 후 배포 완료
4. ✅ Health check 성공

**예상 소요 시간:** 10분

---

### 시나리오 2: 환경변수는 있지만 값이 틀림 (5% 확률)

**단계:**
1. ✅ Vercel Dashboard에서 환경변수 값 재확인
2. ✅ 잘못된 값 수정
3. ✅ Redeploy 실행
4. ✅ Health check 성공

**예상 소요 시간:** 5분

---

### 시나리오 3: 코드 오류 (5% 확률)

**단계:**
1. ✅ Vercel Runtime Logs에서 에러 메시지 확인
2. ✅ 로컬에서 재현 및 수정
3. ✅ Git 커밋 및 푸시
4. ✅ 자동 배포 대기
5. ✅ Health check 성공

**예상 소요 시간:** 15-30분

---

## 🚀 다음 단계

### 즉시 실행 (5분)

1. **Vercel Dashboard 접속**
   ```
   https://vercel.com/dashboard
   ```

2. **로그 확인**
   - Deployments → 최신 배포 클릭
   - Build Logs & Runtime Logs 확인

3. **환경변수 확인**
   - Settings → Environment Variables
   - 7개 환경변수 모두 있는지 확인

4. **재배포**
   - Deployments → Redeploy
   - 배포 완료 대기

5. **Health Check 재시도**
   ```bash
   curl https://homesignal-ai.vercel.app/health
   ```

---

## 📞 지원 요청

### Vercel Dashboard에서 확인할 정보

다음 정보를 제공하시면 더 정확한 도움을 드릴 수 있습니다:

1. **Build Logs의 마지막 20줄**
2. **Runtime Logs의 에러 메시지**
3. **Environment Variables 스크린샷** (값은 가려도 됨)

---

## ✅ 성공 시 예상 응답

환경변수 설정 후 재배포가 성공하면:

```bash
$ curl https://homesignal-ai.vercel.app/health
{
  "status": "healthy",
  "environment": "production",
  "version": "0.1.0"
}
```

```bash
$ curl https://homesignal-ai.vercel.app/
{
  "message": "HomeSignal AI API",
  "docs": "Disabled in production",
  "endpoints": {
    "forecast": "/api/v1/forecast",
    "chat": "/api/v1/chat",
    "news": "/api/v1/news/insights",
    ...
  }
}
```

---

## 📚 관련 문서

- **VERCEL_ENV_SETUP_GUIDE.md** - 환경변수 설정 상세 가이드
- **VERCEL_DEPLOYMENT_GUIDE.md** - 전체 배포 가이드
- **VERCEL_DEPLOY_CHECKLIST.md** - 배포 체크리스트

---

**상태:** ⏳ Vercel Dashboard 확인 및 환경변수 설정 필요
**다음 작업:** 환경변수 설정 → Redeploy → 재확인

**작성자:** Claude Code
**확인 일시:** 2026-03-13
