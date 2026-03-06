# Supabase 프로젝트 DB 현황

**프로젝트 ID:** `yietqoikdaqpwmmvamtv`  
**URL:** https://yietqoikdaqpwmmvamtv.supabase.co  

**대시보드 링크:**
- [Database Tables](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/database/tables)
- [Database Schemas](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/database/schemas)
- [SQL Editor](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new)

**마지막 조회:** 2026-03-06 (Supabase REST API 기준)

---

## 1. 연결 상태

| 항목 | 상태 |
|------|------|
| Supabase REST API (Client) | ✅ 연결됨 |
| PostgreSQL 직접 연결 | ⚠️ 환경 제한 (DNS/네트워크) |

---

## 2. 현재 테이블 현황

| 테이블 | 존재 여부 | 비고 |
|--------|-----------|------|
| `news_signals` | ❌ 없음 | 마이그레이션 미실행 |
| `houses_data` | ❌ 없음 | 마이그레이션 미실행 |
| `predictions` | ❌ 없음 | 마이그레이션 미실행 |

**→ 마이그레이션 `001_setup_pgvector.sql` 실행 필요**

> 💡 **DB 현황 재조회:** `uv run python scripts/inspect_db_via_api.py`

---

## 3. 예정 스키마 (마이그레이션 기준)

### 3.1 Extensions

| 확장 | 용도 |
|------|------|
| `vector` (pgvector) | 벡터 임베딩 저장 및 코사인 유사도 검색 |

### 3.2 테이블: `news_signals`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK, 기본값 gen_random_uuid() |
| title | TEXT | NOT NULL |
| content | TEXT | |
| url | TEXT | UNIQUE |
| keywords | TEXT[] | 기본값 '{}' |
| published_at | TIMESTAMPTZ | NOT NULL |
| embedding | VECTOR(1536) | OpenAI text-embedding-3-small |
| created_at | TIMESTAMPTZ | 기본값 NOW() |
| updated_at | TIMESTAMPTZ | 기본값 NOW() |

**인덱스:**
- `news_signals_embedding_idx` (IVFFLAT, vector_cosine_ops)
- `news_signals_published_at_idx` (published_at DESC)
- `news_signals_keywords_idx` (GIN)

### 3.3 테이블: `houses_data`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| complex_name | TEXT | NOT NULL |
| dong_name | TEXT | |
| price | NUMERIC(15,2) | NOT NULL, CHECK > 0 |
| contract_date | DATE | NOT NULL |
| sqft_living | INT | |
| yr_built | INT | |
| gu_name | TEXT | 기본값 '동대문구' |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**제약조건:** UNIQUE(complex_name, contract_date, price)

**인덱스:**
- `houses_data_contract_date_idx`
- `houses_data_dong_name_idx`
- `houses_data_complex_name_idx`

### 3.4 테이블: `predictions`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| region | TEXT | NOT NULL |
| period | TEXT | CHECK IN ('week', 'month') |
| horizon | INT | NOT NULL, CHECK > 0 |
| predictions | JSONB | NOT NULL |
| confidence_interval | JSONB | |
| model_name | TEXT | NOT NULL |
| model_version | TEXT | |
| created_at | TIMESTAMPTZ | |
| prediction_date | DATE | GENERATED (predictions->0->>'date') |

**인덱스:** `predictions_region_date_idx`

### 3.5 RPC 함수: `match_news_documents`

벡터 유사도 검색용 함수.

**파라미터:**
- `query_embedding` VECTOR(1536)
- `match_count` INT (기본 5)
- `match_threshold` FLOAT (기본 0.5)
- `filter_keywords` TEXT[] (선택)
- `filter_date_from` TIMESTAMPTZ (선택)
- `filter_date_to` TIMESTAMPTZ (선택)

**반환:** id, title, content, url, keywords, published_at, similarity

---

## 4. 마이그레이션 업데이트 (2026-03-06)

### 추가된 내용

1. **houses_data 컬럼 확장**
   - 추가: `bedrooms`, `bathrooms`, `sqft_lot`, `floors`, `waterfront`, `view`, `condition`, `sqft_above`, `sqft_basement`, `yr_renovated`
   - Ingest API 스키마와 완전 일치

2. **ai_predictions 테이블 추가**
   - Ingest API 전용 예측 결과 저장 테이블
   - 컬럼: `model_version`, `target_date`, `predicted_price`, `confidence_score`, `features_used`
   - `predictions` 테이블과 별도 (시계열 예측용 vs 단일 예측값용)

3. **RLS 정책 추가**
   - `ai_predictions`에도 SELECT 정책 적용

### service_role 인증 설정

- `.env`에 `SUPABASE_SERVICE_ROLE_KEY` 설정 완료
- `IngestService`와 `VectorDB`는 service_role 키로 INSERT/UPDATE 수행
- 일반 조회(SELECT)는 anon 키 사용

---

## 5. 다음 단계

1. **Supabase SQL Editor** 접속  
   https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new

2. **마이그레이션 실행**  
   `migrations/001_setup_pgvector.sql` 내용 전체 복사 후 실행

3. **확인**  
   - `uv run python scripts/inspect_db_via_api.py` 재실행  
   - 또는 [Database Tables](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/database/tables)에서 테이블 생성 확인
