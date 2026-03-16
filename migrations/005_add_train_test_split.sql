-- ============================================================================
-- HomeSignal AI - Train/Test Split 및 계층화 그룹 컬럼 추가
-- ============================================================================
-- 목적: ml_training_features 테이블에 학습/평가 데이터 분할을 위한 컬럼 추가
-- 작성일: 2026-03-09
-- ============================================================================

-- 1. ml_training_features에 train_test_split 컬럼 추가
DO $$
BEGIN
    -- train_test_split 컬럼 추가
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ml_training_features' AND column_name = 'train_test_split'
    ) THEN
        ALTER TABLE ml_training_features 
        ADD COLUMN train_test_split TEXT CHECK (train_test_split IN ('train', 'test', 'validation'));
        RAISE NOTICE 'train_test_split 컬럼 추가됨';
    END IF;

    -- stratification_group 컬럼 추가
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ml_training_features' AND column_name = 'stratification_group'
    ) THEN
        ALTER TABLE ml_training_features 
        ADD COLUMN stratification_group TEXT;
        RAISE NOTICE 'stratification_group 컬럼 추가됨';
    END IF;
END $$;

-- 2. 조인 성능 최적화를 위한 인덱스 추가

-- houses_data: dong_name + contract_date 복합 인덱스
CREATE INDEX IF NOT EXISTS houses_data_dong_date_idx 
ON houses_data (dong_name, contract_date DESC);

-- news_signals: published_at + keywords 복합 인덱스
CREATE INDEX IF NOT EXISTS news_signals_published_keywords_idx 
ON news_signals (published_at DESC);

-- ml_training_features: train_test_split 필터링용 인덱스
CREATE INDEX IF NOT EXISTS ml_training_features_split_idx 
ON ml_training_features (train_test_split, region, period_date);

-- ml_training_features: stratification_group 인덱스
CREATE INDEX IF NOT EXISTS ml_training_features_stratification_idx 
ON ml_training_features (stratification_group);

-- 3. 헬퍼 함수: Train 데이터만 조회
CREATE OR REPLACE FUNCTION get_train_features(
    p_region TEXT,
    p_period_type TEXT,
    p_limit INT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    period_date DATE,
    region TEXT,
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
    season_wedding BOOLEAN,
    stratification_group TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mtf.id,
        mtf.period_date,
        mtf.region,
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
        mtf.season_wedding,
        mtf.stratification_group
    FROM ml_training_features mtf
    WHERE mtf.region = p_region
      AND mtf.period_type = p_period_type
      AND mtf.train_test_split = 'train'
    ORDER BY mtf.period_date ASC
    LIMIT p_limit;
END;
$$;

-- 4. 헬퍼 함수: Test 데이터만 조회
CREATE OR REPLACE FUNCTION get_test_features(
    p_region TEXT,
    p_period_type TEXT,
    p_limit INT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    period_date DATE,
    region TEXT,
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
    season_wedding BOOLEAN,
    stratification_group TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mtf.id,
        mtf.period_date,
        mtf.region,
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
        mtf.season_wedding,
        mtf.stratification_group
    FROM ml_training_features mtf
    WHERE mtf.region = p_region
      AND mtf.period_type = p_period_type
      AND mtf.train_test_split = 'test'
    ORDER BY mtf.period_date ASC
    LIMIT p_limit;
END;
$$;

-- 5. 헬퍼 함수: 분할 통계 조회
CREATE OR REPLACE FUNCTION get_split_statistics()
RETURNS TABLE (
    region TEXT,
    period_type TEXT,
    stratification_group TEXT,
    train_count BIGINT,
    test_count BIGINT,
    total_count BIGINT,
    train_ratio NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mtf.region,
        mtf.period_type,
        mtf.stratification_group,
        COUNT(*) FILTER (WHERE mtf.train_test_split = 'train') AS train_count,
        COUNT(*) FILTER (WHERE mtf.train_test_split = 'test') AS test_count,
        COUNT(*) AS total_count,
        ROUND(
            COUNT(*) FILTER (WHERE mtf.train_test_split = 'train')::NUMERIC / 
            NULLIF(COUNT(*), 0)::NUMERIC, 
            2
        ) AS train_ratio
    FROM ml_training_features mtf
    WHERE mtf.train_test_split IS NOT NULL
    GROUP BY mtf.region, mtf.period_type, mtf.stratification_group
    ORDER BY mtf.region, mtf.period_type, mtf.stratification_group;
END;
$$;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Train/Test Split 컬럼 및 인덱스 추가 완료';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '추가된 컬럼:';
    RAISE NOTICE '  - ml_training_features.train_test_split (train/test/validation)';
    RAISE NOTICE '  - ml_training_features.stratification_group (지역_가격분위)';
    RAISE NOTICE '';
    RAISE NOTICE '추가된 인덱스:';
    RAISE NOTICE '  - houses_data_dong_date_idx (dong_name, contract_date)';
    RAISE NOTICE '  - news_signals_published_keywords_idx (published_at)';
    RAISE NOTICE '  - ml_training_features_split_idx (train_test_split, region, period_date)';
    RAISE NOTICE '  - ml_training_features_stratification_idx (stratification_group)';
    RAISE NOTICE '';
    RAISE NOTICE '추가된 함수:';
    RAISE NOTICE '  - get_train_features(region, period_type, limit)';
    RAISE NOTICE '  - get_test_features(region, period_type, limit)';
    RAISE NOTICE '  - get_split_statistics()';
    RAISE NOTICE '';
    RAISE NOTICE '다음 단계: scripts/split_train_test_data.py 실행';
    RAISE NOTICE '============================================================================';
END $$;
