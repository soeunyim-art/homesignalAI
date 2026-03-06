"""Query Planner 스키마 정의"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    """질문 의도 분류"""

    PRICE_INQUIRY = "price_inquiry"  # 현재/과거 시세 조회
    FORECAST = "forecast"  # 미래 가격 예측
    COMPARISON = "comparison"  # 지역/시기 비교
    NEWS_ANALYSIS = "news_analysis"  # 뉴스/정책 영향 분석
    TREND_ANALYSIS = "trend_analysis"  # 가격 추세 분석
    INVESTMENT = "investment"  # 투자 판단 질문
    GENERAL = "general"  # 일반 정보


class IntentClassificationResult(BaseModel):
    """의도 분류 결과"""

    primary_intent: QueryIntent
    secondary_intents: list[QueryIntent] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractedEntities(BaseModel):
    """질문에서 추출된 엔티티"""

    regions: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    time_expressions: list[str] = Field(default_factory=list)
    property_types: list[str] = Field(default_factory=list)


class SubQuery(BaseModel):
    """분해된 하위 질문"""

    intent: QueryIntent
    query_text: str
    region: str | None = None
    keywords: list[str] = Field(default_factory=list)
    time_range: tuple[str, str] | None = None
    priority: int = Field(default=1, ge=1, le=10)


class ExecutionStep(BaseModel):
    """실행 계획의 단일 단계"""

    step_id: int
    action: Literal["vector_search", "forecast", "news_keywords", "aggregate"]
    params: dict
    depends_on: list[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """전체 실행 계획"""

    original_query: str
    intents: list[QueryIntent]
    sub_queries: list[SubQuery]
    steps: list[ExecutionStep]
    strategy: Literal["sequential", "parallel", "parallel_then_aggregate"]
    is_simple: bool = Field(
        default=False,
        description="단순 쿼리 여부 (True면 기존 로직 사용)",
    )


class PlannerMetadata(BaseModel):
    """플래너 메타데이터 (응답에 포함)"""

    intents_detected: list[QueryIntent]
    sub_queries_count: int
    execution_strategy: str
    planning_time_ms: int
    is_simple_query: bool = False
