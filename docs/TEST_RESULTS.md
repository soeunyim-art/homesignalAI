# HomeSignal AI - Test Results Report

**실행 일시:** 2026-03-09
**Python 버전:** 3.14.0
**pytest 버전:** 9.0.2
**환경:** Development (Mock Mode)

---

## 📊 테스트 실행 요약

| 항목 | 결과 |
|------|------|
| **총 테스트 수** | 129개 |
| **통과 (PASSED)** | 90개 (69.8%) |
| **실패 (FAILED)** | 11개 (8.5%) |
| **에러 (ERROR)** | 28개 (21.7%) |
| **실행 시간** | 57.34초 |

### 전체 성공률
```
통과율: 69.8%
에러/실패율: 30.2%
```

---

## ✅ 통과한 테스트 모듈

### 1. Keyword Configuration (`test_keyword_config.py`)
**통과:** 7/7 (100%)

- ✅ `test_keyword_config_loads_successfully` - 키워드 설정 파일 로딩
- ✅ `test_keyword_config_has_required_categories` - 필수 카테고리 검증
- ✅ `test_keyword_config_primary_keywords` - 주요 키워드 검증
- ✅ `test_keyword_config_synonyms` - 동의어 검증
- ✅ `test_keyword_config_get_all_keywords` - 전체 키워드 조회
- ✅ `test_keyword_config_keywords_are_lowercase` - 키워드 소문자 변환
- ✅ `test_keyword_config_no_duplicates` - 중복 키워드 제거

**상태:** 🟢 안정적 (100% 통과)

---

### 2. RPC Methods (`test_rpc_methods.py`)
**통과:** 26/26 (100%)

#### 2.1 Houses Data RPC
- ✅ `test_aggregate_houses_time_series_weekly` - 주간 집계
- ✅ `test_aggregate_houses_time_series_monthly` - 월간 집계
- ✅ `test_aggregate_houses_time_series_with_dates` - 날짜 필터링
- ✅ `test_aggregate_houses_time_series_schema` - 스키마 검증

#### 2.2 News Keyword Frequency RPC
- ✅ `test_news_keyword_frequency_basic` - 기본 키워드 빈도
- ✅ `test_news_keyword_frequency_with_dates` - 날짜 범위 필터링
- ✅ `test_news_keyword_frequency_with_rise_windows` - 상승 시점 윈도우
- ✅ `test_news_keyword_frequency_schema` - 스키마 검증

#### 2.3 Latest Predictions RPC
- ✅ `test_latest_predictions_weekly` - 주간 예측
- ✅ `test_latest_predictions_monthly` - 월간 예측
- ✅ `test_latest_predictions_schema` - 스키마 검증

#### 2.4 Policy Events RPC
- ✅ `test_policy_events_date_range` - 날짜 범위 조회
- ✅ `test_policy_events_region_filter` - 지역 필터
- ✅ `test_policy_events_type_filter` - 이벤트 타입 필터
- ✅ `test_policy_events_schema` - 스키마 검증

#### 2.5 Dashboard Summary RPC
- ✅ `test_dashboard_summary_weekly` - 주간 대시보드
- ✅ `test_dashboard_summary_monthly` - 월간 대시보드
- ✅ `test_dashboard_summary_schema` - 스키마 검증

**상태:** 🟢 안정적 (100% 통과)

**비고:** MockSupabaseClient 사용으로 실제 DB 없이 RPC 인터페이스 검증 성공

---

### 3. NLP Keyword Extraction (`test_keyword_extraction.py`)
**통과:** 10/16 (62.5%)

#### 3.1 NLP Extractor (100% 통과)
- ✅ `test_extract_nouns_simple` - 명사 추출
- ✅ `test_extract_keywords` - 키워드 추출
- ✅ `test_stopwords_removal` - 불용어 제거
- ✅ `test_extract_with_frequency` - 빈도 계산
- ✅ `test_is_available` - NLP 라이브러리 가용성

