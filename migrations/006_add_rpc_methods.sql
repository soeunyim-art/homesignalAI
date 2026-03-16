-- ============================================================================
-- HomeSignal AI - 핵심 RPC 메서드 추가
-- ============================================================================
-- 목적: 시계열 집계, 키워드 빈도, 예측 조회, ML Feature, 정책 이벤트,
--        대시보드 요약을 위한 DB 레벨 RPC 함수
-- 작성일: 2026-03-09
-- 선행: 001_setup_pgvector.sql, 004_create_ml_features_tables.sql,
--        005_add_train_test_split.sql
-- ============================================================================


-- ============================================================================
-- 1. aggregate_houses_time_series
--    부동산 거래 데이터를 주/월 단위로 집계하여 시계열 생성
-- ============================================================================
CREATE OR REPLACE FUNCTION aggregate_houses_time_series(
    p_region TEXT,
    p_period_type TEXT DEFAULT 'week',
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL,
    p_limit INT DEFAULT 104
)
RETURNS TABLE (
    period_date DATE,
    avg_price NUMERIC,
    min_price NUMERIC,
    max_price NUMERIC,
    transaction_count BIGINT,
    price_index FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_start DATE;
    v_end DATE;
    v_base_price NUMERIC;
BEGIN
    v_start := COALESCE(p_start_date, CURRENT_DATE - INTERVAL '2 years');
    v_end   := COALESCE(p_end_date, CURRENT_DATE);

    -- 기간별 집계 (CTE)
    RETURN QUERY
    WITH bucketed AS (
        SELECT
            CASE
                WHEN p_period_type = 'week'  THEN DATE_TRUNC('week',  hd.contract_date)::DATE
                WHEN p_period_type = 'month' THEN DATE_TRUNC('month', hd.contract_date)::DATE
                ELSE DATE_TRUNC('month', hd.contract_date)::DATE
            END AS bucket,
            hd.price
        FROM houses_data hd
        WHERE hd.contract_date BETWEEN v_start AND v_end
          AND (
              p_region = '전체'
              OR p_region = '동대문구'
              OR hd.dong_name = p_region
              OR hd.complex_name ILIKE '%' || p_region || '%'
          )
    ),
    aggregated AS (
        SELECT
            b.bucket                         AS period_date,
            ROUND(AVG(b.price), 2)           AS avg_price,
            MIN(b.price)                     AS min_price,
            MAX(b.price)                     AS max_price,
            COUNT(*)                         AS transaction_count
        FROM bucketed b
        GROUP BY b.bucket
        ORDER BY b.bucket ASC
    ),
    base AS (
        SELECT a.avg_price AS base_price
        FROM aggregated a
        ORDER BY a.period_date ASC
        LIMIT 1
    )
    SELECT
        a.period_date,
        a.avg_price,
        a.min_price,
        a.max_price,
        a.transaction_count,
        CASE
            WHEN base.base_price IS NOT NULL AND base.base_price > 0
            THEN ROUND((a.avg_price / base.base_price * 100)::NUMERIC, 2)::FLOAT
            ELSE NULL
        END AS price_index
    FROM aggregated a
    CROSS JOIN base
    ORDER BY a.period_date DESC
    LIMIT p_limit;
END;
$$;


-- ============================================================================
-- 2. get_news_keyword_frequency
--    키워드별 뉴스 출현 빈도 집계 (상승 시점 윈도우 지원)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_news_keyword_frequency(
    p_keywords TEXT[],
    p_start_date TIMESTAMPTZ DEFAULT NULL,
    p_end_date TIMESTAMPTZ DEFAULT NULL,
    p_rise_point_windows JSONB DEFAULT NULL
)
RETURNS TABLE (
    keyword TEXT,
    frequency BIGINT,
    impact_score FLOAT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_start TIMESTAMPTZ;
    v_end   TIMESTAMPTZ;
    v_total BIGINT;
BEGIN
    IF p_rise_point_windows IS NOT NULL THEN
        RETURN QUERY
        WITH windowed_news AS (
            SELECT ns.id, unnest(ns.keywords) AS kw
            FROM news_signals ns
            INNER JOIN LATERAL (
                SELECT
                    (w->>'start')::TIMESTAMPTZ AS ws,
                    (w->>'end')::TIMESTAMPTZ   AS we
                FROM jsonb_array_elements(p_rise_point_windows) AS w
            ) windows ON ns.published_at BETWEEN windows.ws AND windows.we
            WHERE ns.keywords && p_keywords
        ),
        total AS (
            SELECT COUNT(DISTINCT id) AS cnt FROM windowed_news
        )
        SELECT
            wn.kw                                                        AS keyword,
            COUNT(*)                                                     AS frequency,
            ROUND((COUNT(*)::FLOAT / GREATEST(t.cnt, 1)) * 100, 2)      AS impact_score
        FROM windowed_news wn
        CROSS JOIN total t
        WHERE wn.kw = ANY(p_keywords)
        GROUP BY wn.kw, t.cnt
        ORDER BY frequency DESC;
    ELSE
        v_start := COALESCE(p_start_date, CURRENT_TIMESTAMP - INTERVAL '30 days');
        v_end   := COALESCE(p_end_date,   CURRENT_TIMESTAMP);

        SELECT COUNT(*) INTO v_total
        FROM news_signals
        WHERE published_at BETWEEN v_start AND v_end;

        RETURN QUERY
        SELECT
            kw.keyword                                                      AS keyword,
            COUNT(ns.id)                                                    AS frequency,
            ROUND((COUNT(ns.id)::FLOAT / GREATEST(v_total, 1)) * 100, 2)   AS impact_score
        FROM unnest(p_keywords) AS kw(keyword)
        LEFT JOIN news_signals ns
            ON kw.keyword = ANY(ns.keywords)
           AND ns.published_at BETWEEN v_start AND v_end
        GROUP BY kw.keyword
        ORDER BY frequency DESC;
    END IF;
END;
$$;


-- ============================================================================
-- 3. get_latest_predictions
--    특정 지역의 최신 예측 결과를 개별 행으로 펼쳐서 반환
-- ============================================================================
CREATE OR REPLACE FUNCTION get_latest_predictions(
    p_region TEXT,
    p_period TEXT DEFAULT 'week',
    p_horizon INT DEFAULT 12
)
RETURNS TABLE (
    prediction_date DATE,
    predicted_price NUMERIC,
    lower_bound NUMERIC,
    upper_bound NUMERIC,
    model_name TEXT,
    model_version TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH latest AS (
        SELECT
            p.id,
            p.predictions,
            p.confidence_interval,
            p.model_name,
            p.model_version,
            p.created_at
        FROM predictions p
        WHERE p.region  = p_region
          AND p.period  = p_period
          AND p.horizon = p_horizon
        ORDER BY p.created_at DESC
        LIMIT 1
    )
    SELECT
        (pred.val->>'date')::DATE                   AS prediction_date,
        (pred.val->>'value')::NUMERIC               AS predicted_price,
        (ci.val->>'lower')::NUMERIC                 AS lower_bound,
        (ci.val->>'upper')::NUMERIC                 AS upper_bound,
        l.model_name,
        l.model_version,
        (pred.val->>'confidence')::FLOAT            AS confidence_score,
        l.created_at
    FROM latest l
    CROSS JOIN LATERAL jsonb_array_elements(l.predictions)
        WITH ORDINALITY AS pred(val, idx)
    LEFT JOIN LATERAL jsonb_array_elements(COALESCE(l.confidence_interval, '[]'::jsonb))
        WITH ORDINALITY AS ci(val, idx)
        ON pred.idx = ci.idx
    ORDER BY prediction_date ASC;
END;
$$;


-- ============================================================================
-- 4. get_ml_features_with_news
--    ML 학습용 Feature + 뉴스 빈도 결합 조회
-- ============================================================================
CREATE OR REPLACE FUNCTION get_ml_features_with_news(
    p_region TEXT,
    p_period_type TEXT DEFAULT 'week',
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
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
    season_wedding BOOLEAN,
    transaction_count INT,
    train_test_split TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_start DATE;
    v_end   DATE;
BEGIN
    v_start := COALESCE(p_start_date, CURRENT_DATE - INTERVAL '2 years');
    v_end   := COALESCE(p_end_date,   CURRENT_DATE);

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
        mtf.season_wedding,
        mtf.transaction_count,
        mtf.train_test_split
    FROM ml_training_features mtf
    WHERE mtf.region      = p_region
      AND mtf.period_type = p_period_type
      AND mtf.period_date BETWEEN v_start AND v_end
    ORDER BY mtf.period_date ASC;
END;
$$;


-- ============================================================================
-- 5. get_policy_events_in_range
--    특정 기간 내 정책 이벤트 조회 (지역/이벤트 타입 필터)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_policy_events_in_range(
    p_start_date DATE,
    p_end_date DATE,
    p_region TEXT DEFAULT NULL,
    p_event_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    event_date DATE,
    event_type TEXT,
    event_name TEXT,
    description TEXT,
    impact_level TEXT,
    region TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pe.id,
        pe.event_date,
        pe.event_type,
        pe.event_name,
        pe.description,
        pe.impact_level,
        pe.region
    FROM policy_events pe
    WHERE pe.event_date BETWEEN p_start_date AND p_end_date
      AND (p_region IS NULL OR pe.region IS NULL OR pe.region = p_region)
      AND (p_event_types IS NULL OR pe.event_type = ANY(p_event_types))
    ORDER BY pe.event_date DESC, pe.impact_level DESC;
END;
$$;


-- ============================================================================
-- 6. get_dashboard_summary
--    대시보드용 요약 통계 (가격, 변동률, 뉴스 수, 예측)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_dashboard_summary(
    p_region TEXT,
    p_period_type TEXT DEFAULT 'week'
)
RETURNS TABLE (
    latest_avg_price NUMERIC,
    price_change_pct FLOAT,
    latest_transaction_count INT,
    recent_news_count BIGINT,
    top_keywords TEXT[],
    trend_direction TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_latest_price NUMERIC;
    v_prev_price   NUMERIC;
    v_tx_count     INT;
    v_news_count   BIGINT;
    v_top_kw       TEXT[];
    v_change       FLOAT;
    v_direction    TEXT;
BEGIN
    -- 최신 기간 가격
    SELECT mtf.avg_price, mtf.transaction_count
    INTO v_latest_price, v_tx_count
    FROM ml_training_features mtf
    WHERE mtf.region = p_region AND mtf.period_type = p_period_type
    ORDER BY mtf.period_date DESC
    LIMIT 1;

    -- 직전 기간 가격
    SELECT mtf.avg_price
    INTO v_prev_price
    FROM ml_training_features mtf
    WHERE mtf.region = p_region AND mtf.period_type = p_period_type
    ORDER BY mtf.period_date DESC
    OFFSET 1
    LIMIT 1;

    -- 변경률 계산 (Zero Division 방지)
    IF v_prev_price IS NOT NULL AND v_prev_price > 0 THEN
        v_change := ROUND(((v_latest_price - v_prev_price) / NULLIF(v_prev_price, 0) * 100)::NUMERIC, 2)::FLOAT;
    ELSE
        v_change := NULL;
    END IF;

    -- 트렌드 방향
    IF v_change IS NULL THEN
        v_direction := 'unknown';
    ELSIF v_change > 1.0 THEN
        v_direction := 'rising';
    ELSIF v_change < -1.0 THEN
        v_direction := 'falling';
    ELSE
        v_direction := 'stable';
    END IF;

    -- 최근 7일 뉴스 수
    SELECT COUNT(*) INTO v_news_count
    FROM news_signals
    WHERE published_at >= CURRENT_TIMESTAMP - INTERVAL '7 days';

    -- 최근 30일 인기 키워드 Top 5
    SELECT ARRAY_AGG(sub.keyword ORDER BY sub.freq DESC)
    INTO v_top_kw
    FROM (
        SELECT unnest(ns.keywords) AS keyword, COUNT(*) AS freq
        FROM news_signals ns
        WHERE ns.published_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
        GROUP BY keyword
        ORDER BY freq DESC
        LIMIT 5
    ) sub;

    RETURN QUERY
    SELECT
        v_latest_price   AS latest_avg_price,
        v_change         AS price_change_pct,
        v_tx_count       AS latest_transaction_count,
        v_news_count     AS recent_news_count,
        v_top_kw         AS top_keywords,
        v_direction      AS trend_direction;
END;
$$;


-- ============================================================================
-- 완료 메시지
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'RPC 메서드 추가 완료 (006_add_rpc_methods.sql)';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE '추가된 RPC 함수:';
    RAISE NOTICE '  1. aggregate_houses_time_series(region, period_type, start, end, limit)';
    RAISE NOTICE '     → 부동산 거래 주/월 단위 시계열 집계';
    RAISE NOTICE '  2. get_news_keyword_frequency(keywords, start, end, rise_windows)';
    RAISE NOTICE '     → 키워드별 뉴스 빈도 + impact_score';
    RAISE NOTICE '  3. get_latest_predictions(region, period, horizon)';
    RAISE NOTICE '     → 최신 예측 결과 펼쳐서 조회';
    RAISE NOTICE '  4. get_ml_features_with_news(region, period_type, start, end)';
    RAISE NOTICE '     → ML Feature + 뉴스 빈도 결합';
    RAISE NOTICE '  5. get_policy_events_in_range(start, end, region, event_types)';
    RAISE NOTICE '     → 정책 이벤트 기간/지역 필터';
    RAISE NOTICE '  6. get_dashboard_summary(region, period_type)';
    RAISE NOTICE '     → 대시보드 요약 통계';
    RAISE NOTICE '';
    RAISE NOTICE '다음 단계:';
    RAISE NOTICE '  - DataRepository 인터페이스에 새 메서드 추가';
    RAISE NOTICE '  - SupabaseDataRepository에서 RPC 호출로 전환';
    RAISE NOTICE '============================================================================';
END $$;
