# Cursor 작업 계획서 (2026-03-06)

**목적:** Supabase 마이그레이션 완료 후 코드베이스 동기화 및 크롤링 파이프라인 구축

**참조 문서:** `docs/Migration_Changes_20260306.md`

---

## 🎯 작업 목표

1. ✅ 마이그레이션 SQL 실행 (Supabase DB 스키마 구축)
2. 🔧 코드베이스를 마이그레이션 스키마와 동기화
3. 🚀 뉴스 크롤링 파이프라인 실행
4. ✅ 데이터 수집 검증 및 Vector DB 테스트

---

## 📋 Phase 1: 긴급 수정 사항 (우선순위: 🔴 High)

### 1.1 settings.py 수정

**파일:** `src/config/settings.py`

**작업:**
```python
# 추가 필요
class Settings(BaseSettings):
    # ... 기존 코드 ...

    # Supabase service_role key 추가 (INSERT/UPDATE 권한)
    supabase_service_role_key: str | None = None
```

**이유:** Ingest API와 VectorDB가 INSERT/UPDATE 작업 시 service_role 키 필요

**검증:**
```bash
# .env 파일에 이미 추가됨
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

---

### 1.2 database.py 수정

**파일:** `src/shared/database.py`

**작업:**
```python
@lru_cache
def get_supabase_client(use_service_role: bool = False) -> Client:
    """Supabase 클라이언트 반환

    Args:
        use_service_role: True일 경우 service_role 키 사용 (INSERT/UPDATE 권한)
    """
    settings = get_settings()

    # Mock mode 체크
    if "placeholder" in settings.supabase_url.lower():
        return MockSupabaseClient()

    try:
        if use_service_role:
            if not settings.supabase_service_role_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
            return create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
        else:
            return create_client(
                settings.supabase_url,
                settings.supabase_key
            )
    except Exception:
        return MockSupabaseClient()
