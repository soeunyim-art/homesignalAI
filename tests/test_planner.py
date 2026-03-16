"""Query Planner 단위 테스트"""

import pytest

from src.chat.planner.decomposer import EntityExtractor, QueryDecomposer
from src.chat.planner.plan_generator import PlanGenerator
from src.chat.planner.schemas import (
    ExecutionPlan,
    ExtractedEntities,
    IntentClassificationResult,
    QueryIntent,
    SubQuery,
)


class TestEntityExtractor:
    """EntityExtractor 테스트"""

    def setup_method(self):
        self.extractor = EntityExtractor()

    async def test_extract_single_region(self):
        """단일 지역 추출"""
        query = "청량리 아파트 시세가 얼마인가요?"
        entities = await self.extractor.extract(query)

        assert "청량리" in entities.regions
        assert "아파트" in entities.property_types

    async def test_extract_multiple_regions(self):
        """다중 지역 추출"""
        query = "청량리와 이문동 중 어디가 더 오를까요?"
        entities = await self.extractor.extract(query)

        assert "청량리" in entities.regions
        assert "이문동" in entities.regions or "이문" in entities.regions

    async def test_extract_keywords(self):
        """키워드 추출"""
        query = "GTX-C 개통이 재개발 시세에 미치는 영향은?"
        entities = await self.extractor.extract(query)

        assert any("GTX" in kw.upper() for kw in entities.keywords)
        assert "재개발" in entities.keywords

    async def test_extract_time_expressions(self):
        """시간 표현 추출"""
        query = "최근 1년간 동대문구 아파트 추이는?"
        entities = await self.extractor.extract(query)

        assert len(entities.time_expressions) > 0

    async def test_extract_empty_query(self):
        """빈 쿼리 처리"""
        query = ""
        entities = await self.extractor.extract(query)

        assert entities.regions == []
        assert entities.keywords == []


class TestQueryDecomposer:
    """QueryDecomposer 테스트"""

    def setup_method(self):
        self.decomposer = QueryDecomposer()

    async def test_simple_query_no_decomposition(self):
        """단순 쿼리 - 분해 없음"""
        query = "청량리 아파트 시세가 얼마인가요?"
        intents = [QueryIntent.PRICE_INQUIRY]

        sub_queries = await self.decomposer.decompose(query, intents)

        assert len(sub_queries) == 1
        assert sub_queries[0].intent == QueryIntent.PRICE_INQUIRY

    async def test_comparison_query_decomposition(self):
        """비교 쿼리 분해"""
        query = "청량리와 이문동 중 어디가 더 오를까요?"
        intents = [QueryIntent.COMPARISON, QueryIntent.FORECAST]
        entities = ExtractedEntities(
            regions=["청량리", "이문동"],
            keywords=[],
            time_expressions=[],
            property_types=[],
        )

        sub_queries = await self.decomposer.decompose(query, intents, entities)

        # 각 지역별 예측 + 비교 집계 = 최소 3개
        assert len(sub_queries) >= 3

        # 지역별 예측 쿼리 확인
        forecast_queries = [sq for sq in sub_queries if sq.intent == QueryIntent.FORECAST]
        assert len(forecast_queries) >= 2

        # 비교 쿼리 확인
        comparison_queries = [sq for sq in sub_queries if sq.intent == QueryIntent.COMPARISON]
        assert len(comparison_queries) >= 1

    async def test_news_analysis_decomposition(self):
        """뉴스 분석 쿼리 분해"""
        query = "GTX-C가 청량리 시세에 미치는 영향은?"
        intents = [QueryIntent.NEWS_ANALYSIS]
        entities = ExtractedEntities(
            regions=["청량리"],
            keywords=["GTX-C"],
            time_expressions=[],
            property_types=[],
        )

        sub_queries = await self.decomposer.decompose(query, intents, entities)

        # 뉴스 검색 + 예측 포함
        news_queries = [sq for sq in sub_queries if sq.intent == QueryIntent.NEWS_ANALYSIS]
        assert len(news_queries) >= 1

    def test_is_simple_query(self):
        """단순 쿼리 판단"""
        simple_sub_queries = [
            SubQuery(intent=QueryIntent.PRICE_INQUIRY, query_text="test")
        ]
        complex_sub_queries = [
            SubQuery(intent=QueryIntent.FORECAST, query_text="test1"),
            SubQuery(intent=QueryIntent.FORECAST, query_text="test2"),
            SubQuery(intent=QueryIntent.COMPARISON, query_text="test3"),
        ]

        assert self.decomposer.is_simple_query(simple_sub_queries) is True
        assert self.decomposer.is_simple_query(complex_sub_queries) is False


