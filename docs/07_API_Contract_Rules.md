# HomeSignal AI — API 계약 규칙 (API Contract Rules)

**문서 버전:** 1.0  
**최종 수정일:** 2026-03-09  
**목적:** DB, 백엔드, 프론트엔드 담당자 간 공통 인터페이스 규칙 정의

---

## 개요

HomeSignal AI 프로젝트는 DB(Supabase), 백엔드(FastAPI), 프론트엔드(Next.js) 3개 레이어로 구성됩니다.
이 문서는 **각 담당자가 반드시 준수해야 하는 공통 규칙**을 정의하여 통합 시 발생하는 불일치를 방지합니다.

---

## 1. API 응답 스키마 통일

### 1.1 원칙: 백엔드 Pydantic 스키마가 SSOT (Single Source of Truth)

프론트엔드 TypeScript 타입은 **백엔드 Pydantic 스키마를 정확히 반영**해야 합니다.

### 1.2 주요 API 스키마 정의

#### Forecast API

**엔드포인트:** `GET/POST /api/v1/forecast`

**요청 (ForecastRequest):**
```json
{
  "region": "청량리동",
  "period": "month",
  "horizon": 3,
  "include_news_weight": true
}
```

**응답 (ForecastResponse):**
```json
{
  "region": "청량리동",
  "period": "month",
  "trend": "상승",
  "confidence": 0.85,
  "forecast": [
    {
      "date": "2026-04-01",
      "value": 105000000.0,
      "lower_bound": 100000000.0,
      "upper_bound": 110000000.0
    }
  ],
  "news_weights": [
    {
      "keyword": "GTX",
      "frequency": 45,
      "impact_score": 0.8
    }
  ],
  "model_version": "v1.0"
}
```

**필드 설명:**
- `forecast`: 예측 데이터 포인트 배열 (NOT `predictions`)
- `ForecastPoint.value`: 예측값 (NOT `predicted_price`)
- `trend`: `"상승"` | `"하락"` | `"보합"`
- `news_weights`: 뉴스 가중치 요약 (선택)

#### Chat API

**엔드포인트:** `POST /api/v1/chat`

**요청 (ChatRequest):**
```json
{
  "message": "동대문구 아파트 가격이 오를까요?",
  "session_id": "uuid-string",
  "region": "동대문구"
}
```

**응답 (ChatResponse):**
```json
{
  "answer": "동대문구 아파트 가격은 GTX-C 개통 호재로...",
  "sources": [
    {
      "title": "GTX-C 청량리역 개통 확정",
      "source": "한국경제 2024-12-01",
      "relevance_score": 0.92
    }
  ],
  "forecast_summary": {
    "trend": "상승",
    "confidence": 0.85,
    "next_month_prediction": 105000000.0
  },
  "session_id": "uuid-string",
  "fallback": false,
  "planner_metadata": {
    "intents_detected": ["forecast"],
    "sub_queries_count": 1,
    "execution_strategy": "simple",
    "planning_time_ms": 150,
    "is_simple_query": true
  }
}
```

**필드 설명:**
- `answer`: AI 생성 응답 (NOT `response`)
- `sources`: `SourceReference[]` - `{title, source, relevance_score}` (NOT `{title, url}`)
- `forecast_summary`: 시계열 예측 요약 (선택)
- `fallback`: AI API 장애 시 `true`
- `planner_metadata`: 쿼리 플래너 메타데이터 (디버깅용, 선택)

#### News Insights API

**엔드포인트:** `GET /api/v1/news/insights`

**쿼리 파라미터:**
- `period`: `"week"` | `"month"` | `"quarter"`
- `keywords`: 쉼표 구분 문자열 (예: `"GTX,재개발"`)
- `region`: 지역명 (기본: `"동대문구"`)
- `use_rise_points`: `"true"` | `"false"`

**응답 (NewsInsightsResponse):**
```json
{
  "region": "동대문구",
  "period": "month",
  "analysis_date": "2026-03-09",
  "total_articles": 156,
  "insights": [
    {
      "keyword": "GTX",
      "frequency": 45,
      "trend": "상승",
      "sentiment_score": 0.7,
      "sample_headlines": [
        "GTX-C 청량리역 2028년 개통 확정",
        "GTX 호재로 동대문구 집값 상승세"
      ]
    }
  ],
  "top_issues": [
    "GTX-C 개통 확정",
    "이문휘경 뉴타운 재개발 승인",
    "청량리역 복합개발 착공"
  ]
}
```

