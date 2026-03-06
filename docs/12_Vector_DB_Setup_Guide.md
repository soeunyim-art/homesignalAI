# HomeSignal AI - Vector DB 설정 및 데이터 수집 가이드

**작성일:** 2026-03-06
**목적:** Supabase pgvector 기반 벡터 DB 설정 및 뉴스 임베딩 데이터 수집

---

## 목차

1. [개요](#1-개요)
2. [아키텍처](#2-아키텍처)
3. [Supabase 설정](#3-supabase-설정)
4. [데이터 수집 파이프라인](#4-데이터-수집-파이프라인)
5. [운영 및 모니터링](#5-운영-및-모니터링)
6. [트러블슈팅](#6-트러블슈팅)

---

## 1. 개요

### 1.1 Vector DB의 역할

HomeSignal AI는 RAG (Retrieval-Augmented Generation) 기반 챗봇을 제공하며, 벡터 DB는 다음 기능을 지원합니다:

- **뉴스 유사도 검색**: 사용자 질문과 가장 관련 있는 뉴스 기사 검색
- **문맥 제공**: AI 응답 생성 시 관련 뉴스를 문맥으로 제공
- **출처 추적**: AI 응답의 근거가 되는 뉴스 출처 제공

### 1.2 기술 스택

| 구성 요소 | 기술 | 목적 |
|----------|------|------|
| 벡터 DB | Supabase pgvector | PostgreSQL 기반 벡터 저장 및 검색 |
| 임베딩 모델 | OpenAI text-embedding-3-small | 텍스트를 1536차원 벡터로 변환 |
| 크롤러 | Google News RSS | 동대문구 관련 뉴스 수집 |
| 검색 알고리즘 | 코사인 유사도 (IVFFLAT) | 벡터 간 유사도 측정 |

---

## 2. 아키텍처

### 2.1 데이터 흐름

```
┌──────────────────────────────────────────────────────────────────┐
│                    1. 뉴스 수집 (Crawler)                         │
│  Google News → 크롤링 → 본문 추출 → 키워드 추출                    │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    2. 임베딩 생성                                  │
│  뉴스 제목 + 본문 → OpenAI API → 1536차원 벡터                      │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                  3. 벡터 DB 저장 (Supabase)                       │
│  news_signals 테이블 → embedding 컬럼 (VECTOR 타입)                │
│  IVFFLAT 인덱스로 빠른 검색 지원                                   │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                   4. 유사도 검색 (RAG)                             │
│  사용자 질문 → 임베딩 → pgvector 코사인 유사도 → Top-K 뉴스 반환    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 데이터베이스 스키마

```sql
-- news_signals 테이블
CREATE TABLE news_signals (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url TEXT UNIQUE,
    keywords TEXT[],
    published_at TIMESTAMPTZ NOT NULL,
    embedding VECTOR(1536),  -- 핵심: 벡터 임베딩
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벡터 유사도 검색 인덱스
CREATE INDEX news_signals_embedding_idx
ON news_signals
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 3. Supabase 설정

### 3.1 단계별 설정 가이드

#### Step 1: Supabase 프로젝트 생성

1. [Supabase Dashboard](https://supabase.com/dashboard) 접속
2. "New Project" 클릭
3. 프로젝트 정보 입력:
   - Name: `homesignal-ai`
   - Database Password: 강력한 비밀번호 설정
   - Region: `Northeast Asia (Seoul)` 또는 가까운 리전

#### Step 2: pgvector 확장 활성화 및 스키마 생성

Supabase SQL Editor에서 실행:

```bash
# 1. migrations 폴더의 SQL 파일을 복사하여 실행
# D:\Ai_project\home_signal_ai\migrations\001_setup_pgvector.sql
```

또는 CLI 사용:

```bash
# Supabase CLI 설치 (필요시)
npm install -g supabase

# 로컬 프로젝트 초기화
supabase init

# 마이그레이션 실행
supabase db push
```

#### Step 3: 환경 변수 설정

`.env` 파일에 Supabase 정보 추가:

```bash
# Supabase 설정 (Dashboard > Settings > API에서 확인)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# OpenAI API (임베딩 생성용)
OPENAI_API_KEY=sk-...

# 기타 설정
AI_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

### 3.2 RPC 함수 검증

Supabase SQL Editor에서 테스트:

```sql
-- 더미 벡터로 검색 테스트
SELECT * FROM match_news_documents(
    query_embedding := array_fill(0.1, ARRAY[1536])::vector,
    match_count := 5,
    match_threshold := 0.5
);
```

---

## 4. 데이터 수집 파이프라인

### 4.1 뉴스 크롤링

#### 크롤러 실행

```bash
# 기본 크롤링 (최근 7일 뉴스)
uv run python -m src.crawler.cli crawl

# 커스텀 쿼리 및 옵션
uv run python -m src.crawler.cli crawl \
    -q "GTX-C 청량리" "동대문구 재개발" "이문휘경 뉴타운" \
    --max-results 50 \
    --date-range 14 \
    --no-embeddings  # 임베딩은 나중에 배치 생성

# Dry run (테스트용)
uv run python -m src.crawler.cli crawl --dry-run
```

#### 크롤링 결과 확인

```bash
# Supabase에서 확인
SELECT COUNT(*), MAX(published_at), MIN(published_at)
FROM news_signals
WHERE embedding IS NULL;
```

### 4.2 임베딩 생성

#### 전체 뉴스 임베딩 생성

```bash
# 임베딩 없는 모든 뉴스 처리
uv run python scripts/generate_embeddings.py

# 특정 날짜 이후 뉴스만
uv run python scripts/generate_embeddings.py --date-from 2024-01-01

# 배치 크기 조정 (API 제한 고려)
uv run python scripts/generate_embeddings.py --batch-size 50

# Dry run (테스트)
uv run python scripts/generate_embeddings.py --dry-run --limit 10

# 임베딩 검증만
uv run python scripts/generate_embeddings.py --verify-only
```

#### 임베딩 생성 프로세스

1. **뉴스 조회**: `embedding IS NULL`인 뉴스 조회
2. **텍스트 결합**: 제목 + 본문 (최대 2000자)
3. **배치 임베딩**: OpenAI API 호출 (배치 크기: 100)
4. **DB 업데이트**: `embedding` 컬럼 업데이트
5. **검증**: 샘플 뉴스의 임베딩 차원 확인

### 4.3 자동화 (스케줄링)

#### Cron Job 설정 (Linux/Mac)

```bash
# crontab 편집
crontab -e

# 매일 새벽 2시 크롤링 + 임베딩
0 2 * * * cd /path/to/home_signal_ai && uv run python -m src.crawler.cli crawl >> /var/log/homesignal-crawler.log 2>&1
30 2 * * * cd /path/to/home_signal_ai && uv run python scripts/generate_embeddings.py >> /var/log/homesignal-embeddings.log 2>&1
```

#### GitHub Actions (CI/CD)

```yaml
# .github/workflows/news-crawler.yml
name: News Crawler
on:
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시 (UTC)
  workflow_dispatch:  # 수동 실행 가능

jobs:
  crawl-and-embed:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --extra crawler
      - name: Run crawler
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: uv run python -m src.crawler.cli crawl
      - name: Generate embeddings
        run: uv run python scripts/generate_embeddings.py
```

---

## 5. 운영 및 모니터링

### 5.1 데이터 품질 모니터링

```sql
-- 1. 임베딩 커버리지 확인
SELECT
    COUNT(*) AS total_news,
    COUNT(embedding) AS with_embedding,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) AS coverage_pct
FROM news_signals;

-- 2. 최근 수집 현황
SELECT
    DATE(created_at) AS date,
    COUNT(*) AS news_count,
    COUNT(embedding) AS embedding_count
FROM news_signals
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 3. 키워드별 뉴스 분포
SELECT
    unnest(keywords) AS keyword,
    COUNT(*) AS count
FROM news_signals
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY keyword
ORDER BY count DESC
LIMIT 20;
```

### 5.2 검색 성능 모니터링

```sql
-- 벡터 인덱스 통계
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname = 'news_signals_embedding_idx';

-- 인덱스 크기 확인
SELECT
    pg_size_pretty(pg_relation_size('news_signals_embedding_idx')) AS index_size,
    pg_size_pretty(pg_relation_size('news_signals')) AS table_size;
```

### 5.3 비용 최적화

#### OpenAI 임베딩 비용 추정

- **모델**: text-embedding-3-small
- **가격**: $0.02 / 1M tokens
- **평균 뉴스 길이**: ~500 tokens (제목 + 본문 2000자)

```python
# 월간 비용 추정
daily_news = 50  # 하루 수집 뉴스 수
tokens_per_news = 500
monthly_tokens = daily_news * 30 * tokens_per_news  # 750K tokens
monthly_cost = (monthly_tokens / 1_000_000) * 0.02  # $0.015
```

→ **월 예상 비용: ~$0.02** (매우 저렴)

---

## 6. 트러블슈팅

### 6.1 일반적인 문제

#### Q1. 임베딩 생성 실패 (OpenAI API 오류)

```bash
# 에러: openai.RateLimitError
# 해결: 배치 크기 줄이기
uv run python scripts/generate_embeddings.py --batch-size 20

# 에러: openai.APIConnectionError
# 해결: 네트워크 및 API 키 확인
echo $OPENAI_API_KEY
```

#### Q2. 벡터 검색 결과 없음

```sql
-- 1. 임베딩 존재 확인
SELECT COUNT(*) FROM news_signals WHERE embedding IS NOT NULL;

-- 2. 인덱스 재구성
REINDEX INDEX news_signals_embedding_idx;

-- 3. 임계값 낮추기
SELECT * FROM match_news_documents(
    query_embedding := ...,
    match_threshold := 0.3  -- 기본 0.5에서 낮춤
);
```

#### Q3. 검색 속도 느림

```sql
-- 1. IVFFLAT probes 조정 (정확도 vs 속도)
SET ivfflat.probes = 5;  -- 기본 10, 낮을수록 빠름

-- 2. 인덱스 lists 파라미터 재조정
DROP INDEX news_signals_embedding_idx;
CREATE INDEX news_signals_embedding_idx
ON news_signals
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);  -- 뉴스 수에 따라 조정
```

### 6.2 데이터 정합성 검증

```bash
# 1. 임베딩 차원 확인
uv run python scripts/generate_embeddings.py --verify-only

# 2. 중복 URL 확인
SELECT url, COUNT(*)
FROM news_signals
GROUP BY url
HAVING COUNT(*) > 1;

# 3. Null 값 확인
SELECT
    COUNT(*) FILTER (WHERE title IS NULL) AS null_titles,
    COUNT(*) FILTER (WHERE embedding IS NULL) AS null_embeddings,
    COUNT(*) FILTER (WHERE published_at IS NULL) AS null_dates
FROM news_signals;
```

---

## 7. 다음 단계

### 7.1 초기 설정 체크리스트

- [ ] Supabase 프로젝트 생성 및 pgvector 활성화
- [ ] `001_setup_pgvector.sql` 마이그레이션 실행
- [ ] `.env` 파일에 Supabase 및 OpenAI 키 설정
- [ ] 크롤러로 초기 뉴스 수집 (100-200개)
- [ ] 임베딩 생성 스크립트 실행 및 검증
- [ ] RAG API 테스트 (`POST /api/v1/chat`)

### 7.2 운영 단계

- [ ] Cron job 또는 GitHub Actions 설정
- [ ] 모니터링 대시보드 구성 (Supabase Dashboard)
- [ ] 주간 데이터 품질 리포트 자동화
- [ ] 벡터 인덱스 최적화 (뉴스 수 증가 시)

### 7.3 고급 기능

- [ ] 하이브리드 검색 (키워드 + 벡터 유사도 결합)
- [ ] 뉴스 임베딩 클러스터링 (주제별 그룹화)
- [ ] 임베딩 모델 업그레이드 (text-embedding-3-large)
- [ ] 실시간 크롤링 및 임베딩 생성 파이프라인

---

## 참고 자료

- [Supabase Vector Documentation](https://supabase.com/docs/guides/ai/vector-columns)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [IVFFLAT Index Tuning](https://github.com/pgvector/pgvector#ivfflat)

---

**문서 작성자**: Vector DB Specialist
**최종 업데이트**: 2026-03-06
