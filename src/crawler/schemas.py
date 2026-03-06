"""크롤러 Pydantic 스키마"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CrawledNewsItem(BaseModel):
    """크롤링된 뉴스 아이템 (파싱 직후)"""

    title: str = Field(..., min_length=1, max_length=500)
    url: HttpUrl
    published_at: datetime
    source: str | None = Field(None, description="뉴스 매체명")
    snippet: str | None = Field(None, description="RSS 스니펫")
    content: str | None = Field(None, description="추출된 본문")


class CrawlConfig(BaseModel):
    """크롤링 설정"""

    queries: list[str] = Field(
        default=[
            "동대문구 부동산",
            "청량리 재개발",
            "이문휘경 뉴타운",
            "GTX 청량리",
        ],
        description="검색 쿼리 목록",
    )
    max_results_per_query: int = Field(default=20, ge=1, le=100)
    date_range_days: int = Field(default=7, ge=1, le=30)
    generate_embeddings: bool = Field(default=True)
    extract_content: bool = Field(default=True, description="본문 추출 여부")
    content_max_length: int = Field(default=2000, description="본문 최대 길이")


class CrawlResult(BaseModel):
    """크롤링 실행 결과"""

    total_crawled: int = Field(..., description="총 크롤링 건수")
    content_extracted: int = Field(default=0, description="본문 추출 성공 건수")
    inserted: int = Field(..., description="신규 삽입 건수")
    duplicates: int = Field(..., description="중복 스킵 건수")
    errors: int = Field(..., description="실패 건수")
    duration_seconds: float = Field(..., description="실행 시간")
    batch_id: str | None = Field(None, description="Ingest 배치 ID")


class RateLimiterConfig(BaseModel):
    """Rate Limiter 설정"""

    requests_per_minute: int = Field(default=10, ge=1, le=60)
    min_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    max_delay: float = Field(default=3.0, ge=0.5, le=30.0)
    max_backoff: float = Field(default=60.0, ge=10.0, le=300.0)
