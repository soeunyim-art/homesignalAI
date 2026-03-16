# ⚠️ VERCEL 환경변수 설정 필수 (REQUIRED)

**작성일:** 2026-03-16
**우선순위:** 🚨 CRITICAL - 배포 전 필수 설정
**예상 소요 시간:** 5분

---

## 🚨 **현재 상태: 환경변수 미설정**

Vercel에 배포된 앱이 다음 에러로 실패하고 있습니다:

```
ValidationError: 2 validation errors for Settings
supabase_url - Field required
supabase_key - Field required
```

**원인:** Vercel Dashboard에 환경변수가 설정되지 않았습니다.

---

## ✅ **즉시 수행할 작업**

### **Step 1: Vercel Dashboard 접속**

1. https://vercel.com/dashboard 접속
2. 프로젝트 선택: `homesignal-ai` 또는 `home-signal-ai-backend`
3. **Settings** 탭 클릭
4. 왼쪽 메뉴에서 **Environment Variables** 클릭

---

### **Step 2: 필수 환경변수 추가**

다음 환경변수를 **하나씩** 추가합니다:

#### **🔑 Supabase (필수)**

| 변수명 | 값 | Environment | 설명 |
|--------|---|-------------|------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Production | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | `eyJhbGc...` (anon key) | Production | Public/Anon Key (SELECT용) |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGc...` (service_role) | Production | Service Role Key (INSERT/UPDATE용) |

**Supabase 키 찾는 방법:**
1. https://app.supabase.com 접속
2. 프로젝트 선택
3. Settings → API
4. **Project URL** 복사 → `SUPABASE_URL`
5. **anon public** 복사 → `SUPABASE_KEY`
6. **service_role** 복사 → `SUPABASE_SERVICE_ROLE_KEY`

---

#### **🤖 AI API Keys (필수 - 최소 1개)**

| 변수명 | 값 | Environment | 설명 |
|--------|---|-------------|------|
| `OPENAI_API_KEY` | `sk-proj-...` | Production | OpenAI API Key |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Production | Anthropic API Key (선택) |
| `AI_PROVIDER` | `openai` | Production | 사용할 AI Provider |

**OpenAI API 키 찾는 방법:**
1. https://platform.openai.com/api-keys 접속
2. **Create new secret key** 클릭
3. 생성된 키 복사 (한 번만 표시됨!)

---

#### **⚙️ 앱 설정 (필수)**

| 변수명 | 값 | Environment | 설명 |
|--------|---|-------------|------|
| `APP_ENV` | `production` | Production | 환경 설정 |
| `DEBUG` | `false` | Production | 디버그 모드 비활성화 |

---

#### **🌐 CORS (선택 - Frontend 연동 시)**

| 변수명 | 값 | Environment | 설명 |
|--------|---|-------------|------|
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` | Production | 허용할 Origin (쉼표로 구분) |

---

### **Step 3: 환경변수 추가 방법**

Vercel Dashboard에서:

1. **Add New** 버튼 클릭
2. **Name:** 변수명 입력 (예: `SUPABASE_URL`)
3. **Value:** 값 입력 (예: `https://abc123.supabase.co`)
4. **Environments:** `Production` 체크 ✅
5. **Add** 버튼 클릭
6. 다음 변수로 반복...

---

### **Step 4: 재배포 (Redeploy)**

환경변수 추가 후 반드시 재배포:

**옵션 A: Vercel Dashboard에서**
1. **Deployments** 탭 클릭
2. 최신 배포 클릭
3. **⋮** (더보기) → **Redeploy** 클릭
4. **Redeploy** 확인

**옵션 B: Git Push로 자동 배포**
```bash
# 빈 커밋으로 배포 트리거
git commit --allow-empty -m "chore: trigger redeploy with env vars"
git push origin main
```

---

## 🔍 **배포 검증**

재배포 완료 후 (2-3분 소요):

### **1. Health Check**
```bash
curl https://your-app.vercel.app/health
```

