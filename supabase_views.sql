-- ================================================================
-- HomeSignal AI — Supabase SQL 뷰 생성
-- Supabase > SQL Editor 에서 순서대로 실행
-- ================================================================


-- ────────────────────────────────────────
-- View 1: 동별 월간 매매 집계
-- ────────────────────────────────────────
CREATE OR REPLACE VIEW v_monthly_trade AS
SELECT
    deal_year,
    deal_month,
    dong,
    COUNT(*)                                                          AS trade_count,
    ROUND(AVG(price_10k)::NUMERIC, 0)                                AS avg_price_10k,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY price_10k)::NUMERIC, 0)                          AS median_price_10k,
    ROUND((AVG(price_10k) / NULLIF(AVG(area), 0))::NUMERIC, 1)      AS avg_price_per_sqm,
    ROUND(AVG(area)::NUMERIC, 2)                                     AS avg_area
FROM apt_trade
WHERE deal_year > 0
  AND price_10k > 0
GROUP BY deal_year, deal_month, dong;


-- ────────────────────────────────────────
-- View 2: 동별 월간 전세 집계
-- ────────────────────────────────────────
CREATE OR REPLACE VIEW v_monthly_jeonse AS
SELECT
    deal_year,
    deal_month,
    dong,
    COUNT(*)                                                          AS jeonse_count,
    ROUND(AVG(deposit_10k)::NUMERIC, 0)                              AS avg_deposit_10k,
    ROUND((AVG(deposit_10k) / NULLIF(AVG(area), 0))::NUMERIC, 1)    AS avg_deposit_per_sqm
FROM apt_rent
WHERE contract_type = '전세'
  AND deposit_10k > 0
  AND deal_year > 0
GROUP BY deal_year, deal_month, dong;


-- ────────────────────────────────────────
-- View 3: 동별 월간 월세 집계
-- ────────────────────────────────────────
CREATE OR REPLACE VIEW v_monthly_wolse AS
SELECT
    deal_year,
    deal_month,
    dong,
    COUNT(*)                                                          AS wolse_count,
    ROUND(AVG(monthly_rent_10k)::NUMERIC, 1)                         AS avg_monthly_rent_10k,
    ROUND(AVG(deposit_10k)::NUMERIC, 0)                              AS avg_wolse_deposit_10k
FROM apt_rent
WHERE contract_type = '월세'
  AND monthly_rent_10k > 0
  AND deal_year > 0
GROUP BY deal_year, deal_month, dong;


-- ────────────────────────────────────────
-- View 4: 전국 거시 뉴스 월별 집계
--   금리/규제/완화/GTX/재개발 시그널
--   (5개 구 공통 피처 — 정보 누수 방지를 위해
--    v_model_features에서 1개월 lag로 JOIN)
-- ────────────────────────────────────────
CREATE OR REPLACE VIEW v_monthly_news_macro AS
SELECT
    EXTRACT(YEAR  FROM published_at)::INT  AS news_year,
    EXTRACT(MONTH FROM published_at)::INT  AS news_month,
    COUNT(*)                               AS total_news,
    -- 규제/긴축 시그널 (악재)
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['규제','대출규제','LTV','DSR','금리인상','긴축','거래절벽']
    )                                      AS regulation_news,
    -- 완화/호재 시그널
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['금리인하','규제완화','완화','부양','회복']
    )                                      AS easing_news,
    -- GTX/교통 (5개 구 직접 영향)
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['GTX','GTX-C','지하철','철도','트램']
    )                                      AS transport_news,
    -- 재개발/뉴타운 (동북권 집중 이슈)
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['재개발','뉴타운','재건축','정비사업','도시재생']
    )                                      AS redevelop_news,
    -- 방향성 지수: (호재 - 악재) / 전체 (-1 ~ +1)
    ROUND(
        (COUNT(*) FILTER (WHERE keywords && ARRAY['금리인하','규제완화','재개발','GTX','호재','상승','뉴타운'])
       - COUNT(*) FILTER (WHERE keywords && ARRAY['금리인상','규제','대출규제','하락','위기','긴축']))
       ::NUMERIC / NULLIF(COUNT(*), 0), 3
    )                                      AS macro_sentiment
