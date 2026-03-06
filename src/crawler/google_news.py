"""Google News RSS 크롤러"""

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

from .exceptions import NetworkError, ParseError, RateLimitError
from .rate_limiter import RateLimiter
from .schemas import CrawledNewsItem, RateLimiterConfig

logger = logging.getLogger(__name__)


class GoogleNewsCrawler:
    """Google News RSS 크롤러

    Google News RSS 피드를 사용하여 뉴스를 검색합니다.
    - 한국어/한국 지역 설정
    - Rate limiting으로 차단 방지
    - 지수 백오프 재시도
    """

    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

    # 일반적인 브라우저 User-Agent
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Args:
            rate_limiter: Rate limiter (None이면 기본값 생성)
            http_client: HTTP 클라이언트 (None이면 지연 생성)
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.rate_limiter = rate_limiter or RateLimiter(RateLimiterConfig())
        self._client = http_client
        self._owns_client = http_client is None
        self._timeout = timeout
        self._max_retries = max_retries

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 지연 초기화"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 50,
        date_range_days: int = 7,
    ) -> list[CrawledNewsItem]:
        """Google News RSS 검색

        Args:
            query: 검색어 (예: "동대문구 부동산")
            max_results: 최대 결과 수
            date_range_days: 검색 기간 (일)

        Returns:
            크롤링된 뉴스 목록

        Raises:
            RateLimitError: Google rate limit 초과
            NetworkError: 네트워크 요청 실패
        """
        await self.rate_limiter.acquire()

        # URL 구성
        encoded_query = quote_plus(query)
        url = f"{self.GOOGLE_NEWS_RSS_URL}?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

        client = await self._get_client()

        for attempt in range(self._max_retries):
            try:
                response = await client.get(url)

                if response.status_code == 429:
                    logger.warning(f"Rate limit hit, backing off (attempt {attempt + 1})")
                    await self.rate_limiter.backoff(attempt)
                    continue

                response.raise_for_status()
                items = self._parse_rss(response.text, max_results, date_range_days)
                logger.info(f"Query '{query}': {len(items)} items found")
                return items

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    if attempt == self._max_retries - 1:
                        raise RateLimitError("Google rate limit exceeded after retries")
                    await self.rate_limiter.backoff(attempt)
                    continue
                logger.error(f"HTTP error for query '{query}': {e}")
                raise NetworkError(f"HTTP request failed: {e}")

            except httpx.RequestError as e:
                logger.error(f"Request error for query '{query}': {e}")
                if attempt < self._max_retries - 1:
                    await self.rate_limiter.backoff(attempt)
                    continue
                raise NetworkError(f"Request failed after {self._max_retries} retries: {e}")

        return []

    def _parse_rss(
        self,
        xml_content: str,
        max_results: int,
        date_range_days: int,
    ) -> list[CrawledNewsItem]:
        """RSS XML 파싱"""
        try:
            root = ElementTree.fromstring(xml_content)
        except ElementTree.ParseError as e:
            raise ParseError(f"RSS XML parsing failed: {e}")

        items: list[CrawledNewsItem] = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=date_range_days)

        for item in root.findall(".//item"):
            if len(items) >= max_results:
                break

            try:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                source_elem = item.find("source")

                if title_elem is None or link_elem is None or pub_date_elem is None:
                    continue

                title = title_elem.text or ""
                link = link_elem.text or ""
                pub_date_str = pub_date_elem.text or ""
                source = source_elem.text if source_elem is not None else None

                # 날짜 파싱 (RFC 2822 형식)
                published_at = self._parse_rfc2822_date(pub_date_str)

                # 날짜 필터링
                if published_at < cutoff_date:
                    continue

                # Google News 리디렉션 URL에서 실제 URL 추출 시도
                actual_url = self._extract_actual_url(link)

                items.append(
                    CrawledNewsItem(
                        title=title.strip(),
                        url=actual_url,
                        published_at=published_at,
                        source=source,
                        snippet=None,
                        content=None,
                    )
                )

            except (AttributeError, ValueError) as e:
                logger.debug(f"Failed to parse RSS item: {e}")
                continue

        logger.debug(f"Parsed {len(items)} news items from RSS")
        return items

    @staticmethod
    def _parse_rfc2822_date(date_str: str) -> datetime:
        """RFC 2822 날짜 형식 파싱"""
        try:
            return parsedate_to_datetime(date_str)
        except (TypeError, ValueError):
            # 파싱 실패 시 현재 시간 반환
            return datetime.now(timezone.utc)

    @staticmethod
    def _extract_actual_url(google_news_url: str) -> str:
        """Google News 리디렉션 URL에서 실제 URL 추출

        Google News URL은 리디렉션을 사용하므로, 가능하면 실제 URL을 추출합니다.
        실패 시 원본 URL을 그대로 반환합니다.
        """
        # Google News URL 패턴: https://news.google.com/rss/articles/...
        # 현재는 원본 URL 그대로 사용 (리디렉션은 실제 요청 시 처리)
        return google_news_url

    async def close(self) -> None:
        """HTTP 클라이언트 정리"""
        if self._client and self._owns_client:
            await self._client.aclose()
            self._client = None
