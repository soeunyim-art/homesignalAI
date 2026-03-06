# 🚀 Supabase SQL Editor에서 실행할 SQL

## 실행 방법

1. **[Supabase SQL Editor 열기](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new)** ← 클릭

2. 아래 SQL 전체 복사

3. SQL Editor에 붙여넣기

4. **Run** 버튼 클릭

---

## SQL (ai_predictions 테이블 생성)

```sql
-- ============================================================================
-- ai_predictions 테이블 생성 (Ingest API 전용)
-- ============================================================================

-- 테이블 생성
CREATE TABLE IF NOT EXISTS ai_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version TEXT NOT NULL,
    target_date DATE NOT NULL,
    predicted_price NUMERIC(15, 2) NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    features_used JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS ai_predictions_target_date_idx
ON ai_predictions (target_date DESC);

CREATE INDEX IF NOT EXISTS ai_predictions_model_version_idx
ON ai_predictions (model_version);

-- RLS 정책 설정
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read ai_predictions" ON ai_predictions;
CREATE POLICY "Allow public read ai_predictions" ON ai_predictions FOR SELECT USING (true);

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'ai_predictions 테이블 생성 완료';
END $$;
```

---

## 실행 후 확인

터미널에서 실행:

```bash
uv run python scripts/verify_migration.py
```

**예상 결과:**
```
[OK] news_signals: 존재
[OK] houses_data: 존재
[OK] predictions: 존재
[OK] ai_predictions: 존재  ← 이제 OK로 표시됨
[OK] SUPABASE_SERVICE_ROLE_KEY 설정됨
[OK] 모든 검증 통과
```

---

## 문제 해결

### "table already exists" 에러
- 정상입니다 (IF NOT EXISTS 덕분)
- 무시하고 계속 진행

### "permission denied" 에러
- SQL Editor에서 로그인 상태 확인
- 또는 Project Settings에서 권한 확인

### 여전히 테이블이 없음
- 브라우저 새로고침 (Ctrl+F5)
- 5분 대기 후 재확인
- Database > Tables 페이지에서 직접 확인

---

## 대체 방법: 전체 마이그레이션 재실행

위 SQL로 해결되지 않으면:

1. `migrations/001_setup_pgvector.sql` 파일 열기 (288줄)
2. 전체 복사
3. [SQL Editor](https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new)에 붙여넣기
4. Run 실행

`IF NOT EXISTS` 덕분에 기존 테이블은 영향 없고, 누락된 것만 생성됩니다.
