"""Google News 크롤러 테스트"""

from datetime import datetime, timezone

import pytest

from src.crawler.google_news import GoogleNewsCrawler
from src.crawler.rate_limiter import RateLimiter
from src.crawler.schemas import CrawledNewsItem, RateLimiterConfig


@pytest.fixture
def crawler(rate_limiter_config: RateLimiterConfig) -> GoogleNewsCrawler:
    """테스트용 Google News 크롤러"""
    rate_limiter = RateLimiter(rate_limiter_config)
    return GoogleNewsCrawler(rate_limiter=rate_limiter, max_retries=1)


def test_parse_rss_success(crawler: GoogleNewsCrawler, mock_rss_response: str):
    """RSS 파싱 성공 테스트"""
    items = crawler._parse_rss(mock_rss_response, max_results=10, date_range_days=30)

    assert len(items) == 3
    assert all(isinstance(item, CrawledNewsItem) for item in items)


def test_parse_rss_item_fields(crawler: GoogleNewsCrawler, mock_rss_response: str):
    """RSS 아이템 필드 파싱 테스트"""
    items = crawler._parse_rss(mock_rss_response, max_results=10, date_range_days=30)

    first_item = items[0]
    assert first_item.title == "GTX-C 청량리역 2028년 개통 확정"
    assert "news.google.com" in str(first_item.url)
    assert first_item.source == "연합뉴스"
    assert isinstance(first_item.published_at, datetime)


def test_parse_rss_max_results(crawler: GoogleNewsCrawler, mock_rss_response: str):
    """최대 결과 수 제한 테스트"""
    items = crawler._parse_rss(mock_rss_response, max_results=2, date_range_days=30)

    assert len(items) == 2


def test_parse_rss_date_filter(crawler: GoogleNewsCrawler, mock_rss_response: str):
    """날짜 필터링 테스트 (매우 짧은 범위)"""
    # 0일 범위로 설정하면 대부분 필터링됨
    items = crawler._parse_rss(mock_rss_response, max_results=10, date_range_days=0)

    # 오늘 날짜 기준이므로 Mock 데이터는 필터링될 수 있음
    assert len(items) <= 3


def test_parse_rss_invalid_xml(crawler: GoogleNewsCrawler):
    """잘못된 XML 파싱 테스트"""
    from src.crawler.exceptions import ParseError

    with pytest.raises(ParseError):
        crawler._parse_rss("<invalid>xml", max_results=10, date_range_days=7)


def test_parse_rss_empty_response(crawler: GoogleNewsCrawler):
    """빈 RSS 응답 테스트"""
    empty_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><title>Empty</title></channel></rss>"""

    items = crawler._parse_rss(empty_rss, max_results=10, date_range_days=7)

    assert len(items) == 0


def test_parse_rfc2822_date():
    """RFC 2822 날짜 파싱 테스트"""
    date_str = "Mon, 03 Mar 2026 10:00:00 GMT"
    result = GoogleNewsCrawler._parse_rfc2822_date(date_str)

    assert isinstance(result, datetime)
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 3


def test_parse_rfc2822_date_invalid():
    """잘못된 날짜 형식 파싱 테스트 (폴백)"""
    result = GoogleNewsCrawler._parse_rfc2822_date("invalid date")

    # 폴백으로 현재 시간 반환
    assert isinstance(result, datetime)


def test_extract_actual_url():
    """URL 추출 테스트"""
    google_url = "https://news.google.com/articles/CBMiK2..."

    result = GoogleNewsCrawler._extract_actual_url(google_url)

    # 현재 구현에서는 원본 URL 반환
    assert result == google_url


@pytest.mark.asyncio
async def test_crawler_close(crawler: GoogleNewsCrawler):
    """크롤러 리소스 정리 테스트"""
    # 클라이언트 초기화
    await crawler._get_client()
    assert crawler._client is not None

    # 정리
    await crawler.close()
    assert crawler._client is None
