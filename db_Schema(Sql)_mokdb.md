-- 1. 벡터 검색을 위한 확장 기능 활성화 (RAG용)
create extension if not exists vector;

-- 2. houses_data: 부동산 실거래 및 물리적 속성 테이블
-- Kaggle data.csv의 모든 핵심 변수를 포함합니다.
create table houses_data (
    id uuid default gen_random_uuid() primary key,
    complex_name text not null,                -- 아파트 단지명
    dong_name text,                            -- 법정동 (동대문구 구체화)
    price numeric,                             -- 실거래가
    bedrooms float,                            -- 침실 수
    bathrooms float,                           -- 욕실 수
    sqft_living int,                           -- 전용면적
    sqft_lot int,                              -- 대지면적
    floors float,                              -- 층수
    waterfront int,                            -- 수변 조망 여부
    view int,                                  -- 조망권 등급
    condition int,                             -- 건물 상태
    sqft_above int,                            -- 지상층 면적
    sqft_basement int,                         -- 지하층 면적
    yr_built int,                              -- 준공 연도
    yr_renovated int,                          -- 리모델링 연도
    contract_date timestamp with time zone default now(), -- 계약일 (시계열 기준)
    created_at timestamp with time zone default now()
);

-- 3. news_signals: RAG용 뉴스 및 정책 데이터 테이블 
create table news_signals (
    id uuid default gen_random_uuid() primary key,
    title text not null,
    content text,
    url text,
    keywords text[],                           -- 핵심 키워드 배열 (GTX, 재개발 등)
    embedding vector(1536),                    -- OpenAI(text-embedding-3-small) 규격
    published_at timestamp with time zone,
    created_at timestamp with time zone default now()
);

-- 4. ai_predictions: 시계열 모델 예측 결과 저장 [cite: 429-431]
create table ai_predictions (
    id uuid default gen_random_uuid() primary key,
    model_version text,                        -- 모델 버전 관리 [cite: 227-228]
    target_date date not null,                 -- 예측 대상 일자
    predicted_price numeric,                   -- 예측 가격
    confidence_score float,                    -- 신뢰도 (0~1)
    features_used jsonb,                       -- 예측에 사용된 변수 가중치 정보
    created_at timestamp with time zone default now()
);

-- 5. user_interactions: 챗봇 대화 로그 및 피드백 [cite: 320, 335]
create table user_interactions (
    id uuid default gen_random_uuid() primary key,
    user_query text,
    ai_response text,
    feedback_is_positive boolean,              -- 좋아요/싫어요
    latency_ms int,                            -- 응답 속도 모니터링 [cite: 331]
    created_at timestamp with time zone default now()
);