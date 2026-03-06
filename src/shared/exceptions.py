from typing import Any


class HomeSignalError(Exception):
    """HomeSignal AI 기본 예외 클래스"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DatabaseError(HomeSignalError):
    """데이터베이스 관련 오류"""

    pass


class NotFoundError(HomeSignalError):
    """리소스를 찾을 수 없음"""

    pass


class ValidationError(HomeSignalError):
    """입력값 검증 오류"""

    pass


class AIAPIError(HomeSignalError):
    """AI API 호출 오류 (Fallback 트리거용)"""

    pass


class CacheError(HomeSignalError):
    """캐시 관련 오류 (무시 가능)"""

    pass
