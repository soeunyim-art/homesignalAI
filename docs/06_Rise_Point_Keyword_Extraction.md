# HomeSignal AI — 상승 시점 키워드 추출 가이드

**문서 버전:** 1.0  
**최종 수정일:** 2026-03-04  
**참조:** `01_PRD_HomeSignalAI.md`, `03_AI_Model_Pipeline.md`

---

## 1. 개요 (Overview)

본 문서는 동대문구 부동산 가격 상승 시점 전후의 주요 이슈(GTX, 재개발 등)를 키워드로 추출하고, 시계열 예측 모델의 피처 변수로 활용하는 시스템을 설명합니다.

---

## 2. 상승 시점 감지 (Rise Point Detection)

### 2.1 감지 방법

| 방법 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **MA Crossover** | 단기 MA(5주)가 장기 MA(20주)를 상향 돌파 | 추세 전환 명확히 포착 | 지연 발생 가능 |
| **Rate Threshold** | N주 대비 변동률이 임계값(예: 2%) 초과 | 구현 단순, 빠른 반응 | 노이즈에 민감 |
| **Consecutive Rise** | K주 연속 상승 구간 진입 | 노이즈 완화 | 상승 초기 감지 지연 |

### 2.2 설정 파일

`config/rise_point_config.yaml`:

```yaml
rise_point:
  method: "ma_crossover"  # 감지 방법
  short_ma_weeks: 5       # 단기 이동평균 기간
  long_ma_weeks: 20       # 장기 이동평균 기간
  lookback_weeks: 4       # 상승 시점 전 윈도우
  lookahead_weeks: 4      # 상승 시점 후 윈도우
  rate_threshold_pct: 2.0 # 변동률 임계값 (%)
  consecutive_weeks: 3    # 연속 상승 주수
```

### 2.3 사용 예시

```python
from datetime import date, timedelta
from src.forecast.rise_point_detector import RisePointDetector
from src.shared.rise_point_config import get_rise_point_config

# 설정 로드
config = get_rise_point_config()
detector = RisePointDetector(config)

# 시계열 데이터
dates = [date(2024, 1, 1) + timedelta(weeks=i) for i in range(52)]
values = [100 + i * 0.5 for i in range(52)]

# 상승 시점 감지
rise_points = detector.detect(dates, values)

for rp in rise_points:
    print(f"상승 시점: {rp.date}")
    print(f"윈도우: {rp.window_start} ~ {rp.window_end}")
    print(f"신뢰도: {rp.confidence}")
```

---

## 3. 키워드 설정 (Keyword Configuration)

### 3.1 키워드 카테고리

`config/keywords.yaml`:

| 카테고리 | Primary 키워드 | Synonyms |
|----------|---------------|----------|
| **transport** | GTX, GTX-C, 청량리역 | 수도권광역급행철도, 환승센터 |
| **redevelopment** | 재개발, 뉴타운, 이문휘경뉴타운 | 정비사업, 재건축, 리모델링 |
| **supply** | 분양, 입주, 착공, 준공 | 조합원, 특별공급, 청약 |
| **policy** | 금리, 대출, 규제, 정책 | 기준금리, DSR, LTV |

### 3.2 피처 변수 매핑

```yaml
feature_mapping:
  news_freq_gtx:
    - transport
  news_freq_redev:
    - redevelopment
  news_freq_supply:
    - supply
  news_freq_policy:
    - policy
```

### 3.3 사용 예시

```python
from src.shared.keyword_config import get_keyword_config

config = get_keyword_config()

# 전체 primary 키워드
all_primary = config.get_primary_keywords()

# 특정 카테고리 키워드
transport_keywords = config.get_all_keywords("transport")

# 피처 변수에 매핑된 키워드
gtx_keywords = config.get_keywords_for_feature("news_freq_gtx")
```

---

## 4. 뉴스 키워드 빈도 집계

### 4.1 DataRepository 확장

`DataRepository.get_news_keyword_frequency()` 메서드에 `rise_point_windows` 파라미터 추가:

