from fastapi import APIRouter, Query

from .schemas import NewsInsightsResponse
from .service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/insights", response_model=NewsInsightsResponse)
async def get_news_insights(
    period: str = Query(default="month", description="분석 기간 (week/month/quarter)"),
    keywords: list[str] = Query(
        default=["GTX", "재개발", "청량리"],
        description="분석 대상 키워드",
    ),
    region: str = Query(default="동대문구", description="분석 대상 지역"),
) -> NewsInsightsResponse:
    """
    뉴스 키워드 인사이트 조회

    동대문구 관련 뉴스에서 특정 키워드의 언급 빈도, 트렌드,
    감성 점수를 분석하여 반환합니다.

    - **period**: 분석 기간 (week, month, quarter)
    - **keywords**: 분석 대상 키워드 목록
    - **region**: 분석 대상 지역

    응답에는 키워드별 빈도, 트렌드, 감성 점수, 대표 헤드라인이 포함됩니다.
    """
    from .schemas import NewsInsightsRequest

    request = NewsInsightsRequest(
        period=period,
        keywords=keywords,
        region=region,
    )
    service = NewsService()
    return await service.get_insights(request)
