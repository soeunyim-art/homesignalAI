"""Crawler Runner 테스트"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.crawler.runner import CrawlerRunner, create_crawler_runner
from src.crawler.schemas import CrawlConfig, CrawledNewsItem, RateLimiterConfig


@pytest.fixture
def mock_crawler(mocker, sample_crawled_items):
    """Google News 크롤러 Mock"""
    from src.crawler.google_news import GoogleNewsCrawler

    mock = mocker.AsyncMock(spec=GoogleNewsCrawler)
    mock.search.return_value = sample_crawled_items
    mock.close = mocker.AsyncMock()
    return mock


@pytest.fixture
def mock_content_extractor(mocker):
    """Content Extractor Mock"""
    from src.crawler.content_extractor import ContentExtractor

    mock = mocker.AsyncMock(spec=ContentExtractor)
    mock.extract_batch.return_value = {
        "https://example.com/news/1": "GTX-C 청량리역 본문 내용",
        "https://example.com/news/2": None,  # 추출 실패
    }
    mock.close = mocker.AsyncMock()
    return mock


@pytest.fixture
def runner(
    mock_crawler,
    mock_content_extractor,
    mock_ingest_service,
    rate_limiter_config: RateLimiterConfig,
):
    """테스트용 Crawler Runner"""
    return CrawlerRunner(
        crawler=mock_crawler,
        content_extractor=mock_content_extractor,
        ingest_service=mock_ingest_service,
        rate_limiter_config=rate_limiter_config,
    )


@pytest.mark.asyncio
async def test_runner_run_basic(runner: CrawlerRunner):
    """기본 크롤링 실행 테스트"""
    config = CrawlConfig(queries=["테스트 쿼리"])

    result = await runner.run(config)

    assert result.total_crawled > 0
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_runner_run_dry_run(runner: CrawlerRunner):
    """Dry run 모드 테스트"""
    config = CrawlConfig(queries=["테스트 쿼리"])

    result = await runner.run(config, dry_run=True)

    assert result.inserted == 0
    assert result.batch_id == "dry-run"
    # IngestService가 호출되지 않아야 함
    runner.ingest_service.ingest_news.assert_not_called()


@pytest.mark.asyncio
async def test_runner_run_with_content_extraction(runner: CrawlerRunner):
    """본문 추출 포함 테스트"""
    config = CrawlConfig(queries=["테스트 쿼리"], extract_content=True)

    result = await runner.run(config)

    # Content extractor가 호출되었는지 확인
    runner.content_extractor.extract_batch.assert_called_once()


@pytest.mark.asyncio
async def test_runner_run_without_content_extraction(runner: CrawlerRunner):
    """본문 추출 없이 테스트"""
    config = CrawlConfig(queries=["테스트 쿼리"], extract_content=False)

    result = await runner.run(config)

    # Content extractor가 호출되지 않아야 함
    runner.content_extractor.extract_batch.assert_not_called()


@pytest.mark.asyncio
async def test_runner_deduplication(runner: CrawlerRunner, mocker):
    """URL 기준 중복 제거 테스트"""
    # 중복 URL을 포함한 아이템
    duplicate_items = [
        CrawledNewsItem(
            title="뉴스 1",
            url="https://example.com/same-url",
            published_at=datetime.now(timezone.utc),
        ),
        CrawledNewsItem(
            title="뉴스 2 (중복)",
            url="https://example.com/same-url",
            published_at=datetime.now(timezone.utc),
        ),
        CrawledNewsItem(
            title="뉴스 3",
            url="https://example.com/different-url",
            published_at=datetime.now(timezone.utc),
        ),
    ]
    runner.crawler.search.return_value = duplicate_items

    unique = runner._deduplicate(duplicate_items)

    assert len(unique) == 2  # 중복 제거됨


@pytest.mark.asyncio
async def test_runner_keyword_filtering(runner: CrawlerRunner, mocker):
    """키워드 필터링 테스트"""
    # 관련 키워드가 없는 아이템
    irrelevant_items = [
        CrawledNewsItem(
            title="관련 없는 뉴스",
            url="https://example.com/irrelevant",
            published_at=datetime.now(timezone.utc),
        ),
    ]
    runner.crawler.search.return_value = irrelevant_items

    config = CrawlConfig(queries=["테스트"])
    result = await runner.run(config, dry_run=True)

    # 관련 키워드가 없으므로 적재되지 않음
    assert result.inserted == 0


@pytest.mark.asyncio
async def test_runner_ingest_service_integration(runner: CrawlerRunner):
    """IngestService 연동 테스트"""
    config = CrawlConfig(queries=["GTX 청량리"])

    await runner.run(config)

    # IngestService가 호출되었는지 확인
    runner.ingest_service.ingest_news.assert_called_once()


@pytest.mark.asyncio
async def test_runner_close(runner: CrawlerRunner):
    """리소스 정리 테스트"""
    await runner.close()

    runner.crawler.close.assert_called_once()
    runner.content_extractor.close.assert_called_once()


def test_create_crawler_runner():
    """헬퍼 함수 테스트"""
    runner = create_crawler_runner(
        requests_per_minute=5,
        min_delay=2.0,
        max_delay=5.0,
    )

    assert isinstance(runner, CrawlerRunner)
    assert runner._rate_limiter_config.requests_per_minute == 5
    assert runner._rate_limiter_config.min_delay == 2.0
    assert runner._rate_limiter_config.max_delay == 5.0


@pytest.mark.asyncio
async def test_runner_multiple_queries(runner: CrawlerRunner):
    """여러 쿼리 실행 테스트"""
    config = CrawlConfig(queries=["쿼리1", "쿼리2", "쿼리3"])

    await runner.run(config)

    # 각 쿼리에 대해 search가 호출되었는지 확인
    assert runner.crawler.search.call_count == 3


@pytest.mark.asyncio
async def test_runner_handles_crawler_error(runner: CrawlerRunner, mocker):
    """크롤러 오류 처리 테스트"""
    runner.crawler.search.side_effect = Exception("Network error")

    config = CrawlConfig(queries=["에러 쿼리"])
    result = await runner.run(config, dry_run=True)

    # 오류가 발생해도 결과는 반환
    assert result.total_crawled == 0
