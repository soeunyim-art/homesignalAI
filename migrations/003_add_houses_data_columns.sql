-- ============================================================================
-- HomeSignal AI - houses_data 컬럼 확장
-- ============================================================================
-- 목적: houses_data 테이블에 Ingest API가 사용하는 추가 컬럼 추가
-- 사용: 001 마이그레이션 실행 후 컬럼이 없는 경우
-- ============================================================================

-- 컬럼 추가 (이미 존재하면 에러 발생하지만 무시 가능)
DO $$
BEGIN
    -- bedrooms
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'bedrooms'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN bedrooms FLOAT;
        RAISE NOTICE 'bedrooms 컬럼 추가됨';
    END IF;

    -- bathrooms
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'bathrooms'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN bathrooms FLOAT;
        RAISE NOTICE 'bathrooms 컬럼 추가됨';
    END IF;

    -- sqft_lot
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'sqft_lot'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN sqft_lot INT;
        RAISE NOTICE 'sqft_lot 컬럼 추가됨';
    END IF;

    -- floors
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'floors'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN floors FLOAT;
        RAISE NOTICE 'floors 컬럼 추가됨';
    END IF;

    -- waterfront
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'waterfront'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN waterfront INT CHECK (waterfront IN (0, 1));
        RAISE NOTICE 'waterfront 컬럼 추가됨';
    END IF;

    -- view
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'view'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN view INT CHECK (view >= 0);
        RAISE NOTICE 'view 컬럼 추가됨';
    END IF;

    -- condition
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'condition'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN condition INT CHECK (condition >= 0);
        RAISE NOTICE 'condition 컬럼 추가됨';
    END IF;

    -- sqft_above
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'sqft_above'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN sqft_above INT;
        RAISE NOTICE 'sqft_above 컬럼 추가됨';
    END IF;

    -- sqft_basement
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'sqft_basement'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN sqft_basement INT;
        RAISE NOTICE 'sqft_basement 컬럼 추가됨';
    END IF;

    -- yr_renovated
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'houses_data' AND column_name = 'yr_renovated'
    ) THEN
        ALTER TABLE houses_data ADD COLUMN yr_renovated INT;
        RAISE NOTICE 'yr_renovated 컬럼 추가됨';
    END IF;

    RAISE NOTICE 'houses_data 컬럼 확장 완료';
END $$;
