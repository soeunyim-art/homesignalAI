-- ============================================================================
-- HomeSignal AI - ai_predictions 테이블 추가 (Option 2용)
-- ============================================================================
-- 목적: 001 마이그레이션에서 누락된 ai_predictions 테이블만 추가
-- 사용: 전체 재실행이 어려운 경우 이 파일만 실행
-- ============================================================================

-- ai_predictions 테이블 생성 (Ingest API 전용)
CREATE TABLE IF NOT EXISTS ai_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 예측 정보
    model_version TEXT NOT NULL,
    target_date DATE NOT NULL,
    predicted_price NUMERIC(15, 2) NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),

    -- 피처 메타데이터
    features_used JSONB,

    -- 관리 필드
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
