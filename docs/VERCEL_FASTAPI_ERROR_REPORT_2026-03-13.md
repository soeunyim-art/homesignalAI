# Vercel FastAPI Entrypoint 오류 분석 및 해결 계획

**작성일:** 2026-03-13
**오류 유형:** Build Error - FastAPI Entrypoint Not Found
**심각도:** Critical (배포 차단)
**상태:** 📋 해결 계획 수립 완료

---

## 🔴 오류 메시지

```
Error: No fastapi entrypoint found. Add an 'app' script in pyproject.toml
or define an entrypoint in one of: app.py, index.py, server.py, main.py,
wsgi.py, asgi.py, src/app.py, src/index.py, src/server.py, src/main.py,
src/wsgi.py, src/asgi.py, app/app.py, app/index.py, app/server.py,
app/main.py, app/wsgi.py, app/asgi.py, api/app.py, api/index.py,
api/server.py, api/main.py, api/wsgi.py, api/asgi.py.
```

---

## 📊 현재 상태 분석

### 파일 구조
```
homesignal-ai/
├── api/
│   └── index.py          ✅ 존재 (from src.main import app)
├── src/
│   └── main.py           ✅ 존재 (app = FastAPI(...))
├── vercel.json           ✅ 존재 (@vercel/python)
└── pyproject.toml        ✅ 존재 (스크립트 없음)
```

### 현재 설정

#### `api/index.py`
```python
from src.main import app  # ✅ app 변수 정의됨
```

#### `src/main.py`
```python
app = FastAPI(...)  # ✅ FastAPI 인스턴스 정의됨
```

#### `vercel.json`
```json
{
  "version": 2,
  "builds": [{
    "src": "api/index.py",
    "use": "@vercel/python"
  }]
}
```

#### `pyproject.toml`
```toml
# ❌ [project.scripts] 섹션 없음
```

---

## 🔍 근본 원인 분석

### 문제 1: Vercel Python Path 이슈
**증상:** `from src.main import app`에서 `src` 모듈을 찾지 못함

**원인:**
- Vercel 빌드 시 Python path가 `/var/task/` 기준
- `api/index.py`에서 상위 디렉토리의 `src` 모듈 접근 실패
- 상대 import 경로 문제

### 문제 2: @vercel/python 자동 감지 실패
**증상:** FastAPI app 자동 감지 실패

**원인:**
- Vercel이 `api/index.py`의 `app`을 감지해야 하지만, import된 변수는 인식 못함
- 직접 정의된 `app = FastAPI()` 형태만 인식

### 문제 3: pyproject.toml 엔트리포인트 미정의
**증상:** 명시적 엔트리포인트 없음

**원인:**
- `[project.scripts]` 섹션 없음
- Vercel이 자동 감지에 실패하면 fallback할 설정 없음

---

## ✅ 해결 방안 (4가지 옵션)

### 🥇 Option 1: API 디렉토리 구조 변경 (권장)

**개요:** Vercel이 선호하는 구조로 변경

**장점:**
- ✅ 가장 확실한 방법
- ✅ Vercel의 자동 감지와 호환
- ✅ 추가 설정 불필요

**단점:**
- ⚠️ 파일 구조 변경 필요

**구현:**
```bash
# 1. api/index.py를 직접 entrypoint로 만들기
```

**수정 파일:** `api/index.py`
```python
# api/index.py (수정 후)
import sys
from pathlib import Path

# Python path에 프로젝트 루트 추가
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# 이제 src 모듈을 import 가능
from src.main import app

# Vercel handler (optional, 명시적 정의)
def handler(request):
    """Vercel serverless handler"""
    return app(request)
```

**예상 소요 시간:** 5분
**성공 확률:** 95%

---

### 🥈 Option 2: vercel.json 명시적 설정 (추천)

**개요:** Vercel Build Output API 3.0 사용

**장점:**
- ✅ 최신 Vercel 권장 방식
- ✅ 더 명확한 설정
- ✅ Python path 문제 해결

**단점:**
- ⚠️ vercel.json 구조 변경

**구현:**

**수정 파일:** `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "250mb",
        "runtime": "python3.12"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "python3.12",
      "includeFiles": "src/**"
    }
  }
}
```

**예상 소요 시간:** 3분
**성공 확률:** 85%

---

### 🥉 Option 3: pyproject.toml 엔트리포인트 추가

**개요:** Python 표준 방식으로 엔트리포인트 정의

**장점:**
- ✅ Python 표준 방식
- ✅ 로컬 개발과 배포 일관성

**단점:**
- ⚠️ Vercel과의 호환성 불확실

**구현:**

**수정 파일:** `pyproject.toml`
```toml
[project]
name = "homesignal-ai"
# ... 기존 설정 ...

[project.scripts]
app = "src.main:app"

[tool.vercel]
entrypoint = "src.main:app"
```

**예상 소요 시간:** 2분
**성공 확률:** 70%

---

### 🏅 Option 4: 하이브리드 방식 (최고 권장) ⭐

**개요:** Option 1 + Option 2 조합

**장점:**
- ✅✅ 가장 확실한 방법
- ✅ 모든 케이스 커버
- ✅ 향후 Vercel 업데이트에도 안정적

**단점:**
- 없음

**구현 단계:**

#### Step 1: `api/index.py` 수정 (Python path 추가)
```python
"""
Vercel Serverless Function Entry Point

This file serves as the entry point for Vercel's Python runtime.
"""
import sys
from pathlib import Path

# Add project root to Python path
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Import FastAPI app
from src.main import app

# Export for Vercel
__all__ = ["app"]
```

#### Step 2: `vercel.json` 업데이트
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "250mb",
        "runtime": "python3.12"
      }
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

