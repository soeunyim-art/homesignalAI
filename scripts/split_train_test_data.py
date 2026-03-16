"""
ML Training Features 데이터 분할 스크립트

ml_training_features 테이블의 데이터를 계층화 분할(Stratified Split)하여
train_test_split 플래그를 업데이트합니다.

계층화 전략:
- Stratification Key: region + price_quartile (avg_price 4분위)
- Split Ratio: Train 70%, Test 30%
- 시간 순서 보존: 각 계층 내에서 시간 순서대로 과거 70% 학습, 최근 30% 평가

Usage:
    uv run python scripts/split_train_test_data.py
    uv run python scripts/split_train_test_data.py --region 청량리동
    uv run python scripts/split_train_test_data.py --period-type month
    uv run python scripts/split_train_test_data.py --train-ratio 0.8
    uv run python scripts/split_train_test_data.py --dry-run
"""

import argparse
import asyncio
import logging
from datetime import date

import pandas as pd

from src.shared.database import get_supabase_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TrainTestSplitter:
    """ML Training Features 데이터 분할기"""

    def __init__(self, supabase, train_ratio: float = 0.7):
        self.supabase = supabase
        self.train_ratio = train_ratio
        self.test_ratio = 1.0 - train_ratio

    async def load_features(
        self, region: str | None = None, period_type: str | None = None
    ) -> pd.DataFrame:
        """ml_training_features 데이터 로드"""
        logger.info("ml_training_features 데이터 로드 중...")

        query = self.supabase.table("ml_training_features").select("*")

        if region:
            query = query.eq("region", region)
        if period_type:
            query = query.eq("period_type", period_type)

        response = query.order("period_date", desc=False).execute()

        if not response.data:
            raise ValueError("로드할 데이터가 없습니다.")

        df = pd.DataFrame(response.data)
        df["period_date"] = pd.to_datetime(df["period_date"])

        logger.info(f"로드된 데이터: {len(df)}개 행")
        return df

    def stratified_split(self, df: pd.DataFrame) -> pd.DataFrame:
        """계층화 분할 수행
        
        Args:
            df: ml_training_features 데이터프레임
            
        Returns:
            train_test_split, stratification_group 컬럼이 추가된 데이터프레임
        """
        logger.info("계층화 분할 수행 중...")

        # 1. 가격 4분위 계산
        df["price_quartile"] = pd.qcut(
            df["avg_price"],
            q=4,
            labels=["Q1", "Q2", "Q3", "Q4"],
            duplicates="drop",  # 동일 값이 많을 경우 처리
        )

        # 2. 계층화 그룹 생성 (region + period_type + price_quartile)
        df["stratification_group"] = (
            df["region"].astype(str)
            + "_"
            + df["period_type"].astype(str)
            + "_"
            + df["price_quartile"].astype(str)
        )

        # 3. 각 계층별로 시간 순서 유지하며 분할
        split_results = []

        for group_name, group_df in df.groupby("stratification_group"):
            # 시간 순서대로 정렬
            group_df = group_df.sort_values("period_date").reset_index(drop=True)

            # 70% 지점 계산
            split_idx = int(len(group_df) * self.train_ratio)

            # 최소 1개는 test에 포함되도록
            if split_idx >= len(group_df):
                split_idx = len(group_df) - 1

            # Train/Test 플래그 할당
            group_df["train_test_split"] = ["train"] * split_idx + ["test"] * (
                len(group_df) - split_idx
            )

            split_results.append(group_df)

            logger.info(
                f"  {group_name}: Train {split_idx}개, Test {len(group_df) - split_idx}개"
            )

        # 4. 결과 병합
        result_df = pd.concat(split_results, ignore_index=True)

        # 5. 통계 출력
        self._print_split_statistics(result_df)

        return result_df

    def _print_split_statistics(self, df: pd.DataFrame):
        """분할 통계 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("분할 통계")
        logger.info("=" * 80)

        # 전체 통계
        total_count = len(df)
        train_count = (df["train_test_split"] == "train").sum()
        test_count = (df["train_test_split"] == "test").sum()

        logger.info(f"전체: {total_count}개")
        logger.info(
            f"Train: {train_count}개 ({train_count/total_count*100:.1f}%)"
        )
        logger.info(f"Test: {test_count}개 ({test_count/total_count*100:.1f}%)")

        # 계층별 통계
        logger.info("\n계층별 분할:")
        for group_name, group_df in df.groupby("stratification_group"):
            group_train = (group_df["train_test_split"] == "train").sum()
            group_test = (group_df["train_test_split"] == "test").sum()
            group_total = len(group_df)

            logger.info(
                f"  {group_name}: "
                f"Train {group_train}개 ({group_train/group_total*100:.1f}%), "
                f"Test {group_test}개 ({group_test/group_total*100:.1f}%)"
            )

        # 시간 순서 검증
        logger.info("\n시간 순서 검증:")
        for group_name, group_df in df.groupby("stratification_group"):
            train_df = group_df[group_df["train_test_split"] == "train"]
            test_df = group_df[group_df["train_test_split"] == "test"]

            if len(train_df) > 0 and len(test_df) > 0:
                train_max_date = train_df["period_date"].max()
                test_min_date = test_df["period_date"].min()

                if train_max_date <= test_min_date:
                    status = "✓ OK"
                else:
                    status = "✗ WARNING: Test에 Train보다 과거 데이터 포함"

                logger.info(
                    f"  {group_name}: Train 최대 {train_max_date.date()}, "
                    f"Test 최소 {test_min_date.date()} - {status}"
                )

        logger.info("=" * 80 + "\n")

    async def update_database(self, df: pd.DataFrame, dry_run: bool = False):
        """DB에 train_test_split 플래그 업데이트"""
        if dry_run:
            logger.info("[DRY-RUN] DB 업데이트 생략")
            return

        logger.info("DB 업데이트 중...")

        # Batch 업데이트 (100개씩)
        batch_size = 100
        updated_count = 0

        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i : i + batch_size]

            for _, row in batch_df.iterrows():
                try:
                    self.supabase.table("ml_training_features").update(
                        {
                            "train_test_split": row["train_test_split"],
                            "stratification_group": row["stratification_group"],
                        }
                    ).eq("id", row["id"]).execute()

                    updated_count += 1

                except Exception as e:
                    logger.error(f"업데이트 실패 (id={row['id']}): {e}")

            logger.info(f"  진행: {min(i + batch_size, len(df))}/{len(df)}개")

        logger.info(f"DB 업데이트 완료: {updated_count}개 행")

    async def verify_split(self):
        """분할 결과 검증 (DB에서 직접 조회)"""
        logger.info("\n분할 결과 검증 중...")

        try:
            # get_split_statistics() RPC 함수 호출
            response = self.supabase.rpc("get_split_statistics").execute()

            if not response.data:
                logger.warning("분할된 데이터가 없습니다.")
                return

            logger.info("\nDB 저장된 분할 통계:")
            logger.info("-" * 80)

            for row in response.data:
                logger.info(
                    f"{row['region']} ({row['period_type']}), {row['stratification_group']}: "
                    f"Train {row['train_count']}개 ({float(row['train_ratio'])*100:.1f}%), "
                    f"Test {row['test_count']}개"
                )

            logger.info("-" * 80)

        except Exception as e:
            logger.error(f"검증 실패: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="ML Training Features 데이터 분할 (계층화 + 시간 순서 보존)"
    )
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help="특정 지역만 분할 (기본값: 전체)",
    )
    parser.add_argument(
        "--period-type",
        type=str,
        choices=["week", "month"],
        default=None,
        help="특정 기간 타입만 분할 (기본값: 전체)",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.7,
        help="학습 데이터 비율 (기본값: 0.7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="분할만 수행하고 DB 업데이트 안 함",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="DB에 저장된 분할 통계만 조회",
    )

    args = parser.parse_args()

    # Supabase 클라이언트 (service_role 키 사용 - UPDATE 권한 필요)
    supabase = get_supabase_client(use_service_role=True)
    splitter = TrainTestSplitter(supabase, train_ratio=args.train_ratio)

    try:
        if args.verify_only:
            # 검증만 수행
            await splitter.verify_split()
            return

        # 1. 데이터 로드
        features = await splitter.load_features(args.region, args.period_type)

        # 2. 계층화 분할
        split_features = splitter.stratified_split(features)

        # 3. DB 업데이트
        await splitter.update_database(split_features, dry_run=args.dry_run)

        # 4. 검증
        if not args.dry_run:
            await splitter.verify_split()

        logger.info("\n✓ 데이터 분할 완료!")

        if args.dry_run:
            logger.info(
                "\n[DRY-RUN] DB에 저장되지 않았습니다. "
                "--dry-run 플래그 없이 다시 실행하세요."
            )

    except Exception as e:
        logger.error(f"데이터 분할 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
