"""크롤러 전용 예외 클래스"""

from src.shared.exceptions import HomeSignalError


class CrawlerError(HomeSignalError):
    """크롤러 기본 예외"""

    pass


class RateLimitError(CrawlerError):
    """Rate limit 초과 (429 응답)"""

    pass


class ParseError(CrawlerError):
    """RSS/HTML 파싱 실패"""

    pass


class NetworkError(CrawlerError):
    """네트워크 요청 실패 (연결 오류, 타임아웃)"""

    pass


class ContentExtractionError(CrawlerError):
    """본문 추출 실패"""

    pass
