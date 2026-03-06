# 마이그레이션 실행 가이드

## 현재 상황

- `news_signals`, `houses_data`, `predictions` 테이블은 이미 생성됨
- `ai_predictions` 테이블이 누락됨
- `houses_data` 테이블의 확장 컬럼(bedrooms, bathrooms 등) 확인 필요

---

## 실행 방법 (3가지 옵션)

### Option 1: 전체 마이그레이션 재실행 (권장)

**가장 안전하고 확실한 방법**

1. [Supabase SQL Editor](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new) 접속

2. `migrations/001_setup_pgvector.sql` 파일 열기 (288줄 전체)

3. 전체 내용 복사 후 SQL Editor에 붙여넣기

4. **Run** 버튼 클릭

5. 결과 확인:
   - `IF NOT EXISTS` 덕분에 기존 테이블은 영향 없음
   - `ai_predictions` 테이블 새로 생성됨
   - `houses_data`에 누락된 컬럼이 있다면 에러 발생 (Option 3 필요)

---

### Option 2: ai_predictions만 추가

**빠른 해결이 필요한 경우**

1. [Supabase SQL Editor](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new) 접속

2. `migrations/002_add_ai_predictions_only.sql` 파일 내용 복사

3. SQL Editor에 붙여넣기 후 **Run**

4. 성공 메시지: `ai_predictions 테이블 생성 완료`

**주의:** houses_data 컬럼 확장은 별도로 Option 3 실행 필요

---

### Option 3: houses_data 컬럼 확장

**houses_data에 컬럼이 없는 경우**

1. [Supabase SQL Editor](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new) 접속

2. `migrations/003_add_houses_data_columns.sql` 파일 내용 복사

3. SQL Editor에 붙여넣기 후 **Run**

4. 각 컬럼별 추가 메시지 확인:
   - `bedrooms 컬럼 추가됨`
   - `bathrooms 컬럼 추가됨`
   - ... (10개 컬럼)

---

## 권장 실행 순서

```
1단계: Option 1 시도 (전체 재실행)
   ↓
2단계: 검증 (verify_migration.py)
   ↓
3단계: houses_data 컬럼 확인
   ↓ (컬럼 없으면)
4단계: Option 3 실행
```

---

## 검증 명령어

### 1. 테이블 존재 확인

```bash
uv run python scripts/verify_migration.py
```

**예상 출력:**
```
============================================================
마이그레이션 검증
============================================================
  [OK] news_signals: 존재
  [OK] houses_data: 존재
  [OK] predictions: 존재
  [OK] ai_predictions: 존재

============================================================
service_role 키 확인
============================================================
  [OK] SUPABASE_SERVICE_ROLE_KEY 설정됨
```

### 2. houses_data 컬럼 확인

**방법 A: Python 스크립트**
```bash
uv run python -c "from src.shared.database import get_supabase_client; c = get_supabase_client(); r = c.table('houses_data').select('*').limit(0).execute(); print('Columns:', list(r.data[0].keys()) if r.data else 'No data')"
```

**방법 B: SQL Editor에서 직접 확인**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'houses_data' 
ORDER BY ordinal_position;
```

**필수 컬럼 목록:**
- complex_name, dong_name, price, contract_date
- bedrooms, bathrooms, sqft_living, sqft_lot, floors
- waterfront, view, condition
- sqft_above, sqft_basement
- yr_built, yr_renovated
- gu_name, created_at, updated_at

---

## 문제 해결

### 에러: "table already exists"
- 정상 동작 (IF NOT EXISTS 덕분)
- 무시하고 계속 진행

### 에러: "column already exists"
- houses_data 컬럼이 이미 있는 경우
- Option 3 실행 불필요

### 에러: "permission denied"
- service_role 키로 로그인 필요
- 또는 Supabase 대시보드에서 직접 실행

### ai_predictions 여전히 없음
- Supabase 스키마 캐시 새로고침 필요
- 대시보드에서 Database > Tables 페이지 새로고침
- 또는 5분 대기 후 재확인

---

## 완료 체크리스트

- [ ] `ai_predictions` 테이블 생성됨
- [ ] `houses_data`에 10개 확장 컬럼 존재
- [ ] `verify_migration.py` 실행 시 4개 테이블 모두 [OK]
- [ ] RLS 정책 4개 테이블 모두 적용됨
- [ ] service_role 키 설정 확인됨

---

## 참고 문서

- [Supabase DB Status](./Supabase_DB_Status.md)
- [Migration Changes](./Migration_Changes_20260306.md)
- [마이그레이션 파일](../migrations/001_setup_pgvector.sql)
