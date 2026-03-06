# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HomeSignal AI is a real estate time-series prediction and RAG chatbot service targeting Dongdaemun-gu (동대문구), Seoul. The project combines numerical forecasting with news/event-based signals to provide evidence-based property market insights.

**Current State:** Backend API structure implemented with mock data. Prophet + LightGBM models and real Supabase integration are TODO.

## Development Commands

```bash
# Install dependencies
uv sync

# Install with ML dependencies (Prophet, LightGBM, pandas, numpy)
uv sync --extra ml

# Install with dev dependencies (pytest, ruff, mypy)
uv sync --extra dev

# Install with crawler dependencies (BeautifulSoup, lxml)
uv sync --extra crawler

# Run development server
uv run uvicorn src.main:app --reload

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_forecast.py

# Run single test function
uv run pytest tests/test_forecast.py::test_get_forecast -v

# Run with coverage
uv run pytest --cov=src tests/

# Lint
uv run ruff check src/

# Format code
uv run ruff format src/

# Type check
uv run mypy src/

# Run news crawler CLI
uv run python -m src.crawler.cli crawl
uv run python -m src.crawler.cli crawl -q "GTX-C 청량리" --max-results 50 --dry-run

# Generate embeddings for news (vector DB)
uv run python scripts/generate_embeddings.py
uv run python scripts/generate_embeddings.py --date-from 2024-01-01 --batch-size 50
uv run python scripts/generate_embeddings.py --verify-only
```

## Environment Setup

Create `.env` file with required variables:
```bash
# Supabase (use "placeholder" in URL to trigger mock mode)
SUPABASE_URL=<required>
SUPABASE_KEY=<required>  # anon/public key (SELECT용)
SUPABASE_SERVICE_ROLE_KEY=<required>  # service_role key (INSERT/UPDATE용, Ingest API 필수)

# Optional: Direct PostgreSQL connection for data loading
DATABASE_URL=postgresql://user:pass@host:5432/db

# AI Providers (at least one required for chat features)
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
AI_PROVIDER=openai  # or anthropic

# Cache
REDIS_URL=redis://localhost:6379/0

# App Environment
APP_ENV=development  # development | staging | production
DEBUG=true

# Cache TTL (seconds)
CACHE_TTL_FORECAST=3600  # 1 hour
CACHE_TTL_CHAT=1800      # 30 minutes

# AI API Settings
AI_API_TIMEOUT=30.0

# Embedding Settings
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Query Planner
ENABLE_QUERY_PLANNER=true
PLANNER_AI_CLASSIFICATION=true

# Crawler Settings
CRAWLER_REQUESTS_PER_MINUTE=10
CRAWLER_MIN_DELAY=1.0
CRAWLER_MAX_DELAY=3.0
```

**Mock Mode:** Set `SUPABASE_URL` containing "placeholder" to automatically enable mock implementations for all external dependencies (Supabase, Vector DB, Data Repository). This allows running the entire API without any external services.

## Architecture

### System Flow
1. **Real estate data:** 국토교통부 API → preprocessing → Supabase → Prophet/LightGBM ensemble → forecast API
2. **News data:** Google News crawling → preprocessing → Supabase + Vector DB → RAG / feature weighting
3. **User query:** Chat API → Vector DB search + forecast → AI API (GPT-4o/Claude) → response with sources

### Core Endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET/POST /api/v1/forecast` | Time-series price prediction |
| `POST /api/v1/chat` | RAG chatbot with forecast context |
| `GET /api/v1/news/insights` | News keyword analysis |
| `GET /health` | Health check |

