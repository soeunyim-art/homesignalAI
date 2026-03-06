# HomeSignal AI

동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스

## 프로젝트 개요

HomeSignal AI는 동대문구 지역의 부동산 가격 예측과 뉴스 기반 인사이트를 제공하는 AI 서비스입니다. 단순 수치 예측을 넘어, **과거 뉴스 이슈와 정책적 신호(Signals)**를 결합한 고도화된 예측 시스템을 구축합니다.

## 주요 기능

### 1. 시계열 예측 (Time-Series Forecasting)
- Prophet + LightGBM 앙상블 모델
- 뉴스 키워드 빈도를 피처 변수로 활용
- 상승 시점 전후 이슈 분석

### 2. RAG 챗봇 (RAG Chatbot)
- Vector DB 기반 문서 검색
- AI API (GPT-4o/Claude) 연동
- 근거 기반 답변 생성

### 3. 뉴스 이슈 분석 (News Analysis)
- 키워드별 빈도 분석
- 상승 시점 전후 이슈 추출
- 감성 분석 (Nice to Have)

### 4. 상승 시점 감지 (Rise Point Detection) ⭐ NEW
- 이동평균 교차 방식
- 변동률 임계값 방식
- 연속 상승 방식
- 상승 시점 전후 윈도우 내 뉴스 키워드 추출

## 기술 스택

- **Backend:** FastAPI (Python 3.14)
- **Database:** Supabase (PostgreSQL)
- **Vector DB:** (별도 담당)
- **AI:** OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **ML:** Prophet, LightGBM, NumPy
- **Cache:** Redis

## 설치 및 실행

### 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 또는 uv 사용
uv sync

# ML 의존성 포함
uv sync --extra ml
```

### 환경 변수

`.env` 파일 생성:

```env
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
AI_PROVIDER=openai  # or anthropic
REDIS_URL=redis://localhost:6379/0
```

### 개발 서버 실행

```bash
uvicorn src.main:app --reload
```

### 테스트

```bash
# 전체 테스트
pytest

# 특정 테스트 파일
pytest tests/test_rise_point_detector.py -v

# 커버리지 포함
pytest --cov=src tests/
```

## 설정 파일

### 키워드 설정 (`config/keywords.yaml`)

부동산 관련 키워드를 카테고리별로 정의:

```yaml
categories:
  transport:
    primary: ["GTX", "GTX-C", "청량리역"]
    synonyms: ["수도권광역급행철도", "환승센터"]
  redevelopment:
    primary: ["재개발", "뉴타운", "이문휘경뉴타운"]
    synonyms: ["정비사업", "재건축"]
  # ...
```

### 상승 시점 감지 설정 (`config/rise_point_config.yaml`)

```yaml
rise_point:
  method: "ma_crossover"  # 감지 방법
  short_ma_weeks: 5       # 단기 이동평균
  long_ma_weeks: 20       # 장기 이동평균
  lookback_weeks: 4       # 상승 시점 전 윈도우
  lookahead_weeks: 4      # 상승 시점 후 윈도우
```

## API 엔드포인트

### 시계열 예측

```bash
GET /api/v1/forecast?region=동대문구&period=week&horizon=12
```

### RAG 챗봇

```bash
POST /api/v1/chat
{
  "message": "동대문구 아파트 가격이 오를까요?",
  "session_id": "user-123"
}
```

### 뉴스 이슈 분석

```bash
GET /api/v1/news/insights?keywords=GTX,재개발&use_rise_points=true
```

## 프로젝트 구조

```
home_signal_ai/
├── config/                    # 설정 파일
│   ├── keywords.yaml         # 키워드 정의
│   └── rise_point_config.yaml # 상승 시점 감지 설정
├── docs/                      # 문서
│   ├── 01_PRD_HomeSignalAI.md
│   ├── 02_Architecture_Design.md
│   ├── 03_AI_Model_Pipeline.md
│   ├── 04_Prompt_RAG_Strategy.md
│   ├── 05_Deployment_Operation.md
│   └── 06_Rise_Point_Keyword_Extraction.md
├── src/
│   ├── forecast/             # 시계열 예측
│   │   ├── rise_point_detector.py  # 상승 시점 감지 ⭐
│   │   ├── service.py
│   │   └── schemas.py
│   ├── chat/                 # RAG 챗봇
│   ├── news/                 # 뉴스 분석
│   ├── ingest/               # 데이터 수집
│   └── shared/               # 공통 모듈
│       ├── keyword_config.py      # 키워드 설정 로더 ⭐
│       ├── rise_point_config.py   # 상승 시점 설정 로더 ⭐
│       ├── data_repository.py
│       └── database.py
└── tests/                    # 테스트
    ├── test_rise_point_detector.py ⭐
    └── test_keyword_config.py      ⭐
```

## 상승 시점 키워드 추출 기능

### 개요

가격 상승 시점 전후의 뉴스 키워드를 추출하여 시계열 예측 모델의 피처 변수로 활용합니다.

### 데이터 흐름

```
시계열 데이터
    ↓
RisePointDetector (상승 시점 감지)
    ↓
윈도우 생성 [T-4주, T+4주]
    ↓
뉴스 키워드 빈도 집계
    ↓
피처 변수 (news_freq_gtx, news_freq_redev, ...)
    ↓
Prophet/LightGBM 학습
```

### 사용 예시

```python
from src.forecast.rise_point_detector import RisePointDetector
from src.shared.rise_point_config import get_rise_point_config
from src.shared.keyword_config import get_keyword_config

# 상승 시점 감지
config = get_rise_point_config()
detector = RisePointDetector(config)
rise_points = detector.detect(dates, values)

# 키워드 조회
keyword_config = get_keyword_config()
keywords = keyword_config.get_primary_keywords()

# 상승 시점 윈도우 내 뉴스 키워드 빈도
windows = [(rp.window_start, rp.window_end) for rp in rise_points]
frequencies = await data_repo.get_news_keyword_frequency(
    keywords=keywords,
    rise_point_windows=windows,
)
```

## 문서

- [PRD (제품 요구사항 명세서)](docs/01_PRD_HomeSignalAI.md)
- [아키텍처 설계](docs/02_Architecture_Design.md)
- [AI 모델 파이프라인](docs/03_AI_Model_Pipeline.md)
- [프롬프트 및 RAG 전략](docs/04_Prompt_RAG_Strategy.md)
- [배포 및 운영](docs/05_Deployment_Operation.md)
- [상승 시점 키워드 추출](docs/06_Rise_Point_Keyword_Extraction.md) ⭐

## 개발 가이드

### 코드 스타일

- Python 3.14+
- Type hints 사용
- Async/await 패턴
- Pydantic 스키마 검증

### 커밋 메시지

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 업데이트
test: 테스트 추가/수정
refactor: 코드 리팩토링
```

## 라이선스

MIT License

## 기여

이슈 및 PR 환영합니다!