**필드 설명:**
- `insights`: `KeywordInsight[]` (NOT `keyword_frequencies`)
- `top_issues`: 주요 이슈 요약 (NOT `summary`)
- `total_articles`: 분석된 총 기사 수

### 1.3 프론트엔드 타입 정의 규칙

프론트엔드는 백엔드 스키마를 **정확히 반영**한 TypeScript 인터페이스를 사용합니다.

**위치:** `frontend/lib/api-client.ts` 또는 `frontend/types/api.ts`

**예시:**
```typescript
export interface ForecastResponse {
  region: string
  period: string
  trend: '상승' | '하락' | '보합'
  confidence: number
  forecast: ForecastPoint[]
  news_weights?: NewsWeightSummary[]
  model_version: string
}

export interface ForecastPoint {
  date: string  // ISO 8601
  value: number
  lower_bound: number
  upper_bound: number
}
```

---

## 2. 네이밍 컨벤션

### 2.1 계층별 네이밍 규칙

| 계층 | 규칙 | 예시 |
|------|------|------|
| **DB 테이블/컬럼** | `snake_case` | `houses_data`, `contract_date`, `published_at` |
| **DB RPC 파라미터** | `p_` 접두사 + `snake_case` | `p_region`, `p_start_date`, `p_period_type` |
| **백엔드 Python** | `snake_case` | `get_houses_time_series()`, `forecast_service` |
| **API JSON 필드** | `snake_case` | `{ "forecast_summary": {...} }` |
| **프론트엔드 TS (내부)** | `camelCase` | `forecastSummary`, `sessionId` |
| **API 경로** | `kebab-case` 또는 `snake_case` | `/api/v1/news/insights`, `/api/v1/ingest/houses` |

### 2.2 핵심 원칙

**API JSON 필드명은 `snake_case`로 통일** (FastAPI/Pydantic 기본값).

프론트엔드에서 내부적으로 camelCase 변환이 필요하면 별도 매핑 레이어를 사용하되, **API 통신 시에는 snake_case 유지**.

### 2.3 RPC 파라미터 예외

기존 `match_news_documents` RPC의 파라미터(`query_embedding`, `match_count` 등)는 `p_` 접두사 없이 유지 (하위 호환성).

**새로 추가하는 RPC는 반드시 `p_` 접두사 사용:**
```sql
CREATE OR REPLACE FUNCTION get_latest_predictions(
    p_region TEXT,
    p_period TEXT DEFAULT 'week',
    p_horizon INT DEFAULT 12
)
```

---

## 3. 에러 응답 포맷

### 3.1 표준 에러 응답 구조

