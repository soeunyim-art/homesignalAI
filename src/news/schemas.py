from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class NewsInsightsRequest(BaseModel):
    """뉴스 이슈 분석 요청 스키마"""

    period: Literal["week", "month", "quarter"] = Field(
        default="month",
        description="분석 기간",
    )
    keywords: list[str] = Field(
        default=["GTX", "재개발", "청량리", "이문휘경뉴타운"],
        description="분석 대상 키워드",
    )
    region: str = Field(
        default="동대문구",
        description="분석 대상 지역",
    )
    use_rise_points: bool = Field(
        default=False,
        description="상승 시점 전후 윈도우 내 뉴스만 분석할지 여부",
    )


class KeywordInsight(BaseModel):
    """키워드별 분석 결과"""

    keyword: str
    frequency: int = Field(description="언급 빈도")
    trend: Literal["상승", "하락", "유지"] = Field(description="이전 기간 대비 트렌드")
    sentiment_score: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="감성 점수 (-1: 부정, 0: 중립, 1: 긍정)",
    )
    sample_headlines: list[str] = Field(
        default_factory=list,
        description="대표 뉴스 헤드라인",
    )


class NewsInsightsResponse(BaseModel):
    """뉴스 이슈 분석 응답 스키마"""

    region: str
    period: str
    analysis_date: date
    total_articles: int = Field(description="분석된 총 기사 수")
    insights: list[KeywordInsight]
    top_issues: list[str] = Field(
        description="주요 이슈 요약 (상위 3개)",
    )
