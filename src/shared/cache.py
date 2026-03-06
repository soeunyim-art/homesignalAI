import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from src.config import settings

from .exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis 캐싱 클라이언트"""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    @staticmethod
    def generate_key(prefix: str, params: dict[str, Any]) -> str:
        """파라미터 기반 캐시 키 생성"""
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        hash_str = hashlib.sha256(params_str.encode()).hexdigest()[:16]
        return f"homesignal:{prefix}:{hash_str}"

    async def get(self, key: str) -> Any | None:
        """캐시에서 값 조회"""
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"캐시 조회 실패: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """캐시에 값 저장"""
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self._redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시에서 키 삭제"""
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"캐시 삭제 실패: {e}")
            return False


_cache_client: CacheClient | None = None


async def get_cache_client() -> CacheClient:
    """캐시 클라이언트 싱글톤 반환"""
    global _cache_client
    if _cache_client is None:
        redis_client = redis.from_url(settings.redis_url)
        _cache_client = CacheClient(redis_client)
    return _cache_client
