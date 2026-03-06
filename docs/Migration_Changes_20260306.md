# 마이그레이션 변경 사항 (2026-03-06)

## 개요

Supabase 테이블 스키마와 코드베이스 간 불일치를 해결하기 위한 마이그레이션 업데이트.

---

## 1. houses_data 테이블 컬럼 확장

### 추가된 컬럼

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| `bedrooms` | FLOAT | - | 침실 수 |
| `bathrooms` | FLOAT | - | 욕실 수 |
| `sqft_lot` | INT | - | 대지면적 (제곱미터) |
| `floors` | FLOAT | - | 층수 |
| `waterfront` | INT | CHECK (0 or 1) | 수변 조망 여부 |
| `view` | INT | CHECK (>= 0) | 조망권 등급 |
| `condition` | INT | CHECK (>= 0) | 건물 상태 |
| `sqft_above` | INT | - | 지상층 면적 |
| `sqft_basement` | INT | - | 지하층 면적 |
| `yr_renovated` | INT | - | 리모델링 연도 |

### 이유

Ingest API (`src/ingest/schemas.py` - `HouseDataItem`)에서 사용하는 컬럼이 마이그레이션에 누락되어 있어 INSERT 시 `column does not exist` 오류 발생.

---

## 2. ai_predictions 테이블 추가

### 스키마

```sql
CREATE TABLE IF NOT EXISTS ai_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version TEXT NOT NULL,
    target_date DATE NOT NULL,
    predicted_price NUMERIC(15, 2) NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    features_used JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 인덱스

- `ai_predictions_target_date_idx` (target_date DESC)
- `ai_predictions_model_version_idx` (model_version)

### 이유

Ingest API (`src/ingest/service.py` L334)가 `ai_predictions` 테이블에 INSERT하지만, 마이그레이션에는 `predictions` 테이블만 존재.

**테이블 구분:**
- `predictions`: 시계열 예측 결과 (Prophet/LightGBM, JSONB 배열)
- `ai_predictions`: 단일 예측값 저장 (Ingest API 전용)

---

## 3. RLS 정책 추가

### 추가된 정책

```sql
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read ai_predictions" ON ai_predictions;
CREATE POLICY "Allow public read ai_predictions" ON ai_predictions FOR SELECT USING (true);
```

### 인증 구조

| 역할 | 키 | 권한 | 사용처 |
|------|-----|------|--------|
| `anon` | SUPABASE_KEY | SELECT만 | 일반 API (forecast, chat, news) |
| `service_role` | SUPABASE_SERVICE_ROLE_KEY | 모든 권한 | Ingest API, VectorDB upsert |

---

## 4. 코드 변경 사항

### 4.1 settings.py

```python
# 추가
supabase_service_role_key: str | None = None
```

### 4.2 database.py

```python
# 수정
def get_supabase_client(use_service_role: bool = False) -> Client:
    if use_service_role:
        return create_client(settings.supabase_url, settings.supabase_service_role_key)
    return create_client(settings.supabase_url, settings.supabase_key)
```

### 4.3 ingest/service.py

```python
# 수정
def __init__(self, db: Client | None = None, ...):
    self.db = db or get_supabase_client(use_service_role=True)
```

### 4.4 shared/vector_db.py

```python
# 수정
def _get_client(self) -> Client:
    self._client = get_supabase_client(use_service_role=True)
```

---

## 5. 마이그레이션 실행 방법

1. Supabase SQL Editor 접속:  
   https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new

2. `migrations/001_setup_pgvector.sql` 전체 내용 복사 후 실행

3. 확인:
   ```bash
   uv run python scripts/inspect_db_via_api.py
   ```

---

## 6. 검증 체크리스트

- [ ] `news_signals` 테이블 생성 확인
- [ ] `houses_data` 테이블 생성 및 컬럼 확인 (bedrooms, bathrooms 등)
- [ ] `predictions` 테이블 생성 확인
- [ ] `ai_predictions` 테이블 생성 확인
- [ ] RPC 함수 `match_news_documents` 생성 확인
- [ ] RLS 정책 4개 테이블 모두 적용 확인

---

## 7. 참고 문서

- [Supabase DB Status](./Supabase_DB_Status.md)
- [마이그레이션 파일](../migrations/001_setup_pgvector.sql)
- [Ingest API 스키마](../src/ingest/schemas.py)
