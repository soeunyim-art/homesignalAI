# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HomeSignal AI is a real estate price prediction platform for Seoul's northeast districts (동대문구, 성북구, 중랑구, 강북구, 도봉구). It combines machine learning models with a Next.js dashboard to predict apartment prices 1-3 months ahead using transaction data, interest rates, and news sentiment signals.

**Current Version:** v2.2 (2026-03-23)

**Tech Stack:**
- Frontend: Next.js 16 (React 19, TypeScript), Tailwind CSS 4, Radix UI components
- Backend: Python data pipeline (scikit-learn, pandas), Next.js API routes
- Database: Supabase (PostgreSQL)
- AI: Claude 3.5 Sonnet (Anthropic API) with RAG
- Deployment: Vercel

**Recent Updates:**
- v2.2 (2026-03-23): AI chatbot with RAG system, comprehensive test scripts
- v2.1 (2026-03-20): Next.js web dashboard, 5-tab interface
- v2.0 (2026-03-13): News sentiment signals (macro + local)
- v1.5 (2026-03-06): 5-district expansion, hedonic GBM model
- v1.0 (2026-02-28): MVP with single district (Dongdaemun-gu)

## Repository Structure

```
├── app/                      # Next.js App Router
│   ├── page.tsx             # Main dashboard page
│   ├── layout.tsx           # Root layout with theme provider
│   └── api/                 # API routes (predictions, news, trade-history)
├── components/
│   ├── dashboard/           # Dashboard UI components
│   │   ├── tabs/           # Tab content (overview, region-analysis, price-trends, ai-report, apt-search)
│   │   ├── collapsible-sidebar.tsx
│   │   ├── home-search.tsx
│   │   ├── map-area.tsx
│   │   ├── price-prediction-chart.tsx
│   │   └── news-sentiment-feed.tsx
│   └── ui/                  # Reusable shadcn/ui components
├── lib/
│   ├── supabase.ts         # Supabase client & TypeScript types
│   ├── utils.ts            # cn() utility for class merging
│   └── rag-utils.ts        # RAG utilities (query analysis, context building for chatbot)
├── collect_data.py          # Data collection pipeline (국토부 + ECOS API)
├── predict_model.py         # ML prediction pipeline (Ridge + GBM)
├── test_ml_pipeline.py      # ML pipeline validation script
├── test_supabase_connection.py  # Database connection test
├── system_health_check.py   # Comprehensive system diagnostic
├── supabase_schema.sql      # Database schema (tables: dongs, apartments, predictions, predictions_apt)
├── supabase_views.sql       # SQL views for feature engineering (v_model_features)
├── requirements.txt         # Python dependencies
├── monthly_update.bat       # Windows Task Scheduler script for automated updates
└── docs/                    # Additional documentation
    └── chatbot_upgrade_plan.md  # RAG chatbot implementation plan
```

## Common Development Commands

### Frontend (Next.js)

```bash
# Install dependencies (pnpm preferred)
pnpm install
# or
npm install

# Development server
npm run dev          # http://localhost:3000
# Alternative with Turbopack (may have issues on Windows - see Troubleshooting)
npm run dev:turbo

# Production build
npm run build
npm run start

# Linting
npm run lint
```

**Note:** This project uses pnpm as the preferred package manager (see `pnpm` config in package.json).

### Python ML Pipeline

```bash
# Install dependencies
pip install -r requirements.txt

# Full data collection (2020-01 ~ present)
python collect_data.py full

# Monthly incremental update
python collect_data.py update

# Run prediction model
python predict_model.py

# Testing and Diagnostics
python system_health_check.py           # Comprehensive system health check
python test_ml_pipeline.py              # Validate ML pipeline setup
python test_supabase_connection.py      # Test database connection
```

**Note:** Python scripts require `homesignal.env` file (see environment variable examples below). The ML pipeline must be run manually - no automated scheduler is configured by default.

