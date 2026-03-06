"""HomeSignal AI 뉴스 크롤러 모듈

Google News에서 동대문구 부동산 관련 뉴스를 크롤링하고
IngestService를 통해 Supabase에 적재합니다.

사용법:
    # CLI로 실행
    uv run python -m src.crawler.cli crawl

    # 프로그래매틱 사용
    from src.crawler import CrawlerRunner, CrawlConfig

    runner = CrawlerRunner()
    result = await runner.run(CrawlConfig(queries=["동대문구 재개발"]))
    await runner.close()
"""

from .content_extractor import ContentExtractor
from .exceptions import (
    ContentExtractionError,
    CrawlerError,
    NetworkError,
    ParseError,
    RateLimitError,
)
from .google_news import GoogleNewsCrawler
from .keyword_extractor import KeywordExtractor
from .rate_limiter import RateLimiter
from .runner import CrawlerRunner, create_crawler_runner
from .schemas import CrawlConfig, CrawledNewsItem, CrawlResult, RateLimiterConfig

__all__ = [
    # 메인 클래스
    "CrawlerRunner",
    "GoogleNewsCrawler",
    "ContentExtractor",
    "KeywordExtractor",
    "RateLimiter",
    # 스키마
    "CrawlConfig",
    "CrawlResult",
    "CrawledNewsItem",
    "RateLimiterConfig",
    # 예외
    "CrawlerError",
    "RateLimitError",
    "ParseError",
    "NetworkError",
    "ContentExtractionError",
    # 헬퍼
    "create_crawler_runner",
]
