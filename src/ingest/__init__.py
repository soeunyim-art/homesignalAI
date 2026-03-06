"""
Ingest 도메인 - 데이터 적재 API

개발1(국토교통부), 개발2(뉴스)가 독립적으로 데이터를 적재할 수 있는 API 제공
"""

from .router import router
from .schemas import (
    HouseDataBatchRequest,
    HouseDataBatchResponse,
    HouseDataItem,
    HouseDataStatusResponse,
    NewsSignalBatchRequest,
    NewsSignalBatchResponse,
    NewsSignalItem,
    NewsSignalStatusResponse,
    PredictionBatchRequest,
    PredictionBatchResponse,
    PredictionItem,
)

__all__ = [
    "router",
    "HouseDataItem",
    "HouseDataBatchRequest",
    "HouseDataBatchResponse",
    "HouseDataStatusResponse",
    "NewsSignalItem",
    "NewsSignalBatchRequest",
    "NewsSignalBatchResponse",
    "NewsSignalStatusResponse",
    "PredictionItem",
    "PredictionBatchRequest",
    "PredictionBatchResponse",
]