### Domain Structure
- **forecast/**: Time-series prediction (Prophet + LightGBM ensemble, currently mock), rise point detection
- **chat/**: RAG chatbot with AI fallback logic, includes query planner agent (intent classification, query decomposition, plan generation & execution)
- **news/**: News keyword analysis and insights API
- **crawler/**: Google News crawler with rate limiting, content extraction, keyword extraction (CLI: `uv run python -m src.crawler.cli`)
- **ingest/**: Data ingestion endpoints with JWT role-based auth (houses, news, predictions)
- **shared/**: Database client, AI client abstraction, data repository pattern, cache, vector DB, embedding, config loaders
- **config/**: Centralized YAML configuration for keywords and rise point detection

### Ingest API (Data Collection)
Protected endpoints for data collectors with role-based JWT authentication (`src/ingest/auth.py`):

**Endpoints:**
- `POST /api/v1/ingest/houses` - 국토교통부 property data (role: `data_collector_molit`)
- `POST /api/v1/ingest/news` - News signals with optional embedding generation (role: `data_collector_news`)
- `POST /api/v1/ingest/predictions` - Internal model predictions (role: `service_account`)

**Authentication Flow:**
1. Client sends `Authorization: Bearer <supabase-jwt>`
2. `verify_jwt_token()` validates token with Supabase Auth
3. `check_role()` verifies user has required role from `user_metadata.role`
4. Role names configured in `settings.py` (`ingest_role_molit`, `ingest_role_news`, `ingest_role_internal`)

**Schemas:**
- `HouseDataIngest`: Transaction data with validation (price > 0, valid dates)
- `NewsSignalIngest`: News article with optional embedding
- `PredictionDataIngest`: Model prediction results

**Service Layer** (`src/ingest/service.py`):
- Batch inserts to Supabase
- Automatic embedding generation for news (if enabled)
- Deduplication and conflict handling

### AI Client Abstraction
`src/shared/ai_client.py` provides unified interface for OpenAI/Anthropic:
- **Provider Selection**: Controlled by `AI_PROVIDER` env var (openai | anthropic)
- **Async Clients**: Both implementations use async clients (`AsyncOpenAI`, `AsyncAnthropic`)
- **Timeout**: Configurable via `settings.ai_api_timeout` (default: 30s)
- **Factory**: `get_ai_client()` returns appropriate client based on config
- **Usage**: All chat/RAG features use this abstraction to remain provider-agnostic

### Fallback Logic
On AI API failure: return forecast numbers only with "일시적 장애" message. Fallback responses are not cached.

### Prompt Versioning
Store prompts in `src/chat/prompts/v1.py`, `v2.py` for Git tracking and A/B testing.

### Mock-First Development
The codebase uses automatic mock fallbacks for local development without external services:
- **MockSupabaseClient** (`src/shared/database.py`): Activates when `SUPABASE_URL` contains placeholder values or Supabase library is unavailable. Provides table operations with chainable query methods (select, insert, eq, gt, order, limit, execute).
- **MockVectorDB** (`src/shared/vector_db.py`): Provides simulated vector search results
- **MockDataRepository** (`src/shared/data_repository.py`): Returns hardcoded time-series data, news signals, and keyword frequencies

Services check for these conditions and swap implementations transparently via factory functions (`get_supabase_client()`, `get_data_repository()`). This allows running the API server without any external dependencies.

**Note:** `get_supabase_client(use_service_role=True)` is used by Ingest API and VectorDB for INSERT/UPDATE operations. Regular SELECT operations use the default anon key.

### Rise Point Detection & Keyword Extraction
The system identifies price rise points and extracts news keywords around those periods:
- **Rise Point Detector** (`src/forecast/rise_point_detector.py`): Detects price rise points using:
  - `ma_crossover`: Short-term MA crosses above long-term MA
  - `rate_threshold`: Price change exceeds threshold percentage
  - `consecutive_rise`: N consecutive periods of price increases
- **Keyword Config** (`config/keywords.yaml`): Centralized keyword definitions with:
  - Categories: transport (GTX), redevelopment, supply, policy
  - Primary keywords vs synonyms for each category
  - Loaded via `src/shared/keyword_config.py`
- **Rise Point Config** (`config/rise_point_config.yaml`): Detection parameters:
  - Method selection, MA windows (short: 5, long: 20)
  - Lookback/lookahead windows (default: 4 weeks each)
  - Loaded via `src/shared/rise_point_config.py`
- **Feature Variables**: News keyword frequencies around rise points are used as features for Prophet/LightGBM models via `DataRepository.get_news_keyword_frequency(rise_point_windows=[...])`

## Query Planner Agent

The chat service includes a sophisticated query planning system (`src/chat/planner/`) for handling complex multi-part questions:

### 4-Stage Pipeline
1. **IntentClassifier** (`classifier.py`): Determines query type
   - `forecast`: Price prediction questions
   - `comparison`: Multi-location comparisons
   - `news_analysis`: News impact questions
   - `general`: General real estate questions
   - Uses AI classification if `settings.planner_ai_classification=True`, else rule-based

2. **QueryDecomposer** (`decomposer.py`): Breaks complex queries into sub-queries
   - Example: "청량리와 이문동 중 어디가 더 오를까?" → ["청량리 예측", "이문동 예측", "비교 분석"]
   - Each sub-query has type, region, and required data sources

3. **PlanGenerator** (`plan_generator.py`): Creates execution plan
   - Determines step order and dependencies
   - Maps sub-queries to API calls (forecast, news search, vector DB)
   - Generates `ExecutionPlan` with `ExecutionStep[]`

4. **PlanExecutor** (`executor.py`): Executes plan and synthesizes response
   - Runs steps sequentially or in parallel based on dependencies
   - Collects intermediate results
   - Passes all context to AI for final synthesis

### Schemas
All domain models in `planner/schemas.py`:
- `QueryIntent`: Classified intent with confidence
- `SubQuery`: Decomposed query component
- `ExecutionStep`: Individual step in plan (data fetch, analysis, synthesis)
- `ExecutionPlan`: Complete plan with steps and metadata

### Feature Flag
Toggle via `settings.enable_query_planner`. When disabled, falls back to simple RAG flow.

## News Crawler Architecture

The crawler module (`src/crawler/`) implements a production-ready Google News scraper:

### Components
- **google_news.py**: Google News RSS feed parser
- **content_extractor.py**: HTML article content extraction
- **keyword_extractor.py**: Keyword extraction from article text
- **rate_limiter.py**: Token bucket rate limiting with configurable requests/minute
- **runner.py**: Orchestrates crawl pipeline with retry logic
- **cli.py**: Command-line interface for manual/scheduled crawling

### Crawler Pipeline
1. **Fetch**: Query Google News RSS → parse results
2. **Extract**: Download article HTML → extract main content
3. **Keywords**: Extract keywords from title + content
4. **Embeddings**: Generate embeddings via `src/shared/embedding.py` (optional)
5. **Ingest**: POST to `/api/v1/ingest/news` with deduplication

### Rate Limiting
- Token bucket algorithm with configurable rate (default: 10 req/min)
- Random delay between requests (1.0-3.0s)
- Prevents IP blocking and respects robots.txt

### Configuration
Settings in `src/config/settings.py`:
- `crawler_requests_per_minute`: Rate limit
- `crawler_default_queries`: Default search terms
- `crawler_date_range_days`: How far back to search
- `crawler_extract_content`: Enable/disable full content extraction
- `crawler_content_max_length`: Max content length (default: 2000 chars)

## AI/ML Pipeline

### Time-Series Model Stack (TODO)
- **Prophet:** Baseline for trends and seasonality
- **LightGBM:** Learning weights for news/policy features
- **Ensemble:** Weighted average of both models

### Key Features (피처)
- News keyword frequency (GTX, 재개발, 이문휘경뉴타운)
- Event dummy variables (policy announcements, sales restrictions)
- Moving averages (5-week short-term, 20-week long-term)

### Evaluation Metrics
- RMSE, MAE, MAPE, directional accuracy

## Development Guidelines

### Code Architecture Patterns
- **Repository Pattern**: All data access goes through `DataRepositoryInterface` in `src/shared/data_repository.py`. Add new queries as interface methods, then implement in both `MockDataRepository` and `SupabaseDataRepository`.
- **Factory Functions**: Use `@lru_cache` decorated factory functions for singletons (`get_supabase_client()`, `get_data_repository()`, `get_settings()`).
- **Settings via Pydantic**: All configuration in `src/config/settings.py` using `pydantic-settings` with `.env` file support.
- **Query Planner Agent**: Complex chat queries use a 4-stage pipeline in `src/chat/planner/`: IntentClassifier → QueryDecomposer → PlanGenerator → PlanExecutor.

### Development Principles
- Before writing code, verify alignment with `docs/01_PRD_HomeSignalAI.md`
- Always include data sources in AI responses
- Implement caching for identical requests (target: 2.0s response time)
- Handle API errors gracefully with fallback to numerical data (see `src/chat/fallback.py`)
- Use async/await throughout—all services are designed for non-blocking I/O
- Type hints required (enforced by `mypy --strict`)
- Custom exceptions inherit from `HomeSignalError` in `src/shared/exceptions.py`

## Testing & Quality

### Test Structure
- **conftest.py**: Shared fixtures for sample queries (simple, comparison, news analysis)
- **pytest.ini_options**: `asyncio_mode = "auto"` enables automatic async test handling
- **Test Coverage**: Run `uv run pytest --cov=src tests/` for coverage reports

### Key Test Files
- `tests/test_rise_point_detector.py`: Rise point detection algorithms
- `tests/test_keyword_config.py`: YAML keyword configuration loading
- `tests/test_planner.py`: Query planner agent pipeline

## Key Documentation

| Document | Content |
|----------|---------|
| `docs/01_PRD_HomeSignalAI.md` | Requirements, user needs, success metrics |
| `docs/02_Architecture_Design.md` | System architecture, API specs, data models |
| `docs/03_AI_Model_Pipeline.md` | ML pipeline, feature engineering |
| `docs/04_Prompt_RAG_Strategy.md` | RAG logic, prompt templates |
| `docs/05_Deployment_Operation.md` | Testing, deployment, monitoring |
| `docs/06_Rise_Point_Keyword_Extraction.md` | Rise point detection & keyword extraction strategy |
| `docs/12_Vector_DB_Setup_Guide.md` | Vector DB (pgvector) setup, embedding generation, data ingestion |
| `.cursor/rules/homesignal-ai-master.mdc` | Cursor IDE rules (project identity, AI design principles)

## Critical Architectural Decisions

### Why Repository Pattern?
Abstracts data access behind `DataRepositoryInterface` allowing seamless switching between mock/production implementations. All services (ForecastService, ChatService, NewsService) depend on the interface, not concrete implementations.

### Why Mock-First?
Enables rapid development and testing without external dependencies. Mocks activate automatically when:
- Supabase library unavailable (dev environment)
- `SUPABASE_URL` contains "placeholder"
- Explicit `use_mock=True` parameter

### Why Query Planner Agent?
Complex multi-location or multi-faceted questions require orchestrated data fetching and synthesis. The planner:
- Decomposes "청량리 vs 이문동" into separate forecasts + comparison
- Determines optimal execution order
- Reduces redundant AI calls via structured planning

### Why Centralized YAML Config?
Keywords and rise point parameters change frequently during model tuning. YAML files in `config/` allow non-developers to adjust parameters without code changes. Config loaders cache and validate on startup.

## Implementation Status & Priorities

### ✅ Completed
- FastAPI backend structure with domain-driven design
- Mock-first development pattern
- Ingest API with JWT authentication
- News crawler with rate limiting
- Query planner agent (4-stage pipeline)
- Rise point detection algorithms
- Keyword configuration system
- AI client abstraction (OpenAI/Anthropic)

### 🚧 TODO (Priority Order)
1. **Supabase schema setup** - Execute `migrations/001_setup_pgvector.sql` in Supabase SQL Editor
2. **Vector DB data collection** - Run crawler + embedding generation (see `docs/12_Vector_DB_Setup_Guide.md`)
3. **Prophet + LightGBM models** - Replace mock forecast with real ML predictions
4. **국토교통부 API integration** - Fetch real transaction data
5. **Cache implementation** - Redis-based caching for forecast/chat responses
6. **Production deployment** - Docker, monitoring, logging

## Vector DB Setup & Data Collection

### Quick Start (벡터 DB 초기 설정)

```bash
# 1. Supabase에서 마이그레이션 실행
# Supabase SQL Editor에서 migrations/001_setup_pgvector.sql 실행

# 2. 뉴스 크롤링 (초기 데이터 수집)
uv run python -m src.crawler.cli crawl -q "GTX-C 청량리" "동대문구 재개발" --max-results 100

# 3. 임베딩 생성 및 벡터 DB 적재
uv run python scripts/generate_embeddings.py

# 4. 검증
uv run python scripts/generate_embeddings.py --verify-only
```

### Vector DB Architecture

- **Database**: Supabase PostgreSQL + pgvector extension
- **Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **Search Algorithm**: Cosine similarity with IVFFLAT index
- **RPC Function**: `match_news_documents()` for similarity search

**Files:**
- `migrations/001_setup_pgvector.sql` - Schema and RPC functions
- `scripts/generate_embeddings.py` - Batch embedding generation
- `src/shared/vector_db.py` - Vector DB interface (Mock + Supabase)
- `src/shared/embedding.py` - OpenAI embedding service
- `docs/12_Vector_DB_Setup_Guide.md` - Complete setup guide

**See:** `docs/12_Vector_DB_Setup_Guide.md` for detailed instructions