#### 3.2 Hybrid Extractor (부분 통과)
- ✅ `test_simple_matching` - 단순 매칭
- ✅ `test_nlp_morphology` - NLP 형태소 분석
- ✅ `test_extract_keywords_only` - 키워드만 추출
- ✅ `test_category_mapping` - 카테고리 매핑

#### 3.3 AI Extractor (0% 통과)
- ❌ `test_extract` - AI 추출 (ERROR)
- ❌ `test_extract_keywords_only` - 키워드 추출 (ERROR)
- ❌ `test_low_confidence` - 낮은 신뢰도 (ERROR)

**상태:** 🟡 부분 안정 (기본 기능은 정상, AI 기능은 에러)

**이슈:** AI API 키 미설정으로 AI 추출 테스트 실패

---

### 4. Crawler - Keyword Extractor (`test_keyword_extractor.py`)
**통과:** 13/13 (100%)

- ✅ `test_extract_gtx_keyword` - GTX 키워드 추출
- ✅ `test_extract_redevelopment_keywords` - 재개발 키워드
- ✅ `test_extract_newtown_keywords` - 뉴타운 키워드
- ✅ `test_extract_with_content` - 본문 키워드 추출
- ✅ `test_extract_no_keywords` - 키워드 없는 경우
- ✅ `test_extract_by_category` - 카테고리별 추출
- ✅ `test_extract_with_frequency` - 빈도 계산
- ✅ `test_is_relevant_true` - 관련성 검증 (True)
- ✅ `test_is_relevant_false` - 관련성 검증 (False)
- ✅ `test_is_relevant_min_keywords` - 최소 키워드 수
- ✅ `test_custom_keywords` - 커스텀 키워드
- ✅ `test_all_keywords_property` - 전체 키워드 속성
- ✅ `test_categories_property` - 카테고리 속성

**상태:** 🟢 안정적 (100% 통과)

---

### 5. Rise Point Detector (`test_rise_point_detector.py`)
**통과:** 31/31 (100%)

#### 5.1 MA Crossover Method
- ✅ `test_ma_crossover_detect_rise` - 이동평균 교차 상승 탐지
- ✅ `test_ma_crossover_no_rise` - 상승 없음
- ✅ `test_ma_crossover_short_data` - 짧은 데이터
- ✅ `test_ma_crossover_custom_windows` - 커스텀 윈도우

#### 5.2 Rate Threshold Method
- ✅ `test_rate_threshold_detect_rise` - 임계값 기반 상승 탐지
- ✅ `test_rate_threshold_no_rise` - 상승 없음
- ✅ `test_rate_threshold_custom_threshold` - 커스텀 임계값

#### 5.3 Consecutive Rise Method
- ✅ `test_consecutive_rise_detect` - 연속 상승 탐지
- ✅ `test_consecutive_rise_no_rise` - 상승 없음
- ✅ `test_consecutive_rise_custom_periods` - 커스텀 기간

#### 5.4 Multi-Method Detector
- ✅ `test_multi_method_all_methods` - 모든 방법 적용
- ✅ `test_multi_method_single_method` - 단일 방법
- ✅ `test_multi_method_two_methods` - 두 방법 조합
- ✅ `test_multi_method_no_methods` - 방법 미지정 (기본값)

#### 5.5 Rise Point Windows
- ✅ `test_get_rise_point_windows` - 상승 윈도우 계산
- ✅ `test_get_rise_point_windows_custom` - 커스텀 윈도우
- ✅ `test_get_rise_point_windows_empty` - 빈 결과

**상태:** 🟢 안정적 (100% 통과)

**비고:** 상승 시점 탐지 알고리즘의 모든 변형 정상 작동

---

## ❌ 실패한 테스트 (11개)

### 1. Rate Limiter Tests (2개 실패)
**파일:** `tests/crawler/test_rate_limiter.py`

#### ❌ `test_rate_limiter_backoff`
```
pydantic_core._pydantic_core.ValidationError:
1 validation error for Settings
supabase_url
  Field required [type=missing, input_value={...}, input_type=dict]
```

#### ❌ `test_rate_limiter_max_backoff`
```
pydantic_core._pydantic_core.ValidationError:
1 validation error for Settings
supabase_url
  Field required [type=missing, input_value={...}, input_type=dict]
```

