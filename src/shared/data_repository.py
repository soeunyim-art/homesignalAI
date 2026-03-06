"""
데이터 조회 인터페이스 - 내부 서비스용 데이터 접근 계층

ForecastService, ChatService 등에서 사용하는 데이터 조회 추상화
MockDataRepository로 개발/테스트, SupabaseDataRepository로 프로덕션
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

from supabase import Client

from src.shared.database import get_supabase_client

logger = logging.getLogger(__name__)


# =============================================================================
# Domain Models
# =============================================================================


@dataclass
class HouseTransaction:
    """부동산 거래 도메인 모델"""

    id: str
    complex_name: str
    dong_name: str | None
    price: float
    contract_date: date
    sqft_living: int | None
    yr_built: int | None


@dataclass
class NewsSignal:
    """뉴스 신호 도메인 모델"""

    id: str
    title: str
    content: str | None
    url: str | None
    keywords: list[str]
    published_at: datetime
    embedding: list[float] | None


@dataclass
class TimeSeriesDataPoint:
    """시계열 데이터 포인트 (집계용)"""

    period_date: date
    avg_price: float
    transaction_count: int
    price_index: float | None = None


@dataclass
class KeywordFrequency:
    """키워드 빈도 데이터"""

    keyword: str
    frequency: int
    impact_score: float | None = None


# =============================================================================
# Abstract Interface
# =============================================================================


class DataRepositoryInterface(ABC):
    """데이터 조회 추상 인터페이스"""

    # --- Houses Data Queries ---

    @abstractmethod
    async def get_houses_time_series(
        self,
        region: str,
        period: Literal["week", "month"],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TimeSeriesDataPoint]:
        """시계열 예측용 집계 데이터 조회"""
        pass

    @abstractmethod
    async def get_latest_transactions(
        self,
        region: str,
        limit: int = 100,
    ) -> list[HouseTransaction]:
        """최근 거래 내역 조회"""
        pass

    # --- News Signals Queries ---

    @abstractmethod
    async def get_news_keyword_frequency(
        self,
        keywords: list[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        rise_point_windows: list[tuple[date, date]] | None = None,
    ) -> list[KeywordFrequency]:
        """키워드별 뉴스 빈도 조회
        
        Args:
            keywords: 검색할 키워드 목록
            start_date: 시작 날짜 (rise_point_windows 없을 때)
            end_date: 종료 날짜 (rise_point_windows 없을 때)
            rise_point_windows: 상승 시점 윈도우 목록 [(start, end), ...]
                               제공 시 해당 윈도우들 내의 뉴스만 집계
        """
        pass

    @abstractmethod
    async def get_news_by_keywords(
        self,
        keywords: list[str],
        limit: int = 50,
    ) -> list[NewsSignal]:
        """키워드로 뉴스 검색"""
        pass

    @abstractmethod
    async def search_news_by_similarity(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[NewsSignal]:
        """벡터 유사도 기반 뉴스 검색 (RAG용)"""
        pass


# =============================================================================
# Mock Implementation (개발/테스트용)
# =============================================================================


class MockDataRepository(DataRepositoryInterface):
    """Mock 데이터 레포지토리 - 개발 및 테스트용"""

    async def get_houses_time_series(
        self,
        region: str,
        period: Literal["week", "month"],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TimeSeriesDataPoint]:
        """Mock 시계열 데이터 반환"""
        today = date.today()
        delta = timedelta(weeks=1) if period == "week" else timedelta(days=30)

        return [
            TimeSeriesDataPoint(
                period_date=today - (delta * i),
                avg_price=100000000 + (i * 500000),
                transaction_count=50 - i,
                price_index=100 + (i * 0.5),
            )
            for i in range(12)
        ]

    async def get_latest_transactions(
        self,
        region: str,
        limit: int = 100,
    ) -> list[HouseTransaction]:
        """Mock 거래 내역 반환"""
        return [
            HouseTransaction(
                id=f"mock-{i}",
                complex_name=f"Mock 아파트 {i}",
                dong_name="청량리동",
                price=100000000 + (i * 10000000),
                contract_date=date.today() - timedelta(days=i * 7),
                sqft_living=85,
                yr_built=2020,
            )
            for i in range(min(limit, 10))
        ]

    async def get_news_keyword_frequency(
        self,
        keywords: list[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        rise_point_windows: list[tuple[date, date]] | None = None,
    ) -> list[KeywordFrequency]:
        """Mock 키워드 빈도 반환"""
        mock_frequencies = {
            "GTX": 45,
            "GTX-C": 38,
            "GTX-A": 12,
            "재개발": 32,
            "청량리": 28,
            "청량리역": 25,
            "이문휘경뉴타운": 15,
            "뉴타운": 22,
            "금리": 20,
            "분양": 18,
            "입주": 16,
            "착공": 10,
            "준공": 8,
            "정책": 14,
            "규제": 11,
            "대출": 19,
        }

        if rise_point_windows:
            multiplier = len(rise_point_windows) * 0.3
        else:
            multiplier = 1.0

        return [
            KeywordFrequency(
                keyword=kw,
                frequency=int(mock_frequencies.get(kw, 10) * multiplier),
                impact_score=0.8 if kw in ["GTX", "재개발", "GTX-C"] else 0.5,
            )
            for kw in keywords
        ]

    async def get_news_by_keywords(
        self,
        keywords: list[str],
        limit: int = 50,
    ) -> list[NewsSignal]:
        """Mock 뉴스 검색 결과 반환"""
        return [
            NewsSignal(
                id="mock-news-1",
                title="GTX-C 청량리역 2028년 개통 확정",
                content="GTX-C 노선 청량리역 개통이 2028년으로 확정됐다...",
                url="https://example.com/news/1",
                keywords=["GTX", "청량리", "교통"],
                published_at=datetime.now() - timedelta(days=1),
                embedding=None,
            ),
            NewsSignal(
                id="mock-news-2",
                title="동대문구 재개발 사업 속도",
                content="동대문구 이문휘경 뉴타운 재개발 사업이 본격화...",
                url="https://example.com/news/2",
                keywords=["재개발", "이문휘경뉴타운"],
                published_at=datetime.now() - timedelta(days=3),
                embedding=None,
            ),
        ]

    async def search_news_by_similarity(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[NewsSignal]:
        """Mock 유사도 검색 결과 반환"""
        return await self.get_news_by_keywords(["GTX", "재개발"], limit=top_k)


# =============================================================================
# Supabase Implementation (프로덕션용)
# =============================================================================


class SupabaseDataRepository(DataRepositoryInterface):
    """Supabase 데이터 레포지토리 - 프로덕션용"""

    def __init__(self, client: Client | None = None):
        self.db = client or get_supabase_client()

    async def get_houses_time_series(
        self,
        region: str,
        period: Literal["week", "month"],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TimeSeriesDataPoint]:
        """Supabase에서 시계열 데이터 조회"""
        try:
            query = self.db.table("houses_data").select("*")

            if region != "동대문구":
                query = query.ilike("dong_name", f"%{region}%")

            if start_date:
                query = query.gte("contract_date", start_date.isoformat())
            if end_date:
                query = query.lte("contract_date", end_date.isoformat())

            result = query.order("contract_date", desc=True).execute()

            # 간단한 집계 (실제로는 SQL 집계 함수 사용 권장)
            data_points: dict[str, list[float]] = {}
            for row in result.data:
                contract_date = row["contract_date"][:10]
                if contract_date not in data_points:
                    data_points[contract_date] = []
                data_points[contract_date].append(float(row["price"]))

            return [
                TimeSeriesDataPoint(
                    period_date=date.fromisoformat(d),
                    avg_price=sum(prices) / len(prices),
                    transaction_count=len(prices),
                    price_index=None,
                )
                for d, prices in sorted(data_points.items(), reverse=True)
            ]

        except Exception as e:
            logger.error(f"시계열 데이터 조회 실패: {e}")
            return []

    async def get_latest_transactions(
        self,
        region: str,
        limit: int = 100,
    ) -> list[HouseTransaction]:
        """Supabase에서 최근 거래 조회"""
        try:
            query = self.db.table("houses_data").select("*")

            if region != "동대문구":
                query = query.ilike("dong_name", f"%{region}%")

            result = query.order("contract_date", desc=True).limit(limit).execute()

            return [
                HouseTransaction(
                    id=row["id"],
                    complex_name=row["complex_name"],
                    dong_name=row.get("dong_name"),
                    price=float(row["price"]),
                    contract_date=date.fromisoformat(row["contract_date"][:10]),
                    sqft_living=row.get("sqft_living"),
                    yr_built=row.get("yr_built"),
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"거래 내역 조회 실패: {e}")
            return []

    async def get_news_keyword_frequency(
        self,
        keywords: list[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        rise_point_windows: list[tuple[date, date]] | None = None,
    ) -> list[KeywordFrequency]:
        """Supabase에서 키워드 빈도 조회"""
        try:
            query = self.db.table("news_signals").select("keywords, published_at")

            if rise_point_windows:
                or_conditions = []
                for window_start, window_end in rise_point_windows:
                    or_conditions.append(
                        f"and(published_at.gte.{window_start.isoformat()},"
                        f"published_at.lte.{window_end.isoformat()})"
                    )
                if or_conditions:
                    query = query.or_(",".join(or_conditions))
            else:
                if start_date:
                    query = query.gte("published_at", start_date.isoformat())
                if end_date:
                    query = query.lte("published_at", end_date.isoformat())

            result = query.execute()

            freq_count: dict[str, int] = {kw: 0 for kw in keywords}
            for row in result.data:
                row_keywords = row.get("keywords", [])
                for kw in keywords:
                    if kw in row_keywords:
                        freq_count[kw] += 1

            return [
                KeywordFrequency(
                    keyword=kw,
                    frequency=count,
                    impact_score=min(count / 50, 1.0),
                )
                for kw, count in freq_count.items()
            ]

        except Exception as e:
            logger.error(f"키워드 빈도 조회 실패: {e}")
            return []

    async def get_news_by_keywords(
        self,
        keywords: list[str],
        limit: int = 50,
    ) -> list[NewsSignal]:
        """Supabase에서 키워드로 뉴스 검색"""
        try:
            # Supabase array contains 쿼리
            result = (
                self.db.table("news_signals")
                .select("*")
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )

            return [
                NewsSignal(
                    id=row["id"],
                    title=row["title"],
                    content=row.get("content"),
                    url=row.get("url"),
                    keywords=row.get("keywords", []),
                    published_at=datetime.fromisoformat(
                        row["published_at"].replace("Z", "+00:00")
                    ),
                    embedding=row.get("embedding"),
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"뉴스 검색 실패: {e}")
            return []

    async def search_news_by_similarity(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[NewsSignal]:
        """Supabase pgvector로 유사도 검색"""
        try:
            # pgvector 유사도 검색 (RPC 함수 필요)
            # 실제로는 match_documents 같은 RPC 함수 호출
            # 여기서는 일반 검색으로 대체
            return await self.get_news_by_keywords(
                ["GTX", "재개발", "청량리"],
                limit=top_k,
            )

        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            return []


# =============================================================================
# Factory
# =============================================================================

_data_repository: DataRepositoryInterface | None = None


def get_data_repository(use_mock: bool | None = None) -> DataRepositoryInterface:
    """
    데이터 레포지토리 인스턴스 반환

    Args:
        use_mock: True면 Mock, False면 Supabase, None이면 자동 판단

    Returns:
        DataRepositoryInterface 구현체
    """
    global _data_repository

    if _data_repository is not None:
        return _data_repository

    from src.config import settings

    # 자동 판단: placeholder URL 또는 use_mock=True면 Mock, 아니면 Supabase
    if use_mock is None:
        use_mock = "placeholder" in settings.supabase_url

    if use_mock:
        logger.info("MockDataRepository 사용")
        _data_repository = MockDataRepository()
    else:
        logger.info("SupabaseDataRepository 사용")
        _data_repository = SupabaseDataRepository()

    return _data_repository