모든 API 에러 응답은 아래 JSON 구조를 따릅니다:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자용 에러 메시지",
    "details": {}
  }
}
```

### 3.2 HTTP 상태 코드 매핑

| HTTP 코드 | 예외 타입 | 설명 |
|-----------|----------|------|
| `400` | `ValidationError` | 요청 파라미터 검증 실패 |
| `404` | `NotFoundError` | 리소스를 찾을 수 없음 |
| `500` | `DatabaseError` | 데이터베이스 오류 |
| `500` | `AIAPIError` | AI API 호출 오류 (일반) |
| `503` | `AIAPIError` (fallback) | AI API 장애 (fallback 응답 시에는 200 + `fallback: true`) |

### 3.3 에러 코드 목록

| 코드 | 설명 |
|------|------|
| `VALIDATION_ERROR` | 입력값 검증 실패 |
| `FORECAST_NOT_FOUND` | 예측 데이터 없음 |
| `REGION_NOT_SUPPORTED` | 지원하지 않는 지역 |
| `DATABASE_ERROR` | 데이터베이스 오류 |
| `AI_API_ERROR` | AI API 호출 실패 |
| `RATE_LIMIT_EXCEEDED` | API 호출 제한 초과 |
| `INTERNAL_SERVER_ERROR` | 내부 서버 오류 |

### 3.4 프론트엔드 에러 처리

프론트엔드는 `error.code` 기준으로 분기 처리:

```typescript
try {
  const result = await getForecast(params)
} catch (err) {
  if (err.error?.code === 'FORECAST_NOT_FOUND') {
    // 예측 데이터 없음 UI
  } else if (err.error?.code === 'AI_API_ERROR') {
    // AI 오류 안내 UI
  }
}
```

### 3.5 Fallback 응답 (AI API 장애 시)

AI API 장애 시에는 **HTTP 200 + `fallback: true`**로 응답:

```json
{
  "answer": "일시적 장애로 AI 해설을 생성하지 못했습니다. 예측 수치는 아래와 같습니다.",
  "sources": [],
  "forecast_summary": {
    "trend": "상승",
    "confidence": 0.85,
    "next_month_prediction": 105000000.0
  },
  "session_id": "uuid",
  "fallback": true
}
```

---

## 4. 날짜/시간 포맷

### 4.1 API JSON 포맷

**ISO 8601 표준 사용:**

- **날짜:** `"2026-03-09"` (YYYY-MM-DD)
- **날짜+시간:** `"2026-03-09T15:30:00+09:00"` (타임존 포함)
- **UTC 시간:** `"2026-03-09T06:30:00Z"`

### 4.2 데이터베이스 저장

- **날짜:** `DATE` 타입
- **날짜+시간:** `TIMESTAMPTZ` 타입 (UTC로 저장)

### 4.3 프론트엔드 표시

- **한국어 UI:** `YYYY.MM.DD` (예: `2026.03.09`)
- **상세 시간:** `YYYY.MM.DD HH:mm` (예: `2026.03.09 15:30`)

### 4.4 타임존 처리

- 백엔드는 UTC로 저장 및 전송
- 프론트엔드는 사용자 브라우저 타임존(서울 시간대)으로 변환하여 표시

---

## 5. 페이지네이션 및 필터 파라미터

### 5.1 표준 페이지네이션

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `limit` | `int` | `20` | 반환할 최대 레코드 수 (최대 100) |
| `offset` | `int` | `0` | 건너뛸 레코드 수 |

**예시:**
```
GET /api/v1/news/insights?limit=20&offset=40
```

### 5.2 표준 필터 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `region` | `string` | `"동대문구"` | 지역명 |
| `period` | `string` | `"month"` | 기간 단위 (`"week"` \| `"month"`) |
| `start_date` | `string` | - | 시작 날짜 (ISO 8601) |
| `end_date` | `string` | - | 종료 날짜 (ISO 8601) |
| `keywords` | `string` | - | 쉼표 구분 키워드 (예: `"GTX,재개발"`) |

### 5.3 정렬 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `sort_by` | `string` | - | 정렬 필드 (예: `"published_at"`) |
| `order` | `string` | `"desc"` | 정렬 순서 (`"asc"` \| `"desc"`) |

---

## 6. 지역명(region) 규칙

### 6.1 허용되는 지역명

**전체 지역:**
- `"동대문구"` (전체)
- `"전체"` (동대문구 전체의 별칭)

**세부 동:**
- `"청량리동"`
- `"이문동"`
- `"휘경동"`
- `"전농동"`
- `"답십리동"`
- `"장안동"`
- `"용두동"`
- `"제기동"`
- `"신설동"`

### 6.2 통일 규칙

DB/백엔드/프론트 모두 **동일한 문자열**을 사용합니다.

프론트엔드에서 UI 표시명이 다를 경우 별도 매핑 테이블을 사용하되, **API 통신 시에는 위 표준 지역명 사용**.

**예시:**
```typescript
// 프론트엔드 내부 매핑
const REGION_DISPLAY_NAMES = {
  '동대문구': '동대문구 전체',
  '청량리동': '청량리동',
  // ...
}

