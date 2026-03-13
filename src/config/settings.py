from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 환경변수 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 추가 환경변수 무시
    )

    # Supabase
    # Vercel 환경에서 환경변수 로딩 전 초기화 방지를 위해 기본값 제공
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_key: str = "placeholder-key"  # anon/public key (SELECT용)
    supabase_service_role_key: str | None = None  # service_role key (INSERT/UPDATE용)
    supabase_timeout: int = 10  # Supabase 쿼리 타임아웃 (초)
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

    # CORS 설정
    allowed_origins: list[str] = []

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """쉼표 구분 문자열을 리스트로 파싱"""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v or []

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v):
        """Supabase URL 검증 및 경고"""
        if v == "https://placeholder.supabase.co":
            import os
            if os.environ.get("APP_ENV") == "production":
                raise ValueError(
                    "Production 환경에서 placeholder Supabase URL을 사용할 수 없습니다. "
                    "Vercel 환경변수에서 SUPABASE_URL을 설정하세요."
                )
        return v

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
    """
    Settings 싱글톤 인스턴스를 반환합니다.

    Note: Vercel 환경에서는 환경변수가 런타임에 로드되므로,
    모듈 임포트 시점에 환경변수가 없어도 기본값으로 초기화됩니다.
    실제 환경변수는 첫 호출 시 자동으로 로드됩니다.
    """
    return Settings()


# Module-level에서 초기화 (하위 호환성 유지)
# Vercel 환경에서는 기본값(placeholder)으로 초기화되며,
# 실제 환경변수는 런타임에 로드됩니다.
settings = get_settings()
