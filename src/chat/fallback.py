"""AI API 장애 시 Fallback 처리 로직"""

from src.forecast.schemas import ForecastResponse

from .schemas import ChatResponse, ForecastSummary, SourceReference

FALLBACK_MESSAGE = """죄송합니다. 일시적 장애로 AI 해설을 생성하지 못했습니다.

아래는 시계열 예측 수치 데이터입니다:

- **예측 트렌드:** {trend}
- **예측 신뢰도:** {confidence:.0%}
- **다음 기간 예측:** {next_prediction}

자세한 분석은 잠시 후 다시 시도해 주세요.

---
*본 데이터는 참고용이며, 투자 결정의 근거로 사용하지 마세요.*
"""


def create_fallback_response(
    forecast: ForecastResponse | None = None,
    session_id: str | None = None,
) -> ChatResponse:
    """Fallback 응답 생성"""
    if forecast:
        next_prediction = (
            f"{forecast.forecast[0].value:.2f}" if forecast.forecast else "데이터 없음"
        )
        answer = FALLBACK_MESSAGE.format(
            trend=forecast.trend,
            confidence=forecast.confidence,
            next_prediction=next_prediction,
        )
        forecast_summary = ForecastSummary(
            trend=forecast.trend,
            confidence=forecast.confidence,
            next_month_prediction=forecast.forecast[0].value if forecast.forecast else None,
        )
    else:
        answer = "죄송합니다. 일시적 장애로 응답을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."
        forecast_summary = None

    return ChatResponse(
        answer=answer,
        sources=[],
        forecast_summary=forecast_summary,
        session_id=session_id,
        fallback=True,
    )