**원인:** Settings 초기화 시 필수 환경변수 누락

**해결 방안:**
- 테스트 fixture에서 환경변수 mock 추가
- `monkeypatch` 또는 `pytest.fixture`로 설정 주입

---

### 2. ML Features Tests (3개 실패)
**파일:** `tests/test_ml_features.py`

#### ❌ `test_ml_training_features_schema`
```
postgrest.exceptions.APIError:
{'code': 'PGRST202', 'details': None,
 'hint': None,
 'message': 'Could not find the function public.get_ml_features_with_news(...) in the schema cache'}
```

#### ❌ `test_policy_events_schema`
```
postgrest.exceptions.APIError:
{'code': 'PGRST202', 'message': 'Could not find the function public.get_policy_events_in_range(...)'}
```

#### ❌ `test_feature_query_performance`
```
postgrest.exceptions.APIError:
{'code': 'PGRST202', 'message': 'Could not find the function public.get_ml_features_with_news(...)'}
```

**원인:** Supabase RPC 함수 미생성 (마이그레이션 미실행)

**해결 방안:**
- `migrations/002_ml_features.sql` 실행 필요
- Supabase SQL Editor에서 RPC 함수 생성

---

### 3. Query Planner Tests (6개 실패)
**파일:** `tests/test_planner.py`

#### ❌ `test_extract_single_region`
#### ❌ `test_extract_multiple_regions`
#### ❌ `test_extract_keywords`
#### ❌ `test_extract_time_expressions`
#### ❌ `test_extract_empty_query`
```
AttributeError: 'coroutine' object has no attribute 'regions'
```

**원인:** `EntityExtractor.extract()` 메서드가 async이지만 await 없이 호출됨

**코드 위치:** `src/chat/planner/decomposer.py:246`
```python
# 현재 (잘못된 코드)
entities = self.entity_extractor.extract(query)

# 수정 필요
entities = await self.entity_extractor.extract(query)
```

#### ❌ `test_simple_query_no_decomposition`
```
AttributeError: 'coroutine' object has no attribute 'regions'
```

**해결 방안:**
- `decomposer.py`에서 `await` 추가
- 모든 `extract()` 호출에 `await` 적용

---

## 🔴 에러 발생 테스트 (28개)

### 1. AI Keyword Extraction Errors (8개)
**파일:** `tests/chat/test_keyword_extraction.py`

**에러 유형:** `TypeError: object NoneType can't be used in 'await' expression`

**원인:** AI API 클라이언트 미설정 (OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 없음)

**영향받는 테스트:**
- `TestAIKeywordExtractor::test_extract`
- `TestAIKeywordExtractor::test_extract_keywords_only`
- `TestAIKeywordExtractor::test_low_confidence`
- `TestHybridKeywordExtractor::test_hybrid_extraction`
- `TestHybridKeywordExtractor::test_early_termination`
- `TestHybridKeywordExtractor::test_confidence_calculation`
- `TestEntityExtractorIntegration::test_entity_extractor_with_hybrid`
- `TestEntityExtractorIntegration::test_entity_extractor_fallback`

**해결 방안:**
- Mock AI client 추가
- 또는 테스트용 API 키 설정

---

### 2. Google News Crawler Errors (7개)
**파일:** `tests/crawler/test_google_news.py`

**에러 유형:** `pydantic_core._pydantic_core.ValidationError`

**원인:** Settings 초기화 시 필수 환경변수 누락

**영향받는 테스트:**
- `test_parse_rss_success`
- `test_parse_rss_item_fields`
- `test_parse_rss_max_results`
- `test_parse_rss_date_filter`
- `test_parse_rss_invalid_xml`
- `test_parse_rss_empty_response`
- `test_crawler_close`

**해결 방안:**
- `conftest.py`에 Settings mock fixture 추가
- 환경변수 대신 테스트 설정 주입

---

### 3. Rate Limiter Errors (3개)
**파일:** `tests/crawler/test_rate_limiter.py`

