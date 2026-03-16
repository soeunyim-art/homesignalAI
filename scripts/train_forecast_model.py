"""
시계열 예측 모델 학습 스크립트

ml_training_features에서 데이터를 로드하여 Prophet + LightGBM 앙상블 모델을 학습합니다.

Usage:
    uv run python scripts/train_forecast_model.py
    uv run python scripts/train_forecast_model.py --region 청량리동
    uv run python scripts/train_forecast_model.py --period-type month
"""

import argparse
import asyncio
import json
import logging
import pickle
from datetime import date
from pathlib import Path

import lightgbm as lgb
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from src.shared.database import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForecastModelTrainer:
    """시계열 예측 모델 학습기"""

    def __init__(self, supabase):
        self.supabase = supabase
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)

    async def load_training_data(
        self, region: str, period_type: str = "week", use_split: bool = True
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """ml_training_features에서 학습 데이터 로드
        
        Args:
            region: 지역명
            period_type: 기간 타입 (week/month)
            use_split: train_test_split 플래그 사용 여부
            
        Returns:
            (train_df, test_df) 튜플
        """
        logger.info(f"학습 데이터 로드 중: {region}, {period_type}")

        response = (
            self.supabase.table("ml_training_features")
            .select("*")
            .eq("region", region)
            .eq("period_type", period_type)
            .order("period_date", desc=False)
            .execute()
        )

        if not response.data:
            raise ValueError(f"{region}에 학습 데이터가 없습니다.")

        df = pd.DataFrame(response.data)
        df["period_date"] = pd.to_datetime(df["period_date"])

        logger.info(f"로드된 데이터: {len(df)}개 행")

        # train_test_split 플래그 기반 분할
        if use_split and "train_test_split" in df.columns:
            train_df = df[df["train_test_split"] == "train"].copy()
            test_df = df[df["train_test_split"] == "test"].copy()

            if len(train_df) > 0 and len(test_df) > 0:
                logger.info(
                    f"  DB 플래그 기반 분할: Train {len(train_df)}개, Test {len(test_df)}개"
                )
                return train_df, test_df
            else:
                logger.warning(
                    "train_test_split 플래그가 설정되지 않았습니다. Fallback 분할 수행"
                )

        # Fallback: 시간 기반 분할 (70:30)
        train_size = int(len(df) * 0.7)
        train_df = df[:train_size].copy()
        test_df = df[train_size:].copy()

        logger.info(
            f"  Fallback 시간 기반 분할: Train {len(train_df)}개, Test {len(test_df)}개"
        )
        return train_df, test_df

    def train_prophet(self, train_features: pd.DataFrame) -> Prophet:
        """Prophet 모델 학습
        
        Args:
            train_features: 학습용 데이터프레임
        """
        logger.info("Prophet 모델 학습 중...")

        # Prophet 형식으로 변환
        prophet_df = pd.DataFrame(
            {
                "ds": train_features["period_date"],
                "y": train_features["avg_price"],
            }
        )

        # Prophet 모델 초기화
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
        )

        # 뉴스 피처 추가
        news_features = [
            "news_gtx_freq",
            "news_redevelopment_freq",
            "news_policy_freq",
            "news_supply_freq",
            "news_transport_freq",
        ]
        for col in news_features:
            if col in train_features.columns:
                prophet_df[col] = train_features[col].fillna(0)
                model.add_regressor(col)

        # 이벤트 피처 추가
        event_features = [
            "event_gtx_announcement",
            "event_redevelopment_approval",
            "event_interest_rate_change",
            "event_loan_regulation",
        ]
        for col in event_features:
            if col in train_features.columns:
                prophet_df[col] = train_features[col].astype(int)
                model.add_regressor(col)

        # 계절성 피처 추가
        season_features = ["season_school", "season_moving", "season_wedding"]
        for col in season_features:
            if col in train_features.columns:
                prophet_df[col] = train_features[col].astype(int)
                model.add_regressor(col)

        # 학습
        model.fit(prophet_df)

        logger.info("Prophet 학습 완료")
        return model

    def train_lightgbm(self, train_features: pd.DataFrame) -> lgb.LGBMRegressor:
        """LightGBM 모델 학습
        
        Args:
            train_features: 학습용 데이터프레임
        """
        logger.info("LightGBM 모델 학습 중...")

        # Feature 컬럼 정의
        feature_cols = [
            "ma_5_week",
            "ma_20_week",
            "news_gtx_freq",
            "news_redevelopment_freq",
            "news_policy_freq",
            "news_supply_freq",
            "news_transport_freq",
            "news_economic_freq",
            "news_social_freq",
            "news_location_freq",
            "event_gtx_announcement",
            "event_redevelopment_approval",
            "event_interest_rate_change",
            "event_loan_regulation",
            "event_sales_restriction",
            "season_school",
            "season_moving",
            "season_wedding",
        ]

        # 존재하는 컬럼만 사용
        available_cols = [col for col in feature_cols if col in train_features.columns]

        X = train_features[available_cols].fillna(0)
        # Boolean을 int로 변환
        for col in X.columns:
            if X[col].dtype == bool:
                X[col] = X[col].astype(int)

        y = train_features["avg_price"]

        # LightGBM 모델 초기화
        model = lgb.LGBMRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )

        # 학습
        model.fit(X, y)

        logger.info("LightGBM 학습 완료")
        return model

    def evaluate_models(
        self,
        test_df: pd.DataFrame,
        prophet_model: Prophet,
        lightgbm_model: lgb.LGBMRegressor,
        ensemble_weight: float = 0.6,
    ) -> dict:
        """모델 평가 (Test 데이터 기반)
        
        Args:
            test_df: 평가용 데이터프레임
            prophet_model: 학습된 Prophet 모델
            lightgbm_model: 학습된 LightGBM 모델
            ensemble_weight: Prophet 가중치 (기본값: 0.6)
        """
        logger.info("모델 평가 중...")

        if len(test_df) < 5:
            logger.warning("테스트 데이터가 부족합니다. 평가 생략")
            return {}

        # Prophet 예측
        prophet_test_df = pd.DataFrame(
            {
                "ds": test_df["period_date"],
            }
        )
        # Regressor 추가
        for col in prophet_model.extra_regressors.keys():
            if col in test_df.columns:
                prophet_test_df[col] = test_df[col].fillna(0).astype(float)

        prophet_pred = prophet_model.predict(prophet_test_df)
        prophet_yhat = prophet_pred["yhat"].values

        # LightGBM 예측
        feature_cols = [
            col
            for col in lightgbm_model.feature_name_
            if col in test_df.columns
        ]
        X_test = test_df[feature_cols].fillna(0)
        for col in X_test.columns:
            if X_test[col].dtype == bool:
                X_test[col] = X_test[col].astype(int)

        lightgbm_yhat = lightgbm_model.predict(X_test)

        # 앙상블
        ensemble_yhat = (prophet_yhat * ensemble_weight) + (
            lightgbm_yhat * (1 - ensemble_weight)
        )

        # 실제값
        y_true = test_df["avg_price"].values

        # 평가 지표 계산
        metrics = {
            "prophet": {
                "rmse": mean_squared_error(y_true, prophet_yhat, squared=False),
                "mae": mean_absolute_error(y_true, prophet_yhat),
                "mape": self._calculate_mape(y_true, prophet_yhat),
            },
            "lightgbm": {
                "rmse": mean_squared_error(y_true, lightgbm_yhat, squared=False),
                "mae": mean_absolute_error(y_true, lightgbm_yhat),
                "mape": self._calculate_mape(y_true, lightgbm_yhat),
            },
            "ensemble": {
                "rmse": mean_squared_error(y_true, ensemble_yhat, squared=False),
                "mae": mean_absolute_error(y_true, ensemble_yhat),
                "mape": self._calculate_mape(y_true, ensemble_yhat),
            },
        }

        logger.info("\n평가 결과:")
        for model_name, model_metrics in metrics.items():
            logger.info(f"  {model_name.upper()}:")
            logger.info(f"    RMSE: {model_metrics['rmse']:.2f}")
            logger.info(f"    MAE: {model_metrics['mae']:.2f}")
            logger.info(f"    MAPE: {model_metrics['mape']:.2f}%")

        return metrics

    def _calculate_mape(self, y_true, y_pred) -> float:
        """MAPE (Mean Absolute Percentage Error) 계산"""
        return (abs((y_true - y_pred) / y_true).mean()) * 100

    def save_models(
        self,
        prophet_model: Prophet,
        lightgbm_model: lgb.LGBMRegressor,
        region: str,
        period_type: str,
        metrics: dict,
    ):
        """모델 저장"""
        logger.info("모델 저장 중...")

        # 파일명
        prophet_path = self.models_dir / f"prophet_{region}_{period_type}_v1.pkl"
        lightgbm_path = self.models_dir / f"lightgbm_{region}_{period_type}_v1.pkl"
        config_path = self.models_dir / f"ensemble_{region}_{period_type}_config.json"

        # Prophet 저장
        with open(prophet_path, "wb") as f:
            pickle.dump(prophet_model, f)
        logger.info(f"  ✓ Prophet 저장: {prophet_path}")

        # LightGBM 저장
        with open(lightgbm_path, "wb") as f:
            pickle.dump(lightgbm_model, f)
        logger.info(f"  ✓ LightGBM 저장: {lightgbm_path}")

        # 앙상블 설정 저장
        ensemble_config = {
            "region": region,
            "period_type": period_type,
            "prophet_weight": 0.6,
            "lightgbm_weight": 0.4,
            "metrics": metrics,
            "trained_at": date.today().isoformat(),
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(ensemble_config, f, indent=2, ensure_ascii=False)
        logger.info(f"  ✓ 앙상블 설정 저장: {config_path}")


async def main():
    parser = argparse.ArgumentParser(description="시계열 예측 모델 학습")
    parser.add_argument(
        "--region",
        type=str,
        default="청량리동",
        help="학습 대상 지역",
    )
    parser.add_argument(
        "--period-type",
        type=str,
        choices=["week", "month"],
        default="week",
        help="기간 타입",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="평가만 수행 (모델 저장 안 함)",
    )

    args = parser.parse_args()

    # Supabase 클라이언트
    supabase = get_supabase_client()
    trainer = ForecastModelTrainer(supabase)

    try:
        # 1. 학습 데이터 로드 (Train/Test 분할)
        train_df, test_df = await trainer.load_training_data(
            args.region, args.period_type
        )

        logger.info(f"\n데이터 분할:")
        logger.info(f"  Train: {len(train_df)}개 행")
        logger.info(f"  Test: {len(test_df)}개 행")

        # 2. Prophet 학습
        prophet_model = trainer.train_prophet(train_df)

        # 3. LightGBM 학습
        lightgbm_model = trainer.train_lightgbm(train_df)

        # 4. 평가 (Test 데이터 사용)
        metrics = trainer.evaluate_models(
            test_df, prophet_model, lightgbm_model
        )

        # 5. 모델 저장
        if not args.dry_run:
            trainer.save_models(
                prophet_model,
                lightgbm_model,
                args.region,
                args.period_type,
                metrics,
            )
            logger.info("\n모델 학습 및 저장 완료!")
        else:
            logger.info("\n[DRY-RUN] 평가만 완료, 모델 저장 생략")

    except Exception as e:
        logger.error(f"모델 학습 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
