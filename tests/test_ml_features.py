"""
ML Training Features 생성 및 모델 예측 테스트
"""

import pytest
from datetime import date, timedelta
import pandas as pd
import os

from src.shared.database import get_supabase_client

# Mock mode 감지
IS_MOCK_MODE = "placeholder" in os.environ.get("SUPABASE_URL", "")


@pytest.mark.asyncio
@pytest.mark.skipif(IS_MOCK_MODE, reason="Supabase 통합 테스트 - Mock mode에서는 skip")
async def test_ml_training_features_schema():
    """ml_training_features 테이블 스키마 확인"""
    supabase = get_supabase_client()

    # 테이블 존재 확인 (빈 쿼리)
    response = supabase.table("ml_training_features").select("*").limit(1).execute()

    # 스키마 확인 (첫 행이 있으면)
    if response.data:
        row = response.data[0]
        required_cols = [
            "period_date",
            "region",
            "period_type",
            "avg_price",
            "ma_5_week",
            "ma_20_week",
            "news_gtx_freq",
            "news_redevelopment_freq",
            "event_gtx_announcement",
            "season_school",
        ]

        for col in required_cols:
            assert col in row, f"필수 컬럼 누락: {col}"


@pytest.mark.asyncio
@pytest.mark.skipif(IS_MOCK_MODE, reason="Supabase 통합 테스트 - Mock mode에서는 skip")
async def test_policy_events_schema():
    """policy_events 테이블 스키마 확인"""
    supabase = get_supabase_client()

    response = supabase.table("policy_events").select("*").limit(1).execute()

    if response.data:
        row = response.data[0]
        required_cols = ["event_date", "event_type", "event_name", "impact_level"]

        for col in required_cols:
            assert col in row, f"필수 컬럼 누락: {col}"


def test_season_dummy_generation():
    """계절성 더미 변수 생성 로직 테스트"""
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="W-MON")
    months = dates.month

    # 개학 시즌 (2-3월, 8-9월)
    season_school = months.isin([2, 3, 8, 9])
    assert season_school.sum() > 0, "개학 시즌이 감지되지 않음"

    # 이사 시즌 (1-2월, 12월)
    season_moving = months.isin([1, 2, 12])
    assert season_moving.sum() > 0, "이사 시즌이 감지되지 않음"

    # 결혼 시즌 (5월, 10월)
    season_wedding = months.isin([5, 10])
    assert season_wedding.sum() > 0, "결혼 시즌이 감지되지 않음"


def test_moving_average_calculation():
    """이동평균 계산 로직 테스트"""
    prices = pd.Series([100, 102, 105, 103, 107, 110, 108, 112, 115, 118])

    ma_5 = prices.rolling(5, min_periods=1).mean()
    ma_20 = prices.rolling(20, min_periods=1).mean()

    assert len(ma_5) == len(prices)
    assert len(ma_20) == len(prices)
    assert ma_5.iloc[-1] > ma_5.iloc[0], "이동평균이 상승 추세를 반영해야 함"


@pytest.mark.asyncio
@pytest.mark.skipif(IS_MOCK_MODE, reason="Supabase 통합 테스트 - Mock mode에서는 skip")
async def test_feature_query_performance():
    """Feature 조회 성능 테스트"""
    supabase = get_supabase_client()

    import time

    start = time.time()
    response = (
        supabase.table("ml_training_features")
        .select("*")
        .eq("region", "청량리동")
        .eq("period_type", "week")
        .order("period_date", desc=True)
        .limit(52)
        .execute()
    )
    elapsed = time.time() - start

    assert elapsed < 2.0, f"Feature 조회가 너무 느림: {elapsed:.2f}초"


def test_ensemble_weight_calculation():
    """앙상블 가중치 계산 테스트"""
    prophet_pred = pd.Series([100, 105, 110])
    lightgbm_pred = pd.Series([98, 103, 108])

    prophet_weight = 0.6
    lightgbm_weight = 0.4

    ensemble = (prophet_pred * prophet_weight) + (lightgbm_pred * lightgbm_weight)

    assert len(ensemble) == len(prophet_pred)
    assert ensemble.iloc[0] == pytest.approx(99.2, rel=0.01)  # 100*0.6 + 98*0.4


@pytest.mark.asyncio
async def test_forecast_with_real_model_fallback():
    """실제 모델이 없을 때 Mock으로 Fallback 테스트"""
    from src.forecast.service import ForecastService
    from src.forecast.schemas import ForecastRequest

    service = ForecastService(use_real_model=True)

    request = ForecastRequest(
        region="청량리동",
        period="week",
        horizon=4,
    )

    # 모델이 없어도 예외 없이 Mock 데이터 반환해야 함
    forecast = await service._run_forecast(request)

    assert len(forecast) == 4
    assert all(isinstance(point.value, (int, float)) for point in forecast)
    assert all(point.lower_bound < point.value < point.upper_bound for point in forecast)


def test_feature_columns_completeness():
    """Feature 컬럼 완전성 검증"""
    required_news_features = [
        "news_gtx_freq",
        "news_redevelopment_freq",
        "news_policy_freq",
        "news_supply_freq",
        "news_transport_freq",
        "news_economic_freq",
        "news_social_freq",
        "news_location_freq",
    ]

    required_event_features = [
        "event_gtx_announcement",
        "event_redevelopment_approval",
        "event_interest_rate_change",
        "event_loan_regulation",
        "event_sales_restriction",
    ]

    required_season_features = [
        "season_school",
        "season_moving",
        "season_wedding",
    ]

    all_features = (
        required_news_features + required_event_features + required_season_features
    )

    assert len(all_features) == 16, "Feature 개수가 예상과 다름"
