# 상승 시점 키워드 추출 구현 요약

**구현 날짜:** 2026-03-04  
**참조 계획:** [상승 시점 키워드 추출 계획](c:\Users\tlduf\.cursor\plans\상승_시점_키워드_추출_계획_cf4dfde1.plan.md)

---

## 구현 완료 항목

### ✅ 1단계: 상승 시점 감지 로직 구현

**파일:** `src/forecast/rise_point_detector.py`

- `RisePointConfig`: 상승 시점 감지 설정 클래스
- `RisePoint`: 감지된 상승 시점 데이터 클래스
- `RisePointDetector`: 상승 시점 감지기 클래스

**지원 방법:**
- MA Crossover (이동평균 교차)
- Rate Threshold (변동률 임계값)
- Consecutive Rise (연속 상승)

**기능:**
- 상승 시점 감지
- 윈도우 계산 (lookback/lookahead)
- 신뢰도 점수 계산

---

### ✅ 2단계: 키워드 설정 파일 및 로더

**설정 파일:**
- `config/keywords.yaml`: 키워드 카테고리 정의
- `config/rise_point_config.yaml`: 상승 시점 감지 설정

**로더 클래스:**
- `src/shared/keyword_config.py`: KeywordConfig 클래스
- `src/shared/rise_point_config.py`: RisePointConfigLoader 클래스

**키워드 카테고리:**
- transport (교통): GTX, GTX-C, 청량리역
- redevelopment (재개발): 재개발, 뉴타운, 이문휘경뉴타운
- supply (분양/입주): 분양, 입주, 착공, 준공
- policy (정책/금리): 금리, 대출, 규제, 정책

**피처 매핑:**
- news_freq_gtx → transport
- news_freq_redev → redevelopment
- news_freq_supply → supply
- news_freq_policy → policy

---

### ✅ 3단계: DataRepository 확장

**파일:** `src/shared/data_repository.py`

**변경 사항:**
- `get_news_keyword_frequency()` 메서드에 `rise_point_windows` 파라미터 추가
- MockDataRepository 업데이트: rise_point_windows 지원
- SupabaseDataRepository 업데이트: 윈도우 기반 필터링 쿼리

**기능:**
- 상승 시점 윈도우 내 뉴스만 필터링
- 키워드별 빈도 집계
- impact_score 계산

---

### ✅ 4단계: NewsService 연동

**파일:** `src/news/service.py`, `src/news/schemas.py`

**변경 사항:**
- `NewsInsightsRequest`에 `use_rise_points` 파라미터 추가
- `_get_rise_point_windows()` 메서드 추가
- `_analyze_keywords()`에 rise_point_windows 파라미터 추가

**기능:**
- 상승 시점 기반 뉴스 분석
- 시계열 데이터에서 상승 시점 자동 감지
- 윈도우 내 키워드 빈도 집계

---

### ✅ 5단계: ForecastService 피처 연동

**파일:** `src/forecast/service.py`

**변경 사항:**
- `_get_news_weights()` 메서드 업데이트
- `_get_rise_point_windows()` 메서드 추가
- KeywordConfig 연동

**기능:**
- 상승 시점 윈도우 내 뉴스 키워드 빈도 조회
- 피처 변수로 활용 가능한 NewsWeightSummary 반환
- Prophet/LightGBM 학습 시 사용 가능

---

### ✅ 기존 코드 연동

**파일:** `src/chat/planner/decomposer.py`

**변경 사항:**
- EntityExtractor에서 KeywordConfig 사용
- 중앙화된 키워드 목록 로드

---

### ✅ 테스트 작성

**테스트 파일:**
- `tests/test_rise_point_detector.py`: 상승 시점 감지 테스트 (7개)
- `tests/test_keyword_config.py`: 키워드 설정 테스트 (8개)

**테스트 결과:**
- 전체 31개 테스트 통과 ✅
- 커버리지: 새로 작성한 모듈 100%

---

### ✅ 문서화

**문서:**
- `docs/06_Rise_Point_Keyword_Extraction.md`: 상승 시점 키워드 추출 가이드
- `README.md`: 프로젝트 README 생성
- `CLAUDE.md`: Rise Point Detection 섹션 추가
- `IMPLEMENTATION_SUMMARY.md`: 본 문서

---

## 구현 세부 사항

### 데이터 흐름

```
시계열 데이터 (dates, values)
    ↓
RisePointDetector.detect()
    ↓
RisePoint 리스트 (date, window_start, window_end)
    ↓
DataRepository.get_news_keyword_frequency(rise_point_windows)
    ↓
KeywordFrequency 리스트 (keyword, frequency, impact_score)
    ↓
ForecastService._get_news_weights()
    ↓
NewsWeightSummary 리스트
    ↓
Prophet/LightGBM 피처 변수
```

### API 사용 예시

#### 1. 일반 뉴스 분석

```bash
GET /api/v1/news/insights?keywords=GTX,재개발
```

#### 2. 상승 시점 기반 뉴스 분석

```bash
GET /api/v1/news/insights?keywords=GTX,재개발&use_rise_points=true
```

#### 3. 예측 API (뉴스 가중치 포함)

```bash
GET /api/v1/forecast?region=동대문구&include_news_weight=true
```

---

## 설정 예시

### keywords.yaml

