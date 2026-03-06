from fastapi import APIRouter, Depends

from src.shared.cache import CacheClient, get_cache_client

from .schemas import ForecastRequest, ForecastResponse
from .service import ForecastService

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("", response_model=ForecastResponse)
async def get_forecast(
    region: str = "동대문구",
    period: str = "month",
    horizon: int = 3,
    include_news_weight: bool = True,
    cache: CacheClient = Depends(get_cache_client),
) -> ForecastResponse:
    """
    시계열 예측 조회 (GET)

    - **region**: 예측 대상 지역 (동대문구 또는 세부 동 단위)
    - **period**: 예측 기간 단위 (week/month)
    - **horizon**: 예측 기간 수
    - **include_news_weight**: 뉴스 이슈 가중치 포함 여부
    """
    request = ForecastRequest(
        region=region,
        period=period,
        horizon=horizon,
        include_news_weight=include_news_weight,
    )
    service = ForecastService(cache=cache)
    return await service.get_forecast(request)


@router.post("", response_model=ForecastResponse)
async def create_forecast(
    request: ForecastRequest,
    cache: CacheClient = Depends(get_cache_client),
) -> ForecastResponse:
    """
    시계열 예측 조회 (POST)

    복잡한 필터 조건이 필요한 경우 POST 사용
    """
    service = ForecastService(cache=cache)
    return await service.get_forecast(request)
