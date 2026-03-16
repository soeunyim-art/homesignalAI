"""
모델 로더 유틸리티

학습된 Prophet + LightGBM 모델을 로드하고 캐싱합니다.
"""

import json
import logging
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Literal

# import lightgbm as lgb (Moved to load_lightgbm)
# from prophet import Prophet (Moved to load_prophet)

logger = logging.getLogger(__name__)


class ModelLoader:
    """학습된 모델 로더"""

    def __init__(self, models_dir: Path | str = "models"):
        self.models_dir = Path(models_dir)
        if not self.models_dir.exists():
            logger.warning(f"모델 디렉토리가 없습니다: {self.models_dir}")
            self.models_dir.mkdir(exist_ok=True)

    def load_prophet(
        self, region: str = "청량리동", period_type: Literal["week", "month"] = "week"
    ) -> "Prophet | None":
        """Prophet 모델 로드"""
        try:
            from prophet import Prophet
        except ImportError:
            logger.error("Prophet 라이브러리가 설치되어 있지 않습니다.")
            return None

        model_path = self.models_dir / f"prophet_{region}_{period_type}_v1.pkl"

        if not model_path.exists():
            logger.warning(f"Prophet 모델 파일이 없습니다: {model_path}")
            return None

        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            logger.info(f"Prophet 모델 로드 완료: {model_path.name}")
            return model
        except Exception as e:
            logger.error(f"Prophet 모델 로드 실패: {e}")
            return None

    def load_lightgbm(
        self, region: str = "청량리동", period_type: Literal["week", "month"] = "week"
    ) -> "lgb.LGBMRegressor | None":
        """LightGBM 모델 로드"""
        try:
            import lightgbm as lgb
        except ImportError:
            logger.error("LightGBM 라이브러리가 설치되어 있지 않습니다.")
            return None

        model_path = self.models_dir / f"lightgbm_{region}_{period_type}_v1.pkl"

        if not model_path.exists():
            logger.warning(f"LightGBM 모델 파일이 없습니다: {model_path}")
            return None

        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            logger.info(f"LightGBM 모델 로드 완료: {model_path.name}")
            return model
        except Exception as e:
            logger.error(f"LightGBM 모델 로드 실패: {e}")
            return None

    def load_ensemble_config(
        self, region: str = "청량리동", period_type: Literal["week", "month"] = "week"
    ) -> dict | None:
        """앙상블 설정 로드"""
        config_path = self.models_dir / f"ensemble_{region}_{period_type}_config.json"

        if not config_path.exists():
            logger.warning(f"앙상블 설정 파일이 없습니다: {config_path}")
            return None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"앙상블 설정 로드 완료: {config_path.name}")
            return config
        except Exception as e:
            logger.error(f"앙상블 설정 로드 실패: {e}")
            return None

    def get_ensemble_weights(
        self, region: str = "청량리동", period_type: Literal["week", "month"] = "week"
    ) -> tuple[float, float]:
        """앙상블 가중치 반환 (Prophet, LightGBM)"""
        config = self.load_ensemble_config(region, period_type)

        if config:
            return config.get("prophet_weight", 0.6), config.get("lightgbm_weight", 0.4)

        # 기본값
        return 0.6, 0.4

    def list_available_models(self) -> list[dict]:
        """사용 가능한 모델 목록 반환"""
        models = []

        for config_file in self.models_dir.glob("ensemble_*_config.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                models.append(
                    {
                        "region": config.get("region"),
                        "period_type": config.get("period_type"),
                        "trained_at": config.get("trained_at"),
                        "prophet_weight": config.get("prophet_weight"),
                        "metrics": config.get("metrics"),
                    }
                )
            except Exception as e:
                logger.error(f"설정 파일 읽기 실패: {config_file} - {e}")

        return models


@lru_cache(maxsize=4)
def get_model_loader() -> ModelLoader:
    """ModelLoader 싱글톤 인스턴스 반환"""
    return ModelLoader()
