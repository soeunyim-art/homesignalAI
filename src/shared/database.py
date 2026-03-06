"""
Supabase 데이터베이스 클라이언트

개발 모드에서 Supabase 라이브러리 로드 실패 시 Mock 클라이언트 사용
"""

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# Supabase 라이브러리 동적 임포트 시도
try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Supabase 라이브러리 로드 실패: {e}")
    SUPABASE_AVAILABLE = False
    Client = Any  # type: ignore


class MockSupabaseTable:
    """Mock Supabase 테이블 - 개발/테스트용"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._data: list[dict] = []

    def select(self, *args, **kwargs):
        return self

    def insert(self, data: dict):
        self._data.append(data)
        return self

    def update(self, data: dict):
        return self

    def delete(self):
        return self

    def eq(self, column: str, value: Any):
        return self

    def neq(self, column: str, value: Any):
        return self

    def gt(self, column: str, value: Any):
        return self

    def gte(self, column: str, value: Any):
        return self

    def lt(self, column: str, value: Any):
        return self

    def lte(self, column: str, value: Any):
        return self

    def ilike(self, column: str, pattern: str):
        return self

    def order(self, column: str, desc: bool = False):
        return self

    def limit(self, count: int):
        return self

    def execute(self):
        """Mock execute - 빈 결과 반환"""

        class MockResponse:
            data: list = []
            count: int = 0

        return MockResponse()


class MockSupabaseAuth:
    """Mock Supabase Auth - 개발/테스트용"""

    def get_user(self, token: str):
        """Mock user 반환"""

        class MockUser:
            id = "mock-user-id"
            email = "mock@example.com"
            user_metadata = {"role": "service_account"}

        class MockResponse:
            user = MockUser()

        return MockResponse()


class MockSupabaseClient:
    """Mock Supabase 클라이언트 - 개발/테스트용"""

    def __init__(self):
        self.auth = MockSupabaseAuth()
        self._tables: dict[str, MockSupabaseTable] = {}
        logger.info("MockSupabaseClient 사용 중 (개발 모드)")

    def table(self, table_name: str) -> MockSupabaseTable:
        if table_name not in self._tables:
            self._tables[table_name] = MockSupabaseTable(table_name)
        return self._tables[table_name]


@lru_cache
def get_supabase_client(use_service_role: bool = False) -> Client:
    """Supabase 클라이언트 싱글톤 반환
    
    Args:
        use_service_role: True면 service_role 키 사용 (INSERT/UPDATE용),
                         False면 anon 키 사용 (SELECT용)
    """
    from src.config import settings

    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase 사용 불가 - MockSupabaseClient 사용")
        return MockSupabaseClient()  # type: ignore

    # placeholder URL 체크
    if "placeholder" in settings.supabase_url:
        logger.warning("Supabase placeholder URL 감지 - MockSupabaseClient 사용")
        return MockSupabaseClient()  # type: ignore

    if use_service_role:
        if not settings.supabase_service_role_key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다. "
                "Ingest API 사용을 위해 .env에 service_role 키를 추가하세요."
            )
        logger.debug("service_role 키로 Supabase 클라이언트 생성")
        return create_client(settings.supabase_url, settings.supabase_service_role_key)
    
    return create_client(settings.supabase_url, settings.supabase_key)
