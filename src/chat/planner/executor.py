"""Plan Executor - 실행 계획을 기반으로 데이터 수집 및 결과 집계"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from src.forecast.schemas import ForecastRequest
from src.forecast.service import ForecastService
from src.shared.cache import CacheClient
from src.shared.vector_db import VectorDBInterface, get_vector_db

from .schemas import ExecutionPlan, ExecutionStep

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """단일 실행 단계의 결과"""

    step_id: int
    action: str
    success: bool
    data: Any = None
    error: str | None = None


@dataclass
class ExecutionResult:
    """전체 실행 결과"""

    plan: ExecutionPlan
    step_results: list[StepResult] = field(default_factory=list)
    aggregated_forecast: dict | None = None
    aggregated_documents: list[dict] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """전체 실행 성공 여부"""
        return all(r.success for r in self.step_results)


class PlanExecutor:
    """실행 계획 실행기"""

    def __init__(
        self,
        vector_db: VectorDBInterface | None = None,
        cache: CacheClient | None = None,
    ):
        self.vector_db = vector_db or get_vector_db()
        self.forecast_service = ForecastService(cache=cache)
        self.cache = cache

    async def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        """실행 계획을 실행합니다.

        Args:
            plan: 실행 계획

        Returns:
            ExecutionResult: 실행 결과
        """
        result = ExecutionResult(plan=plan)
        step_data: dict[int, Any] = {}

        if plan.strategy == "sequential":
            # 순차 실행
            for step in plan.steps:
                step_result = await self._execute_step(step, step_data)
                result.step_results.append(step_result)
                if step_result.success:
                    step_data[step.step_id] = step_result.data

        elif plan.strategy == "parallel":
            # 병렬 실행
            tasks = [self._execute_step(step, step_data) for step in plan.steps]
            step_results = await asyncio.gather(*tasks)
            result.step_results.extend(step_results)
            for sr in step_results:
                if sr.success:
                    step_data[sr.step_id] = sr.data

        elif plan.strategy == "parallel_then_aggregate":
            # 의존성 없는 단계 먼저 병렬 실행
            independent_steps = [s for s in plan.steps if not s.depends_on]
            dependent_steps = [s for s in plan.steps if s.depends_on]

            # 독립 단계 병렬 실행
            if independent_steps:
                tasks = [self._execute_step(step, step_data) for step in independent_steps]
                step_results = await asyncio.gather(*tasks)
                result.step_results.extend(step_results)
                for sr in step_results:
                    if sr.success:
                        step_data[sr.step_id] = sr.data

            # 의존 단계 순차 실행
            for step in dependent_steps:
                step_result = await self._execute_step(step, step_data)
                result.step_results.append(step_result)
                if step_result.success:
                    step_data[step.step_id] = step_result.data

        # 결과 집계
        result = self._aggregate_results(result, step_data)

        return result

    async def _execute_step(
        self,
        step: ExecutionStep,
        previous_data: dict[int, Any],
    ) -> StepResult:
        """단일 실행 단계를 실행합니다."""
        try:
            if step.action == "forecast":
                data = await self._execute_forecast(step.params)
            elif step.action == "vector_search":
                data = await self._execute_vector_search(step.params)
            elif step.action == "news_keywords":
                data = await self._execute_news_keywords(step.params)
            elif step.action == "aggregate":
                data = self._execute_aggregate(step.params, previous_data)
            else:
                raise ValueError(f"Unknown action: {step.action}")

            return StepResult(
                step_id=step.step_id,
                action=step.action,
                success=True,
                data=data,
            )

        except Exception as e:
            logger.error(f"Step {step.step_id} ({step.action}) failed: {e}")
            return StepResult(
                step_id=step.step_id,
                action=step.action,
                success=False,
                error=str(e),
            )

    async def _execute_forecast(self, params: dict) -> dict:
        """시계열 예측 실행"""
        request = ForecastRequest(
            region=params.get("region", "동대문구"),
            period="month",
            horizon=params.get("horizon", 3),
            include_news_weight=True,
        )
        forecast = await self.forecast_service.get_forecast(request)

        return {
            "region": params.get("region"),
            "trend": forecast.trend,
            "confidence": forecast.confidence,
            "forecast": [
                {"date": str(p.date), "value": p.value}
                for p in forecast.forecast
            ],
        }

    async def _execute_vector_search(self, params: dict) -> list[dict]:
        """Vector DB 검색 실행"""
        query = params.get("query", "")
        top_k = params.get("top_k", 5)

        chunks = await self.vector_db.search(query, top_k=top_k)

        return [
            {
                "content": chunk.content,
                "source": chunk.source,
                "score": chunk.score,
                "keywords": params.get("keywords", []),
            }
            for chunk in chunks
        ]

    async def _execute_news_keywords(self, params: dict) -> dict:
        """뉴스 키워드 분석 실행 (현재는 vector_search와 동일)"""
        keywords = params.get("keywords", [])
        query = " ".join(keywords) if keywords else ""

        chunks = await self.vector_db.search(query, top_k=5)

        return {
            "keywords": keywords,
            "documents": [
                {"content": chunk.content, "source": chunk.source, "score": chunk.score}
                for chunk in chunks
            ],
        }

    def _execute_aggregate(
        self,
        params: dict,
        previous_data: dict[int, Any],
    ) -> dict:
        """결과 집계 실행"""
        agg_type = params.get("type", "comparison")

        if agg_type == "comparison":
            # 예측 데이터 비교 집계
            forecasts = [
                v for v in previous_data.values()
                if isinstance(v, dict) and "trend" in v
            ]
            return {
                "type": "comparison",
                "forecasts": forecasts,
                "summary": self._create_comparison_summary(forecasts),
            }

        return {"type": agg_type, "data": list(previous_data.values())}

    def _create_comparison_summary(self, forecasts: list[dict]) -> str:
        """비교 요약 생성"""
        if not forecasts:
            return "비교할 데이터가 없습니다."

        summaries = []
        for f in forecasts:
            region = f.get("region", "알 수 없음")
            trend = f.get("trend", "알 수 없음")
            confidence = f.get("confidence", 0)
            summaries.append(f"{region}: {trend} (신뢰도 {confidence:.0%})")

        return " vs ".join(summaries)

    def _aggregate_results(
        self,
        result: ExecutionResult,
        step_data: dict[int, Any],
    ) -> ExecutionResult:
        """모든 결과를 집계합니다."""
        # 예측 데이터 집계
        forecasts = []
        documents = []

        for data in step_data.values():
            if isinstance(data, dict):
                if "trend" in data:
                    forecasts.append(data)
                if "documents" in data:
                    documents.extend(data["documents"])
            elif isinstance(data, list):
                # vector_search 결과
                documents.extend(data)

        # 가장 관련성 높은 예측 선택 (첫 번째)
        if forecasts:
            result.aggregated_forecast = forecasts[0]
            if len(forecasts) > 1:
                # 여러 지역 비교인 경우 모두 포함
                result.aggregated_forecast = {
                    "regions": forecasts,
                    "primary": forecasts[0],
                }

        # 중복 제거 후 상위 문서 선택
        seen_contents = set()
        unique_docs = []
        for doc in sorted(documents, key=lambda x: x.get("score", 0), reverse=True):
            content = doc.get("content", "")
            if content not in seen_contents:
                seen_contents.add(content)
                unique_docs.append(doc)
                if len(unique_docs) >= 5:
                    break

        result.aggregated_documents = unique_docs

        return result
