"""
ML Training Features 생성 스크립트

houses_data, news_signals, policy_events를 통합하여
ml_training_features 테이블에 시계열 Feature를 생성합니다.

Usage:
    uv run python scripts/generate_ml_features.py
    uv run python scripts/generate_ml_features.py --start-date 2024-01-01 --end-date 2024-12-31
    uv run python scripts/generate_ml_features.py --region 청량리동
    uv run python scripts/generate_ml_features.py --dry-run
"""

import argparse
import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Literal

import pandas as pd
import yaml
from supabase import Client

from src.config import settings
from src.shared.database import get_supabase_client
from src.shared.keyword_config import get_keyword_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureGenerator:
    """ML Training Features 생성기"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.keyword_config = get_keyword_config()

    async def generate_features(
        self,
        region: str,
        period_type: Literal["week", "month"],
        start_date: date,
        end_date: date,
        dry_run: bool = False,
    ) -> pd.DataFrame:
        """통합 Feature 생성"""
        logger.info(
            f"Feature 생성 시작: {region}, {period_type}, {start_date} ~ {end_date}"
        )

        # 1. 실거래가 집계
        houses_ts = await self._aggregate_houses(region, period_type, start_date, end_date)
        if houses_ts.empty:
            logger.warning(f"{region}에 실거래가 데이터가 없습니다.")
            return pd.DataFrame()

        # 2. 뉴스 키워드 빈도 계산
        news_features = await self._calculate_news_frequencies(
            region, period_type, start_date, end_date
        )

        # 3. 이벤트 더미 생성
        event_features = await self._generate_event_dummies(region, start_date, end_date)

        # 4. 계절성 더미 생성
        season_features = self._generate_season_dummies(houses_ts["period_date"])

        # 5. 이동평균 계산
        houses_ts = houses_ts.sort_values("period_date")
        houses_ts["ma_5_week"] = houses_ts["avg_price"].rolling(5, min_periods=1).mean()
        houses_ts["ma_20_week"] = houses_ts["avg_price"].rolling(20, min_periods=1).mean()

        # 6. 모든 피처 병합
        features = houses_ts.merge(news_features, on="period_date", how="left")
        features = features.merge(event_features, on="period_date", how="left")
        features = features.merge(season_features, on="period_date", how="left")

        # 7. 결측치 처리
        features = features.fillna(
            {
                "news_gtx_freq": 0,
                "news_redevelopment_freq": 0,
                "news_policy_freq": 0,
                "news_supply_freq": 0,
                "news_transport_freq": 0,
                "news_economic_freq": 0,
                "news_social_freq": 0,
                "news_location_freq": 0,
                "event_gtx_announcement": False,
                "event_redevelopment_approval": False,
                "event_interest_rate_change": False,
                "event_loan_regulation": False,
                "event_sales_restriction": False,
            }
        )

        # 8. region, period_type 추가
        features["region"] = region
        features["period_type"] = period_type

        logger.info(f"생성된 Feature 행 수: {len(features)}")

        # 9. Supabase INSERT
        if not dry_run:
            await self._insert_features(features)
        else:
            logger.info("Dry-run 모드: 실제 INSERT 생략")
            logger.info(f"\n{features.head(10)}")

        return features

    async def _aggregate_houses(
        self,
        region: str,
        period_type: Literal["week", "month"],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """houses_data에서 주간/월간 집계"""
        logger.info(f"실거래가 집계 중: {region}")

        response = (
            self.supabase.table("houses_data")
            .select("contract_date, price, dong_name")
            .gte("contract_date", start_date.isoformat())
            .lte("contract_date", end_date.isoformat())
            .ilike("dong_name", f"%{region}%")
            .execute()
        )

        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        df["contract_date"] = pd.to_datetime(df["contract_date"])
        df["price"] = pd.to_numeric(df["price"])

        # 주간/월간 집계
        freq = "W-MON" if period_type == "week" else "MS"
        aggregated = (
            df.groupby(pd.Grouper(key="contract_date", freq=freq))
            .agg(
                avg_price=("price", "mean"),
                transaction_count=("price", "count"),
            )
            .reset_index()
        )

        aggregated.rename(columns={"contract_date": "period_date"}, inplace=True)
        aggregated["period_date"] = aggregated["period_date"].dt.date

        return aggregated

    async def _calculate_news_frequencies(
        self,
        region: str,
        period_type: Literal["week", "month"],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """뉴스 키워드 빈도 계산"""
        logger.info(f"뉴스 키워드 빈도 계산 중: {region}")

        # keywords.yaml의 카테고리 매핑
        category_mapping = {
            "transport": "news_transport_freq",
            "redevelopment": "news_redevelopment_freq",
            "policy": "news_policy_freq",
            "supply": "news_supply_freq",
            "economic_indicators": "news_economic_freq",
            "social_issues": "news_social_freq",
            "location_specific": "news_location_freq",
        }

        # GTX는 transport 카테고리에서 분리
        categories = list(category_mapping.keys())

        # 날짜 범위 생성
        freq = "W-MON" if period_type == "week" else "MS"
        date_range = pd.date_range(start_date, end_date, freq=freq)

        freq_data = []
        for period_date in date_range:
            row = {"period_date": period_date.date()}

            # 기간 범위 계산
            if period_type == "week":
                period_start = period_date - timedelta(days=7)
                period_end = period_date
            else:
                period_start = period_date
                period_end = period_date + timedelta(days=30)

            # 카테고리별 빈도 계산
            for category, col_name in category_mapping.items():
                keywords = self.keyword_config.get_keywords_by_category(category)
                freq = await self._count_news_in_period(
                    keywords, period_start, period_end
                )
                row[col_name] = freq

            # GTX 키워드는 별도 집계
            gtx_keywords = ["GTX", "GTX-C", "GTX-A", "수도권광역급행철도"]
            row["news_gtx_freq"] = await self._count_news_in_period(
                gtx_keywords, period_start, period_end
            )

            freq_data.append(row)

        return pd.DataFrame(freq_data)

    async def _count_news_in_period(
        self, keywords: list[str], start_date: datetime | date, end_date: datetime | date
    ) -> int:
        """특정 기간 내 키워드 포함 뉴스 개수"""
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date):
            end_date = datetime.combine(end_date, datetime.max.time())

        response = (
            self.supabase.table("news_signals")
            .select("id", count="exact")
            .gte("published_at", start_date.isoformat())
            .lte("published_at", end_date.isoformat())
            .overlaps("keywords", keywords)
            .execute()
        )

        return response.count or 0

    async def _generate_event_dummies(
        self, region: str | None, start_date: date, end_date: date
    ) -> pd.DataFrame:
        """정책 이벤트 더미 변수 생성"""
        logger.info("정책 이벤트 더미 생성 중")

        # policy_events 테이블에서 이벤트 조회
        response = (
            self.supabase.table("policy_events")
            .select("event_date, event_type, region")
            .gte("event_date", start_date.isoformat())
            .lte("event_date", end_date.isoformat())
            .execute()
        )

        if not response.data:
            # 이벤트 없으면 빈 DataFrame 반환
            date_range = pd.date_range(start_date, end_date, freq="W-MON")
            return pd.DataFrame(
                {
                    "period_date": [d.date() for d in date_range],
                    "event_gtx_announcement": False,
                    "event_redevelopment_approval": False,
                    "event_interest_rate_change": False,
                    "event_loan_regulation": False,
                    "event_sales_restriction": False,
                }
            )

        events_df = pd.DataFrame(response.data)
        events_df["event_date"] = pd.to_datetime(events_df["event_date"]).dt.date

        # 날짜 범위 생성
        date_range = pd.date_range(start_date, end_date, freq="W-MON")
        dummy_df = pd.DataFrame({"period_date": [d.date() for d in date_range]})

        # 이벤트 타입별 더미 생성
        event_type_mapping = {
            "gtx_announcement": "event_gtx_announcement",
            "redevelopment_approval": "event_redevelopment_approval",
            "interest_rate": "event_interest_rate_change",
            "loan_regulation": "event_loan_regulation",
            "sales_restriction": "event_sales_restriction",
            "supply_announcement": "event_sales_restriction",  # supply도 sales_restriction으로 매핑
        }

        for event_type, col_name in event_type_mapping.items():
            dummy_df[col_name] = False

        # 이벤트 발생 주에 True 설정
        for _, event in events_df.iterrows():
            event_date = event["event_date"]
            event_type = event["event_type"]
            event_region = event.get("region")

            # 지역 필터링 (region이 None이면 전체 적용)
            if event_region and region and event_region != region:
                continue

            # 해당 주 찾기
            for idx, row_date in enumerate(dummy_df["period_date"]):
                if abs((row_date - event_date).days) <= 7:
                    col_name = event_type_mapping.get(event_type)
                    if col_name:
                        dummy_df.at[idx, col_name] = True
                    break

        return dummy_df

    def _generate_season_dummies(self, dates: pd.Series) -> pd.DataFrame:
        """계절성 더미 변수 생성"""
        logger.info("계절성 더미 생성 중")

        season_df = pd.DataFrame({"period_date": dates})

        # 월 추출
        months = pd.to_datetime(dates).dt.month

        # 개학 시즌 (2-3월, 8-9월)
        season_df["season_school"] = months.isin([2, 3, 8, 9])

        # 이사 시즌 (1-2월, 12월)
        season_df["season_moving"] = months.isin([1, 2, 12])

        # 결혼 시즌 (5월, 10월)
        season_df["season_wedding"] = months.isin([5, 10])

        return season_df

    async def _insert_features(self, features: pd.DataFrame) -> None:
        """ml_training_features 테이블에 INSERT"""
        logger.info(f"Supabase에 {len(features)}개 행 삽입 중...")

        # DataFrame을 dict 리스트로 변환
        records = features.to_dict("records")

        # 날짜를 문자열로 변환
        for record in records:
            if isinstance(record.get("period_date"), date):
                record["period_date"] = record["period_date"].isoformat()

        # Batch INSERT (100개씩)
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table("ml_training_features").upsert(
                    batch, on_conflict="region,period_date,period_type"
                ).execute()
                logger.info(f"  {i + len(batch)}/{len(records)} 삽입 완료")
            except Exception as e:
                logger.error(f"Batch {i} 삽입 실패: {e}")
                raise

        logger.info("Feature 생성 완료!")


async def main():
    parser = argparse.ArgumentParser(description="ML Training Features 생성")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="시작 날짜 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=date.today().isoformat(),
        help="종료 날짜 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help="특정 지역만 생성 (예: 청량리동)",
    )
    parser.add_argument(
        "--period-type",
        type=str,
        choices=["week", "month"],
        default="week",
        help="기간 타입 (week 또는 month)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 INSERT 없이 미리보기만",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="가장 최근 업데이트된 피처의 날짜 이후부터만 갱신 (Incremental Update)",
    )

    args = parser.parse_args()

    # Supabase 클라이언트
    supabase = get_supabase_client()
    generator = FeatureGenerator(supabase)

    # 지역 목록
    regions = (
        [args.region]
        if args.region
        else [
            "청량리동",
            "회기동",
            "휘경동",
            "이문동",
            "장안동",
            "답십리동",
            "전농동",
            "용두동",
        ]
    )

    # 각 지역별로 Feature 생성
    for region in regions:
        try:
            # Incremental 로직 처리
            if args.incremental:
                logger.info(f"{region}의 최근 피처 생성 날짜를 조회합니다...")
                try:
                    latest_response = (
                        supabase.table("ml_training_features")
                        .select("period_date")
                        .eq("region", region)
                        .eq("period_type", args.period_type)
                        .order("period_date", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if latest_response.data and latest_response.data[0].get("period_date"):
                        # 가장 최신 날짜부터 갱신 시작 (겹치게 해서 갱신해도 upsert이므로 문제없음)
                        latest_date_str = latest_response.data[0]["period_date"]
                        start_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
                        logger.info(f"Incremental Update: {region}의 최근 생성일은 {start_date} 입니다.")
                    else:
                        logger.info(f"Incremental Update: 기존 피처가 없어 기본 시작일({args.start_date})을 사용합니다.")
                        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
                except Exception as db_err:
                    logger.warning(f"최근 피처 날짜 조회 중 오류 발생 (schema 반영 여부 확인 필요): {db_err}")
                    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            else:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()

            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

            if start_date > end_date:
                logger.info(f"✓ {region}은 이미 구하고자 하는 기간({end_date})까지 최신 상태입니다.")
                continue

            features = await generator.generate_features(
                region=region,
                period_type=args.period_type,
                start_date=start_date,
                end_date=end_date,
                dry_run=args.dry_run,
            )

            if not features.empty:
                logger.info(f"✓ {region} Feature 생성 완료: {len(features)}개 행")
            else:
                logger.warning(f"✗ {region} 데이터 없음")

        except Exception as e:
            logger.error(f"✗ {region} Feature 생성 실패: {e}")

    logger.info("전체 Feature 생성 작업 완료!")


if __name__ == "__main__":
    asyncio.run(main())
