from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 환경변수 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Supabase
    supabase_url: str
    supabase_key: str  # anon/public key (SELECT용)
    supabase_service_role_key: str | None = None  # service_role key (INSERT/UPDATE용)
    # PostgreSQL 직접 연결 (선택, 데이터 적재/마이그레이션용)
    database_url: str | None = None

    # AI API
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: Literal["openai", "anthropic"] = "openai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # 앱 설정
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # 캐시 TTL (초)
    cache_ttl_forecast: int = 3600  # 1시간
    cache_ttl_chat: int = 1800  # 30분

    # API 응답 타임아웃 (초)
    ai_api_timeout: float = 30.0

    # Supabase Auth 역할 매핑
    # 각 역할은 Supabase Auth의 user_metadata.role에 저장
    ingest_role_molit: str = "data_collector_molit"
    ingest_role_news: str = "data_collector_news"
    ingest_role_internal: str = "service_account"

    # 임베딩 설정
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Query Planner 설정
    enable_query_planner: bool = True
    planner_ai_classification: bool = True

    # Crawler 설정
    crawler_requests_per_minute: int = 10
    crawler_min_delay: float = 1.0
    crawler_max_delay: float = 3.0
    crawler_default_queries: list[str] = [
        # 기본 쿼리
        "동대문구 부동산",
        "청량리 재개발",
        "이문휘경 뉴타운",
        "GTX 청량리",
        # 교통 인프라
        "청량리역 환승센터",
        "경춘선 복선전철",
        "동대문구 GTX-A",
        # 지역별 개발
        "회기동 역세권개발",
        "답십리 재개발",
        "용두동 뉴타운",
        # 가격 관련
        "동대문구 아파트 시세",
        "청량리 전세가",
        # 정책
        "동대문구 청약",
        "서울 재개발 규제",
    ]
    crawler_date_range_days: int = 7
    crawler_max_results: int = 50
    crawler_extract_content: bool = True
    crawler_content_max_length: int = 2000

    # Keyword Extraction 설정
    enable_nlp_extraction: bool = True  # NLP 형태소 분석 사용
    enable_ai_extraction: bool = False  # AI 추출 사용 (비용 고려하여 기본 비활성화)
    ai_extraction_min_confidence: float = 0.5  # AI 추출 최소 신뢰도
    nlp_min_noun_length: int = 2  # NLP 명사 최소 길이

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
