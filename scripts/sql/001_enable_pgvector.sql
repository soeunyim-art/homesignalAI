-- ============================================================================
-- HomeSignal AI - pgvector 확장 활성화 및 테이블 설정
--
-- 실행 방법:
--   Supabase Dashboard > SQL Editor에서 실행
--   또는 psql로 직접 실행
-- ============================================================================

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. news_signals 테이블 생성 (없는 경우)
CREATE TABLE IF NOT EXISTS news_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    keywords TEXT[] DEFAULT '{}',
    embedding vector(1536),  -- OpenAI text-embedding-3-small 차원
    published_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 기존 테이블에 embedding 컬럼 추가 (이미 있으면 무시)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'news_signals' AND column_name = 'embedding'
    ) THEN
        ALTER TABLE news_signals ADD COLUMN embedding vector(1536);
    END IF;
END $$;

-- 4. 벡터 유사도 검색용 인덱스 생성 (IVFFLAT)
-- lists 값은 데이터 양에 따라 조정 (sqrt(n) 권장)
DROP INDEX IF EXISTS news_signals_embedding_idx;
CREATE INDEX news_signals_embedding_idx
    ON news_signals
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 5. 키워드 검색용 GIN 인덱스
CREATE INDEX IF NOT EXISTS news_signals_keywords_idx
    ON news_signals USING GIN (keywords);

-- 6. 발행일 인덱스
CREATE INDEX IF NOT EXISTS news_signals_published_at_idx
    ON news_signals (published_at DESC);

-- 7. URL 고유 인덱스 (upsert용)
CREATE UNIQUE INDEX IF NOT EXISTS news_signals_url_idx
    ON news_signals (url)
    WHERE url IS NOT NULL;

-- 8. updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS news_signals_updated_at ON news_signals;
CREATE TRIGGER news_signals_updated_at
    BEFORE UPDATE ON news_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'pgvector 설정 완료: news_signals 테이블 준비됨';
END $$;
