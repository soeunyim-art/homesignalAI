from pydantic import BaseModel, Field

from .planner.schemas import PlannerMetadata, QueryIntent


class ChatRequest(BaseModel):
    """RAG 챗봇 요청 스키마"""

    message: str = Field(
        description="사용자 질문",
        min_length=1,
        max_length=2000,
        examples=["동대문구 아파트 가격이 오를까요?"],
    )
    session_id: str | None = Field(
        default=None,
        description="세션 ID (대화 히스토리 유지용)",
    )
    region: str = Field(
        default="동대문구",
        description="질문 대상 지역",
    )


class SourceReference(BaseModel):
    """응답 출처 정보"""

    title: str
    source: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ForecastSummary(BaseModel):
    """시계열 예측 요약"""

    trend: str
    confidence: float
    next_month_prediction: float | None = None


class ChatResponse(BaseModel):
    """RAG 챗봇 응답 스키마"""

    answer: str = Field(description="AI 생성 응답")
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="참고 자료 출처",
    )
    forecast_summary: ForecastSummary | None = Field(
        default=None,
        description="시계열 예측 요약",
    )
    session_id: str | None = Field(default=None)
    fallback: bool = Field(
        default=False,
        description="AI API 장애로 Fallback 응답인 경우 True",
    )
    planner_metadata: PlannerMetadata | None = Field(
        default=None,
        description="쿼리 플래너 메타데이터 (디버깅/분석용)",
    )
