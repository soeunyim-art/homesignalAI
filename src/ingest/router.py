"""
Ingest API 라우터 - 데이터 적재 엔드포인트

/api/v1/ingest/* 경로로 데이터 적재 API 제공
"""

import logging

from fastapi import APIRouter, Depends

from .auth import (
    UserRole,
    require_any_ingest_role,
    require_internal_role,
    require_molit_role,
    require_news_role,
)
from .schemas import (
    HouseDataBatchRequest,
    HouseDataBatchResponse,
    HouseDataStatusResponse,
    NewsSignalBatchRequest,
    NewsSignalBatchResponse,
    NewsSignalStatusResponse,
    PredictionBatchRequest,
    PredictionBatchResponse,
)
from .service import IngestService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


# =============================================================================
# Houses Data Endpoints (개발1 - 국토교통부 API)
# =============================================================================


@router.post(
    "/houses",
    response_model=HouseDataBatchResponse,
    summary="부동산 거래 데이터 적재",
    description="""
    국토교통부 실거래가 API에서 수집한 부동산 거래 데이터를 배치로 적재합니다.

    **인증:** Supabase Auth JWT 토큰 필요 (data_collector_molit 또는 service_account 역할)

    **제한:** 요청당 최대 1000건

    **중복 처리:** (complex_name, contract_date, price) 기준으로 중복 가능 (별도 체크 없음)
    """,
)
async def ingest_houses(
    request: HouseDataBatchRequest,
    user: UserRole = Depends(require_molit_role),
) -> HouseDataBatchResponse:
    logger.info(f"부동산 데이터 적재 요청: user={user.user_id}, items={len(request.items)}")
    service = IngestService()
    return await service.ingest_houses(request)


@router.get(
    "/houses/status",
    response_model=HouseDataStatusResponse,
    summary="부동산 데이터 현황 조회",
    description="현재 적재된 부동산 데이터의 통계 정보를 조회합니다.",
)
async def get_houses_status(
    user: UserRole = Depends(require_any_ingest_role),
) -> HouseDataStatusResponse:
    logger.info(f"부동산 데이터 현황 조회: user={user.user_id}")
    service = IngestService()
    return await service.get_houses_status()


# =============================================================================
# News Signals Endpoints (개발2 - 뉴스 크롤링)
# =============================================================================


@router.post(
    "/news",
    response_model=NewsSignalBatchResponse,
    summary="뉴스 데이터 적재",
    description="""
    뉴스 크롤러에서 수집한 뉴스 데이터를 배치로 적재합니다.

    **인증:** Supabase Auth JWT 토큰 필요 (data_collector_news 또는 service_account 역할)

    **제한:** 요청당 최대 500건

    **임베딩 처리:**
    - `embedding` 필드에 벡터 포함 시: 그대로 저장
    - `embedding` 없고 `generate_embeddings=True`: 백엔드가 OpenAI API로 자동 생성
    - `embedding` 없고 `generate_embeddings=False`: 임베딩 없이 저장

    **중복 처리:** URL 기준으로 중복 체크 (기존 URL이 있으면 스킵)
    """,
)
async def ingest_news(
    request: NewsSignalBatchRequest,
    user: UserRole = Depends(require_news_role),
) -> NewsSignalBatchResponse:
    logger.info(
        f"뉴스 데이터 적재 요청: user={user.user_id}, items={len(request.items)}, "
        f"generate_embeddings={request.generate_embeddings}"
    )
    service = IngestService()
    return await service.ingest_news(request)


@router.get(
    "/news/status",
    response_model=NewsSignalStatusResponse,
    summary="뉴스 데이터 현황 조회",
    description="현재 적재된 뉴스 데이터의 통계 정보를 조회합니다.",
)
async def get_news_status(
    user: UserRole = Depends(require_any_ingest_role),
) -> NewsSignalStatusResponse:
    logger.info(f"뉴스 데이터 현황 조회: user={user.user_id}")
    service = IngestService()
    return await service.get_news_status()


# =============================================================================
# Predictions Endpoints (백엔드 내부용)
# =============================================================================


@router.post(
    "/predictions",
    response_model=PredictionBatchResponse,
    summary="예측 결과 저장 (내부용)",
    description="""
    시계열 예측 모델의 결과를 저장합니다.

    **인증:** Supabase Auth JWT 토큰 필요 (service_account 역할만)

    예측 결과 히스토리를 저장하여 모델 성능 비교에 활용합니다.
    """,
)
async def ingest_predictions(
    request: PredictionBatchRequest,
    user: UserRole = Depends(require_internal_role),
) -> PredictionBatchResponse:
    logger.info(f"예측 결과 저장 요청: user={user.user_id}, items={len(request.items)}")
    service = IngestService()
    return await service.ingest_predictions(request)
