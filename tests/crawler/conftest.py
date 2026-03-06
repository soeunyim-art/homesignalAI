"""크롤러 테스트 fixtures"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.crawler.schemas import CrawledNewsItem, RateLimiterConfig
from src.ingest.schemas import NewsSignalBatchResponse


@pytest.fixture
def mock_rss_response() -> str:
    """Google News RSS 응답 Mock"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Google News - 동대문구 부동산</title>
        <item>
          <title>GTX-C 청량리역 2028년 개통 확정</title>
          <link>https://news.google.com/articles/gtx-c-news</link>
          <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
          <source>연합뉴스</source>
        </item>
        <item>
          <title>동대문구 재개발 사업 속도</title>
          <link>https://news.google.com/articles/redevelopment-news</link>
          <pubDate>Sun, 02 Mar 2026 15:00:00 GMT</pubDate>
          <source>한국경제</source>
        </item>
        <item>
          <title>이문휘경뉴타운 분양 일정 공개</title>
          <link>https://news.google.com/articles/newtown-news</link>
          <pubDate>Sat, 01 Mar 2026 09:00:00 GMT</pubDate>
          <source>조선일보</source>
        </item>
      </channel>
    </rss>"""


@pytest.fixture
def mock_html_content() -> str:
    """뉴스 기사 HTML Mock"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>GTX-C 청량리역 개통 소식</title></head>
    <body>
        <nav>네비게이션</nav>
        <article>
            <h1>GTX-C 청량리역 2028년 개통 확정</h1>
            <div class="article-body">
                수도권광역급행철도(GTX) C노선의 청량리역이 2028년에 개통될 예정이다.
                이번 개통으로 동대문구 일대의 부동산 가치가 상승할 것으로 전망된다.
                특히 청량리역 인근 재개발 지역의 관심이 높아지고 있다.
            </div>
        </article>
        <footer>푸터</footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_crawled_items() -> list[CrawledNewsItem]:
    """샘플 크롤링 결과"""
    return [
        CrawledNewsItem(
            title="GTX-C 청량리역 2028년 개통 확정",
            url="https://example.com/news/1",
            published_at=datetime(2026, 3, 3, 10, 0, 0, tzinfo=timezone.utc),
            source="연합뉴스",
            content="GTX-C노선 청량리역이 2028년 개통 예정이다.",
        ),
        CrawledNewsItem(
            title="동대문구 재개발 사업 속도",
            url="https://example.com/news/2",
            published_at=datetime(2026, 3, 2, 15, 0, 0, tzinfo=timezone.utc),
            source="한국경제",
            content=None,
        ),
    ]


@pytest.fixture
def rate_limiter_config() -> RateLimiterConfig:
    """테스트용 Rate Limiter 설정 (빠른 테스트)"""
    return RateLimiterConfig(
        requests_per_minute=60,  # 빠른 테스트를 위해 높게
        min_delay=0.01,  # 최소화
        max_delay=0.02,
        max_backoff=1.0,
    )


@pytest.fixture
def mock_ingest_service(mocker) -> AsyncMock:
    """IngestService Mock"""
    from src.ingest.service import IngestService

    mock = mocker.AsyncMock(spec=IngestService)
    mock.ingest_news.return_value = NewsSignalBatchResponse(
        success=True,
        inserted_count=5,
        duplicate_count=2,
        embedding_generated_count=5,
        failed_count=0,
        errors=None,
        batch_id="test-batch-123",
    )
    return mock
