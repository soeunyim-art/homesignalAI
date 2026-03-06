"""Plan Generator - SubQuery를 기반으로 실행 계획 생성"""

from typing import Literal

from .schemas import ExecutionPlan, ExecutionStep, QueryIntent, SubQuery


class PlanGenerator:
    """실행 계획 생성기"""

    # Intent별 액션 매핑
    INTENT_TO_ACTION: dict[QueryIntent, str] = {
        QueryIntent.PRICE_INQUIRY: "forecast",  # 시세 조회도 forecast 데이터 활용
        QueryIntent.FORECAST: "forecast",
        QueryIntent.COMPARISON: "aggregate",
        QueryIntent.NEWS_ANALYSIS: "vector_search",
        QueryIntent.TREND_ANALYSIS: "forecast",
        QueryIntent.INVESTMENT: "forecast",
        QueryIntent.GENERAL: "vector_search",
    }

    def generate(
        self,
        query: str,
        intents: list[QueryIntent],
        sub_queries: list[SubQuery],
    ) -> ExecutionPlan:
        """실행 계획을 생성합니다.

        Args:
            query: 원본 질문
            intents: 분류된 의도들
            sub_queries: 분해된 하위 질문들

        Returns:
            ExecutionPlan: 실행 계획
        """
        steps = self._generate_steps(sub_queries)
        strategy = self._determine_strategy(sub_queries, steps)
        is_simple = len(sub_queries) == 1 and len(steps) <= 2

        return ExecutionPlan(
            original_query=query,
            intents=intents,
            sub_queries=sub_queries,
            steps=steps,
            strategy=strategy,
            is_simple=is_simple,
        )

    def _generate_steps(self, sub_queries: list[SubQuery]) -> list[ExecutionStep]:
        """SubQuery들로부터 실행 단계를 생성합니다."""
        steps: list[ExecutionStep] = []
        step_id = 0

        for sq in sub_queries:
            action = self.INTENT_TO_ACTION.get(sq.intent, "vector_search")

            if action == "aggregate":
                # aggregate는 이전 단계들에 의존
                depends_on = list(range(step_id))
                steps.append(
                    ExecutionStep(
                        step_id=step_id,
                        action="aggregate",
                        params={
                            "type": "comparison",
                            "sub_query": sq.query_text,
                        },
                        depends_on=depends_on,
                    )
                )
            elif action == "forecast":
                steps.append(
                    ExecutionStep(
                        step_id=step_id,
                        action="forecast",
                        params={
                            "region": sq.region or "동대문구",
                            "horizon": 3,  # 기본 3개월 예측
                        },
                        depends_on=[],
                    )
                )
            elif action == "vector_search":
                steps.append(
                    ExecutionStep(
                        step_id=step_id,
                        action="vector_search",
                        params={
                            "query": sq.query_text,
                            "top_k": 5,
                            "keywords": sq.keywords,
                        },
                        depends_on=[],
                    )
                )
            elif action == "news_keywords":
                steps.append(
                    ExecutionStep(
                        step_id=step_id,
                        action="news_keywords",
                        params={
                            "keywords": sq.keywords,
                            "region": sq.region,
                        },
                        depends_on=[],
                    )
                )

            step_id += 1

        # 뉴스 분석이 포함된 경우, 항상 vector_search 추가
        has_news = any(sq.intent == QueryIntent.NEWS_ANALYSIS for sq in sub_queries)
        has_vector_search = any(s.action == "vector_search" for s in steps)

        if has_news and not has_vector_search:
            keywords = []
            for sq in sub_queries:
                keywords.extend(sq.keywords)
            keywords = list(set(keywords))

            steps.insert(
                0,
                ExecutionStep(
                    step_id=0,
                    action="vector_search",
                    params={
                        "query": " ".join(keywords) if keywords else sub_queries[0].query_text,
                        "top_k": 5,
                        "keywords": keywords,
                    },
                    depends_on=[],
                ),
            )
            # step_id 재조정
            for i, step in enumerate(steps):
                step.step_id = i
                if step.depends_on:
                    step.depends_on = [d + 1 for d in step.depends_on if d < len(steps) - 1]

        return steps

    def _determine_strategy(
        self,
        sub_queries: list[SubQuery],
        steps: list[ExecutionStep],
    ) -> Literal["sequential", "parallel", "parallel_then_aggregate"]:
        """실행 전략을 결정합니다."""
        # 의존성 있는 step이 있는지 확인
        has_dependencies = any(s.depends_on for s in steps)

        if len(steps) == 1:
            return "sequential"

        if has_dependencies:
            # 일부는 병렬, 마지막은 순차 (집계)
            return "parallel_then_aggregate"

        # 모든 step이 독립적이면 병렬
        return "parallel"
