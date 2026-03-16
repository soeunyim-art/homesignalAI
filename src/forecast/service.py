import logging
from datetime import date, timedelta

# import pandas as pd (Moved to individual methods to avoid ImportError on Vercel)

from src.config import settings
from src.forecast.rise_point_detector import RisePointDetector
from src.shared.cache import CacheClient
from src.shared.data_repository import (
    DataRepositoryInterface,
    get_data_repository,
)
from src.shared.database import get_supabase_client
from src.shared.keyword_config import get_keyword_config
from src.shared.rise_point_config import get_rise_point_config

from .model_loader import get_model_loader
from .schemas import (
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    NewsWeightSummary,
)

logger = logging.getLogger(__name__)


class ForecastService:
    """시계열 예측 비즈니스 로직"""

    def __init__(
        self,
        cache: CacheClient | None = None,
        data_repo: DataRepositoryInterface | None = None,
        use_real_model: bool = True,
    ):
        self.cache = cache
        self.db = get_supabase_client()
        self.data_repo = data_repo or get_data_repository()
        self.use_real_model = use_real_model
        self.model_loader = get_model_loader() if use_real_model else None

    async def get_forecast(self, request: ForecastRequest) -> ForecastResponse:
        """시계열 예측 결과 반환"""
        # 캐시 확인
        if self.cache:
            cache_key = CacheClient.generate_key(
                "forecast",
                {
                    "region": request.region,
                    "period": request.period,
                    "horizon": request.horizon,
                    "include_news_weight": request.include_news_weight,
                },
            )
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info(f"캐시 히트: {cache_key}")
                return ForecastResponse(**cached)

        # 예측 실행
        forecast_data = await self._run_forecast(request)

        # 뉴스 가중치 조회
        news_weights = None
        if request.include_news_weight:
            news_weights = await self._get_news_weights(request.region)

        # 트렌드 판단
        trend = self._calculate_trend(forecast_data)
        confidence = self._calculate_confidence(forecast_data)

        response = ForecastResponse(
            region=request.region,
            period=request.period,
            trend=trend,
            confidence=confidence,
            forecast=forecast_data,
            news_weights=news_weights,
        )

        # 캐시 저장
        if self.cache:
            await self.cache.set(
                cache_key,
                response.model_dump(mode="json"),
                ttl=settings.cache_ttl_forecast,
            )

        return response

    async def _run_forecast(self, request: ForecastRequest) -> list[ForecastPoint]:
        """
        시계열 예측 모델 실행
        
        use_real_model=True: Prophet + LightGBM 앙상블 사용
        use_real_model=False: Mock 데이터 반환
        """
        if self.use_real_model and self.model_loader:
            return await self._run_real_forecast(request)
        else:
            return await self._run_mock_forecast(request)

    async def _run_real_forecast(self, request: ForecastRequest) -> list[ForecastPoint]:
        """실제 Prophet + LightGBM 앙상블 예측"""
        try:
            import pandas as pd
        except ImportError:
            logger.error("Pandas를 로드할 수 없습니다. 실제 모델 예측이 불가합니다.")
            return await self._run_mock_forecast(request)

        try:
            # 1. 모델 로드
            prophet_model = self.model_loader.load_prophet(
                region=request.region, period_type=request.period
            )
            lightgbm_model = self.model_loader.load_lightgbm(
                region=request.region, period_type=request.period
            )

            if not prophet_model or not lightgbm_model:
                logger.warning("모델 파일이 없어 Mock 데이터로 대체합니다.")
                return await self._run_mock_forecast(request)

            # 2. 최신 Feature 조회 (ml_training_features)
            latest_features = await self._get_latest_features(
                request.region, request.period
            )

            if latest_features.empty:
                logger.warning("Feature 데이터가 없어 Mock 데이터로 대체합니다.")
                return await self._run_mock_forecast(request)

            # 3. 미래 날짜 생성
            last_date = latest_features["period_date"].max()
            delta = timedelta(weeks=1) if request.period == "week" else timedelta(days=30)
            future_dates = [last_date + (delta * i) for i in range(1, request.horizon + 1)]

            # 4. Prophet 예측
            prophet_future = pd.DataFrame({"ds": future_dates})
            
            # Regressor 추가 (최신 값 사용 또는 평균)
            for regressor in prophet_model.extra_regressors.keys():
                if regressor in latest_features.columns:
                    prophet_future[regressor] = latest_features[regressor].iloc[-1]
                else:
                    prophet_future[regressor] = 0

            prophet_pred = prophet_model.predict(prophet_future)

            # 5. LightGBM 예측
            feature_cols = lightgbm_model.feature_name_
            X_future = pd.DataFrame()
            for col in feature_cols:
                if col in latest_features.columns:
                    X_future[col] = [latest_features[col].iloc[-1]] * request.horizon
                else:
                    X_future[col] = 0

            lightgbm_pred = lightgbm_model.predict(X_future)

            # 6. 앙상블 (가중 평균)
            prophet_weight, lightgbm_weight = self.model_loader.get_ensemble_weights(
                request.region, request.period
            )
            ensemble_pred = (prophet_pred["yhat"].values * prophet_weight) + (
                lightgbm_pred * lightgbm_weight
            )

            # 7. ForecastPoint 생성
            forecast_points = []
            for i, future_date in enumerate(future_dates):
                forecast_points.append(
                    ForecastPoint(
                        date=future_date,
                        value=round(float(ensemble_pred[i]), 2),
                        lower_bound=round(float(prophet_pred["yhat_lower"].values[i]), 2),
                        upper_bound=round(float(prophet_pred["yhat_upper"].values[i]), 2),
                    )
                )

            logger.info(f"실제 모델 예측 완료: {len(forecast_points)}개 포인트")
            return forecast_points

        except Exception as e:
            logger.error(f"실제 모델 예측 실패, Mock으로 대체: {e}")
            return await self._run_mock_forecast(request)

    async def _run_mock_forecast(self, request: ForecastRequest) -> list[ForecastPoint]:
        """Mock 예측 데이터 반환 (Fallback)"""
        today = date.today()
        delta = timedelta(weeks=1) if request.period == "week" else timedelta(days=30)

        forecast_points = []
        base_value = 105.0

        for i in range(1, request.horizon + 1):
            forecast_date = today + (delta * i)
            value = base_value + (i * 0.5)
            forecast_points.append(
                ForecastPoint(
                    date=forecast_date,
                    value=round(value, 2),
                    lower_bound=round(value - 2.0, 2),
                    upper_bound=round(value + 2.0, 2),
                )
            )

        return forecast_points

    async def _get_latest_features(
        self, region: str, period: str, limit: int = 52
    ) -> "pd.DataFrame":
        """ml_training_features에서 최신 Feature 조회"""
        try:
            import pandas as pd
        except ImportError:
            logger.error("Pandas를 로드할 수 없습니다. Feature 조회 결과를 DataFrame으로 변환할 수 없습니다.")
            # fallback or return empty dict if needed, but here we expect DataFrame
            raise ImportError("Pandas required for this method")

        response = (
            self.db.table("ml_training_features")
            .select("*")
            .eq("region", region)
            .eq("period_type", period)
            .order("period_date", desc=True)
            .limit(limit)
            .execute()
        )

        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        df["period_date"] = pd.to_datetime(df["period_date"]).dt.date
        df = df.sort_values("period_date")

        return df

    async def _get_news_weights(self, region: str) -> list[NewsWeightSummary]:
        """
        뉴스 키워드 가중치 조회

        상승 시점 전후 윈도우 내 뉴스 키워드 빈도를 조회하여 피처 변수로 활용
        """
        keyword_config = get_keyword_config()
        
        keywords = keyword_config.get_primary_keywords()

        rise_point_windows = await self._get_rise_point_windows(region)
        
        keyword_frequencies = await self.data_repo.get_news_keyword_frequency(
            keywords=keywords,
            rise_point_windows=rise_point_windows if rise_point_windows else None,
        )

        return [
            NewsWeightSummary(
                keyword=kf.keyword,
                frequency=kf.frequency,
                impact_score=kf.impact_score or 0.5,
            )
            for kf in keyword_frequencies
        ]

    async def _get_rise_point_windows(
        self, region: str
    ) -> list[tuple[date, date]]:
        """상승 시점 윈도우 조회"""
        try:
            time_series = await self.data_repo.get_houses_time_series(
                region=region,
                period="week",
                start_date=date.today() - timedelta(weeks=52),
                end_date=date.today(),
            )

            if not time_series:
                logger.warning("시계열 데이터가 없어 상승 시점을 감지할 수 없습니다")
                return []

            dates = [point.period_date for point in time_series]
            values = [point.avg_price for point in time_series]

            config = get_rise_point_config()
            detector = RisePointDetector(config)
            rise_points = detector.detect(dates, values)

            logger.info(f"상승 시점 {len(rise_points)}개 감지")
            return [(rp.window_start, rp.window_end) for rp in rise_points]

        except Exception as e:
            logger.error(f"상승 시점 윈도우 조회 실패: {e}")
            return []

    def _calculate_trend(
        self, forecast: list[ForecastPoint]
    ) -> str:
        """예측 트렌드 판단"""
        if len(forecast) < 2:
            return "보합"

        first_value = forecast[0].value
        last_value = forecast[-1].value
        change_rate = (last_value - first_value) / first_value

        if change_rate > 0.01:
            return "상승"
        elif change_rate < -0.01:
            return "하락"
        return "보합"

    def _calculate_confidence(self, forecast: list[ForecastPoint]) -> float:
        """예측 신뢰도 계산"""
        # TODO: 실제 모델의 불확실성 지표 활용
        return 0.85
