from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """시계열 예측 요청 스키마"""

    region: str = Field(
        default="동대문구",
        description="예측 대상 지역 (동대문구 또는 세부 동 단위)",
        examples=["동대문구", "청량리동", "이문동"],
    )
    period: Literal["week", "month"] = Field(
        default="month",
        description="예측 기간 단위",
    )
    horizon: int = Field(
        default=3,
        ge=1,
        le=12,
        description="예측 기간 수 (주 또는 월 단위)",
    )
    include_news_weight: bool = Field(
        default=True,
        description="뉴스 이슈 가중치 포함 여부",
    )


class ForecastPoint(BaseModel):
    """개별 예측 데이터 포인트"""

    date: date
    value: float = Field(description="예측 매매가 지수")
    lower_bound: float = Field(description="신뢰구간 하한")
    upper_bound: float = Field(description="신뢰구간 상한")


class NewsWeightSummary(BaseModel):
    """뉴스 이슈 가중치 요약"""

    keyword: str
    frequency: int
    impact_score: float = Field(ge=-1.0, le=1.0, description="영향도 점수 (-1 ~ 1)")


class ForecastResponse(BaseModel):
    """시계열 예측 응답 스키마"""

    region: str
    period: str
    trend: Literal["상승", "하락", "보합"]
    confidence: float = Field(ge=0.0, le=1.0, description="예측 신뢰도")
    forecast: list[ForecastPoint]
    news_weights: list[NewsWeightSummary] | None = Field(
        default=None,
        description="뉴스 이슈 가중치 (include_news_weight=True 시 포함)",
    )
    model_version: str = Field(default="v1.0", description="사용된 모델 버전")