```

**이유:** Ingest API는 service_role 키로 INSERT 권한 필요, 일반 API는 anon 키로 SELECT만 수행

---

### 1.3 ingest/service.py 수정

**파일:** `src/ingest/service.py`

**작업:**
```python
class IngestService:
    def __init__(
        self,
        db: Client | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        # service_role 키로 클라이언트 생성 (INSERT 권한 필요)
        self.db = db or get_supabase_client(use_service_role=True)
        self.embedding_service = embedding_service or EmbeddingService()
```

**이유:** Ingest API는 데이터 삽입 작업 수행, anon 키로는 RLS에 막혀 INSERT 불가

---

### 1.4 vector_db.py 수정

**파일:** `src/shared/vector_db.py`

**작업:**
```python
class SupabaseVectorDB(VectorDBInterface):
    def _get_client(self) -> Client:
        """Supabase 클라이언트 lazy loading (service_role 사용)"""
        if self._client is None:
            # 벡터 임베딩 upsert에 service_role 키 필요
            self._client = get_supabase_client(use_service_role=True)
        return self._client
```

**이유:** news_signals 테이블에 embedding 컬럼 INSERT/UPDATE 시 service_role 권한 필요

---

## 📋 Phase 2: 스키마 검증 (우선순위: 🟡 Medium)

### 2.1 DB 스키마 확인 스크립트 실행

**명령어:**
```bash
uv run python scripts/inspect_db_via_api.py
```

**예상 출력:**
- ✅ `news_signals` (11개 컬럼: id, title, content, url, keywords, published_at, embedding, created_at, updated_at)
- ✅ `houses_data` (17개 컬럼: 기존 + bedrooms, bathrooms, sqft_lot, floors, waterfront, view, condition, sqft_above, sqft_basement, yr_renovated)
- ✅ `predictions` (9개 컬럼)
- ✅ `ai_predictions` (7개 컬럼: id, model_version, target_date, predicted_price, confidence_score, features_used, created_at)

**검증 항목:**
- [ ] 4개 테이블 모두 존재
- [ ] `houses_data`에 새 컬럼 10개 추가 확인
- [ ] `ai_predictions` 테이블 존재 확인
- [ ] RPC 함수 `match_news_documents` 존재 확인

---

### 2.2 RLS 정책 확인

**Supabase Dashboard:**
https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/auth/policies

**확인 사항:**
- [ ] `news_signals`: "Allow public read news_signals" 정책 활성화
- [ ] `houses_data`: "Allow public read houses_data" 정책 활성화
- [ ] `predictions`: "Allow public read predictions" 정책 활성화
- [ ] `ai_predictions`: "Allow public read ai_predictions" 정책 활성화

---

## 📋 Phase 3: 크롤링 파이프라인 실행 (우선순위: 🟢 Ready)

### 3.1 테스트 크롤링 (Dry Run)

**명령어:**
```bash
uv run python -m src.crawler.cli crawl \
  -q "GTX-C 청량리" "동대문구 재개발" \
  --max-results 10 \
  --dry-run
```

**목적:** 크롤러 동작 확인 (DB 저장 없음)

**예상 출력:**
```
크롤링 결과
==================================================
총 크롤링:      10
본문 추출:      10
신규 삽입:      0 (dry-run)
중복 스킵:      0
실패:          0
소요 시간:      XX초
```

---

### 3.2 실제 크롤링 (초기 데이터 수집)

**명령어:**
```bash
uv run python -m src.crawler.cli crawl \
  -q "GTX-C 청량리" "동대문구 재개발" "이문휘경뉴타운" \
  --max-results 100 \
  --date-range 30
```

**목적:** 최근 30일 뉴스 100개 수집 및 news_signals 테이블 저장

**파라미터:**
- `-q`: 검색 키워드 (3개)
- `--max-results`: 쿼리당 최대 결과 수
- `--date-range`: 검색 기간 (일)

**예상 소요 시간:** 약 5-10분 (rate limiting: 10 req/min)

---

### 3.3 임베딩 생성 및 Vector DB 적재

**명령어:**
```bash
uv run python scripts/generate_embeddings.py
```

**목적:** news_signals 테이블의 title + content → OpenAI embedding 생성 후 UPDATE

**전제 조건:**
- [ ] `.env`에 `OPENAI_API_KEY` 설정 필요
- [ ] 크롤링으로 news_signals에 데이터 존재

**예상 출력:**
```
임베딩 생성 완료
==================================================
처리된 뉴스:    100
성공:          100
실패:          0
소요 시간:      XX초
```

---

### 3.4 Vector DB 검증

**명령어:**
```bash
uv run python scripts/generate_embeddings.py --verify-only
```

**목적:** embedding 컬럼에 NULL 값 없는지 확인

**또는 Python REPL:**
```python
from src.shared.vector_db import get_vector_db

vdb = get_vector_db()
results = vdb.search("GTX 청량리 개통", top_k=5)

for r in results:
    print(f"[{r.similarity:.3f}] {r.title}")
```

---

## 📋 Phase 4: Ingest API 테스트 (우선순위: 🔵 Optional)

### 4.1 뉴스 수동 삽입 테스트

**명령어:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest/news \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 뉴스",
    "content": "GTX-C 노선이 청량리에 개통됩니다.",
    "url": "https://example.com/test",
    "keywords": ["GTX", "청량리"],
    "published_at": "2026-03-06T10:00:00Z"
  }'
```

**예상 응답:**
```json
{
  "message": "뉴스 신호 1개 삽입 완료",
  "inserted": 1,
  "duplicates": 0
}
```

---

### 4.2 부동산 데이터 삽입 테스트

**명령어:**
```bash
curl -X POST http://localhost:8000/api/v1/ingest/houses \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{
      "complex_name": "청량리 롯데캐슬",
      "dong_name": "청량리동",
      "price": 850000000,
      "contract_date": "2026-02-15",
      "bedrooms": 3,
      "bathrooms": 2,
      "sqft_living": 84,
      "yr_built": 2018
    }]
  }'
```

---

## 🔍 Phase 5: 통합 테스트 (우선순위: 🟣 Final)

### 5.1 API 서버 실행

**명령어:**
```bash
uv run uvicorn src.main:app --reload
```

**접속:** http://localhost:8000/docs

---

### 5.2 Forecast API 테스트

**요청:**
```bash
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "region": "청량리동",
    "period": "week",
    "horizon": 12
  }'
```

**예상 응답:** Mock 데이터 또는 실제 예측 결과

---

### 5.3 Chat API 테스트 (RAG)

**요청:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "청량리 부동산 가격이 오를까요?",
    "session_id": "test-session"
  }'
