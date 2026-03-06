-- ============================================================================
-- HomeSignal AI - Supabase pgvector 설정
-- ============================================================================
-- 목적: 뉴스 데이터의 벡터 임베딩을 저장하고 코사인 유사도 검색 지원
-- 작성일: 2026-03-06
-- ============================================================================

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. news_signals 테이블 생성
CREATE TABLE IF NOT EXISTS news_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 뉴스 기본 정보
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,

    -- 키워드 및 메타데이터
    keywords TEXT[] DEFAULT '{}',
    published_at TIMESTAMPTZ NOT NULL,

    -- 벡터 임베딩 (OpenAI text-embedding-3-small: 1536차원)
    embedding VECTOR(1536),

    -- 관리 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 인덱스 생성
-- 3.1 벡터 유사도 검색을 위한 IVFFLAT 인덱스
-- 빈 테이블에서도 생성 가능 (lists=10). 데이터 1만건 이상 시 REINDEX 권장
CREATE INDEX IF NOT EXISTS news_signals_embedding_idx
ON news_signals
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);

-- 3.2 일반 쿼리 최적화 인덱스
CREATE INDEX IF NOT EXISTS news_signals_published_at_idx
ON news_signals (published_at DESC);

CREATE INDEX IF NOT EXISTS news_signals_keywords_idx
ON news_signals USING GIN (keywords);

-- 4. 코사인 유사도 검색 RPC 함수
CREATE OR REPLACE FUNCTION match_news_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5,
    filter_keywords TEXT[] DEFAULT NULL,
    filter_date_from TIMESTAMPTZ DEFAULT NULL,
    filter_date_to TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    url TEXT,
    keywords TEXT[],
    published_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ns.id,
        ns.title,
        ns.content,
        ns.url,
        ns.keywords,
        ns.published_at,
        1 - (ns.embedding <=> query_embedding) AS similarity
    FROM news_signals ns
    WHERE
        ns.embedding IS NOT NULL
        AND (filter_keywords IS NULL OR ns.keywords && filter_keywords)
        AND (filter_date_from IS NULL OR ns.published_at >= filter_date_from)
        AND (filter_date_to IS NULL OR ns.published_at <= filter_date_to)
        AND (1 - (ns.embedding <=> query_embedding)) >= match_threshold
    ORDER BY ns.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 5. houses_data 테이블 생성 (부동산 실거래가)
CREATE TABLE IF NOT EXISTS houses_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 거래 정보
    complex_name TEXT NOT NULL,
    dong_name TEXT,
    price NUMERIC(15, 2) NOT NULL CHECK (price > 0),
    contract_date DATE NOT NULL,

    -- 부동산 상세 정보
    bedrooms FLOAT,
    bathrooms FLOAT,
    sqft_living INT,
    sqft_lot INT,
    floors FLOAT,
    waterfront INT CHECK (waterfront IN (0, 1)),
    view INT CHECK (view >= 0),
    condition INT CHECK (condition >= 0),
    sqft_above INT,
    sqft_basement INT,
    yr_built INT,
    yr_renovated INT,

    -- 지역 정보 (동대문구 세부 구분)
    gu_name TEXT DEFAULT '동대문구',

    -- 관리 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 중복 방지 (같은 단지, 날짜, 가격 조합)
    CONSTRAINT unique_transaction UNIQUE (complex_name, contract_date, price)
);

-- 6. houses_data 인덱스
CREATE INDEX IF NOT EXISTS houses_data_contract_date_idx
ON houses_data (contract_date DESC);

CREATE INDEX IF NOT EXISTS houses_data_dong_name_idx
ON houses_data (dong_name);

CREATE INDEX IF NOT EXISTS houses_data_complex_name_idx
ON houses_data (complex_name);

-- 7. predictions 테이블 생성 (모델 예측 결과 저장)
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 예측 정보
    region TEXT NOT NULL,
    period TEXT NOT NULL CHECK (period IN ('week', 'month')),
    horizon INT NOT NULL CHECK (horizon > 0),

    -- 예측 결과
    predictions JSONB NOT NULL,
    confidence_interval JSONB,

    -- 모델 메타데이터
    model_name TEXT NOT NULL,
    model_version TEXT,

    -- 관리 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 인덱스를 위한 컬럼 (트리거로 자동 채워짐)
    prediction_date DATE
);