FROM news_signals
GROUP BY news_year, news_month;


-- ────────────────────────────────────────
-- View 5: 구별 로컬 뉴스 월별 집계
--   title에서 5개 구 / 주요 동 이름 추출
--   (구별 차별화 피처)
-- ────────────────────────────────────────
CREATE OR REPLACE VIEW v_monthly_news_local AS
SELECT
    EXTRACT(YEAR  FROM published_at)::INT  AS news_year,
    EXTRACT(MONTH FROM published_at)::INT  AS news_month,
    gu_name,
    COUNT(*)                               AS local_news_count,
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['재개발','뉴타운','재건축','정비사업']
    )                                      AS local_redevelop_count,
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['규제','제한','불허']
    )                                      AS local_regulation_count,
    COUNT(*) FILTER (
        WHERE keywords && ARRAY['GTX','GTX-C','지하철','역세권']
    )                                      AS local_transport_count
FROM (
    SELECT
        ns.*,
        CASE
            WHEN title LIKE '%동대문%' OR title LIKE '%이문동%' OR title LIKE '%장안동%'
              OR title LIKE '%답십리%' OR title LIKE '%전농%' OR title LIKE '%휘경%'
              OR title LIKE '%청량리%' OR title LIKE '%제기동%' OR title LIKE '%용두동%'
                THEN '동대문구'
            WHEN title LIKE '%성북%' OR title LIKE '%길음%' OR title LIKE '%장위%'
              OR title LIKE '%돈암%' OR title LIKE '%석관%' OR title LIKE '%종암%'
              OR title LIKE '%월곡%' OR title LIKE '%정릉%'
                THEN '성북구'
            WHEN title LIKE '%중랑%' OR title LIKE '%면목%' OR title LIKE '%망우%'
              OR title LIKE '%신내%' OR title LIKE '%묵동%' OR title LIKE '%상봉%'
              OR title LIKE '%중화%' OR title LIKE '%태릉%'
                THEN '중랑구'
            WHEN title LIKE '%강북%' OR title LIKE '%미아%' OR title LIKE '%수유%'
              OR title LIKE '%번동%' OR title LIKE '%우이%' OR title LIKE '%삼각산%'
                THEN '강북구'
            WHEN title LIKE '%도봉%' OR title LIKE '%창동%' OR title LIKE '%쌍문%'
              OR title LIKE '%방학%' OR title LIKE '%노원%'
                THEN '도봉구'
            ELSE NULL
        END AS gu_name
    FROM news_signals ns
) sub
WHERE gu_name IS NOT NULL
GROUP BY news_year, news_month, gu_name;


-- ────────────────────────────────────────
-- View 6: 모델 피처 통합 뷰
--   매매 + 전세 + 월세 + 금리 3종
--   + 전국 거시 뉴스 (1개월 lag)
--   + 구별 로컬 뉴스 (1개월 lag)
-- ────────────────────────────────────────
CREATE OR REPLACE VIEW v_model_features AS
-- 동 → 구 매핑 CTE (dongs 테이블 gu_name 컬럼 활용)
WITH dong_gu AS (
    SELECT dong_name, gu_name FROM dongs WHERE gu_name IS NOT NULL AND gu_name <> ''
)
SELECT
    t.deal_year,
    t.deal_month,
    t.dong,
    -- 매매
    t.trade_count,
    t.avg_price_10k,
    t.median_price_10k,
    t.avg_price_per_sqm,
    t.avg_area,
    -- 전세
    j.jeonse_count,
    j.avg_deposit_10k       AS avg_jeonse_10k,
    j.avg_deposit_per_sqm   AS avg_jeonse_per_sqm,
    -- 월세
    w.wolse_count,
    w.avg_monthly_rent_10k,
    -- 금리 3종
    ir_base.rate            AS rate_base,
    ir_cd.rate              AS rate_cd,
    ir_bond.rate            AS rate_bond3y,
    -- 전국 거시 뉴스 (전달 뉴스: 1개월 lag)
    nm.total_news,
    nm.regulation_news,
    nm.easing_news,
    nm.transport_news,
    nm.redevelop_news,
    nm.macro_sentiment,
    -- 구별 로컬 뉴스 (전달 뉴스: 1개월 lag)
    nl.local_news_count,
    nl.local_redevelop_count,
    nl.local_regulation_count,
    nl.local_transport_count
