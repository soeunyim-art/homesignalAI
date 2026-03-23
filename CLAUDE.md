# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HomeSignal AI is a real estate price prediction platform for Seoul's northeast districts (동대문구, 성북구, 중랑구, 강북구, 도봉구). It combines machine learning models with a Next.js dashboard to predict apartment prices 1-3 months ahead using transaction data, interest rates, and news sentiment signals.

**Tech Stack:**
- Frontend: Next.js 16 (React 19, TypeScript), Tailwind CSS 4, Radix UI components
- Backend: Python data pipeline (scikit-learn, pandas), Next.js API routes
- Database: Supabase (PostgreSQL)
- Deployment: Vercel

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
│   └── utils.ts            # cn() utility for class merging
├── collect_data.py          # Data collection pipeline (국토부 + ECOS API)
├── predict_model.py         # ML prediction pipeline (Ridge + GBM)
├── supabase_schema.sql      # Database schema (tables: dongs, apartments, predictions, predictions_apt)
├── supabase_views.sql       # SQL views for feature engineering (v_model_features)
└── requirements.txt         # Python dependencies
```

## Common Development Commands

### Frontend (Next.js)

```bash
# Install dependencies
npm install
# or
pnpm install

# Development server
npm run dev          # http://localhost:3000

# Production build
npm run build
npm run start

# Linting
npm run lint
```

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
```

**Note:** Python scripts require `homesignal.env` file (see `.env.example`). The ML pipeline must be run manually - no automated scheduler is configured by default.

## Environment Variables

### Frontend (.env or .env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
```

### Python (homesignal.env)
```bash
PUBLIC_DATA_API_KEY=your_public_data_api_key    # 공공데이터포털
ECOS_API_KEY=your_ecos_api_key                  # 한국은행 ECOS
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
```

**IMPORTANT:** Never commit `.env` or `homesignal.env` files. Use `.env.example` as template.

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

### Testing Predictions

1. Ensure Supabase views are up to date
2. Run `python predict_model.py` locally
3. Check output CSV files and PNG charts
4. Verify data appears in dashboard at `http://localhost:3000`

### Scheduled Updates

The `monthly_update.bat` script can be registered with Windows Task Scheduler to automate monthly data collection:

```bat
cd /d "path\to\project"
python collect_data.py update >> logs\update.log 2>&1
```

## Important Notes

- **News Features:** 1-month lag prevents look-ahead bias. Pre-2026-02 data has news features set to 0.
- **Target Districts:** Only 5 districts (동대문구, 성북구, 중랑구, 강북구, 도봉구). Do not add other districts without updating `collect_data.py:TARGET_DISTRICTS`.
- **Font Rendering:** ML script uses "Malgun Gothic" for Korean. May need adjustment on non-Windows systems.
- **API Rate Limits:** 공공데이터포털 API has rate limits. `collect_data.py` includes 1-second delays between requests.
- **Vercel Deployment:** `vercel.json` configured for hybrid Next.js + Python deployment (Python backend not actively used).

## Component Patterns

- Use `"use client"` directive for interactive components
- Radix UI components imported from `@/components/ui/`
- Styling via Tailwind CSS with `cn()` utility for conditional classes
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