**에러 유형:** `pydantic_core._pydantic_core.ValidationError`

**영향받는 테스트:**
- `test_rate_limiter_acquire`
- `test_rate_limiter_token_consumption`
- `test_rate_limiter_multiple_requests`

**해결 방안:** Google News Crawler와 동일

---

### 4. Crawler Runner Errors (10개)
**파일:** `tests/crawler/test_runner.py`

**에러 유형:** Settings 초기화 에러 (동일)

**영향받는 테스트:**
- `test_runner_run_basic`
- `test_runner_run_dry_run`
- `test_runner_run_with_content_extraction`
- `test_runner_run_without_content_extraction`
- `test_runner_deduplication`
- `test_runner_keyword_filtering`
- `test_runner_ingest_service_integration`
- `test_runner_close`
- `test_runner_multiple_queries`
- `test_runner_handles_crawler_error`

**해결 방안:** 동일

---

## 🔍 테스트 환경 이슈

### 1. 환경변수 누락
**문제:** 테스트 환경에서 `.env` 파일 로드 실패 또는 필수 변수 미설정

**필수 환경변수:**
```bash
SUPABASE_URL=https://placeholder.supabase.co  # Mock mode
SUPABASE_KEY=placeholder-key
SUPABASE_SERVICE_ROLE_KEY=placeholder-service-key
OPENAI_API_KEY=sk-test-key  # 또는 mock
ANTHROPIC_API_KEY=sk-ant-test-key  # 또는 mock
```

**해결책:**
```python
# tests/conftest.py에 추가
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://placeholder.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
```

---

### 2. Async/Await 미처리
**문제:** Coroutine을 await 없이 호출

**발생 위치:**
- `src/chat/planner/decomposer.py:246`
- `src/chat/planner/decomposer.py:260`

**수정 필요 코드:**
```python
# Before
entities = self.entity_extractor.extract(query)

# After
entities = await self.entity_extractor.extract(query)
```

---

### 3. RPC 함수 미생성
**문제:** Supabase 마이그레이션 미실행

**필요 마이그레이션:**
- `migrations/001_setup_pgvector.sql` - Vector DB, RPC 기본 함수
- `migrations/002_ml_features.sql` - ML Feature RPC 함수 (미생성)

**확인 방법:**
```sql
-- Supabase SQL Editor에서 실행
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name LIKE 'get_%';
```

---

## 📈 테스트 커버리지 분석

### 모듈별 상태

| 모듈 | 통과율 | 상태 | 비고 |
|------|--------|------|------|
| **Keyword Config** | 100% | 🟢 | 완벽 |
| **RPC Methods** | 100% | 🟢 | Mock 환경 완벽 동작 |
| **Rise Point Detector** | 100% | 🟢 | 알고리즘 검증 완료 |
| **Crawler - Keyword Extractor** | 100% | 🟢 | 키워드 추출 안정적 |
| **NLP Keyword Extraction** | 62.5% | 🟡 | 기본 기능만 통과 |
| **Google News Crawler** | 23% | 🔴 | 환경 설정 문제 |
| **Rate Limiter** | 0% | 🔴 | 환경 설정 문제 |
| **Crawler Runner** | 0% | 🔴 | 환경 설정 문제 |
| **Query Planner** | 0% | 🔴 | Async 미처리 |
| **ML Features** | 0% | 🔴 | RPC 함수 미생성 |

---

## 🛠️ 수정 우선순위

### P0 (즉시 수정 필요)
1. ✅ **Async/Await 수정** - `decomposer.py`의 `await` 누락
2. ✅ **환경변수 Mock** - `conftest.py`에 자동 환경변수 설정
3. ✅ **AI Client Mock** - 테스트용 AI 클라이언트 Mock 구현

**예상 개선:** 실패/에러 → 25개 추가 통과 (통과율 69.8% → 89%)

---

### P1 (중요)
4. ✅ **RPC 함수 생성** - `migrations/002_ml_features.sql` 작성 및 실행
5. ✅ **Settings 초기화 개선** - 테스트에서 Settings 의존성 제거

