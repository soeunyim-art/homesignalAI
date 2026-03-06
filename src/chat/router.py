from fastapi import APIRouter, Depends

from src.shared.ai_client import AIClient, get_ai_client
from src.shared.cache import CacheClient, get_cache_client

from .schemas import ChatRequest, ChatResponse
from .service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    cache: CacheClient = Depends(get_cache_client),
) -> ChatResponse:
    """
    RAG 챗봇 질의

    동대문구 부동산 시장에 대한 질문에 시계열 예측 데이터와
    관련 뉴스를 기반으로 근거 있는 답변을 생성합니다.

    - **message**: 사용자 질문
    - **session_id**: 대화 히스토리 유지용 세션 ID (선택)
    - **region**: 질문 대상 지역 (기본: 동대문구)

    응답에는 AI 생성 답변, 참고 자료 출처, 시계열 예측 요약이 포함됩니다.
    AI API 장애 시 시계열 수치 데이터만 포함된 Fallback 응답이 반환됩니다.
    """
    service = ChatService(ai_client=ai_client, cache=cache)
    return await service.chat(request)
