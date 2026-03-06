"""Rate Limiter 테스트"""

import asyncio
import time

import pytest

from src.crawler.rate_limiter import RateLimiter
from src.crawler.schemas import RateLimiterConfig


@pytest.mark.asyncio
async def test_rate_limiter_acquire(rate_limiter_config: RateLimiterConfig):
    """토큰 획득 및 딜레이 테스트"""
    limiter = RateLimiter(rate_limiter_config)

    start = time.monotonic()
    await limiter.acquire()
    elapsed = time.monotonic() - start

    # 최소 딜레이 적용 확인
    assert elapsed >= rate_limiter_config.min_delay


@pytest.mark.asyncio
async def test_rate_limiter_token_consumption(rate_limiter_config: RateLimiterConfig):
    """토큰 소비 테스트"""
    limiter = RateLimiter(rate_limiter_config)

    initial_tokens = limiter.available_tokens
    await limiter.acquire()
    remaining_tokens = limiter.available_tokens

    # 토큰이 소비되었는지 확인 (시간 경과로 약간 충전될 수 있음)
    assert remaining_tokens < initial_tokens


@pytest.mark.asyncio
async def test_rate_limiter_backoff():
    """지수 백오프 테스트"""
    config = RateLimiterConfig(max_backoff=2.0, min_delay=0.01, max_delay=0.02)
    limiter = RateLimiter(config)

    start = time.monotonic()
    delay = await limiter.backoff(0)  # 첫 번째 재시도
    elapsed = time.monotonic() - start

    # 백오프가 적용되었는지 확인
    assert delay >= 1.0  # 2^0 = 1
    assert elapsed >= 1.0


@pytest.mark.asyncio
async def test_rate_limiter_max_backoff():
    """최대 백오프 제한 테스트"""
    config = RateLimiterConfig(max_backoff=1.0, min_delay=0.01, max_delay=0.02)
    limiter = RateLimiter(config)

    delay = await limiter.backoff(10)  # 높은 재시도 횟수

    # 최대 백오프 제한 확인
    assert delay <= config.max_backoff + 1  # 지터 포함


@pytest.mark.asyncio
async def test_rate_limiter_multiple_requests(rate_limiter_config: RateLimiterConfig):
    """여러 요청의 순차 처리 테스트"""
    limiter = RateLimiter(rate_limiter_config)

    start = time.monotonic()
    for _ in range(3):
        await limiter.acquire()
    elapsed = time.monotonic() - start

    # 3번의 요청에 최소 딜레이 * 3 이상 소요
    min_expected = rate_limiter_config.min_delay * 3
    assert elapsed >= min_expected