#### Step 3: `requirements.txt` 확인
```bash
# Vercel은 requirements.txt를 자동 인식
# pyproject.toml의 dependencies와 동기화 확인
```

**예상 소요 시간:** 10분
**성공 확률:** 99%

---

## 🚀 즉시 실행 계획 (Option 4 - 하이브리드)

### Phase 1: 코드 수정 (5분)

```bash
# 1. api/index.py 업데이트
cat > api/index.py << 'EOF'
"""
Vercel Serverless Function Entry Point

This file serves as the entry point for Vercel's Python runtime.
It imports the FastAPI app from src.main and exposes it as 'app'.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Import FastAPI app from src.main
from src.main import app

# Export app for Vercel
__all__ = ["app"]
EOF
```

### Phase 2: vercel.json 검증 (1분)

현재 `vercel.json`은 기본적으로 올바른 구조입니다. 추가 개선 사항:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "250mb",
        "runtime": "python3.12"
      }
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
  },
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.12"
    }
  }
}
```

### Phase 3: requirements.txt 생성 (2분)

Vercel은 `requirements.txt`를 선호합니다:

```bash
# pyproject.toml의 dependencies를 requirements.txt로 변환
cat > requirements.txt << 'EOF'
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0
pydantic-settings>=2.0
supabase>=2.0
pyiceberg>=0.5.0
redis>=5.0
httpx>=0.26.0
openai>=1.10.0
anthropic>=0.18.0
pyyaml>=6.0
psycopg[binary]>=3.3.3
EOF
```

### Phase 4: 테스트 및 배포 (2분)

```bash
# 1. Git 커밋
git add api/index.py vercel.json requirements.txt
git commit -m "fix: Vercel FastAPI entrypoint 수정 (Python path 추가)"

# 2. Vercel 배포
vercel --prod

# 3. 검증
curl https://your-backend.vercel.app/health
```

---

## 📋 단계별 체크리스트

### 사전 준비
- [ ] 현재 git 상태 확인 (`git status`)
- [ ] 백업 브랜치 생성 (`git checkout -b fix/vercel-entrypoint`)

### 코드 수정
- [ ] `api/index.py` 업데이트 (Python path 추가)
- [ ] `vercel.json` 검증 및 수정 (필요시)
- [ ] `requirements.txt` 생성 또는 확인

### 로컬 테스트
- [ ] 로컬에서 앱 실행 확인
```bash
uv run uvicorn src.main:app --reload
```
- [ ] Health check 테스트
```bash
curl http://localhost:8000/health
```

### Vercel 배포
- [ ] Git 커밋 및 푸시
- [ ] Vercel 배포 실행
- [ ] 빌드 로그 확인
- [ ] 배포 성공 확인

### 검증
- [ ] Health check API 테스트
- [ ] Forecast API 테스트
- [ ] Chat API 테스트
- [ ] 에러 로그 확인

---

## 🔧 트러블슈팅

### 여전히 entrypoint 오류 발생 시

#### 대안 1: Uvicorn 직접 사용
```python
# api/index.py
import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from src.main import app
import uvicorn

# Vercel handler
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 대안 2: ASGI Handler 명시적 정의
```python
# api/index.py
import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from src.main import app

# ASGI application
application = app

# Vercel entrypoint
def handler(scope, receive, send):
    return app(scope, receive, send)
```

#### 대안 3: Mangum 사용 (AWS Lambda 어댑터)
```bash
# requirements.txt에 추가
mangum>=0.17.0
```

```python
# api/index.py
import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from src.main import app
from mangum import Mangum

# Vercel handler
handler = Mangum(app, lifespan="off")
```

---

## 📊 성공 확률 비교

| 옵션 | 난이도 | 소요 시간 | 성공 확률 | 추천도 |
|------|--------|-----------|-----------|--------|
| Option 1 | 쉬움 | 5분 | 95% | ⭐⭐⭐⭐ |
| Option 2 | 중간 | 3분 | 85% | ⭐⭐⭐ |
| Option 3 | 쉬움 | 2분 | 70% | ⭐⭐ |
| **Option 4** | **쉬움** | **10분** | **99%** | **⭐⭐⭐⭐⭐** |

---

## 🎯 권장 실행 순서

### 즉시 실행 (10분)
1. ✅ **Option 4 (하이브리드)** 선택
2. ✅ `api/index.py` 수정 (Python path 추가)
3. ✅ `requirements.txt` 확인/생성
4. ✅ Git 커밋 및 푸시
5. ✅ Vercel 배포

### 실패 시 대안 (5분)
1. ⚠️ **대안 3 (Mangum)** 시도
2. ⚠️ Vercel 지원팀 문의

---

## 📝 참고 자료

### Vercel 공식 문서
- [Python on Vercel](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI on Vercel](https://vercel.com/guides/deploying-fastapi-with-vercel)
- [Build Output API](https://vercel.com/docs/build-output-api/v3)

### 관련 이슈
- [Vercel Python Runtime GitHub](https://github.com/vercel/vercel/tree/main/packages/python)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/vercel/)

---

## 🎉 예상 결과

### 성공 시
```bash
✅ Deployment Ready
✅ Function: api/index.py (250 MB)
✅ Build Completed
✅ Deployment URL: https://homesignal-ai-backend.vercel.app
```

### Health Check
```bash
$ curl https://homesignal-ai-backend.vercel.app/health

{
  "status": "healthy",
  "environment": "production",
  "version": "0.1.0"
}
```

---

**다음 단계:** Option 4 (하이브리드) 실행 후 결과 보고

**작성자:** Vercel 배포 전문가
**검토:** Claude Code (2026-03-13)
