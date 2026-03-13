# Vercel 배포 체크리스트 및 빠른 가이드

**작성일:** 2026-03-13
**목적:** FastAPI Entrypoint 오류 해결 후 배포

---

## ✅ 완료된 수정사항

### 1. API Entrypoint 수정
- [x] `api/index.py` - Python path 추가 ✅
- [x] `vercel.json` - Runtime 명시적 설정 ✅
- [x] `requirements.txt` - 검증 완료 ✅

### 2. 로컬 테스트 완료
- [x] Python import 테스트 통과 ✅
- [x] FastAPI app 로드 확인 ✅

---

## 🚀 즉시 배포 단계 (5분)

### Step 1: 변경사항 커밋 (1분)

```bash
# 변경된 파일 확인
git status

# 스테이징
git add api/index.py vercel.json src/config/settings.py

# 커밋
git commit -m "fix: Vercel FastAPI entrypoint 수정

- api/index.py: Python path 자동 추가로 src 모듈 import 해결
- vercel.json: runtime 명시적 설정 추가
- src/config/settings.py: 환경변수 기본값 추가 (이전 커밋)"
```

### Step 2: GitHub 푸시 (30초)

```bash
# GitHub에 푸시
git push siyeol main
```

### Step 3: Vercel 배포 (3분)

```bash
# Vercel 배포 (자동 또는 수동)
vercel --prod
```

또는 GitHub Actions가 설정되어 있다면 자동 배포됩니다.

### Step 4: 배포 확인 (30초)

```bash
# Health check
curl https://your-backend.vercel.app/health

# 예상 응답
# {
#   "status": "healthy",
#   "environment": "production",
#   "version": "0.1.0"
# }
```

---

## 🔍 배포 전 최종 체크리스트

### 코드 변경
- [x] `api/index.py` - Python path 추가
- [x] `vercel.json` - Runtime 설정
- [x] `src/config/settings.py` - 환경변수 기본값

### Vercel 환경변수 (필수)
- [ ] `SUPABASE_URL` 설정됨
- [ ] `SUPABASE_KEY` 설정됨
- [ ] `SUPABASE_SERVICE_ROLE_KEY` 설정됨
- [ ] `OPENAI_API_KEY` 설정됨
- [ ] `APP_ENV=production` 설정됨
- [ ] `DEBUG=false` 설정됨

**환경변수 확인:**
```bash
vercel env ls
```

**환경변수 설정 (미설정 시):**
```bash
# 자동화 스크립트 사용
chmod +x scripts/setup_vercel_env.sh
./scripts/setup_vercel_env.sh

# 또는 수동 설정
vercel env add SUPABASE_URL production
vercel env add SUPABASE_KEY production
# ... (나머지 변수들)
```

### 로컬 테스트
- [x] Python import 테스트 통과
- [ ] 로컬 서버 실행 확인

**로컬 서버 테스트:**
```bash
uv run uvicorn src.main:app --reload

# 별도 터미널에서
curl http://localhost:8000/health
```

---

## 📊 수정사항 요약

### api/index.py (변경 전 → 후)

**Before:**
```python
from src.main import app  # ❌ Python path 오류 가능
```

**After:**
```python
import sys
from pathlib import Path

# Add project root to Python path
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.main import app  # ✅ 정상 작동
```

### vercel.json (변경 전 → 후)

**Before:**
```json
{
  "builds": [{
    "src": "api/index.py",
    "use": "@vercel/python",
    "config": { "maxLambdaSize": "250mb" }
  }]
}
```

**After:**
```json
{
  "builds": [{
    "src": "api/index.py",
    "use": "@vercel/python",
    "config": {
      "maxLambdaSize": "250mb",
      "runtime": "python3.12"  // ✅ 추가
    }
  }],
  "functions": {  // ✅ 추가
    "api/**/*.py": {
      "runtime": "python3.12"
    }
  }
}
```

---

## 🎯 빠른 배포 (원라이너)

```bash
# 전체 과정 한 번에 실행
git add api/index.py vercel.json src/config/settings.py && \
git commit -m "fix: Vercel FastAPI entrypoint 수정" && \
git push siyeol main && \
vercel --prod
```

---

## 🔧 배포 실패 시 트러블슈팅

### 오류 1: 여전히 "No fastapi entrypoint found"

**해결책:**
```bash
# requirements.txt에 uvicorn 명시
echo "uvicorn[standard]>=0.27.0" >> requirements.txt
git add requirements.txt
git commit -m "fix: Add uvicorn to requirements"
git push siyeol main
```

### 오류 2: "ModuleNotFoundError: No module named 'src'"

**해결책:**
```bash
# api/index.py 수정 확인
cat api/index.py | grep "sys.path"

# 출력이 없으면 수정 재적용
```

### 오류 3: 환경변수 오류

**해결책:**
```bash
# Vercel Dashboard에서 환경변수 확인
# 또는
vercel env pull .env.vercel
cat .env.vercel
```

### 오류 4: Build size exceeded

**해결책:**
```bash
# requirements.txt에서 불필요한 패키지 제거
# ML 라이브러리(Prophet, LightGBM)는 이미 제외되어 있음
```

---

## 📞 지원 및 도움

### Vercel 로그 확인
```bash
# 배포 로그 확인
vercel logs [deployment-url]

# 실시간 로그
vercel logs --follow
```

### Vercel Dashboard
- URL: https://vercel.com/dashboard
- **Deployments** 탭에서 빌드 로그 확인
- **Settings** > **Environment Variables** 확인

### 추가 문서
- `docs/VERCEL_ERROR_REPORT_2026-03-13.md` - 환경변수 오류
- `docs/VERCEL_FASTAPI_ERROR_REPORT_2026-03-13.md` - Entrypoint 오류
- `VERCEL_DEPLOYMENT_GUIDE.md` - 전체 배포 가이드

---

## ✅ 성공 확인

### 1. 배포 성공 메시지
```
✓ Deployment ready
✓ Build Completed in 1m 30s
✓ Deployment URL: https://homesignal-ai-backend.vercel.app
```

### 2. Health Check 성공
```bash
$ curl https://homesignal-ai-backend.vercel.app/health

{
  "status": "healthy",
  "environment": "production",
  "version": "0.1.0"
}
```

### 3. API 엔드포인트 테스트
```bash
# Forecast API (Mock 응답)
curl -X POST https://homesignal-ai-backend.vercel.app/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{"region": "청량리동", "period": "week", "horizon": 12}'

# Chat API (Mock 응답)
curl -X POST https://homesignal-ai-backend.vercel.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "청량리 집값 전망은?"}'
```

---

## 🎉 다음 단계

배포 성공 후:
1. [ ] Frontend 프로젝트에서 Backend URL 업데이트
2. [ ] CORS 설정 확인 (ALLOWED_ORIGINS)
3. [ ] 실제 데이터 수집 시작 (뉴스 크롤링)
4. [ ] ML 모델 학습 및 배포 (별도 서비스)
5. [ ] 모니터링 설정 (Sentry, Vercel Analytics)

---

**마지막 업데이트:** 2026-03-13
**작성자:** Claude Code
