"""
RPC 메서드 기반 DataRepository 단위 테스트

MockDataRepository의 새 메서드 + SupabaseDataRepository RPC 호출 구조 검증
"""

from datetime import date, datetime, timedelta
from typing import Literal

import pytest

from src.shared.data_repository import (
    DashboardSummary,
    KeywordFrequency,
    MLFeatureRow,
    MockDataRepository,
    PolicyEvent,
    PredictionPoint,
    TimeSeriesDataPoint,
)


@pytest.fixture
def repo():
    return MockDataRepository()


# =============================================================================
# 기존 메서드 (RPC 전환 후에도 동일한 반환 타입 유지 확인)
# =============================================================================


class TestGetHousesTimeSeries:
    @pytest.mark.asyncio
    async def test_returns_list_of_datapoints(self, repo: MockDataRepository):
        result = await repo.get_houses_time_series("청량리동", "week")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(r, TimeSeriesDataPoint) for r in result)

    @pytest.mark.asyncio
    async def test_period_week_uses_weekly_delta(self, repo: MockDataRepository):
        result = await repo.get_houses_time_series("청량리동", "week")
        if len(result) >= 2:
            diff = abs((result[0].period_date - result[1].period_date).days)
            assert diff == 7

    @pytest.mark.asyncio
    async def test_period_month_uses_monthly_delta(self, repo: MockDataRepository):
        result = await repo.get_houses_time_series("청량리동", "month")
        if len(result) >= 2:
            diff = abs((result[0].period_date - result[1].period_date).days)
            assert diff >= 28


class TestGetNewsKeywordFrequency:
    @pytest.mark.asyncio
    async def test_returns_frequencies_for_given_keywords(self, repo: MockDataRepository):
        result = await repo.get_news_keyword_frequency(["GTX", "재개발"])
        assert len(result) == 2
        keywords = [r.keyword for r in result]
        assert "GTX" in keywords
        assert "재개발" in keywords

    @pytest.mark.asyncio
    async def test_rise_point_windows_adjusts_frequency(self, repo: MockDataRepository):
        windows = [
            (date(2024, 1, 1), date(2024, 1, 31)),
            (date(2024, 6, 1), date(2024, 6, 30)),
        ]
        result = await repo.get_news_keyword_frequency(
            ["GTX"], rise_point_windows=windows
        )
        assert len(result) == 1
        assert result[0].frequency > 0

    @pytest.mark.asyncio
    async def test_impact_score_present(self, repo: MockDataRepository):
        result = await repo.get_news_keyword_frequency(["GTX"])
        assert result[0].impact_score is not None


# =============================================================================
# 새 RPC 메서드: get_latest_predictions
# =============================================================================


class TestGetLatestPredictions:
    @pytest.mark.asyncio
    async def test_returns_prediction_points(self, repo: MockDataRepository):
        result = await repo.get_latest_predictions("청량리동")
        assert isinstance(result, list)
        assert len(result) == 12
        assert all(isinstance(r, PredictionPoint) for r in result)

    @pytest.mark.asyncio
    async def test_prediction_dates_are_future(self, repo: MockDataRepository):
        result = await repo.get_latest_predictions("청량리동")
        today = date.today()
        for p in result:
            assert p.prediction_date > today

    @pytest.mark.asyncio
    async def test_confidence_bounds_exist(self, repo: MockDataRepository):
        result = await repo.get_latest_predictions("청량리동")
        for p in result:
            assert p.lower_bound is not None
            assert p.upper_bound is not None
            assert p.lower_bound < p.predicted_price < p.upper_bound

    @pytest.mark.asyncio
    async def test_custom_horizon(self, repo: MockDataRepository):
        result = await repo.get_latest_predictions("청량리동", horizon=6)
        assert len(result) == 6

    @pytest.mark.asyncio
    async def test_model_metadata(self, repo: MockDataRepository):
        result = await repo.get_latest_predictions("청량리동")
        assert result[0].model_name == "mock-ensemble"
        assert result[0].model_version is not None


# =============================================================================
# 새 RPC 메서드: get_ml_features
# =============================================================================


class TestGetMLFeatures:
    @pytest.mark.asyncio
    async def test_returns_feature_rows(self, repo: MockDataRepository):
        result = await repo.get_ml_features("청량리동")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(r, MLFeatureRow) for r in result)

    @pytest.mark.asyncio
    async def test_feature_has_moving_averages(self, repo: MockDataRepository):
        result = await repo.get_ml_features("청량리동")
        for row in result:
            assert row.ma_5_week is not None
            assert row.ma_20_week is not None

    @pytest.mark.asyncio
    async def test_feature_has_news_frequencies(self, repo: MockDataRepository):
        result = await repo.get_ml_features("청량리동")
        assert any(r.news_gtx_freq > 0 for r in result)
        assert any(r.news_redevelopment_freq > 0 for r in result)

    @pytest.mark.asyncio
    async def test_train_test_split_labels(self, repo: MockDataRepository):
        result = await repo.get_ml_features("청량리동")
        splits = {r.train_test_split for r in result}
        assert "train" in splits
        assert "test" in splits

    @pytest.mark.asyncio
    async def test_event_flags_are_boolean(self, repo: MockDataRepository):
        result = await repo.get_ml_features("청량리동")
        for row in result:
            assert isinstance(row.event_gtx_announcement, bool)
            assert isinstance(row.season_school, bool)