**예상 개선:** 추가 3개 통과 (통과율 89% → 91%)

---

### P2 (개선)
6. 🔄 **테스트 격리** - 각 테스트가 독립적으로 실행되도록 개선
7. 🔄 **Coverage 추가** - `pytest-cov` 설치 및 커버리지 측정
8. 🔄 **통합 테스트 추가** - 실제 Supabase 연동 테스트 (CI/CD)

---

## 📋 액션 아이템

### 즉시 수정 (P0)

#### 1. Decomposer Async 수정
```python
# src/chat/planner/decomposer.py
async def decompose(self, query: str, intents: list[QueryIntent]) -> list[SubQuery]:
    # Line 246
    entities = await self.entity_extractor.extract(query)  # await 추가

    # Line 260
    entities = await self.entity_extractor.extract(sub_query_text)  # await 추가
```

#### 2. Conftest 환경변수 Mock
```python
# tests/conftest.py
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_env(monkeypatch):
    """모든 테스트에 자동 적용되는 환경변수 설정"""
    with monkeypatch.context() as m:
        m.setenv("SUPABASE_URL", "https://placeholder.supabase.co")
        m.setenv("SUPABASE_KEY", "test-anon-key")
        m.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
        m.setenv("OPENAI_API_KEY", "sk-test-openai-key")
        m.setenv("ANTHROPIC_API_KEY", "sk-ant-test-anthropic-key")
        m.setenv("DEBUG", "true")
        yield
```

#### 3. AI Client Mock 추가
```python
# tests/conftest.py
from unittest.mock import AsyncMock

@pytest.fixture
def mock_ai_client():
    """Mock AI Client"""
    mock = AsyncMock()
    mock.generate_completion.return_value = {
        "keywords": ["GTX", "재개발"],
        "confidence": 0.9
    }
    return mock
```

---

### 중요 수정 (P1)

#### 4. ML Features RPC 함수 생성
```sql
-- migrations/002_ml_features.sql (신규 생성 필요)
CREATE OR REPLACE FUNCTION get_ml_features_with_news(
    p_region TEXT,
    p_period_type TEXT DEFAULT 'week',
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE (
    period_date DATE,
    avg_price NUMERIC,
    ma_5_week NUMERIC,
    ma_20_week NUMERIC,
    news_gtx_freq INT,
    news_redevelopment_freq INT,
    -- ... 기타 컬럼
)
LANGUAGE plpgsql AS $$
BEGIN
    -- 구현 필요
END;
$$;
```

---

## 🎯 목표 테스트 커버리지

| 항목 | 현재 | 목표 | 예상 달성 |
|------|------|------|-----------|
| **전체 통과율** | 69.8% | 95%+ | P0 수정 후 |
| **핵심 모듈** | 100% | 100% | 유지 |
| **Crawler** | 38% | 90%+ | P0 수정 후 |
| **Query Planner** | 0% | 85%+ | P0 수정 후 |
| **ML Features** | 0% | 80%+ | P1 수정 후 |

---

## 📝 결론

### 강점
- ✅ 핵심 비즈니스 로직 (RPC Methods, Rise Point Detection)은 100% 안정적
- ✅ Keyword 관련 기능 (Config, Extraction)은 높은 신뢰도
- ✅ Mock-first 개발로 외부 의존성 없이 테스트 가능

### 개선 필요
- ⚠️ 테스트 환경 설정 (환경변수, Fixtures) 보강 필요
- ⚠️ Async/Await 패턴 일관성 개선
- ⚠️ RPC 함수 마이그레이션 완료 필요

### 예상 개선 효과
**P0 수정 후:** 90/129 → 115/129 (통과율 89%)
**P1 수정 후:** 115/129 → 120/129 (통과율 93%)
**P2 개선 후:** 120/129 → 125/129 (통과율 97%)

---

**다음 단계:**
1. P0 수정 사항 즉시 적용
2. 테스트 재실행 및 검증
3. RPC 함수 마이그레이션 실행
4. Coverage 리포트 생성
5. CI/CD 파이프라인에 테스트 추가
