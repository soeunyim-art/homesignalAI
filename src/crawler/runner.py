"""뉴스 크롤링 오케스트레이터"""

import asyncio
import logging
import time

from src.ingest.schemas import NewsSignalBatchRequest, NewsSignalItem
from src.ingest.service import IngestService

from .content_extractor import ContentExtractor
from .google_news import GoogleNewsCrawler
from .keyword_extractor import KeywordExtractor
from .rate_limiter import RateLimiter
from .schemas import CrawlConfig, CrawledNewsItem, CrawlResult, RateLimiterConfig

logger = logging.getLogger(__name__)


class CrawlerRunner:
    """뉴스 크롤링 오케스트레이터

    Google News 크롤링 → 본문 추출 → 키워드 태깅 → IngestService 적재
    """

    def __init__(
        self,
        crawler: GoogleNewsCrawler | None = None,
        content_extractor: ContentExtractor | None = None,
        keyword_extractor: KeywordExtractor | None = None,
        ingest_service: IngestService | None = None,
        rate_limiter_config: RateLimiterConfig | None = None,
    ):
        """
        Args:
            crawler: Google News 크롤러 (None이면 기본 생성)
            content_extractor: 본문 추출기 (None이면 기본 생성)
            keyword_extractor: 키워드 추출기 (None이면 기본 생성)
            ingest_service: 데이터 적재 서비스 (None이면 기본 생성)
            rate_limiter_config: Rate limiter 설정
        """
        self._rate_limiter_config = rate_limiter_config or RateLimiterConfig()
        self._rate_limiter = RateLimiter(self._rate_limiter_config)

        self.crawler = crawler or GoogleNewsCrawler(self._rate_limiter)
        self.content_extractor = content_extractor or ContentExtractor(
            rate_limiter=self._rate_limiter,
            max_content_length=2000,
        )
        self.keyword_extractor = keyword_extractor or KeywordExtractor()
        self.ingest_service = ingest_service

    def _get_ingest_service(self) -> IngestService:
        """IngestService 지연 초기화"""
        if self.ingest_service is None:
            self.ingest_service = IngestService()
        return self.ingest_service

    async def run(
        self,
        config: CrawlConfig | None = None,
        dry_run: bool = False,
    ) -> CrawlResult:
        """크롤링 실행

        Args:
            config: 크롤링 설정 (None이면 기본값 사용)
            dry_run: True면 실제 적재 없이 테스트

        Returns:
            크롤링 결과
        """
        config = config or CrawlConfig()
        start_time = time.monotonic()

        logger.info(
            f"크롤링 시작: queries={config.queries}, "
            f"max_results={config.max_results_per_query}, "
            f"extract_content={config.extract_content}"
        )

        # 1. 뉴스 크롤링
        all_items: list[CrawledNewsItem] = []
        for query in config.queries:
            try:
                items = await self.crawler.search(
                    query=query,
                    max_results=config.max_results_per_query,
                    date_range_days=config.date_range_days,
                )
                all_items.extend(items)
                logger.info(f"Query '{query}': {len(items)} items")
            except Exception as e:
                logger.error(f"Query '{query}' failed: {e}")

        logger.info(f"총 크롤링: {len(all_items)} items")

        # 2. URL 기준 중복 제거 (크롤링 단계에서)
        unique_items = self._deduplicate(all_items)
        logger.info(f"중복 제거 후: {len(unique_items)} items")

        # 3. 본문 추출 (설정된 경우)
        content_extracted_count = 0
        if config.extract_content and unique_items:
            content_extracted_count = await self._extract_contents(unique_items)
            logger.info(f"본문 추출 성공: {content_extracted_count} items")

        # 4. 키워드 추출 및 관련성 필터링
        relevant_items: list[tuple[CrawledNewsItem, list[str]]] = []
        for item in unique_items:
            keywords = self.keyword_extractor.extract(item.title, item.content)
            if keywords:  # 최소 1개 키워드 필요
                relevant_items.append((item, keywords))

        logger.info(f"관련 뉴스: {len(relevant_items)} items")

        # 5. IngestService 호출 (dry_run이 아닌 경우)
        if dry_run:
            logger.info("DRY RUN 모드 - 실제 적재 스킵")
            ingest_result = {
                "inserted": 0,
                "duplicates": 0,
                "errors": 0,
                "batch_id": "dry-run",
            }
        elif relevant_items:
            ingest_result = await self._ingest_items(
                relevant_items,
                config.generate_embeddings,
            )
        else:
            ingest_result = {
                "inserted": 0,
                "duplicates": 0,
                "errors": 0,
                "batch_id": None,
            }

        # 6. 결과 반환
        duration = time.monotonic() - start_time

        result = CrawlResult(
            total_crawled=len(all_items),
            content_extracted=content_extracted_count,
            inserted=ingest_result["inserted"],
            duplicates=ingest_result["duplicates"],
            errors=ingest_result["errors"],
            duration_seconds=round(duration, 2),
            batch_id=ingest_result.get("batch_id"),
        )

        logger.info(f"크롤링 완료: {result}")
        return result

    def _deduplicate(
        self,
        items: list[CrawledNewsItem],
    ) -> list[CrawledNewsItem]:
        """URL 기준 중복 제거"""
        seen_urls: set[str] = set()
        unique: list[CrawledNewsItem] = []

        for item in items:
            url_str = str(item.url)
            if url_str not in seen_urls:
                seen_urls.add(url_str)
                unique.append(item)

        return unique

    async def _extract_contents(
        self,
        items: list[CrawledNewsItem],
        concurrency: int = 3,
    ) -> int:
        """여러 기사에서 본문 추출 (병렬)

        Returns:
            본문 추출 성공 건수
        """
        urls = [str(item.url) for item in items]
        url_to_item = {str(item.url): item for item in items}

        contents = await self.content_extractor.extract_batch(
            urls,
            concurrency=concurrency,
        )

        success_count = 0
        for url, content in contents.items():
            if content and url in url_to_item:
                # CrawledNewsItem은 Pydantic 모델이므로 직접 수정
                # model_copy를 사용하거나, 새로 생성해야 하지만
                # 여기서는 items 리스트의 원본을 수정
                item = url_to_item[url]
                # Pydantic v2에서는 직접 할당 가능
                object.__setattr__(item, "content", content)
                success_count += 1

        return success_count

    async def _ingest_items(
        self,
        items: list[tuple[CrawledNewsItem, list[str]]],
        generate_embeddings: bool,
    ) -> dict:
        """IngestService를 통해 데이터 적재"""
        news_items = [
            NewsSignalItem(
                title=item.title,
                content=item.content,
                url=str(item.url),
                keywords=keywords,
                embedding=None,  # IngestService에서 생성
                published_at=item.published_at,
            )
            for item, keywords in items
        ]

        request = NewsSignalBatchRequest(
            source="google_news_crawler",
            items=news_items,
            generate_embeddings=generate_embeddings,
        )

        service = self._get_ingest_service()
        response = await service.ingest_news(request)

        return {
            "inserted": response.inserted_count,
            "duplicates": response.duplicate_count,
            "errors": response.failed_count,
            "batch_id": response.batch_id,
        }

    async def close(self) -> None:
        """리소스 정리"""
        await self.crawler.close()
        await self.content_extractor.close()


def create_crawler_runner(
    requests_per_minute: int = 10,
    min_delay: float = 1.0,
    max_delay: float = 3.0,
) -> CrawlerRunner:
    """CrawlerRunner 인스턴스 생성 헬퍼

    Args:
        requests_per_minute: 분당 요청 수
        min_delay: 최소 딜레이 (초)
        max_delay: 최대 딜레이 (초)

    Returns:
        설정된 CrawlerRunner 인스턴스
    """
    config = RateLimiterConfig(
        requests_per_minute=requests_per_minute,
        min_delay=min_delay,
        max_delay=max_delay,
    )
    return CrawlerRunner(rate_limiter_config=config)