# =============================================================================
# 새 RPC 메서드: get_policy_events
# =============================================================================


class TestGetPolicyEvents:
    @pytest.mark.asyncio
    async def test_returns_policy_events(self, repo: MockDataRepository):
        result = await repo.get_policy_events(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(r, PolicyEvent) for r in result)

    @pytest.mark.asyncio
    async def test_event_has_required_fields(self, repo: MockDataRepository):
        result = await repo.get_policy_events(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        for event in result:
            assert event.id
            assert event.event_date
            assert event.event_type
            assert event.event_name

    @pytest.mark.asyncio
    async def test_event_types_valid(self, repo: MockDataRepository):
        result = await repo.get_policy_events(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        valid_types = {"gtx", "redevelopment", "transport", "policy", "interest_rate", "supply"}
        for event in result:
            assert event.event_type in valid_types

    @pytest.mark.asyncio
    async def test_impact_levels(self, repo: MockDataRepository):
        result = await repo.get_policy_events(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        valid_levels = {"low", "medium", "high", None}
        for event in result:
            assert event.impact_level in valid_levels


# =============================================================================
# 새 RPC 메서드: get_dashboard_summary
# =============================================================================


class TestGetDashboardSummary:
    @pytest.mark.asyncio
    async def test_returns_dashboard_summary(self, repo: MockDataRepository):
        result = await repo.get_dashboard_summary("청량리동")
        assert isinstance(result, DashboardSummary)

    @pytest.mark.asyncio
    async def test_summary_has_price_info(self, repo: MockDataRepository):
        result = await repo.get_dashboard_summary("청량리동")
        assert result.latest_avg_price is not None
        assert result.latest_avg_price > 0

    @pytest.mark.asyncio
    async def test_summary_has_change_pct(self, repo: MockDataRepository):
        result = await repo.get_dashboard_summary("청량리동")
        assert result.price_change_pct is not None

    @pytest.mark.asyncio
    async def test_summary_has_news_count(self, repo: MockDataRepository):
        result = await repo.get_dashboard_summary("청량리동")
        assert result.recent_news_count >= 0

    @pytest.mark.asyncio
    async def test_summary_has_top_keywords(self, repo: MockDataRepository):
        result = await repo.get_dashboard_summary("청량리동")
        assert isinstance(result.top_keywords, list)
        assert len(result.top_keywords) > 0

    @pytest.mark.asyncio
    async def test_trend_direction_valid(self, repo: MockDataRepository):
        result = await repo.get_dashboard_summary("청량리동")
        assert result.trend_direction in ("rising", "falling", "stable", "unknown")


# =============================================================================
# MockSupabaseClient RPC 호환성 테스트
# =============================================================================


class TestMockSupabaseRPC:
    def test_mock_client_has_rpc_method(self):
        from src.shared.database import MockSupabaseClient

        client = MockSupabaseClient()
        assert hasattr(client, "rpc")

    def test_rpc_returns_executable(self):
        from src.shared.database import MockSupabaseClient

        client = MockSupabaseClient()
        rpc_call = client.rpc("aggregate_houses_time_series", {"p_region": "청량리동"})
        result = rpc_call.execute()
        assert hasattr(result, "data")
        assert isinstance(result.data, list)

    def test_rpc_returns_empty_data(self):
        from src.shared.database import MockSupabaseClient

        client = MockSupabaseClient()
        result = client.rpc("get_dashboard_summary", {"p_region": "청량리동"}).execute()
        assert result.data == []


# =============================================================================
# Domain Model 생성 테스트
# =============================================================================


class TestDomainModels:
    def test_prediction_point_defaults(self):
        p = PredictionPoint(
            prediction_date=date.today(),
            predicted_price=100000000.0,
        )
        assert p.lower_bound is None
        assert p.upper_bound is None
        assert p.confidence_score is None

    def test_ml_feature_row_defaults(self):
        f = MLFeatureRow(
            period_date=date.today(),
            avg_price=100000000.0,
        )
        assert f.news_gtx_freq == 0
        assert f.event_gtx_announcement is False
        assert f.train_test_split is None

    def test_dashboard_summary_defaults(self):
        d = DashboardSummary()
        assert d.latest_avg_price is None
        assert d.trend_direction == "unknown"
        assert d.top_keywords == []

    def test_policy_event_creation(self):
        e = PolicyEvent(
            id="test-1",
            event_date=date(2025, 1, 1),
            event_type="gtx",
            event_name="GTX-C 착공",
        )
        assert e.description is None
        assert e.region is None

    def test_time_series_data_point_extended_fields(self):
        t = TimeSeriesDataPoint(
            period_date=date.today(),
            avg_price=100000000.0,
            transaction_count=50,
            min_price=90000000.0,
            max_price=110000000.0,
            price_index=100.0,
        )
        assert t.min_price == 90000000.0
        assert t.max_price == 110000000.0