```

**예상 동작:**
1. Vector DB에서 "청량리" 관련 뉴스 검색
2. Forecast API에서 예측값 조회
3. AI API (GPT-4o/Claude)로 답변 생성
4. 출처와 함께 응답 반환

---

## ✅ 체크리스트 (완료 시 체크)

### 긴급 수정 (Phase 1)
- [ ] `settings.py`에 `supabase_service_role_key` 추가
- [ ] `database.py`에 `use_service_role` 파라미터 구현
- [ ] `ingest/service.py`에서 `use_service_role=True` 사용
- [ ] `vector_db.py`에서 `use_service_role=True` 사용

### 스키마 검증 (Phase 2)
- [ ] `inspect_db_via_api.py` 실행 → 4개 테이블 확인
- [ ] `houses_data` 새 컬럼 10개 확인
- [ ] `ai_predictions` 테이블 존재 확인
- [ ] RLS 정책 4개 테이블 모두 활성화 확인

### 크롤링 (Phase 3)
- [ ] Dry-run 테스트 성공
- [ ] 실제 크롤링 100개 뉴스 수집 완료
- [ ] 임베딩 생성 완료 (OpenAI API 사용)
- [ ] Vector DB 검색 테스트 성공

### Ingest API (Phase 4)
- [ ] 뉴스 삽입 테스트 성공
- [ ] 부동산 데이터 삽입 테스트 성공

### 통합 테스트 (Phase 5)
- [ ] API 서버 정상 실행
- [ ] Forecast API 응답 확인
- [ ] Chat API (RAG) 응답 확인

---

## 🚨 주의사항

### 1. 환경 변수 필수 설정
```bash
# .env 파일 확인
SUPABASE_URL=https://yietqoikdaqpwmmvamtv.supabase.co
SUPABASE_KEY=eyJ...  # anon key (SELECT용)
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # service_role key (INSERT/UPDATE용)
OPENAI_API_KEY=sk-...  # 임베딩 생성용
```

### 2. Rate Limiting
- Google News 크롤러: 기본 10 req/min
- 대량 크롤링 시 IP 차단 주의

### 3. OpenAI API 비용
- text-embedding-3-small: $0.00002/1K tokens
- 100개 뉴스 × 평균 500 tokens = 약 $0.001

### 4. Mock Mode
- `SUPABASE_URL`에 "placeholder" 포함 시 자동으로 Mock 모드 활성화
- 실제 DB 테스트 시 반드시 실제 URL 사용

---

## 📚 참고 문서

| 문서 | 경로 |
|------|------|
| 마이그레이션 변경 사항 | `docs/Migration_Changes_20260306.md` |
| 마이그레이션 SQL | `migrations/001_setup_pgvector.sql` |
| Vector DB 설정 가이드 | `docs/12_Vector_DB_Setup_Guide.md` |
| Ingest API 스키마 | `src/ingest/schemas.py` |
| 크롤러 구조 | `src/crawler/` |
| 프로젝트 가이드 | `CLAUDE.md` |

---

## 🎯 다음 단계 (크롤링 완료 후)

1. **Prophet + LightGBM 모델 구현**
   - Mock ForecastService를 실제 시계열 모델로 교체
   - Rise point detection + news keyword 피처 통합

2. **국토교통부 API 연동**
   - 실거래가 데이터 자동 수집
   - houses_data 테이블 주기적 업데이트

3. **Redis 캐싱 구현**
   - Forecast API 응답 캐싱 (TTL: 1시간)
   - Chat API 응답 캐싱 (TTL: 30분)

4. **프로덕션 배포**
   - Docker 컨테이너화
   - 모니터링 및 로깅 설정

---

**작성일:** 2026-03-06
**작성자:** Claude Code
**버전:** 1.0