## Environment Variables

The project uses **two separate environment files** for different components:

### Frontend (.env or .env.local)
Used by Next.js (app/, components/, lib/)

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key    # Service role key (admin access)

# AI Chatbot (Required for /api/chat)
ANTHROPIC_API_KEY=sk-ant-api03-...            # Claude 3.5 Sonnet API key
```

**Notes:**
- `SUPABASE_SERVICE_KEY` is used by API routes for full database access
- `ANTHROPIC_API_KEY` is required for the AI chatbot feature
- Create `.env` file in project root (not `.env.local` for Vercel deployment)

### Python (homesignal.env)
Used by Python scripts (collect_data.py, predict_model.py)

```bash
# Data Collection APIs
PUBLIC_DATA_API_KEY=your_public_data_api_key    # 공공데이터포털 (data.go.kr)
ECOS_API_KEY=your_ecos_api_key                  # 한국은행 ECOS (ecos.bok.or.kr)

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key     # Same as SUPABASE_SERVICE_KEY above
```

**Notes:**
- API keys are optional for running `predict_model.py` (only needed for `collect_data.py`)
- `SUPABASE_KEY` should be the service role key for write access
- No `.env.example` file exists - use the examples shown above as templates
- **Never commit** `.env` or `homesignal.env` files (already in `.gitignore`)

### Environment Variable Files
```
.env              → Next.js frontend & API routes (create manually)
homesignal.env    → Python ML pipeline (create manually)
```

**IMPORTANT:**
- Never commit `.env` or `homesignal.env` files. They are already in `.gitignore`.
- No `.env.example` template file exists - use the examples shown in the sections above to create your environment files.

## Architecture & Data Flow

### 1. Data Collection (`collect_data.py`)
- Fetches apartment transaction data from 국토교통부 API (5 districts)
- Fetches interest rates from 한국은행 ECOS API
- Stores to Supabase tables: `apt_trade`, `apt_rent`, `interest_rate`
- Manual news signals stored in `news_signals` table

### 2. Feature Engineering (Supabase Views)
Run `supabase_views.sql` in Supabase SQL Editor to create views:

- **v_monthly_trade** - Monthly trade aggregates by dong
- **v_monthly_jeonse** - Monthly jeonse (전세) aggregates
- **v_monthly_wolse** - Monthly monthly rent (월세) aggregates
- **v_monthly_news_macro** - National news sentiment signals
- **v_monthly_news_local** - District-level news signals
- **v_model_features** - Unified feature view with 1-month lag joins (32 features total)

Features include:
- Transaction prices (매매가, 전세가) with lag 1-3 months
- Interest rates (기준금리, CD금리, 국고채3년) with lag
- Derived features (전세가율, MoM/YoY changes, seasonality)
- News signals (10 features: regulation, easing, redevelopment, transport, sentiment)

### 3. ML Prediction (`predict_model.py`)
Two models run in sequence:

**Model 1: Ridge Regression (동별 예측)**
- Predicts average price per dong for 1/2/3 months ahead
- Outputs: `prediction_result.csv` → `predictions` table

**Model 2: Hedonic GBM (아파트별 예측)**
- Predicts individual apartment prices using dong predictions + building attributes
- Outputs: `prediction_result_apt.csv` → `predictions_apt` table

Visualization outputs:
- `price_trend.png` - Time series of prices and rates
- `correlation_heatmap.png` - Feature correlations
- `importance_1m.png`, `importance_2m.png`, `importance_3m.png` - Feature importance
- `actual_vs_pred.png` - Prediction accuracy scatter plot

### 4. Frontend Dashboard (Next.js)

**Page Structure:**
- `app/page.tsx` - Main dashboard with search functionality
- State toggles between "home" (search page) and "dashboard" (results)

**API Routes:**
- `GET /api/predictions` - Latest dong-level predictions (from `predictions` table)
- `GET /api/predictions/apt` - Latest apartment-level predictions (from `predictions_apt` table)
- `GET /api/news` - Recent news signals
- `GET /api/trade-history` - Historical transaction data
- `POST /api/chat` - AI chatbot with RAG (Retrieval-Augmented Generation)

**Dashboard Tabs:**
1. **Overview** (`tabs/overview.tsx`) - KPIs, map, price chart, news feed, risk radar
2. **Region Analysis** (`tabs/region-analysis.tsx`) - District comparison table
3. **Price Trends** (`tabs/price-trends.tsx`) - Historical price trends with filters
4. **Apt Search** (`tabs/apt-search.tsx`) - Search apartments with predictions
5. **AI Report** (`tabs/ai-report.tsx`) - AI-generated market analysis

**Key Components:**
- `CollapsibleSidebar` - Tab navigation (5 main tabs)
- `HomeSearch` - Landing page search with district/dong selection
- `PricePredictionChart` - Recharts-based time series visualization
- `MapArea` - SVG-based Seoul district map
- `NewsSentimentFeed` - Real-time news signal display
- `GuDetailSheet` - District detail modal with prediction data
- `AIChatbot` - Floating chatbot with RAG-powered responses (uses `lib/rag-utils.ts`)

## TypeScript Configuration

- Strict mode enabled but build errors ignored (`next.config.mjs: ignoreBuildErrors: true`)
- Path alias: `@/*` maps to project root
- Target: ES6, Module: esnext

## Database Schema

**Core Tables:**
- `dongs` - Dong master (populated from `apt_trade`)
- `apartments` - Apartment master with FK to `dongs`
- `predictions` - Dong-level predictions (unique on `run_date`, `dong`)
- `predictions_apt` - Apartment-level predictions
- `apt_trade` - Raw transaction data (매매)
- `apt_rent` - Raw rental data (전월세)
- `interest_rate` - Monthly interest rates
- `news_signals` - News keyword signals

**Important:** `dongs.gu_name` column must be populated to enable local news features. Run `supabase_schema.sql` first, then `supabase_views.sql`.

## Development Workflow

### First-Time Setup

**Complete setup workflow for new developers:**

```bash
# 1. Clone and install dependencies
git clone <repository-url>
cd home_signal_ai
pnpm install  # or npm install
pip install -r requirements.txt

# 2. Configure environment variables
# Create .env file with Supabase and Anthropic keys (see Environment Variables section)
# Create homesignal.env with API keys (optional for initial testing)

# 3. Setup Supabase database
# In Supabase SQL Editor, run in order:
#   a. supabase_schema.sql
#   b. supabase_views.sql

# 4. Run system health check
python system_health_check.py
# → Fix any issues identified before proceeding

# 5. (Optional) Collect initial data
python collect_data.py full
# → Takes 30-60 minutes, skip if using existing data

# 6. Run prediction model
python test_ml_pipeline.py  # Validate setup first
python predict_model.py     # Generate predictions

# 7. Start development server
npm run dev
# → Open http://localhost:3000

# 8. Verify functionality
# - Search for an apartment
# - Check predictions display
# - Test AI chatbot (requires ANTHROPIC_API_KEY)
```

### Adding New Features

1. **Frontend Changes:**
   - Add UI components in `components/dashboard/` or `components/ui/`
   - Create new API routes in `app/api/` if needed
   - Update types in `lib/supabase.ts`

2. **ML Pipeline Changes:**
   - Modify feature engineering in `supabase_views.sql`
   - Update `predict_model.py` for new models or features
   - Test with `python predict_model.py`

3. **Database Changes:**
   - Update `supabase_schema.sql` for schema changes
   - Update `supabase_views.sql` for new features
   - Run both scripts in order in Supabase SQL Editor
   - Run `python test_ml_pipeline.py` to verify views

### Testing Predictions

1. Validate setup: `python test_ml_pipeline.py`
2. Ensure Supabase views are up to date
3. Run prediction model: `python predict_model.py`
4. Check output CSV files and PNG charts in project root
5. Verify data appears in dashboard at `http://localhost:3000`
6. Check API endpoints:
   - http://localhost:3000/api/predictions
   - http://localhost:3000/api/predictions/apt

### Scheduled Updates

The `monthly_update.bat` script can be registered with Windows Task Scheduler to automate monthly data collection:

```bat
cd /d "path\to\project"
python collect_data.py update >> logs\update.log 2>&1
```

## Testing and Diagnostics

The project includes comprehensive testing utilities to validate system configuration and health.

### System Health Check

Run the full system diagnostic to check all components:

```bash
python system_health_check.py
```

This script validates:
1. **Environment Variables** - Checks all required .env configurations
2. **Supabase Connection** - Tests database connectivity and table/view existence
3. **Data Availability** - Verifies core data exists (predictions, news, transactions)
4. **Python Packages** - Confirms all ML dependencies are installed
5. **Data Flow** - Visualizes the complete pipeline architecture

Output includes actionable recommendations for any issues found.

### ML Pipeline Validation

Test the ML pipeline setup before running predictions:

```bash
python test_ml_pipeline.py
```

Validates:
- Environment variables (`SUPABASE_URL`, `SUPABASE_KEY`, API keys)
- Supabase views existence (all 6 feature engineering views)
- `v_model_features` data availability
- Python package installations (pandas, numpy, sklearn, etc.)

**Use this before running `predict_model.py` for the first time.**

### Database Connection Test

Quick test for Supabase connectivity:

```bash
python test_supabase_connection.py
```

Checks:
- All 8 core tables (apt_trade, dongs, predictions, etc.)
- Row counts for each table
- Latest prediction data sample

### Frontend Testing

```bash
# Type checking (note: build errors ignored in next.config.mjs)
npx tsc --noEmit

# Lint check
npm run lint

# Development server
npm run dev
# → Manually test at http://localhost:3000
```

## Troubleshooting

### Common Issues

**Issue: "Module not found" when running Python scripts**
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Verify installation
python test_ml_pipeline.py
```

**Issue: "Supabase view not found" when running predict_model.py**
```bash
# Solution: Run SQL scripts in Supabase SQL Editor in order
# 1. supabase_schema.sql (creates tables)
# 2. supabase_views.sql (creates views)

# Verify views exist
python test_ml_pipeline.py
```

**Issue: Dashboard shows no prediction data**
```bash
# Solution: Check data pipeline in order
# Step 1: Verify Supabase connection
python test_supabase_connection.py

# Step 2: Run predictions
python predict_model.py

# Step 3: Check API endpoint
curl http://localhost:3000/api/predictions

# Step 4: Check browser console for errors
npm run dev
```

**Issue: AI Chatbot returns "API Error"**
```bash
# Solution: Check environment variables
# 1. Verify .env contains ANTHROPIC_API_KEY
# 2. Restart Next.js dev server
npm run dev

# 3. Check API route logs in terminal
```

**Issue: Korean fonts not rendering in ML charts (macOS/Linux)**
```python
# Solution: Edit predict_model.py (around line 20)
# Change from "Malgun Gothic" to:
# macOS: "AppleGothic" or "Arial Unicode MS"
# Linux: Install and use "NanumGothic"
plt.rcParams["font.family"] = "AppleGothic"  # macOS
```

**Issue: Data collection is very slow**
```bash
# This is normal - API rate limits require 1-second delays
# First-time collection (2020-present): ~30-60 minutes
# Monthly updates: ~5-10 minutes

# Use incremental updates instead of full collection:
python collect_data.py update
```

**Issue: Environment variables not loading**
```bash
# Frontend uses .env or .env.local
# Python uses homesignal.env
# Make sure correct file exists in project root

# Check what's loaded:
python system_health_check.py  # Shows all env vars
```

**Issue: Turbopack dev server fails on Windows (NUL device error)**
```bash
# Solution: Use webpack instead of Turbopack
npm run dev  # Uses webpack by default

# Or explicitly disable Turbopack:
TURBOPACK=0 npm run dev

# Note: next.config.mjs is configured to work with webpack on Windows
# The dev:turbo script is available but may not work on all Windows systems
```

## Important Notes

- **Package Manager:** pnpm is the preferred package manager (see `pnpm` config in package.json). npm also works but pnpm is recommended.
- **News Features:** 1-month lag prevents look-ahead bias. Pre-2026-02 data has news features set to 0.
- **Target Districts:** Only 5 districts (동대문구, 성북구, 중랑구, 강북구, 도봉구). Do not add other districts without updating `collect_data.py:TARGET_DISTRICTS`.
- **Font Rendering:** ML script uses "Malgun Gothic" for Korean. May need adjustment on non-Windows systems (see Troubleshooting section).
- **API Rate Limits:** 공공데이터포털 API has rate limits. `collect_data.py` includes 1-second delays between requests.
- **Vercel Deployment:** `vercel.json` configured for hybrid Next.js + Python deployment (Python backend not actively used).
- **Test Scripts:** Always run `system_health_check.py` or `test_ml_pipeline.py` before reporting issues - they provide detailed diagnostics.
- **Tailwind CSS 4:** Uses new CSS-first configuration (no traditional config file). See Component Patterns section.
- **Windows Development:** Turbopack may have issues on Windows - use standard `npm run dev` which uses webpack by default.

## Component Patterns

- Use `"use client"` directive for interactive components
- Radix UI components imported from `@/components/ui/`
- Styling via Tailwind CSS 4 with `cn()` utility for conditional classes
  - **Note:** This project uses Tailwind CSS 4's new CSS-first configuration
  - No traditional `tailwind.config.js` file - configuration is in `@tailwindcss/postcss` plugin
  - Global styles defined in `app/globals.css`
- Framer Motion for animations (AnimatePresence, motion.div)
- Recharts for data visualization
- React Hook Form + Zod for form validation (if adding forms)

## Supabase Client Usage

```typescript
import { supabase } from "@/lib/supabase";

// Query example
const { data, error } = await supabase
  .from("predictions")
  .select("*")
  .order("run_date", { ascending: false })
  .limit(100);
```

**Note:** API routes use `SUPABASE_SERVICE_KEY` for full access. Frontend should use `NEXT_PUBLIC_SUPABASE_URL` with anon key (not currently configured).

## AI Chatbot & RAG System

The dashboard includes an AI-powered chatbot (`components/dashboard/ai-chatbot.tsx`) that uses Retrieval-Augmented Generation (RAG) to answer questions about the real estate market with live data from Supabase.

### Architecture

**Data Flow:**
```
User Question → Intent Analysis → Data Retrieval → Context Building → Claude API → Response
```

**Implementation:**

1. **User Query Analysis** (`lib/rag-utils.ts:analyzeUserIntent`)
   - Extracts intent type: prediction, news, comparison, trend, general
   - Parses location references (dong/gu names in Korean)
   - Identifies timeframe (1m/2m/3m)

2. **Data Retrieval** (`lib/rag-utils.ts:getRelevantData`)
   - Queries Supabase for relevant predictions, news, trade history
   - Filters by location if specified
   - Calculates statistics (averages, trends, confidence scores)

3. **Context Building** (`lib/rag-utils.ts:buildContextPrompt`)
   - Constructs structured prompt with fetched data
   - Includes latest predictions, news signals, and market stats
   - Formats data for optimal Claude understanding

4. **LLM Response** (`app/api/chat/route.ts`)
   - Calls Claude 3.5 Sonnet with context-enriched prompt
   - System message enforces data-grounded responses
   - Returns natural language answer based on real data

### Key Features

- **Intent Classification** - Automatically categorizes user questions
- **Location Parsing** - Extracts Seoul district/dong names from Korean queries
- **Live Data Integration** - Always uses latest predictions and news from database
- **Grounded Responses** - LLM instructed to only use provided data, no hallucinations
- **Statistical Analysis** - Calculates averages, trends, and confidence scores

### Example Queries

```typescript
// 1. Prediction query
"동대문구 아파트 가격 전망은?"
→ Returns predictions for Dongdaemun-gu with latest data

// 2. News query
"최근 부동산 뉴스 요약해줘"
→ Summarizes recent news_signals entries

// 3. Comparison query
"성북구랑 중랑구 비교해줘"
→ Compares predictions and trends for both districts

// 4. Trend analysis
"가장 상승률 높은 동은?"
→ Ranks dongs by predicted price change percentage
```

### API Usage

```typescript
// Frontend call (from ai-chatbot.tsx)
const response = await fetch("/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [
      { role: "user", content: "동대문구 아파트 가격 전망은?" }
    ]
  })
});

const data = await response.json();
console.log(data.message); // AI-generated response
```

**Dependencies:**
- `@anthropic-ai/sdk` - Claude API client
- `@supabase/supabase-js` - Database queries
- Environment variable: `ANTHROPIC_API_KEY` required

**Planning Documents:**
- See `docs/chatbot_upgrade_plan.md` for detailed implementation plan (Phase 1-3)
- Plan outlines migration from mock data to full RAG system

## Quick Reference

### Most Common Commands

```bash
# Daily Development
npm run dev                          # Start Next.js dev server (port 3000)
python predict_model.py              # Generate new predictions
python system_health_check.py        # Check all systems

# Data Pipeline
python collect_data.py update        # Collect latest data (monthly)
python test_ml_pipeline.py           # Validate before predictions

# Troubleshooting
python test_supabase_connection.py   # Test database connectivity
npm run lint                         # Check frontend code quality
npx tsc --noEmit                     # Check TypeScript errors
```

### Key File Locations

| Purpose | File Path |
|---------|-----------|
| Main dashboard | `app/page.tsx` |
| AI chatbot UI | `components/dashboard/ai-chatbot.tsx` |
| Chat API route | `app/api/chat/route.ts` |
| RAG utilities | `lib/rag-utils.ts` |
| Supabase client | `lib/supabase.ts` |
| ML prediction | `predict_model.py` |
| Data collection | `collect_data.py` |
| Database schema | `supabase_schema.sql` |
| Feature views | `supabase_views.sql` |

### Environment Files

| File | Used By | Purpose |
|------|---------|---------|
| `.env` | Next.js | Frontend + API routes config (create manually) |
| `homesignal.env` | Python | ML pipeline + data collection (create manually) |

**Note:** No template files exist - refer to the Environment Variables section for examples.

### API Endpoints

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/predictions` | GET | Dong-level predictions |
| `/api/predictions/apt` | GET | Apartment-level predictions |
| `/api/news` | GET | News sentiment signals |
| `/api/trade-history` | GET | Historical transaction data |
| `/api/chat` | POST | AI chatbot responses (RAG) |

### Supabase Tables

**Data Tables:**
- `apt_trade` - Raw transaction data
- `apt_rent` - Rental data (전월세)
- `interest_rate` - Monthly interest rates
- `news_signals` - News keyword signals

**Master Tables:**
- `dongs` - Dong master (must have `gu_name` populated)
- `apartments` - Apartment master

**Prediction Results:**
- `predictions` - Dong-level predictions (updated by predict_model.py)
- `predictions_apt` - Apartment-level predictions

**SQL Views (Feature Engineering):**
- `v_monthly_trade`, `v_monthly_jeonse`, `v_monthly_wolse`
- `v_monthly_news_macro`, `v_monthly_news_local`
- `v_model_features` - Main feature view (32 features)
