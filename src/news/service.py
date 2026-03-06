import logging
from datetime import date, timedelta

from src.forecast.rise_point_detector import RisePointDetector
from src.shared.data_repository import (
    DataRepositoryInterface,
    get_data_repository,
)
from src.shared.database import get_supabase_client
from src.shared.rise_point_config import get_rise_point_config

from .schemas import KeywordInsight, NewsInsightsRequest, NewsInsightsResponse

logger = logging.getLogger(__name__)


class NewsService:
    """뉴스 이슈 분석 비즈니스 로직"""

    def __init__(self, data_repo: DataRepositoryInterface | None = None):
        self.db = get_supabase_client()
        self.data_repo = data_repo or get_data_repository()

    async def get_insights(self, request: NewsInsightsRequest) -> NewsInsightsResponse:
        """뉴스 키워드 인사이트 조회"""
        rise_point_windows = None

        if request.use_rise_points:
            rise_point_windows = await self._get_rise_point_windows(request.region)
            logger.info(f"상승 시점 윈도우 {len(rise_point_windows)}개 감지")

        insights = await self._analyze_keywords(
            request.keywords, request.region, rise_point_windows
        )
        top_issues = self._extract_top_issues(insights)

        return NewsInsightsResponse(
            region=request.region,
            period=request.period,
            analysis_date=date.today(),
            total_articles=sum(i.frequency for i in insights),
            insights=insights,
            top_issues=top_issues,
        )

    async def _get_rise_point_windows(
        self, region: str
    ) -> list[tuple[date, date]]:
        """상승 시점 윈도우 조회"""
        try:
            time_series = await self.data_repo.get_houses_time_series(
                region=region,
                period="week",
                start_date=date.today() - timedelta(weeks=52),
                end_date=date.today(),
            )

            if not time_series:
                logger.warning("시계열 데이터가 없어 상승 시점을 감지할 수 없습니다")
                return []

            dates = [point.period_date for point in time_series]
            values = [point.avg_price for point in time_series]

            config = get_rise_point_config()
            detector = RisePointDetector(config)
            rise_points = detector.detect(dates, values)

            return [(rp.window_start, rp.window_end) for rp in rise_points]

        except Exception as e:
            logger.error(f"상승 시점 윈도우 조회 실패: {e}")
            return []

    async def _analyze_keywords(
        self,
        keywords: list[str],
        region: str,
        rise_point_windows: list[tuple[date, date]] | None = None,
    ) -> list[KeywordInsight]:
        """
        키워드별 분석 수행
        
        rise_point_windows가 제공되면 해당 윈도우 내 뉴스만 분석
        """
        keyword_frequencies = await self.data_repo.get_news_keyword_frequency(
            keywords=keywords,
            rise_point_windows=rise_point_windows,
        )

        mock_data = {
            "GTX": {
                "frequency": 45,
                "trend": "상승",
                "sentiment_score": 0.72,
                "headlines": [
                    "GTX-C 청량리역 2028년 개통 확정",
                    "GTX 호재에 동대문구 아파트 거래량 증가",
                ],
            },
            "재개발": {
                "frequency": 38,
                "trend": "상승",
                "sentiment_score": 0.58,
                "headlines": [
                    "이문휘경뉴타운 재개발 속도전",
                    "동대문구 재개발 기대감 고조",
                ],
            },
            "청량리": {
                "frequency": 52,
                "trend": "유지",
                "sentiment_score": 0.65,
                "headlines": [
                    "청량리 일대 상권 활성화",
                    "청량리역 환승센터 이용객 증가",
                ],
            },
            "이문휘경뉴타운": {
                "frequency": 28,
                "trend": "상승",
                "sentiment_score": 0.80,
                "headlines": [
                    "이문휘경뉴타운 조합원 분양가 확정",
                    "이문동 신축 아파트 관심 급증",
                ],
            },
        }

        insights = []
        for kf in keyword_frequencies:
            data = mock_data.get(
                kf.keyword,
                {
                    "frequency": kf.frequency,
                    "trend": "유지",
                    "sentiment_score": 0.0,
                    "headlines": [],
                },
            )
            
            trend = "유지"
            if kf.frequency > data.get("frequency", 0) * 1.2:
                trend = "상승"
            elif kf.frequency < data.get("frequency", 0) * 0.8:
                trend = "하락"
            
            insights.append(
                KeywordInsight(
                    keyword=kf.keyword,
                    frequency=kf.frequency,
                    trend=data.get("trend", trend),
                    sentiment_score=data.get("sentiment_score", 0.0),
                    sample_headlines=data.get("headlines", []),
                )
            )

        return insights

    def _extract_top_issues(self, insights: list[KeywordInsight]) -> list[str]:
        """주요 이슈 추출"""
        # 빈도 기준 상위 3개 키워드 선정
        sorted_insights = sorted(insights, key=lambda x: x.frequency, reverse=True)[:3]
        return [
            f"{insight.keyword}: {insight.frequency}건 ({insight.trend})"
            for insight in sorted_insights
        ]
