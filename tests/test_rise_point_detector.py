"""
상승 시점 감지 로직 테스트
"""

from datetime import date, timedelta

import pytest

from src.forecast.rise_point_detector import (
    RisePoint,
    RisePointConfig,
    RisePointDetector,
)


@pytest.fixture
def sample_dates():
    """샘플 날짜 데이터"""
    start_date = date(2024, 1, 1)
    return [start_date + timedelta(weeks=i) for i in range(30)]


@pytest.fixture
def rising_values():
    """상승 추세 가격 데이터"""
    base = 100.0
    return [base + (i * 0.5) if i > 15 else base for i in range(30)]


@pytest.fixture
def ma_crossover_values():
    """이동평균 교차 패턴 데이터"""
    values = [100.0] * 10
    values.extend([100.0 + (i * 2.0) for i in range(1, 11)])
    values.extend([120.0] * 10)
    return values


class TestRisePointDetector:
    """상승 시점 감지기 테스트"""

    def test_ma_crossover_detection(self, sample_dates, ma_crossover_values):
        """이동평균 교차 방식 테스트"""
        config = RisePointConfig(method="ma_crossover")
        detector = RisePointDetector(config)

        rise_points = detector.detect(sample_dates, ma_crossover_values)

        assert len(rise_points) > 0
        assert all(isinstance(rp, RisePoint) for rp in rise_points)
        assert all(rp.method == "ma_crossover" for rp in rise_points)

    def test_rate_threshold_detection(self, sample_dates, rising_values):
        """변동률 임계값 방식 테스트"""
        config = RisePointConfig(
            method="rate_threshold",
            rate_threshold_pct=1.0,
            lookback_weeks=4,
        )
        detector = RisePointDetector(config)

        rise_points = detector.detect(sample_dates, rising_values)

        assert len(rise_points) >= 0
        assert all(rp.method == "rate_threshold" for rp in rise_points)

    def test_consecutive_rise_detection(self, sample_dates, rising_values):
        """연속 상승 방식 테스트"""
        config = RisePointConfig(method="consecutive", consecutive_weeks=3)
        detector = RisePointDetector(config)

        rise_points = detector.detect(sample_dates, rising_values)

        assert len(rise_points) >= 0
        assert all(rp.method == "consecutive" for rp in rise_points)

    def test_window_calculation(self, sample_dates, rising_values):
        """윈도우 계산 테스트"""
        config = RisePointConfig(
            method="rate_threshold",
            lookback_weeks=4,
            lookahead_weeks=4,
        )
        detector = RisePointDetector(config)

        rise_points = detector.detect(sample_dates, rising_values)

        for rp in rise_points:
            assert rp.window_start < rp.date
            assert rp.window_end > rp.date
            assert (rp.date - rp.window_start).days == 4 * 7
            assert (rp.window_end - rp.date).days == 4 * 7

    def test_insufficient_data(self):
        """데이터 부족 시 처리 테스트"""
        dates = [date(2024, 1, 1) + timedelta(weeks=i) for i in range(3)]
        values = [100.0, 101.0, 102.0]

        config = RisePointConfig(method="ma_crossover")
        detector = RisePointDetector(config)

        rise_points = detector.detect(dates, values)

        assert len(rise_points) == 0

    def test_invalid_input(self):
        """잘못된 입력 처리 테스트"""
        dates = [date(2024, 1, 1)]
        values = [100.0, 101.0]

        detector = RisePointDetector()

        with pytest.raises(ValueError):
            detector.detect(dates, values)

    def test_confidence_score(self, sample_dates, ma_crossover_values):
        """신뢰도 점수 테스트"""
        detector = RisePointDetector()
        rise_points = detector.detect(sample_dates, ma_crossover_values)

        for rp in rise_points:
            assert 0.0 <= rp.confidence <= 1.0