-- 8. predictions prediction_date 자동 채우기 함수
CREATE OR REPLACE FUNCTION set_prediction_date()
RETURNS TRIGGER AS $$
BEGIN
    -- predictions JSONB의 첫 번째 항목에서 date 추출
    IF NEW.predictions IS NOT NULL AND jsonb_array_length(NEW.predictions) > 0 THEN
        NEW.prediction_date := (NEW.predictions->0->>'date')::DATE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 9. predictions 테이블에 트리거 적용
CREATE TRIGGER set_predictions_date_trigger
    BEFORE INSERT OR UPDATE ON predictions
    FOR EACH ROW
    EXECUTE FUNCTION set_prediction_date();

-- 10. predictions 인덱스
CREATE INDEX IF NOT EXISTS predictions_region_date_idx
ON predictions (region, prediction_date DESC);

-- 11. 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 12. 각 테이블에 업데이트 트리거 적용 (재실행 시 기존 트리거 제거)
DROP TRIGGER IF EXISTS update_news_signals_updated_at ON news_signals;
CREATE TRIGGER update_news_signals_updated_at
    BEFORE UPDATE ON news_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_houses_data_updated_at ON houses_data;
CREATE TRIGGER update_houses_data_updated_at
    BEFORE UPDATE ON houses_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 11. ai_predictions 테이블 생성 (Ingest API 전용)
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

-- 12. ai_predictions 인덱스
CREATE INDEX IF NOT EXISTS ai_predictions_target_date_idx
ON ai_predictions (target_date DESC);

CREATE INDEX IF NOT EXISTS ai_predictions_model_version_idx
ON ai_predictions (model_version);

-- 13. RLS 정책 (anon 키로 API 읽기 허용, 재실행 시 기존 정책 제거)
ALTER TABLE news_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE houses_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read news_signals" ON news_signals;
CREATE POLICY "Allow public read news_signals" ON news_signals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow public read houses_data" ON houses_data;
CREATE POLICY "Allow public read houses_data" ON houses_data FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow public read predictions" ON predictions;
CREATE POLICY "Allow public read predictions" ON predictions FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow public read ai_predictions" ON ai_predictions;
CREATE POLICY "Allow public read ai_predictions" ON ai_predictions FOR SELECT USING (true);

-- INSERT/UPDATE: service_role 키 사용 (서버 전용). Ingest API는 SUPABASE_SERVICE_ROLE_KEY 필요

-- ============================================================================
-- 사용 예시
-- ============================================================================

-- 1. 벡터 유사도 검색 (RPC 함수 사용)
-- SELECT * FROM match_news_documents(
--     query_embedding := '[0.1, 0.2, ..., 0.3]'::vector,
--     match_count := 5,
--     match_threshold := 0.7,
--     filter_keywords := ARRAY['GTX', '청량리']
-- );

-- 2. 직접 코사인 유사도 계산
-- SELECT
--     title,
--     1 - (embedding <=> '[0.1, 0.2, ..., 0.3]'::vector) AS similarity
-- FROM news_signals
-- ORDER BY embedding <=> '[0.1, 0.2, ..., 0.3]'::vector
-- LIMIT 5;

-- 3. 특정 키워드 뉴스 검색
-- SELECT * FROM news_signals
-- WHERE keywords && ARRAY['GTX', '재개발']
-- ORDER BY published_at DESC
-- LIMIT 10;

-- ============================================================================
-- 성능 최적화 팁
-- ============================================================================
-- 1. IVFFLAT 인덱스의 lists 파라미터:
--    - 작은 데이터셋 (<10K): lists = 30-50
--    - 중간 데이터셋 (10K-100K): lists = 100-200
--    - 큰 데이터셋 (>100K): lists = √n

-- 2. 검색 정확도 vs 속도 트레이드오프:
--    SET ivfflat.probes = 10;  -- 기본값, 높을수록 정확하지만 느림

-- 3. 임베딩 저장 시 정규화 권장:
--    - OpenAI embeddings는 이미 정규화되어 있음
--    - 코사인 유사도 = 1 - cosine distance

-- ============================================================================
