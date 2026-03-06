-- ============================================================================
-- HomeSignal AI - 뉴스 문서 유사도 검색 RPC 함수
--
-- 사용법:
--   SELECT * FROM match_news_documents(
--     query_embedding := '[0.1, 0.2, ...]'::vector,
--     match_count := 5,
--     match_threshold := 0.5
--   );
-- ============================================================================

-- 기본 유사도 검색 함수
CREATE OR REPLACE FUNCTION match_news_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.5
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    url TEXT,
    keywords TEXT[],
    published_at TIMESTAMPTZ,
    similarity float
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
    WHERE ns.embedding IS NOT NULL
      AND 1 - (ns.embedding <=> query_embedding) > match_threshold
    ORDER BY ns.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 키워드 필터 포함 유사도 검색 함수
CREATE OR REPLACE FUNCTION match_news_documents_with_filters(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.5,
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
    similarity float
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
    WHERE ns.embedding IS NOT NULL
      AND 1 - (ns.embedding <=> query_embedding) > match_threshold
      -- 키워드 필터 (배열 교집합)
      AND (filter_keywords IS NULL OR ns.keywords && filter_keywords)
      -- 날짜 범위 필터
      AND (filter_date_from IS NULL OR ns.published_at >= filter_date_from)
      AND (filter_date_to IS NULL OR ns.published_at <= filter_date_to)
    ORDER BY ns.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 하이브리드 검색 함수 (벡터 + 키워드)
CREATE OR REPLACE FUNCTION hybrid_search_news(
    query_embedding vector(1536),
    query_keywords TEXT[],
    match_count int DEFAULT 10,
    vector_weight float DEFAULT 0.7,
    keyword_weight float DEFAULT 0.3
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    url TEXT,
    keywords TEXT[],
    published_at TIMESTAMPTZ,
    vector_score float,
    keyword_score float,
    combined_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_matches AS (
        SELECT
            ns.id,
            ns.title,
            ns.content,
            ns.url,
            ns.keywords,
            ns.published_at,
            1 - (ns.embedding <=> query_embedding) AS v_score
        FROM news_signals ns
        WHERE ns.embedding IS NOT NULL
    ),
    keyword_matches AS (
        SELECT
            ns.id,
            -- 키워드 매칭 점수: 교집합 크기 / 쿼리 키워드 수
            CASE
                WHEN array_length(query_keywords, 1) > 0
                THEN (
                    SELECT COUNT(*)::float
                    FROM unnest(ns.keywords) kw
                    WHERE kw = ANY(query_keywords)
                ) / array_length(query_keywords, 1)::float
                ELSE 0
            END AS k_score
        FROM news_signals ns
    )
    SELECT
        vm.id,
        vm.title,
        vm.content,
        vm.url,
        vm.keywords,
        vm.published_at,
        vm.v_score AS vector_score,
        COALESCE(km.k_score, 0) AS keyword_score,
        (vm.v_score * vector_weight + COALESCE(km.k_score, 0) * keyword_weight) AS combined_score
    FROM vector_matches vm
    LEFT JOIN keyword_matches km ON vm.id = km.id
    WHERE vm.v_score > 0.3  -- 최소 벡터 유사도
    ORDER BY (vm.v_score * vector_weight + COALESCE(km.k_score, 0) * keyword_weight) DESC
    LIMIT match_count;
END;
$$;

-- 임베딩 없는 문서 조회 (임베딩 생성 대상)
CREATE OR REPLACE FUNCTION get_documents_without_embedding(
    batch_size int DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ns.id,
        ns.title,
        ns.content
    FROM news_signals ns
    WHERE ns.embedding IS NULL
    ORDER BY ns.created_at DESC
    LIMIT batch_size;
END;
$$;

-- 임베딩 업데이트 함수
CREATE OR REPLACE FUNCTION update_document_embedding(
    doc_id UUID,
    new_embedding vector(1536)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE news_signals
    SET embedding = new_embedding,
        updated_at = NOW()
    WHERE id = doc_id;

    RETURN FOUND;
END;
$$;

-- 통계 함수: 임베딩 현황
CREATE OR REPLACE FUNCTION get_embedding_stats()
RETURNS TABLE (
    total_documents BIGINT,
    with_embedding BIGINT,
    without_embedding BIGINT,
    embedding_coverage_pct NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) AS total_documents,
        COUNT(embedding) AS with_embedding,
        COUNT(*) - COUNT(embedding) AS without_embedding,
        ROUND(COUNT(embedding)::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS embedding_coverage_pct
    FROM news_signals;
END;
$$;

-- 권한 설정 (Supabase anon/service_role)
GRANT EXECUTE ON FUNCTION match_news_documents TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION match_news_documents_with_filters TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION hybrid_search_news TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_documents_without_embedding TO service_role;
GRANT EXECUTE ON FUNCTION update_document_embedding TO service_role;
GRANT EXECUTE ON FUNCTION get_embedding_stats TO anon, authenticated, service_role;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'RPC 함수 생성 완료: match_news_documents, hybrid_search_news 등';
END $$;
