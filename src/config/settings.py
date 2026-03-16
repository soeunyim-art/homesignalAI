import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 환경변수 설정"""

    model_config = SettingsConfigDict(
        # Vercel 환경에서는 시스템 환경변수만 사용
        # 로컬 개발 환경에서는 .env 파일도 시도하지만 없어도 무시
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 추가 환경변수 무시
        # .env 파일이 없어도 에러 발생하지 않음
        env_ignore_empty=True,
        validate_default=False,  # 기본값 검증 생략
    )

    # Supabase
    # CRITICAL: Optional로 설정하여 Pydantic이 빈 dict 받아도 에러 안 나게 함
    # model_validator에서 None이면 기본값 설정
    supabase_url: str | None = None
    supabase_key: str | None = None
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

    @model_validator(mode='after')
    def set_required_defaults(self):
        """
        CRITICAL: Pydantic이 빈 dict를 받아도 기본값 설정.

        Vercel 환경에서 .env 파일이 없으면 Pydantic은 빈 dict {}를 source로 받아
        Optional 필드를 None으로 설정합니다. 이 validator에서 None을 감지하고
        안전한 기본값으로 설정하여 애플리케이션 크래시를 방지합니다.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Supabase URL
        if not self.supabase_url:
            self.supabase_url = "https://placeholder.supabase.co"
            logger.warning(
                "SUPABASE_URL 환경변수가 설정되지 않아 placeholder로 초기화됨. "
                "Mock mode로 작동합니다."
            )

        # Supabase Key
        if not self.supabase_key:
            self.supabase_key = "placeholder-key"
            logger.warning(
                "SUPABASE_KEY 환경변수가 설정되지 않아 placeholder로 초기화됨. "
                "Mock mode로 작동합니다."
            )

        # Service Role Key
        if not self.supabase_service_role_key:
            self.supabase_service_role_key = "placeholder-service-key"
            logger.debug("SUPABASE_SERVICE_ROLE_KEY가 설정되지 않아 placeholder로 초기화됨.")

        # Production 환경에서 placeholder 사용 경고
        if self.app_env == "production":
            if "placeholder" in self.supabase_url:
                logger.critical(
                    "🚨 CRITICAL: Production 환경에서 placeholder Supabase URL 사용 중! "
                    "Vercel Dashboard → Environment Variables에서 설정하세요."
                )
            if self.supabase_key == "placeholder-key":
                logger.critical(
                    "🚨 CRITICAL: Production 환경에서 placeholder Supabase KEY 사용 중! "
                    "Vercel Dashboard → Environment Variables에서 설정하세요."
                )

        return self

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


# Global singleton instance (lazy initialized)
_settings: Settings | None = None


@lru_cache
def get_settings() -> Settings:
    """
    Settings 싱글톤 인스턴스를 반환합니다 (Lazy Initialization).

    CRITICAL: 모듈 임포트 시점이 아닌 첫 호출 시점에 초기화됩니다.
    이는 Vercel 환경에서 환경변수 로딩 타이밍 이슈를 방지합니다.

    Note: Vercel 환경에서는 환경변수가 런타임에 로드되므로,
    api/index.py에서 환경변수를 설정한 후 이 함수를 호출해야 합니다.
    """
    global _settings

    if _settings is not None:
        return _settings

    try:
        _settings = Settings()
        return _settings
    except Exception as e:
        # Vercel 초기 로딩 시 환경변수 없어도 크래시 방지
        import logging
        logging.critical(
            f"CRITICAL: Settings 초기화 실패: {e}. "
            f"환경변수 확인: SUPABASE_URL={os.getenv('SUPABASE_URL', 'NOT SET')}, "
            f"SUPABASE_KEY={'SET' if os.getenv('SUPABASE_KEY') else 'NOT SET'}. "
            "기본값으로 강제 초기화합니다."
        )
        # 환경변수 강제 설정하여 재시도
        os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
        os.environ.setdefault("SUPABASE_KEY", "placeholder-key")
        os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder-service-key")
        _settings = Settings()
        return _settings


# IMPORTANT: 모듈 레벨에서 초기화하지 않음!
# 하위 호환성을 위해 __getattr__로 lazy loading 지원
def __getattr__(name: str):
    """
    모듈 레벨 lazy attribute access.

    'settings' 접근 시 자동으로 get_settings() 호출하여
    하위 호환성 유지 + lazy initialization 달성.
    """
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# 실제 사용 시: from src.config import settings (자동으로 get_settings() 호출됨)
# 또는: from src.config.settings import get_settings; settings = get_settings()
