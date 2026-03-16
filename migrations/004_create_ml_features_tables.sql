-- ============================================================================
-- HomeSignal AI - ML Training Features 테이블 생성
-- ============================================================================
-- 목적: Prophet + LightGBM 앙상블 모델 학습을 위한 통합 Feature 테이블
-- 작성일: 2026-03-09
-- ============================================================================

-- 1. ml_training_features 테이블 생성
CREATE TABLE IF NOT EXISTS ml_training_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 시계열 키
    period_date DATE NOT NULL,
    region TEXT NOT NULL,
    period_type TEXT NOT NULL CHECK (period_type IN ('week', 'month')),
    
    -- Target 변수 (예측 대상)
    avg_price NUMERIC(15, 2) NOT NULL,
    price_index FLOAT,
    transaction_count INT,
    
    -- 이동평균 피처
    ma_5_week FLOAT,
    ma_20_week FLOAT,
    
    -- 뉴스 키워드 빈도 피처 (주요 카테고리별)
    news_gtx_freq INT DEFAULT 0,
    news_redevelopment_freq INT DEFAULT 0,
    news_policy_freq INT DEFAULT 0,
    news_supply_freq INT DEFAULT 0,
    news_transport_freq INT DEFAULT 0,
    news_economic_freq INT DEFAULT 0,
    news_social_freq INT DEFAULT 0,
    news_location_freq INT DEFAULT 0,
    
    -- 이벤트 더미 변수
    event_gtx_announcement BOOLEAN DEFAULT FALSE,
    event_redevelopment_approval BOOLEAN DEFAULT FALSE,
    event_interest_rate_change BOOLEAN DEFAULT FALSE,
    event_loan_regulation BOOLEAN DEFAULT FALSE,
    event_sales_restriction BOOLEAN DEFAULT FALSE,
    
    -- 계절성 더미 변수
    season_school BOOLEAN DEFAULT FALSE,      -- 개학 (2-3월, 8-9월)
    season_moving BOOLEAN DEFAULT FALSE,      -- 이사 (1-2월, 12월)
    season_wedding BOOLEAN DEFAULT FALSE,     -- 결혼 (5월, 10월)
    
    -- 외부 경제 지표 (향후 확장)
    interest_rate FLOAT,
    unemployment_rate FLOAT,
    
    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 복합 유니크 제약 (같은 지역, 날짜, 기간 타입 중복 방지)
    CONSTRAINT unique_feature_row UNIQUE (region, period_date, period_type)
);

-- 2. ml_training_features 인덱스
CREATE INDEX IF NOT EXISTS ml_training_features_region_date_idx 
ON ml_training_features (region, period_date DESC);

CREATE INDEX IF NOT EXISTS ml_training_features_period_type_idx 
ON ml_training_features (period_type);

CREATE INDEX IF NOT EXISTS ml_training_features_period_date_idx 
ON ml_training_features (period_date DESC);

-- 3. policy_events 테이블 생성
CREATE TABLE IF NOT EXISTS policy_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    event_date DATE NOT NULL,
    event_type TEXT NOT NULL,
    event_name TEXT NOT NULL,
    description TEXT,
    impact_level TEXT CHECK (impact_level IN ('low', 'medium', 'high')),
    region TEXT,  -- NULL이면 전체 지역 적용
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. policy_events 인덱스
CREATE INDEX IF NOT EXISTS policy_events_date_idx 
ON policy_events (event_date DESC);

CREATE INDEX IF NOT EXISTS policy_events_type_idx 
ON policy_events (event_type);

CREATE INDEX IF NOT EXISTS policy_events_region_idx 
ON policy_events (region);

-- 5. ml_training_features 업데이트 트리거
DROP TRIGGER IF EXISTS update_ml_training_features_updated_at ON ml_training_features;
CREATE TRIGGER update_ml_training_features_updated_at
    BEFORE UPDATE ON ml_training_features
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 6. RLS 정책 설정
ALTER TABLE ml_training_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read ml_training_features" ON ml_training_features;
CREATE POLICY "Allow public read ml_training_features" 
ON ml_training_features FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow public read policy_events" ON policy_events;
CREATE POLICY "Allow public read policy_events" 
ON policy_events FOR SELECT USING (true);

-- 7. 헬퍼 함수: Feature 조회 (최신 N개 기간)
CREATE OR REPLACE FUNCTION get_latest_features(
    p_region TEXT,
    p_period_type TEXT,
    p_limit INT DEFAULT 52
)
RETURNS TABLE (
    period_date DATE,
    avg_price NUMERIC,
    ma_5_week FLOAT,
    ma_20_week FLOAT,
    news_gtx_freq INT,
    news_redevelopment_freq INT,
    news_policy_freq INT,
    news_supply_freq INT,
    news_transport_freq INT,
    news_economic_freq INT,
    news_social_freq INT,
    news_location_freq INT,
    event_gtx_announcement BOOLEAN,
    event_redevelopment_approval BOOLEAN,
    event_interest_rate_change BOOLEAN,
    event_loan_regulation BOOLEAN,
    event_sales_restriction BOOLEAN,
    season_school BOOLEAN,
    season_moving BOOLEAN,
    season_wedding BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mtf.period_date,
        mtf.avg_price,
        mtf.ma_5_week,
        mtf.ma_20_week,
        mtf.news_gtx_freq,
        mtf.news_redevelopment_freq,
        mtf.news_policy_freq,
        mtf.news_supply_freq,
        mtf.news_transport_freq,
        mtf.news_economic_freq,
        mtf.news_social_freq,
        mtf.news_location_freq,
        mtf.event_gtx_announcement,
        mtf.event_redevelopment_approval,
        mtf.event_interest_rate_change,
        mtf.event_loan_regulation,
        mtf.event_sales_restriction,
        mtf.season_school,
        mtf.season_moving,
        mtf.season_wedding
    FROM ml_training_features mtf
    WHERE mtf.region = p_region
      AND mtf.period_type = p_period_type
    ORDER BY mtf.period_date DESC
    LIMIT p_limit;
END;
$$;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'ML Training Features 테이블 생성 완료';
    RAISE NOTICE '- ml_training_features: 시계열 Feature 통합 테이블';
    RAISE NOTICE '- policy_events: 정책 이벤트 마스터 데이터';
    RAISE NOTICE '다음 단계: scripts/generate_ml_features.py 실행';
END $$;
