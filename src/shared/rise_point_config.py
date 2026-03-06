"""
상승 시점 감지 설정 로더

config/rise_point_config.yaml 파일을 로드하고 RisePointConfig 제공
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from src.forecast.rise_point_detector import RisePointConfig

logger = logging.getLogger(__name__)


class RisePointConfigLoader:
    """상승 시점 감지 설정 로더"""

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent
                / "config"
                / "rise_point_config.yaml"
            )

        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self):
        """설정 파일 로드"""
        if not self.config_path.exists():
            logger.warning(f"상승 시점 설정 파일이 없습니다: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
            logger.info(f"상승 시점 설정 로드 완료: {self.config_path}")
        except Exception as e:
            logger.error(f"상승 시점 설정 로드 실패: {e}")

    def get_rise_point_config(self) -> RisePointConfig:
        """RisePointConfig 객체 반환"""
        rise_point_data = self._config.get("rise_point", {})

        return RisePointConfig(
            method=rise_point_data.get("method", "ma_crossover"),
            short_ma_weeks=rise_point_data.get("short_ma_weeks", 5),
            long_ma_weeks=rise_point_data.get("long_ma_weeks", 20),
            lookback_weeks=rise_point_data.get("lookback_weeks", 4),
            lookahead_weeks=rise_point_data.get("lookahead_weeks", 4),
            rate_threshold_pct=rise_point_data.get("rate_threshold_pct", 2.0),
            consecutive_weeks=rise_point_data.get("consecutive_weeks", 3),
        )


# 싱글톤 인스턴스
_loader: RisePointConfigLoader | None = None


def get_rise_point_config() -> RisePointConfig:
    """상승 시점 감지 설정 싱글톤 인스턴스 반환"""
    global _loader
    if _loader is None:
        _loader = RisePointConfigLoader()
    return _loader.get_rise_point_config()
