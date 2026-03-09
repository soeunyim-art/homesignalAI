import json
import logging
import time

from src.config import settings
from src.forecast.schemas import ForecastRequest
from src.forecast.service import ForecastService
from src.shared.ai_client import AIClient
from src.shared.cache import CacheClient
from src.shared.exceptions import AIAPIError
from src.shared.vector_db import VectorDBInterface, get_vector_db

from .fallback import create_fallback_response
from .planner import (
    IntentClassifier,
    PlanExecutor,
    PlanGenerator,
    PlannerMetadata,
    QueryDecomposer,
)
from .prompts import SYSTEM_PROMPT_V1, build_context_message
from .schemas import (
    ChatRequest,
    ChatResponse,
    ForecastSummary,
    SourceReference,
)

logger = logging.getLogger(__name__)


class ChatService:
    """RAG 챗봇 비즈니스 로직"""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        cache: CacheClient | None = None,
        vector_db: VectorDBInterface | None = None,
        enable_planner: bool = True,
    ):
        self.ai_client = ai_client or AIClient()
        self.cache = cache
        self.vector_db = vector_db or get_vector_db()
        self.forecast_service = ForecastService(cache=cache)
        self.enable_planner = enable_planner

        # Query Planner 컴포넌트 초기화
        if self.enable_planner:
            self.classifier = IntentClassifier(self.ai_client)
            self.decomposer = QueryDecomposer(ai_client=self.ai_client)
            self.plan_generator = PlanGenerator()
            self.plan_executor = PlanExecutor(
                vector_db=self.vector_db,
                cache=self.cache,
            )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """RAG 챗봇 응답 생성"""
        # 캐시 확인
        cache_key = None
        if self.cache:
            cache_key = CacheClient.generate_key(
                "chat",
                {"message": request.message, "region": request.region},
            )
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info(f"캐시 히트: {cache_key}")
                return ChatResponse(**cached)

        # 플래너 활성화 시 플래너 기반 처리
        if self.enable_planner:
            return await self._chat_with_planner(request, cache_key)

        # 플래너 비활성화 시 기존 로직
        return await self._chat_simple(request, cache_key)

    async def _chat_with_planner(
        self,
        request: ChatRequest,
        cache_key: str | None,
    ) -> ChatResponse:
        """플래너를 사용한 RAG 처리"""
        planning_start = time.time()

        # 1. 의도 분류
        classification = await self.classifier.classify(request.message)
        intents = [classification.primary_intent] + classification.secondary_intents

        # 2. 엔티티 추출 및 질문 분해
        entities = await self.decomposer.extractor.extract(request.message)
        sub_queries = self.decomposer.decompose(request.message, intents, entities)

        # 3. 실행 계획 생성
        plan = self.plan_generator.generate(request.message, intents, sub_queries)

        planning_time_ms = int((time.time() - planning_start) * 1000)

        # 4. 단순 쿼리면 기존 로직 사용
        if plan.is_simple:
            logger.info(f"단순 쿼리 감지, 기존 로직 사용: {classification.primary_intent}")
            response = await self._chat_simple(request, cache_key)

            # 플래너 메타데이터 추가
            response.planner_metadata = PlannerMetadata(
                intents_detected=intents,
                sub_queries_count=len(sub_queries),
                execution_strategy=plan.strategy,
                planning_time_ms=planning_time_ms,
                is_simple_query=True,
            )
            return response

        # 5. 복합 쿼리 - 플랜 실행
        logger.info(
            f"복합 쿼리 처리: intents={intents}, sub_queries={len(sub_queries)}, "
            f"strategy={plan.strategy}"
        )
        execution_result = await self.plan_executor.execute(plan)

        # 6. 실행 결과로 AI 응답 생성
        try:
            response = await self._generate_ai_response_from_plan(
                request=request,
                execution_result=execution_result,
            )
        except AIAPIError as e:
            logger.warning(f"AI API 오류, Fallback 실행: {e}")
            # Fallback 응답 생성
            forecast_data = execution_result.aggregated_forecast
            if forecast_data:
                from .fallback import FallbackForecast
                fallback_forecast = FallbackForecast(
                    trend=forecast_data.get("trend", "알 수 없음"),
                    confidence=forecast_data.get("confidence", 0.0),
                    forecast=forecast_data.get("forecast", []),
                )
                response = create_fallback_response(
                    forecast=fallback_forecast,
                    session_id=request.session_id,
                )
            else:
                response = ChatResponse(
                    answer="일시적 장애로 응답을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
                    sources=[],
                    forecast_summary=None,
                    session_id=request.session_id,
                    fallback=True,
                )

        # 플래너 메타데이터 추가
        response.planner_metadata = PlannerMetadata(
            intents_detected=intents,
            sub_queries_count=len(sub_queries),
            execution_strategy=plan.strategy,
            planning_time_ms=planning_time_ms,
            is_simple_query=False,
        )

        # 캐시 저장 (Fallback 응답은 캐시하지 않음)
        if self.cache and cache_key and not response.fallback:
            await self.cache.set(
                cache_key,
                response.model_dump(mode="json"),
                ttl=settings.cache_ttl_chat,
            )

        return response

    async def _chat_simple(
        self,
        request: ChatRequest,
        cache_key: str | None,
    ) -> ChatResponse:
        """기존 단순 RAG 처리 로직"""
        # 1. 시계열 예측 조회
        forecast = await self._get_forecast(request.region)

        # 2. Vector DB 검색 (RAG)
        relevant_docs = await self._search_relevant_documents(request.message)

        # 3. AI 응답 생성 (with Fallback)
        try:
            response = await self._generate_ai_response(
                request=request,
                forecast=forecast,
                relevant_docs=relevant_docs,
            )
        except AIAPIError as e:
            logger.warning(f"AI API 오류, Fallback 실행: {e}")
            response = create_fallback_response(
                forecast=forecast,
                session_id=request.session_id,
            )

        # 캐시 저장 (Fallback 응답은 캐시하지 않음)
        if self.cache and cache_key and not response.fallback:
            await self.cache.set(
                cache_key,
                response.model_dump(mode="json"),
                ttl=settings.cache_ttl_chat,
            )

        return response

    async def _get_forecast(self, region: str):
        """시계열 예측 조회"""
        forecast_request = ForecastRequest(
            region=region,
            period="month",
            horizon=3,
            include_news_weight=True,
        )
        return await self.forecast_service.get_forecast(forecast_request)

    async def _search_relevant_documents(self, query: str) -> list[dict]:
        """Vector DB에서 관련 문서 검색"""
        chunks = await self.vector_db.search(query, top_k=5)
        return [
            {
                "content": chunk.content,
                "source": chunk.source,
                "score": chunk.score,
            }
            for chunk in chunks
        ]

    async def _generate_ai_response(
        self,
        request: ChatRequest,
        forecast,
        relevant_docs: list[dict],
    ) -> ChatResponse:
        """AI 응답 생성"""
        # 컨텍스트 메시지 생성
        forecast_dict = {
            "trend": forecast.trend,
            "confidence": forecast.confidence,
            "forecast": [
                {"date": str(p.date), "value": p.value}
                for p in forecast.forecast[:3]
            ],
        }
        context_message = build_context_message(
            user_query=request.message,
            forecast_json=json.dumps(forecast_dict, ensure_ascii=False, indent=2),
            news_chunks=relevant_docs,
        )

        # AI API 호출
        answer = await self.ai_client.generate(
            system_prompt=SYSTEM_PROMPT_V1,
            user_message=context_message,
        )

        # 응답 구성
        sources = [
            SourceReference(
                title=doc.get("content", "")[:50] + "...",
                source=doc.get("source", ""),
                relevance_score=doc.get("score", 0.0),
            )
            for doc in relevant_docs
        ]

        forecast_summary = ForecastSummary(
            trend=forecast.trend,
            confidence=forecast.confidence,
            next_month_prediction=forecast.forecast[0].value if forecast.forecast else None,
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            forecast_summary=forecast_summary,
            session_id=request.session_id,
            fallback=False,
        )

    async def _generate_ai_response_from_plan(
        self,
        request: ChatRequest,
        execution_result,
    ) -> ChatResponse:
        """플랜 실행 결과로 AI 응답 생성"""
        from .planner.executor import ExecutionResult

        execution_result: ExecutionResult = execution_result

        # 예측 데이터 준비
        forecast_data = execution_result.aggregated_forecast
        if forecast_data:
            # 다중 지역 비교인 경우
            if "regions" in forecast_data:
                forecast_json = json.dumps(
                    {
                        "comparison": True,
                        "regions": forecast_data["regions"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            else:
                forecast_json = json.dumps(
                    {
                        "trend": forecast_data.get("trend"),
                        "confidence": forecast_data.get("confidence"),
                        "forecast": forecast_data.get("forecast", []),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
        else:
            forecast_json = "{}"

        # 문서 데이터 준비
        relevant_docs = execution_result.aggregated_documents

        # 컨텍스트 메시지 생성
        context_message = build_context_message(
            user_query=request.message,
            forecast_json=forecast_json,
            news_chunks=relevant_docs,
        )

        # AI API 호출
        answer = await self.ai_client.generate(
            system_prompt=SYSTEM_PROMPT_V1,
            user_message=context_message,
        )

        # 응답 구성
        sources = [
            SourceReference(
                title=doc.get("content", "")[:50] + "...",
                source=doc.get("source", ""),
                relevance_score=doc.get("score", 0.0),
            )
            for doc in relevant_docs
        ]

        # ForecastSummary 구성
        if forecast_data:
            if "regions" in forecast_data and forecast_data["regions"]:
                primary = forecast_data["primary"]
                forecast_summary = ForecastSummary(
                    trend=primary.get("trend", "알 수 없음"),
                    confidence=primary.get("confidence", 0.0),
                    next_month_prediction=(
                        primary["forecast"][0]["value"]
                        if primary.get("forecast")
                        else None
                    ),
                )
            else:
                forecast_summary = ForecastSummary(
                    trend=forecast_data.get("trend", "알 수 없음"),
                    confidence=forecast_data.get("confidence", 0.0),
                    next_month_prediction=(
                        forecast_data["forecast"][0]["value"]
                        if forecast_data.get("forecast")
                        else None
                    ),
                )
        else:
            forecast_summary = None

        return ChatResponse(
            answer=answer,
            sources=sources,
            forecast_summary=forecast_summary,
            session_id=request.session_id,
            fallback=False,
        )