FROM v_monthly_trade t
LEFT JOIN v_monthly_jeonse j
       ON t.deal_year  = j.deal_year
      AND t.deal_month = j.deal_month
      AND t.dong       = j.dong
LEFT JOIN v_monthly_wolse w
       ON t.deal_year  = w.deal_year
      AND t.deal_month = w.deal_month
      AND t.dong       = w.dong
LEFT JOIN interest_rate ir_base
       ON EXTRACT(YEAR  FROM ir_base.stat_date)::INT = t.deal_year
      AND EXTRACT(MONTH FROM ir_base.stat_date)::INT = t.deal_month
      AND ir_base.rate_type = '기준금리'
LEFT JOIN interest_rate ir_cd
       ON EXTRACT(YEAR  FROM ir_cd.stat_date)::INT   = t.deal_year
      AND EXTRACT(MONTH FROM ir_cd.stat_date)::INT   = t.deal_month
      AND ir_cd.rate_type   = 'CD금리(91일)'
LEFT JOIN interest_rate ir_bond
       ON EXTRACT(YEAR  FROM ir_bond.stat_date)::INT = t.deal_year
      AND EXTRACT(MONTH FROM ir_bond.stat_date)::INT = t.deal_month
      AND ir_bond.rate_type = '국고채(3년)'
-- 전국 거시 뉴스: 전달(lag 1) JOIN
LEFT JOIN v_monthly_news_macro nm
       ON (t.deal_year * 12 + t.deal_month - 1) = (nm.news_year * 12 + nm.news_month)
-- 구별 로컬 뉴스: 전달(lag 1) + 동→구 매핑 JOIN
LEFT JOIN dong_gu dg
       ON t.dong = dg.dong_name
LEFT JOIN v_monthly_news_local nl
       ON (t.deal_year * 12 + t.deal_month - 1) = (nl.news_year * 12 + nl.news_month)
      AND dg.gu_name = nl.gu_name
ORDER BY t.deal_year, t.deal_month, t.dong;


-- ────────────────────────────────────────
-- 검증 쿼리 (뷰 생성 후 확인)
-- ────────────────────────────────────────

-- 1) 전체 행수 및 기간 확인
SELECT
    COUNT(*)                          AS total_rows,
    MIN(deal_year || '-' || LPAD(deal_month::TEXT, 2, '0')) AS min_ym,
    MAX(deal_year || '-' || LPAD(deal_month::TEXT, 2, '0')) AS max_ym,
    COUNT(DISTINCT dong)              AS dong_count
FROM v_model_features;

-- 2) 동별 최근 3개월 매매가 및 전세가
SELECT
    dong,
    deal_year,
    deal_month,
    avg_price_10k,
    avg_jeonse_10k,
    ROUND((avg_jeonse_10k / NULLIF(avg_price_10k, 0) * 100)::NUMERIC, 1) AS jeonse_ratio_pct,
    rate_base
FROM v_model_features
WHERE deal_year = 2025 AND deal_month >= 10
ORDER BY dong, deal_year, deal_month;

-- 3) 뉴스 거시 시그널 월별 확인
SELECT
    news_year, news_month,
    total_news, regulation_news, easing_news,
    transport_news, redevelop_news, macro_sentiment
FROM v_monthly_news_macro
ORDER BY news_year DESC, news_month DESC
LIMIT 12;

-- 4) 구별 로컬 뉴스 확인
SELECT
    news_year, news_month, gu_name,
    local_news_count, local_redevelop_count, local_transport_count
FROM v_monthly_news_local
ORDER BY news_year DESC, news_month DESC, gu_name;

-- 5) 뉴스 피처가 잘 붙었는지 확인 (최근 3개월)
SELECT
    deal_year, deal_month, dong,
    avg_price_10k,
    total_news, macro_sentiment,
    local_news_count, local_redevelop_count
FROM v_model_features
WHERE deal_year = 2025 AND deal_month >= 10
ORDER BY deal_year DESC, deal_month DESC, dong
LIMIT 30;