// API 호출 시에는 표준 지역명 사용
await getForecast({ region: '청량리동', ... })
```

### 6.3 유효성 검증

백엔드는 허용되지 않은 지역명에 대해 `400 REGION_NOT_SUPPORTED` 에러를 반환합니다.

---

## 7. API 버저닝

### 7.1 현재 버전

**현재 API 버전:** `v1`

**API 경로 prefix:** `/api/v1/`

### 7.2 버저닝 정책

**Breaking Change 발생 시:**
1. 새 버전 추가: `/api/v2/`
2. 기존 버전 유지: 최소 **3개월** 동안 `/api/v1/` 유지
3. 사전 공지: 변경 사항 및 마이그레이션 가이드 제공

**Non-breaking Change:**
- 새 필드 추가 (선택 필드)
- 새 엔드포인트 추가
- 버전 업그레이드 불필요

### 7.3 데이터베이스 스키마 버저닝

DB 스키마 변경 시 반드시 `migrations/` 폴더에 마이그레이션 파일 생성:

**파일명 규칙:** `{순번}_{설명}.sql`

**예시:**
- `001_setup_pgvector.sql`
- `002_add_ai_predictions_only.sql`
- `003_add_houses_data_columns.sql`

**실행 순서:** 순번대로 실행

---

## 8. 보안 및 인증

### 8.1 API 키 관리

| 키 | 저장 위치 | 용도 |
|-----|----------|------|
| `OPENAI_API_KEY` | 백엔드 환경변수 | AI API 호출 |
| `ANTHROPIC_API_KEY` | 백엔드 환경변수 | AI API 호출 |
| `SUPABASE_KEY` | 백엔드 환경변수 | Supabase anon 키 (SELECT) |
| `SUPABASE_SERVICE_ROLE_KEY` | 백엔드 환경변수 | Supabase service_role 키 (INSERT/UPDATE) |

**절대 금지:** 프론트엔드 환경변수(`NEXT_PUBLIC_*`)에 API 키 저장

### 8.2 CORS 설정

**개발 환경:**
```python
allow_origins=["http://localhost:3000"]
```

**프로덕션 환경:**
```python
allow_origins=["https://your-app.vercel.app"]
```

**절대 금지:** `allow_origins=["*"]` (프로덕션)

### 8.3 Ingest API 인증

Ingest API는 JWT 기반 역할(role) 인증 사용:

**헤더:**
```
Authorization: Bearer <supabase-jwt-token>
```

**역할 매핑:**
- `data_collector_molit`: `/api/v1/ingest/houses`
- `data_collector_news`: `/api/v1/ingest/news`
- `service_account`: `/api/v1/ingest/predictions`

---

## 9. 성능 및 캐싱

### 9.1 응답 시간 목표

| API | 목표 응답 시간 |
|-----|--------------|
| Forecast | 1.5초 이내 |
| Chat | 2.0초 이내 |
| News Insights | 1.0초 이내 |

### 9.2 캐싱 전략

**캐시 대상:**
- 시계열 예측 결과 (TTL: 1시간)
- 뉴스 인사이트 (TTL: 30분)

**캐시 키 구성:**
```
forecast:{region}:{period}:{horizon}
news_insights:{keywords}:{period}
```

**캐시 무효화:**
- 새 데이터 수집 시 (Ingest API 호출 시)
- TTL 만료 시

---

## 10. 테스트 및 검증

### 10.1 백엔드 테스트

**필수 테스트:**
- 각 API 엔드포인트의 정상 응답 검증
- 에러 케이스별 HTTP 상태 코드 및 에러 응답 포맷 검증
- Pydantic 스키마 검증 (입력/출력)

**테스트 위치:** `tests/test_*.py`

### 10.2 프론트엔드 테스트

**필수 테스트:**
- API 클라이언트 함수의 타입 안정성 검증
- 에러 응답 파싱 검증
- 날짜 포맷 변환 검증

### 10.3 통합 테스트

**시나리오:**
1. 프론트 → 백엔드 Forecast API 호출 → 응답 파싱
2. 프론트 → 백엔드 Chat API 호출 → 응답 파싱
3. 에러 케이스 (404, 500) → 에러 응답 파싱

---

## 11. 문서 업데이트 정책

### 11.1 스키마 변경 시

1. **백엔드 Pydantic 스키마 수정** (`src/*/schemas.py`)
2. **본 문서 업데이트** (`docs/07_API_Contract_Rules.md`)
3. **프론트엔드 타입 업데이트** (`frontend/lib/api-client.ts`)
4. **변경 사항 공지** (팀 채널 또는 문서)

### 11.2 문서 버전 관리

- 주요 변경 시 문서 버전 증가 (1.0 → 1.1 → 2.0)
- 변경 이력 기록 (최종 수정일 업데이트)

---

## 부록 A: 체크리스트

### DB 담당자

- [ ] 테이블/컬럼명은 `snake_case` 사용
- [ ] RPC 파라미터는 `p_` 접두사 사용 (신규)
- [ ] 날짜는 `DATE`, 날짜+시간은 `TIMESTAMPTZ` (UTC) 사용
- [ ] 마이그레이션 파일 순번 관리

### 백엔드 담당자

- [ ] Pydantic 스키마가 SSOT 역할
- [ ] API JSON 필드명은 `snake_case`
- [ ] 에러 응답은 표준 포맷 준수
- [ ] 날짜는 ISO 8601 포맷 사용
- [ ] CORS 설정은 프로덕션 도메인만 허용
- [ ] API 키는 환경변수로만 관리

### 프론트엔드 담당자

- [ ] TypeScript 타입은 백엔드 스키마와 정확히 일치
- [ ] API 통신 시 `snake_case` 필드명 사용
- [ ] 에러 응답 파싱 시 `error.code` 기준 분기
- [ ] 날짜 표시 시 한국어 포맷 변환
- [ ] API 키는 절대 프론트 환경변수에 저장 금지

---

**문서 작성자:** 시스템 아키텍트  
**검토자:** DB/Backend/Frontend 담당자  
**다음 검토일:** 2026-06-09
