"""기사 본문 추출기"""

import logging
import re
from urllib.parse import urlparse

import httpx

from .exceptions import ContentExtractionError, NetworkError
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# BeautifulSoup는 선택적 의존성
try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("beautifulsoup4 not installed. Content extraction disabled.")


class ContentExtractor:
    """기사 본문 추출기

    주요 뉴스 사이트별 셀렉터를 사용하여 본문을 추출합니다.
    실패 시 graceful degradation으로 제목만 사용합니다.
    """

    # 주요 뉴스 사이트별 본문 셀렉터
    SITE_SELECTORS: dict[str, list[str]] = {
        # 연합뉴스
        "yna.co.kr": ["article.story-news", "div.article-txt", "div#articleBody"],
        # 한국경제
        "hankyung.com": ["div#articletxt", "div.article-body", "div.txt-body"],
        # 조선일보
        "chosun.com": ["section#article-view", "div.article-body", "div.par"],
        # 중앙일보
        "joongang.co.kr": ["div#article_body", "div.article_body"],
        # 매일경제
        "mk.co.kr": ["div#article_body", "div.art_txt"],
        # 서울경제
        "sedaily.com": ["div.article_view", "div#contents"],
        # 아시아경제
        "asiae.co.kr": ["div#articleBody", "div.article"],
        # 머니투데이
        "mt.co.kr": ["div#textBody", "div.view_text"],
        # 뉴스1
        "news1.kr": ["div#articles_detail", "div.detail"],
        # 뉴시스
        "newsis.com": ["div#articleBody", "div.view_text"],
    }

    # 범용 셀렉터 (사이트 매칭 실패 시)
    GENERIC_SELECTORS = [
        "article",
        "div.article-body",
        "div.article-content",
        "div.article_body",
        "div#article-body",
        "div#articleBody",
        "div.post-content",
        "div.entry-content",
        "main",
    ]

    # 일반적인 브라우저 User-Agent
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 15.0,
        max_content_length: int = 2000,
    ):
        """
        Args:
            rate_limiter: Rate limiter (공유 가능)
            http_client: HTTP 클라이언트 (공유 가능)
            timeout: 요청 타임아웃 (초)
            max_content_length: 추출 본문 최대 길이
        """
        if not BS4_AVAILABLE:
            logger.warning("BeautifulSoup not available. Install with: uv sync --extra crawler")

        self.rate_limiter = rate_limiter
        self._client = http_client
        self._owns_client = http_client is None
        self._timeout = timeout
        self._max_length = max_content_length

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 지연 초기화"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
            )
        return self._client

    async def extract(self, url: str) -> str | None:
        """URL에서 본문 추출

        Args:
            url: 기사 URL

        Returns:
            추출된 본문 텍스트 또는 None (실패 시)
        """
        if not BS4_AVAILABLE:
            return None

        try:
            # Rate limiting (설정된 경우)
            if self.rate_limiter:
                await self.rate_limiter.acquire()

            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()

            html = response.text
            content = self._parse_content(html, url)

            if content:
                # 길이 제한 적용
                if len(content) > self._max_length:
                    content = content[: self._max_length] + "..."
                logger.debug(f"Extracted {len(content)} chars from {url}")

            return content

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error extracting {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Request error extracting {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            return None

    def _parse_content(self, html: str, url: str) -> str | None:
        """HTML에서 본문 파싱"""
        soup = BeautifulSoup(html, "html.parser")

        # 불필요한 요소 제거
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # 도메인 추출
        domain = urlparse(url).netloc.lower()

        # 사이트별 셀렉터 시도
        selectors = self._get_selectors_for_domain(domain)

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self._clean_text(element.get_text())
                if len(text) > 100:  # 최소 길이 체크
                    return text

        # 범용 셀렉터 시도
        for selector in self.GENERIC_SELECTORS:
            element = soup.select_one(selector)
            if element:
                text = self._clean_text(element.get_text())
                if len(text) > 100:
                    return text

        logger.debug(f"No content found for {url}")
        return None

    def _get_selectors_for_domain(self, domain: str) -> list[str]:
        """도메인에 맞는 셀렉터 목록 반환"""
        for site_domain, selectors in self.SITE_SELECTORS.items():
            if site_domain in domain:
                return selectors
        return []

    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 연속 공백 제거
        text = re.sub(r"\s+", " ", text)
        # 앞뒤 공백 제거
        text = text.strip()
        return text

    async def extract_batch(
        self,
        urls: list[str],
        concurrency: int = 3,
    ) -> dict[str, str | None]:
        """여러 URL에서 본문 일괄 추출

        Args:
            urls: URL 목록
            concurrency: 동시 요청 수

        Returns:
            URL: 본문 딕셔너리
        """
        import asyncio

        results: dict[str, str | None] = {}
        semaphore = asyncio.Semaphore(concurrency)

        async def extract_with_semaphore(url: str) -> tuple[str, str | None]:
            async with semaphore:
                content = await self.extract(url)
                return url, content

        tasks = [extract_with_semaphore(url) for url in urls]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for result in completed:
            if isinstance(result, Exception):
                logger.warning(f"Batch extraction error: {result}")
                continue
            url, content = result
            results[url] = content

        return results

    async def close(self) -> None:
        """HTTP 클라이언트 정리"""
        if self._client and self._owns_client:
            await self._client.aclose()
            self._client = None