**성공 응답:**
```json
{
  "status": "healthy",
  "service": "HomeSignal AI",
  "environment": "production"
}
```

**실패 시 emergency mode:**
```json
{
  "status": "emergency_mode",
  "message": "🚨 Application failed to initialize"
}
```
→ `/error/trace` 엔드포인트에서 상세 에러 확인

---

### **2. Vercel 빌드 로그 확인**

**성공 시 로그:**
```
[Vercel] Environment Variables Check:
  - SUPABASE_URL: ✓ SET
  - SUPABASE_KEY: ✓ SET
  - OPENAI_API_KEY: ✓ SET
  - APP_ENV: production

[Vercel] ✅ SUCCESS: FastAPI app loaded
[Vercel] ✅ Vercel serverless function ready
```

**실패 시 로그:**
```
[Vercel] ❌ CRITICAL ERROR: Failed to load FastAPI app
[Vercel] ValidationError: supabase_url - Field required
```
→ 환경변수 다시 확인

---

## 📋 **체크리스트**

배포 전 필수 확인:

- [ ] Vercel Dashboard → Environment Variables 접속
- [ ] `SUPABASE_URL` 추가 (Production 환경)
- [ ] `SUPABASE_KEY` 추가 (Production 환경)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` 추가 (Production 환경)
- [ ] `OPENAI_API_KEY` 추가 (Production 환경)
- [ ] `AI_PROVIDER=openai` 추가 (Production 환경)
- [ ] `APP_ENV=production` 추가 (Production 환경)
- [ ] `DEBUG=false` 추가 (Production 환경)
- [ ] Redeploy 실행
- [ ] `/health` 엔드포인트 테스트
- [ ] Vercel 빌드 로그에서 "✅ SUCCESS" 확인

---

## 🚀 **빠른 복사용 템플릿**

```bash
# Production 환경변수 (값은 실제 값으로 교체)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGc...your-anon-key...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...your-service-role-key...
OPENAI_API_KEY=sk-proj-...your-openai-key...
AI_PROVIDER=openai
APP_ENV=production
DEBUG=false
```

**⚠️ 주의:**
- 절대 이 값을 Git에 커밋하지 마세요!
- Vercel Dashboard에서만 설정하세요!

---

## 🆘 **트러블슈팅**

### **문제 1: "Field required" 에러 계속 발생**

**확인사항:**
1. Vercel Dashboard에서 환경변수 확인
2. Environment가 **Production**으로 설정되었는지 확인
3. 변수명 오타 확인 (대소문자 구분!)
4. 재배포 실행했는지 확인

### **문제 2: "Emergency mode" 응답**

```bash
# 상세 에러 확인
curl https://your-app.vercel.app/error/trace
```

→ Traceback에서 정확한 에러 원인 확인

### **문제 3: Placeholder URL 사용 경고**

**로그:**
```
🚨 CRITICAL: Production 환경에서 placeholder Supabase URL 사용 중!
```

**해결:**
- `SUPABASE_URL` 환경변수가 Vercel에 제대로 설정되지 않음
- Dashboard에서 다시 확인 및 재배포

---

## 📚 **참고 문서**

- [Vercel 환경변수 공식 문서](https://vercel.com/docs/projects/environment-variables)
- [Supabase API 키 관리](https://supabase.com/docs/guides/api/api-keys)
- 프로젝트 문서: `VERCEL_DEPLOYMENT_FIX.md`
- API 계약: `docs/07_API_Contract_Rules.md`

---

## 🎯 **요약**

1. ✅ Vercel Dashboard → Environment Variables
2. ✅ 8개 필수 환경변수 추가
3. ✅ Redeploy
4. ✅ `/health` 테스트
5. ✅ 성공 확인!

**예상 소요 시간:** 5분
**현재 상태:** ⚠️ 미완료 - 즉시 설정 필요!

---

**작성자:** Claude Code (Vercel Deployment Specialist)
**긴급도:** 🚨🚨🚨 CRITICAL
**다음 단계:** 지금 즉시 Vercel Dashboard에서 환경변수 설정!