class TestPlanGenerator:
    """PlanGenerator 테스트"""

    def setup_method(self):
        self.generator = PlanGenerator()

    def test_generate_simple_plan(self):
        """단순 계획 생성"""
        query = "청량리 아파트 시세"
        intents = [QueryIntent.PRICE_INQUIRY]
        sub_queries = [
            SubQuery(intent=QueryIntent.PRICE_INQUIRY, query_text=query, region="청량리")
        ]

        plan = self.generator.generate(query, intents, sub_queries)

        assert plan.is_simple is True
        assert plan.strategy == "sequential"
        assert len(plan.steps) >= 1

    def test_generate_parallel_plan(self):
        """병렬 계획 생성"""
        query = "청량리와 이문동 비교"
        intents = [QueryIntent.COMPARISON, QueryIntent.FORECAST]
        sub_queries = [
            SubQuery(intent=QueryIntent.FORECAST, query_text="청량리 전망", region="청량리"),
            SubQuery(intent=QueryIntent.FORECAST, query_text="이문동 전망", region="이문동"),
        ]

        plan = self.generator.generate(query, intents, sub_queries)

        assert plan.is_simple is False
        assert plan.strategy in ["parallel", "parallel_then_aggregate"]

    def test_generate_plan_with_aggregate(self):
        """집계 포함 계획 생성"""
        query = "청량리와 이문동 중 어디가 더 오를까요?"
        intents = [QueryIntent.COMPARISON]
        sub_queries = [
            SubQuery(intent=QueryIntent.FORECAST, query_text="청량리 전망", region="청량리"),
            SubQuery(intent=QueryIntent.FORECAST, query_text="이문동 전망", region="이문동"),
            SubQuery(intent=QueryIntent.COMPARISON, query_text=query),
        ]

        plan = self.generator.generate(query, intents, sub_queries)

        # aggregate 단계 포함 확인
        aggregate_steps = [s for s in plan.steps if s.action == "aggregate"]
        assert len(aggregate_steps) >= 1

        # aggregate 단계는 이전 단계에 의존
        for agg_step in aggregate_steps:
            assert len(agg_step.depends_on) > 0

    def test_plan_execution_steps(self):
        """실행 단계 생성 확인"""
        query = "GTX-C가 시세에 미치는 영향"
        intents = [QueryIntent.NEWS_ANALYSIS]
        sub_queries = [
            SubQuery(
                intent=QueryIntent.NEWS_ANALYSIS,
                query_text="GTX-C 뉴스",
                keywords=["GTX-C"],
            )
        ]

        plan = self.generator.generate(query, intents, sub_queries)

        # vector_search 단계 포함 확인
        search_steps = [s for s in plan.steps if s.action == "vector_search"]
        assert len(search_steps) >= 1


class TestIntentClassificationResult:
    """IntentClassificationResult 스키마 테스트"""

    def test_valid_classification(self):
        """유효한 분류 결과"""
        result = IntentClassificationResult(
            primary_intent=QueryIntent.FORECAST,
            secondary_intents=[QueryIntent.NEWS_ANALYSIS],
            confidence=0.85,
        )

        assert result.primary_intent == QueryIntent.FORECAST
        assert len(result.secondary_intents) == 1
        assert result.confidence == 0.85

    def test_confidence_bounds(self):
        """신뢰도 범위 검증"""
        # 유효한 범위
        valid_result = IntentClassificationResult(
            primary_intent=QueryIntent.GENERAL,
            confidence=0.5,
        )
        assert valid_result.confidence == 0.5

        # 경계값
        edge_result = IntentClassificationResult(
            primary_intent=QueryIntent.GENERAL,
            confidence=1.0,
        )
        assert edge_result.confidence == 1.0


class TestExecutionPlan:
    """ExecutionPlan 스키마 테스트"""

    def test_plan_with_all_fields(self):
        """모든 필드가 있는 계획"""
        from src.chat.planner.schemas import ExecutionStep

        plan = ExecutionPlan(
            original_query="테스트 쿼리",
            intents=[QueryIntent.FORECAST],
            sub_queries=[
                SubQuery(intent=QueryIntent.FORECAST, query_text="테스트")
            ],
            steps=[
                ExecutionStep(
                    step_id=0,
                    action="forecast",
                    params={"region": "동대문구"},
                )
            ],
            strategy="sequential",
            is_simple=True,
        )

        assert plan.original_query == "테스트 쿼리"
        assert plan.is_simple is True
        assert plan.strategy == "sequential"