```python
async def get_news_keyword_frequency(
    self,
    keywords: list[str],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    rise_point_windows: list[tuple[date, date]] | None = None,
) -> list[KeywordFrequency]:
    """
    키워드별 뉴스 빈도 조회
    
    rise_point_windows가 제공되면 해당 윈도우들 내의 뉴스만 집계
    """
```

### 4.2 사용 예시

```python
from src.shared.data_repository import get_data_repository

repo = get_data_repository()

# 상승 시점 윈도우 내 뉴스 키워드 빈도
keywords = ["GTX", "재개발", "분양"]
windows = [
    (date(2024, 1, 1), date(2024, 2, 1)),
    (date(2024, 5, 1), date(2024, 6, 1)),
]

frequencies = await repo.get_news_keyword_frequency(
    keywords=keywords,
    rise_point_windows=windows,
)

for freq in frequencies:
    print(f"{freq.keyword}: {freq.frequency}건")
```

---

## 5. ForecastService 연동

### 5.1 뉴스 가중치 조회

`ForecastService._get_news_weights()` 메서드가 상승 시점 윈도우 내 키워드 빈도를 조회:

```python
async def _get_news_weights(self, region: str) -> list[NewsWeightSummary]:
    """
    상승 시점 전후 윈도우 내 뉴스 키워드 빈도를 조회하여 피처 변수로 활용
    """
    keyword_config = get_keyword_config()
    keywords = keyword_config.get_primary_keywords()
    
    # 상승 시점 윈도우 조회
    rise_point_windows = await self._get_rise_point_windows(region)
    
    # 윈도우 내 키워드 빈도 집계
    keyword_frequencies = await self.data_repo.get_news_keyword_frequency(
        keywords=keywords,
        rise_point_windows=rise_point_windows,
    )
    
    return [
        NewsWeightSummary(
            keyword=kf.keyword,
            frequency=kf.frequency,
            impact_score=kf.impact_score or 0.5,
        )
        for kf in keyword_frequencies
    ]
```

### 5.2 Prophet/LightGBM 피처 주입

예측 모델 학습 시 `news_freq_*` 변수를 추가:

```python
# Prophet
model = Prophet()
for keyword, frequency in news_weights.items():
    model.add_regressor(f"news_freq_{keyword}")

# LightGBM
features = df[["price", "volume", "news_freq_gtx", "news_freq_redev", ...]]
```

---

## 6. NewsService 연동

### 6.1 상승 시점 기반 분석

`NewsInsightsRequest`에 `use_rise_points` 파라미터 추가:

```python
class NewsInsightsRequest(BaseModel):
    period: Literal["week", "month", "quarter"] = "month"
    keywords: list[str] = ["GTX", "재개발"]
    region: str = "동대문구"
    use_rise_points: bool = False  # 상승 시점 윈도우 사용 여부
```

### 6.2 사용 예시

```bash
# 일반 뉴스 분석
GET /api/v1/news/insights?keywords=GTX,재개발

# 상승 시점 전후 뉴스만 분석
GET /api/v1/news/insights?keywords=GTX,재개발&use_rise_points=true
```

---

## 7. 데이터 흐름

```
시계열 데이터
    ↓
RisePointDetector
    ↓
상승 시점 T 감지
    ↓
윈도우 [T-4주, T+4주] 생성
    ↓
뉴스 데이터 필터링 (윈도우 내)
    ↓
키워드 빈도 집계
    ↓
피처 변수 (news_freq_gtx, news_freq_redev, ...)
    ↓
Prophet/LightGBM 학습
```

---

## 8. 테스트

### 8.1 상승 시점 감지 테스트

```bash
uv run pytest tests/test_rise_point_detector.py -v
```

### 8.2 키워드 설정 테스트

```bash
uv run pytest tests/test_keyword_config.py -v
```

---

## 9. 참고 문서

- [01_PRD_HomeSignalAI.md](01_PRD_HomeSignalAI.md) - §3.2 Should Have
- [03_AI_Model_Pipeline.md](03_AI_Model_Pipeline.md) - §4 피처 엔지니어링
- [04_Prompt_RAG_Strategy.md](04_Prompt_RAG_Strategy.md) - §3.1 Query Transformation