```yaml
categories:
  transport:
    primary: ["GTX", "GTX-C", "청량리역"]
    synonyms: ["수도권광역급행철도", "환승센터"]
  redevelopment:
    primary: ["재개발", "뉴타운", "이문휘경뉴타운"]
    synonyms: ["정비사업", "재건축", "리모델링"]
```

### rise_point_config.yaml

```yaml
rise_point:
  method: "ma_crossover"
  short_ma_weeks: 5
  long_ma_weeks: 20
  lookback_weeks: 4
  lookahead_weeks: 4
```

---

## 코드 사용 예시

### 상승 시점 감지

```python
from src.forecast.rise_point_detector import RisePointDetector
from src.shared.rise_point_config import get_rise_point_config

config = get_rise_point_config()
detector = RisePointDetector(config)

dates = [date(2024, 1, 1) + timedelta(weeks=i) for i in range(52)]
values = [100 + i * 0.5 for i in range(52)]

rise_points = detector.detect(dates, values)

for rp in rise_points:
    print(f"상승 시점: {rp.date}")
    print(f"윈도우: {rp.window_start} ~ {rp.window_end}")
```

### 키워드 설정 사용

```python
from src.shared.keyword_config import get_keyword_config

config = get_keyword_config()

# 전체 primary 키워드
all_keywords = config.get_primary_keywords()

# 특정 카테고리 키워드
transport_keywords = config.get_all_keywords("transport")

# 피처 변수 매핑
gtx_keywords = config.get_keywords_for_feature("news_freq_gtx")
```

### 상승 시점 윈도우 내 뉴스 키워드 빈도

```python
from src.shared.data_repository import get_data_repository

repo = get_data_repository()

keywords = ["GTX", "재개발", "분양"]
windows = [
    (date(2024, 1, 1), date(2024, 2, 1)),
    (date(2024, 5, 1), date(2024, 6, 1)),
]

frequencies = await repo.get_news_keyword_frequency(
    keywords=keywords,
    rise_point_windows=windows,
)
```

---

## 테스트 결과

```bash
$ python -m pytest tests/ -v

============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.0.2, pluggy-1.6.0
collected 31 items

tests/test_keyword_config.py::TestKeywordConfig::test_load_config PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_get_category PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_get_primary_keywords PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_get_all_keywords PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_get_feature_mapping PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_get_keywords_for_feature PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_singleton PASSED
tests/test_keyword_config.py::TestKeywordConfig::test_default_fallback PASSED
tests/test_planner.py::TestEntityExtractor::test_extract_single_region PASSED
tests/test_planner.py::TestEntityExtractor::test_extract_multiple_regions PASSED
tests/test_planner.py::TestEntityExtractor::test_extract_keywords PASSED
tests/test_planner.py::TestEntityExtractor::test_extract_time_expressions PASSED
tests/test_planner.py::TestEntityExtractor::test_extract_empty_query PASSED
tests/test_planner.py::TestQueryDecomposer::test_simple_query_no_decomposition PASSED
tests/test_planner.py::TestQueryDecomposer::test_comparison_query_decomposition PASSED
tests/test_planner.py::TestQueryDecomposer::test_news_analysis_decomposition PASSED
tests/test_planner.py::TestQueryDecomposer::test_is_simple_query PASSED
tests/test_planner.py::TestPlanGenerator::test_generate_simple_plan PASSED
tests/test_planner.py::TestPlanGenerator::test_generate_parallel_plan PASSED
tests/test_planner.py::TestPlanGenerator::test_generate_plan_with_aggregate PASSED
tests/test_planner.py::TestPlanGenerator::test_plan_execution_steps PASSED
tests/test_planner.py::TestIntentClassificationResult::test_valid_classification PASSED
tests/test_planner.py::TestIntentClassificationResult::test_confidence_bounds PASSED
tests/test_planner.py::TestExecutionPlan::test_plan_with_all_fields PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_ma_crossover_detection PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_rate_threshold_detection PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_consecutive_rise_detection PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_window_calculation PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_insufficient_data PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_invalid_input PASSED
tests/test_rise_point_detector.py::TestRisePointDetector::test_confidence_score PASSED

======================== 31 passed, 1 warning in 5.34s ========================
```

---

## 다음 단계 (TODO)

### Prophet/LightGBM 모델 학습

```python
# Prophet
model = Prophet()
for keyword, frequency in news_weights.items():
    model.add_regressor(f"news_freq_{keyword}")

# LightGBM
features = df[["price", "volume", "news_freq_gtx", "news_freq_redev", ...]]
model = lgb.LGBMRegressor()
model.fit(features, target)
```

### 실제 데이터 연동

- 국토교통부 API 연동
- Google News 크롤링
- Supabase 테이블 생성 및 데이터 적재

### 감성 분석 (Nice to Have)

- 뉴스 본문 감성 분석
- sentiment_score를 피처 변수로 추가

---

## 참고 문서

- [PRD](docs/01_PRD_HomeSignalAI.md) - §3.2 Should Have
- [아키텍처 설계](docs/02_Architecture_Design.md)
- [AI 모델 파이프라인](docs/03_AI_Model_Pipeline.md) - §4 피처 엔지니어링
- [상승 시점 키워드 추출 가이드](docs/06_Rise_Point_Keyword_Extraction.md)
- [구현 계획](c:\Users\tlduf\.cursor\plans\상승_시점_키워드_추출_계획_cf4dfde1.plan.md)
