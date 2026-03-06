"""토큰 버킷 기반 Rate Limiter"""

import asyncio
import logging
import random
import time

from .schemas import RateLimiterConfig

logger = logging.getLogger(__name__)


class RateLimiter:
    """토큰 버킷 알고리즘 기반 Rate Limiter

    Google News 크롤링 시 차단 방지를 위한 요청 속도 제어.
    - 토큰 버킷으로 burst 허용
    - 랜덤 딜레이로 봇 탐지 회피
    - 지수 백오프로 429 응답 처리
    """

    def __init__(self, config: RateLimiterConfig | None = None):
        self.config = config or RateLimiterConfig()
        self._tokens = float(self.config.requests_per_minute)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """요청 전 토큰 획득 및 랜덤 딜레이 적용"""
        async with self._lock:
            self._refill_tokens()

            if self._tokens < 1:
                # 토큰 부족 시 대기
                wait_time = 60.0 / self.config.requests_per_minute
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for token")
                await asyncio.sleep(wait_time)
                self._refill_tokens()

            self._tokens -= 1

        # 랜덤 딜레이 추가 (봇 탐지 회피)
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        logger.debug(f"Random delay: {delay:.2f}s")
        await asyncio.sleep(delay)

    async def backoff(self, attempt: int) -> float:
        """지수 백오프 대기

        Args:
            attempt: 현재 재시도 횟수 (0부터 시작)

        Returns:
            실제 대기한 시간 (초)
        """
        # 지수 백오프 + 지터
        delay = min(
            (2**attempt) + random.uniform(0, 1),
            self.config.max_backoff,
        )
        logger.warning(f"Backoff: attempt {attempt + 1}, waiting {delay:.2f}s")
        await asyncio.sleep(delay)
        return delay

    def _refill_tokens(self) -> None:
        """시간 경과에 따른 토큰 충전"""
        now = time.monotonic()
        elapsed = now - self._last_refill

        # 분당 토큰 수에 비례하여 충전
        tokens_to_add = elapsed * (self.config.requests_per_minute / 60.0)
        self._tokens = min(
            self._tokens + tokens_to_add,
            float(self.config.requests_per_minute),
        )
        self._last_refill = now

    @property
    def available_tokens(self) -> float:
        """현재 사용 가능한 토큰 수 (디버깅용)"""
        return self._tokens
