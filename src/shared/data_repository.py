"""
데이터 조회 인터페이스 - 내부 서비스용 데이터 접근 계층

ForecastService, ChatService 등에서 사용하는 데이터 조회 추상화
MockDataRepository로 개발/테스트, SupabaseDataRepository로 프로덕션
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Literal

from supabase import Client

from src.shared.database import get_supabase_client
from src.shared.exceptions import DatabaseError

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
    min_price: float | None = None
    max_price: float | None = None
    price_index: float | None = None


@dataclass
class KeywordFrequency:
    """키워드 빈도 데이터"""

    keyword: str
    frequency: int
    impact_score: float | None = None


@dataclass
class PredictionPoint:
    """예측 결과 단일 포인트"""

    prediction_date: date
    predicted_price: float
    lower_bound: float | None = None
    upper_bound: float | None = None
    model_name: str | None = None
    model_version: str | None = None
    confidence_score: float | None = None


@dataclass
class PolicyEvent:
    """정책 이벤트 도메인 모델"""

    id: str
    event_date: date
    event_type: str
    event_name: str
    description: str | None = None
    impact_level: str | None = None
    region: str | None = None


@dataclass
class MLFeatureRow:
    """ML 학습용 통합 Feature 행"""

    period_date: date
    avg_price: float
    ma_5_week: float | None = None
    ma_20_week: float | None = None
    news_gtx_freq: int = 0
    news_redevelopment_freq: int = 0
    news_policy_freq: int = 0
    news_supply_freq: int = 0
    news_transport_freq: int = 0
    event_gtx_announcement: bool = False
    event_redevelopment_approval: bool = False
    event_interest_rate_change: bool = False
    season_school: bool = False
    season_moving: bool = False
    transaction_count: int = 0
    train_test_split: str | None = None


@dataclass
class DashboardSummary:
    """대시보드 요약 통계"""

    latest_avg_price: float | None = None
    price_change_pct: float | None = None
    latest_transaction_count: int | None = None
    recent_news_count: int = 0
    top_keywords: list[str] = field(default_factory=list)
    trend_direction: str = "unknown"


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
        """시계열 예측용 집계 데이터 조회 (RPC: aggregate_houses_time_series)"""
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
        """키워드별 뉴스 빈도 조회 (RPC: get_news_keyword_frequency)

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

    # --- Predictions Queries ---

    @abstractmethod
    async def get_latest_predictions(
        self,
        region: str,
        period: Literal["week", "month"] = "week",
        horizon: int = 12,
    ) -> list[PredictionPoint]:
        """최신 예측 결과 조회 (RPC: get_latest_predictions)"""
        pass

    # --- ML Features Queries ---

    @abstractmethod
    async def get_ml_features(
        self,
        region: str,
        period_type: Literal["week", "month"] = "week",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[MLFeatureRow]:
        """ML Feature + 뉴스 빈도 결합 조회 (RPC: get_ml_features_with_news)"""
        pass

    # --- Policy Events Queries ---

    @abstractmethod
    async def get_policy_events(
        self,
        start_date: date,
        end_date: date,
        region: str | None = None,
        event_types: list[str] | None = None,
    ) -> list[PolicyEvent]:
        """정책 이벤트 조회 (RPC: get_policy_events_in_range)"""
        pass

    # --- Dashboard ---

    @abstractmethod
    async def get_dashboard_summary(
        self,
        region: str,
        period_type: Literal["week", "month"] = "week",
    ) -> DashboardSummary:
        """대시보드 요약 통계 (RPC: get_dashboard_summary)"""
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

    async def get_latest_predictions(
        self,
        region: str,
        period: Literal["week", "month"] = "week",
        horizon: int = 12,
    ) -> list[PredictionPoint]:
        """Mock 예측 결과 반환"""
        today = date.today()
        delta = timedelta(weeks=1) if period == "week" else timedelta(days=30)
        base_price = 105000000.0
        return [
            PredictionPoint(
                prediction_date=today + (delta * (i + 1)),
                predicted_price=base_price + (i * 800000),
                lower_bound=base_price + (i * 800000) - 3000000,
                upper_bound=base_price + (i * 800000) + 3000000,
                model_name="mock-ensemble",
                model_version="0.1.0",
                confidence_score=0.85 - (i * 0.02),
            )
            for i in range(horizon)
        ]

    async def get_ml_features(
        self,
        region: str,
        period_type: Literal["week", "month"] = "week",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[MLFeatureRow]:
        """Mock ML Feature 반환"""
        today = date.today()
        delta = timedelta(weeks=1) if period_type == "week" else timedelta(days=30)
        return [
            MLFeatureRow(
                period_date=today - (delta * i),
                avg_price=100000000 + (i * 500000),
                ma_5_week=100000000 + (i * 400000),
                ma_20_week=99000000 + (i * 300000),
                news_gtx_freq=max(0, 10 - i),
                news_redevelopment_freq=max(0, 8 - i),
                news_policy_freq=max(0, 5 - i),
                event_gtx_announcement=i == 3,
                season_school=i in (2, 3),
                transaction_count=50 - i,
                train_test_split="train" if i > 2 else "test",
            )
            for i in range(12)
        ]

    async def get_policy_events(
        self,
        start_date: date,
        end_date: date,
        region: str | None = None,
        event_types: list[str] | None = None,
    ) -> list[PolicyEvent]:
        """Mock 정책 이벤트 반환"""
        return [
            PolicyEvent(
                id="mock-event-1",
                event_date=date(2025, 6, 15),
                event_type="gtx",
                event_name="GTX-C 청량리역 착공",
                description="GTX-C 노선 청량리역 구간 착공 시작",
                impact_level="high",
                region="청량리동",
            ),
            PolicyEvent(
                id="mock-event-2",
                event_date=date(2025, 3, 1),
                event_type="redevelopment",
                event_name="이문휘경 뉴타운 사업 승인",
                description="이문휘경 뉴타운 재개발 정비 사업 최종 승인",
                impact_level="high",
                region="이문동",
            ),
        ]

    async def get_dashboard_summary(
        self,
        region: str,
        period_type: Literal["week", "month"] = "week",
    ) -> DashboardSummary:
        """Mock 대시보드 요약 반환"""
        return DashboardSummary(
            latest_avg_price=105000000,
            price_change_pct=1.5,
            latest_transaction_count=48,
            recent_news_count=23,
            top_keywords=["GTX", "재개발", "청량리", "뉴타운", "금리"],
            trend_direction="rising",
        )


# =============================================================================
# Supabase Implementation (프로덕션용)
# =============================================================================


class SupabaseDataRepository(DataRepositoryInterface):
    """Supabase 데이터 레포지토리 - 프로덕션용

    RPC 함수를 통해 DB 레벨에서 집계/필터링을 수행하여
    네트워크 전송량과 Python 측 처리를 최소화합니다.
    """

    def __init__(self, client: Client | None = None):
        self.db = client or get_supabase_client()

    def _rpc(self, fn_name: str, params: dict[str, Any]) -> Any:
        """RPC 함수 호출 헬퍼 (공통 에러 처리)"""
        return self.db.rpc(fn_name, params).execute()

    async def get_houses_time_series(
        self,
        region: str,
        period: Literal["week", "month"],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TimeSeriesDataPoint]:
        """RPC: aggregate_houses_time_series 호출"""
        try:
            params: dict[str, Any] = {
                "p_region": region,
                "p_period_type": period,
                "p_limit": 104,
            }
            if start_date:
                params["p_start_date"] = start_date.isoformat()
            if end_date:
                params["p_end_date"] = end_date.isoformat()

            result = self._rpc("aggregate_houses_time_series", params)

            return [
                TimeSeriesDataPoint(
                    period_date=date.fromisoformat(row["period_date"]),
                    avg_price=float(row["avg_price"]),
                    transaction_count=int(row["transaction_count"]),
                    min_price=float(row["min_price"]) if row.get("min_price") else None,
                    max_price=float(row["max_price"]) if row.get("max_price") else None,
                    price_index=float(row["price_index"]) if row.get("price_index") else None,
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"시계열 데이터 조회 실패: {e}")
            raise DatabaseError(
                message="시계열 데이터 조회에 실패했습니다",
                details={"region": region, "period": period, "error": str(e)},
            )

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
            raise DatabaseError(
                message="거래 내역 조회에 실패했습니다",
                details={"region": region, "limit": limit, "error": str(e)},
            )

    async def get_news_keyword_frequency(
        self,
        keywords: list[str],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        rise_point_windows: list[tuple[date, date]] | None = None,
    ) -> list[KeywordFrequency]:
        """RPC: get_news_keyword_frequency 호출"""
        try:
            params: dict[str, Any] = {"p_keywords": keywords}

            if rise_point_windows:
                windows_json = [
                    {"start": ws.isoformat(), "end": we.isoformat()}
                    for ws, we in rise_point_windows
                ]
                params["p_rise_point_windows"] = json.dumps(windows_json)
            else:
                if start_date:
                    params["p_start_date"] = start_date.isoformat()
                if end_date:
                    params["p_end_date"] = end_date.isoformat()

            result = self._rpc("get_news_keyword_frequency", params)

            return [
                KeywordFrequency(
                    keyword=row["keyword"],
                    frequency=int(row["frequency"]),
                    impact_score=float(row["impact_score"]) if row.get("impact_score") is not None else None,
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"키워드 빈도 조회 실패: {e}")
            raise DatabaseError(
                message="키워드 빈도 조회에 실패했습니다",
                details={"keywords": keywords, "error": str(e)},
            )

    async def get_news_by_keywords(
        self,
        keywords: list[str],
        limit: int = 50,
    ) -> list[NewsSignal]:
        """Supabase에서 키워드로 뉴스 검색"""
        try:
            # 충분한 데이터를 가져온 후 Python에서 필터링
            # TODO: PostgreSQL 배열 연산자 또는 RPC 함수로 최적화 필요
            result = (
                self.db.table("news_signals")
                .select("*")
                .order("published_at", desc=True)
                .limit(limit * 3)  # 여유있게 가져오기
                .execute()
            )

            # 키워드 필터링: keywords 배열에 검색 키워드 중 하나라도 포함된 경우
            filtered_results = []
            for row in result.data:
                row_keywords = row.get("keywords", [])
                # 대소문자 구분 없이 비교
                row_keywords_lower = [kw.lower() for kw in row_keywords]
                keywords_lower = [kw.lower() for kw in keywords]

                # 검색 키워드 중 하나라도 뉴스의 키워드에 포함되면 선택
                if any(kw in row_keywords_lower for kw in keywords_lower):
                    filtered_results.append(row)
                    if len(filtered_results) >= limit:
                        break

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
                for row in filtered_results
            ]

        except Exception as e:
            logger.error(f"뉴스 검색 실패: {e}")
            raise DatabaseError(
                message="뉴스 검색에 실패했습니다",
                details={"keywords": keywords, "limit": limit, "error": str(e)},
            )

    async def search_news_by_similarity(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[NewsSignal]:
        """RPC: match_news_documents 호출 (pgvector 코사인 유사도)"""
        try:
            result = self._rpc("match_news_documents", {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "match_threshold": 0.5,
            })

            return [
                NewsSignal(
                    id=row["id"],
                    title=row["title"],
                    content=row.get("content"),
                    url=row.get("url"),
                    keywords=row.get("keywords", []),
                    published_at=datetime.fromisoformat(
                        str(row["published_at"]).replace("Z", "+00:00")
                    ),
                    embedding=None,
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            raise DatabaseError(
                message="유사도 검색에 실패했습니다",
                details={"top_k": top_k, "error": str(e)},
            )

    async def get_latest_predictions(
        self,
        region: str,
        period: Literal["week", "month"] = "week",
        horizon: int = 12,
    ) -> list[PredictionPoint]:
        """RPC: get_latest_predictions 호출"""
        try:
            result = self._rpc("get_latest_predictions", {
                "p_region": region,
                "p_period": period,
                "p_horizon": horizon,
            })

            return [
                PredictionPoint(
                    prediction_date=date.fromisoformat(row["prediction_date"]),
                    predicted_price=float(row["predicted_price"]),
                    lower_bound=float(row["lower_bound"]) if row.get("lower_bound") else None,
                    upper_bound=float(row["upper_bound"]) if row.get("upper_bound") else None,
                    model_name=row.get("model_name"),
                    model_version=row.get("model_version"),
                    confidence_score=float(row["confidence_score"]) if row.get("confidence_score") else None,
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"예측 결과 조회 실패: {e}")
            raise DatabaseError(
                message="예측 결과 조회에 실패했습니다",
                details={"region": region, "period": period, "error": str(e)},
            )

    async def get_ml_features(
        self,
        region: str,
        period_type: Literal["week", "month"] = "week",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[MLFeatureRow]:
        """RPC: get_ml_features_with_news 호출"""
        try:
            params: dict[str, Any] = {
                "p_region": region,
                "p_period_type": period_type,
            }
            if start_date:
                params["p_start_date"] = start_date.isoformat()
            if end_date:
                params["p_end_date"] = end_date.isoformat()

            result = self._rpc("get_ml_features_with_news", params)

            return [
                MLFeatureRow(
                    period_date=date.fromisoformat(row["period_date"]),
                    avg_price=float(row["avg_price"]),
                    ma_5_week=float(row["ma_5_week"]) if row.get("ma_5_week") is not None else None,
                    ma_20_week=float(row["ma_20_week"]) if row.get("ma_20_week") is not None else None,
                    news_gtx_freq=int(row.get("news_gtx_freq", 0)),
                    news_redevelopment_freq=int(row.get("news_redevelopment_freq", 0)),
                    news_policy_freq=int(row.get("news_policy_freq", 0)),
                    news_supply_freq=int(row.get("news_supply_freq", 0)),
                    news_transport_freq=int(row.get("news_transport_freq", 0)),
                    event_gtx_announcement=bool(row.get("event_gtx_announcement", False)),
                    event_redevelopment_approval=bool(row.get("event_redevelopment_approval", False)),
                    event_interest_rate_change=bool(row.get("event_interest_rate_change", False)),
                    season_school=bool(row.get("season_school", False)),
                    season_moving=bool(row.get("season_moving", False)),
                    transaction_count=int(row.get("transaction_count", 0)),
                    train_test_split=row.get("train_test_split"),
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"ML Feature 조회 실패: {e}")
            raise DatabaseError(
                message="ML Feature 조회에 실패했습니다",
                details={"region": region, "period_type": period_type, "error": str(e)},
            )

    async def get_policy_events(
        self,
        start_date: date,
        end_date: date,
        region: str | None = None,
        event_types: list[str] | None = None,
    ) -> list[PolicyEvent]:
        """RPC: get_policy_events_in_range 호출"""
        try:
            params: dict[str, Any] = {
                "p_start_date": start_date.isoformat(),
                "p_end_date": end_date.isoformat(),
            }
            if region:
                params["p_region"] = region
            if event_types:
                params["p_event_types"] = event_types

            result = self._rpc("get_policy_events_in_range", params)

            return [
                PolicyEvent(
                    id=str(row["id"]),
                    event_date=date.fromisoformat(row["event_date"]),
                    event_type=row["event_type"],
                    event_name=row["event_name"],
                    description=row.get("description"),
                    impact_level=row.get("impact_level"),
                    region=row.get("region"),
                )
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"정책 이벤트 조회 실패: {e}")
            raise DatabaseError(
                message="정책 이벤트 조회에 실패했습니다",
                details={"start_date": str(start_date), "end_date": str(end_date), "error": str(e)},
            )

    async def get_dashboard_summary(
        self,
        region: str,
        period_type: Literal["week", "month"] = "week",
    ) -> DashboardSummary:
        """RPC: get_dashboard_summary 호출"""
        try:
            result = self._rpc("get_dashboard_summary", {
                "p_region": region,
                "p_period_type": period_type,
            })

            if not result.data:
                return DashboardSummary()

            row = result.data[0]
            return DashboardSummary(
                latest_avg_price=float(row["latest_avg_price"]) if row.get("latest_avg_price") else None,
                price_change_pct=float(row["price_change_pct"]) if row.get("price_change_pct") is not None else None,
                latest_transaction_count=int(row["latest_transaction_count"]) if row.get("latest_transaction_count") else None,
                recent_news_count=int(row.get("recent_news_count", 0)),
                top_keywords=row.get("top_keywords") or [],
                trend_direction=row.get("trend_direction", "unknown"),
            )

        except Exception as e:
            logger.error(f"대시보드 요약 조회 실패: {e}")
            raise DatabaseError(
                message="대시보드 요약 조회에 실패했습니다",
                details={"region": region, "error": str(e)},
            )


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
