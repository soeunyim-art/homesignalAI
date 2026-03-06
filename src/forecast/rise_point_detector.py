"""
상승 시점 감지 로직 (Rise Point Detection)

가격 상승 시점을 식별하여 뉴스 키워드 추출 윈도우를 설정하는 모듈
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RisePointConfig:
    """상승 시점 감지 설정"""

    method: Literal["ma_crossover", "rate_threshold", "consecutive"] = "ma_crossover"
    short_ma_weeks: int = 5
    long_ma_weeks: int = 20
    lookback_weeks: int = 4
    lookahead_weeks: int = 4
    rate_threshold_pct: float = 2.0
    consecutive_weeks: int = 3


@dataclass
class RisePoint:
    """감지된 상승 시점"""

    date: date
    value: float
    window_start: date
    window_end: date
    method: str
    confidence: float = 1.0


class RisePointDetector:
    """가격 상승 시점 감지기"""

    def __init__(self, config: RisePointConfig | None = None):
        self.config = config or RisePointConfig()

    def detect(
        self, dates: list[date], values: list[float]
    ) -> list[RisePoint]:
        """상승 시점을 감지합니다.

        Args:
            dates: 날짜 리스트 (시계열 순서)
            values: 가격/지수 값 리스트

        Returns:
            감지된 상승 시점 리스트
        """
        if len(dates) != len(values):
            raise ValueError("dates와 values의 길이가 일치해야 합니다")

        if len(dates) < max(self.config.short_ma_weeks, self.config.long_ma_weeks):
            logger.warning("데이터가 부족하여 상승 시점을 감지할 수 없습니다")
            return []

        method = self.config.method

        if method == "ma_crossover":
            return self._detect_ma_crossover(dates, values)
        elif method == "rate_threshold":
            return self._detect_rate_threshold(dates, values)
        elif method == "consecutive":
            return self._detect_consecutive_rise(dates, values)
        else:
            raise ValueError(f"지원하지 않는 감지 방법: {method}")

    def _detect_ma_crossover(
        self, dates: list[date], values: list[float]
    ) -> list[RisePoint]:
        """이동평균 교차 방식으로 상승 시점 감지

        단기 MA가 장기 MA를 상향 돌파하는 시점을 감지
        """
        short_ma = self._calculate_moving_average(
            values, self.config.short_ma_weeks
        )
        long_ma = self._calculate_moving_average(values, self.config.long_ma_weeks)

        rise_points = []

        for i in range(1, len(dates)):
            if short_ma[i - 1] <= long_ma[i - 1] and short_ma[i] > long_ma[i]:
                window_start = dates[i] - timedelta(weeks=self.config.lookback_weeks)
                window_end = dates[i] + timedelta(weeks=self.config.lookahead_weeks)

                rise_points.append(
                    RisePoint(
                        date=dates[i],
                        value=values[i],
                        window_start=window_start,
                        window_end=window_end,
                        method="ma_crossover",
                        confidence=self._calculate_crossover_confidence(
                            short_ma[i], long_ma[i]
                        ),
                    )
                )

        logger.info(f"MA 교차 방식으로 {len(rise_points)}개 상승 시점 감지")
        return rise_points

    def _detect_rate_threshold(
        self, dates: list[date], values: list[float]
    ) -> list[RisePoint]:
        """변동률 임계값 방식으로 상승 시점 감지

        N주 대비 가격 변동률이 임계값을 초과하는 시점을 감지
        """
        lookback = self.config.lookback_weeks
        threshold = self.config.rate_threshold_pct / 100.0

        rise_points = []

        for i in range(lookback, len(dates)):
            prev_value = values[i - lookback]
            curr_value = values[i]
            rate = (curr_value - prev_value) / prev_value

            if rate > threshold:
                window_start = dates[i] - timedelta(weeks=self.config.lookback_weeks)
                window_end = dates[i] + timedelta(weeks=self.config.lookahead_weeks)

                rise_points.append(
                    RisePoint(
                        date=dates[i],
                        value=curr_value,
                        window_start=window_start,
                        window_end=window_end,
                        method="rate_threshold",
                        confidence=min(rate / threshold, 2.0) / 2.0,
                    )
                )

        logger.info(f"변동률 임계값 방식으로 {len(rise_points)}개 상승 시점 감지")
        return rise_points

    def _detect_consecutive_rise(
        self, dates: list[date], values: list[float]
    ) -> list[RisePoint]:
        """연속 상승 방식으로 상승 시점 감지

        K주 연속 상승 구간 진입 시점을 감지
        """
        consecutive_count = 0
        rise_points = []

        for i in range(1, len(dates)):
            if values[i] > values[i - 1]:
                consecutive_count += 1

                if consecutive_count == self.config.consecutive_weeks:
                    window_start = dates[i] - timedelta(
                        weeks=self.config.lookback_weeks
                    )
                    window_end = dates[i] + timedelta(
                        weeks=self.config.lookahead_weeks
                    )

                    rise_points.append(
                        RisePoint(
                            date=dates[i],
                            value=values[i],
                            window_start=window_start,
                            window_end=window_end,
                            method="consecutive",
                            confidence=1.0,
                        )
                    )
            else:
                consecutive_count = 0

        logger.info(f"연속 상승 방식으로 {len(rise_points)}개 상승 시점 감지")
        return rise_points

    @staticmethod
    def _calculate_moving_average(values: list[float], window: int) -> list[float]:
        """이동평균 계산"""
        if len(values) < window:
            return values

        ma = []
        for i in range(len(values)):
            if i < window - 1:
                ma.append(np.mean(values[: i + 1]))
            else:
                ma.append(np.mean(values[i - window + 1 : i + 1]))

        return ma

    @staticmethod
    def _calculate_crossover_confidence(short_ma: float, long_ma: float) -> float:
        """교차 신뢰도 계산

        단기 MA가 장기 MA를 얼마나 명확하게 상회하는지 측정
        """
        if long_ma == 0:
            return 0.5

        diff_ratio = (short_ma - long_ma) / long_ma
        confidence = min(abs(diff_ratio) * 10, 1.0)
        return confidence
