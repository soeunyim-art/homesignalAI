"""
데이터 무결성 검증 스크립트

테이블 간 참조 무결성, 고아 레코드, 데이터 일관성을 검증합니다.

검증 항목:
1. ml_training_features.region이 houses_data에 존재하는지
2. 이벤트 더미 변수가 TRUE인 경우 policy_events에 대응 이벤트 존재하는지
3. Train/Test 분할 비율 및 시간 순서 검증
4. 중복 데이터 확인
5. NULL 값 검증

Usage:
    uv run python scripts/validate_data_integrity.py
    uv run python scripts/validate_data_integrity.py --table ml_training_features
    uv run python scripts/validate_data_integrity.py --verbose
    uv run python scripts/validate_data_integrity.py --fix-orphans
"""

import argparse
import asyncio
import logging
from datetime import datetime, timedelta

from src.shared.database import get_supabase_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataIntegrityValidator:
    """데이터 무결성 검증기"""

    def __init__(self, supabase):
        self.supabase = supabase
        self.errors = []
        self.warnings = []

    def add_error(self, message: str):
        """에러 추가"""
        self.errors.append(message)
        logger.error(f"✗ {message}")

    def add_warning(self, message: str):
        """경고 추가"""
        self.warnings.append(message)
        logger.warning(f"⚠ {message}")

    def add_success(self, message: str):
        """성공 메시지"""
        logger.info(f"✓ {message}")

    async def validate_region_references(self, fix_orphans: bool = False) -> bool:
        """ml_training_features.region이 houses_data에 존재하는지 검증 및 고아 레코드 삭제 처리"""
        logger.info("\n[1] Region 참조 무결성 검증 중...")

        try:
            # ml_training_features의 고유 region 목록
            mtf_response = (
                self.supabase.table("ml_training_features")
                .select("region")
                .execute()
            )

            if not mtf_response.data:
                self.add_warning("ml_training_features에 데이터가 없습니다.")
                return True

            mtf_regions = set(row["region"] for row in mtf_response.data)

            # houses_data의 고유 dong_name 목록
            houses_response = (
                self.supabase.table("houses_data").select("dong_name").execute()
            )

            houses_regions = set(
                row["dong_name"]
                for row in houses_response.data
                if row["dong_name"]
            )

            # 고아 region 확인
            orphan_regions = mtf_regions - houses_regions

            if orphan_regions:
                self.add_error(
                    f"ml_training_features에 houses_data에 없는 region 존재: {orphan_regions}"
                )
                
                if fix_orphans:
                    logger.info("  --fix-orphans 옵션 활성화: 고아 레코드 삭제 진행 중...")
                    for orphan in orphan_regions:
                        try:
                            self.supabase.table("ml_training_features").delete().eq("region", orphan).execute()
                            logger.info(f"  ✓ 고아 region 삭제 완료: {orphan}")
                        except Exception as delete_err:
                            self.add_error(f"  ✗ 고아 region 삭제 실패 ({orphan}): {delete_err}")
                
                return False
            else:
                self.add_success(
                    f"모든 region이 houses_data에 존재합니다. (총 {len(mtf_regions)}개)"
                )
                return True

        except Exception as e:
            self.add_error(f"Region 참조 검증 실패: {e}")
            return False

    async def validate_event_dummies(self, verbose: bool = False) -> bool:
        """이벤트 더미 변수가 TRUE인 경우 policy_events에 대응 이벤트 존재하는지 검증"""
        logger.info("\n[2] 이벤트 더미 변수 검증 중...")

        event_mappings = {
            "event_gtx_announcement": "gtx_announcement",
            "event_redevelopment_approval": "redevelopment_approval",
            "event_interest_rate_change": "interest_rate_change",
            "event_loan_regulation": "loan_regulation",
            "event_sales_restriction": "sales_restriction",
        }

        all_valid = True

        for dummy_col, event_type in event_mappings.items():
            try:
                # 더미가 TRUE인 피처 행 조회
                mtf_response = (
                    self.supabase.table("ml_training_features")
                    .select("id, period_date, region, period_type")
                    .eq(dummy_col, True)
                    .execute()
                )

                if not mtf_response.data:
                    if verbose:
                        self.add_success(f"{dummy_col}: TRUE인 행이 없습니다.")
                    continue

                # 각 행에 대해 대응 이벤트 존재 확인
                for row in mtf_response.data:
                    period_date = datetime.fromisoformat(
                        row["period_date"]
                    ).date()
                    region = row["region"]
                    period_type = row["period_type"]

                    # 기간 범위 계산
                    if period_type == "week":
                        end_date = period_date + timedelta(days=6)
                    else:  # month
                        end_date = period_date + timedelta(days=30)

                    # 대응 이벤트 조회
                    event_response = (
                        self.supabase.table("policy_events")
                        .select("id, event_date, event_name")
                        .eq("event_type", event_type)
                        .gte("event_date", period_date.isoformat())
                        .lte("event_date", end_date.isoformat())
                        .execute()
                    )

                    # region 필터링 (NULL이면 전체 지역 적용)
                    matching_events = [
                        e
                        for e in event_response.data
                        if e.get("region") is None or e.get("region") == region
                    ]

                    if not matching_events:
                        self.add_warning(
                            f"{dummy_col}=TRUE이지만 대응 이벤트 없음: "
                            f"region={region}, period_date={period_date}"
                        )
                        all_valid = False
                    elif verbose:
                        logger.info(
                            f"  ✓ {dummy_col}: {region} {period_date} - "
                            f"대응 이벤트 {len(matching_events)}개 발견"
                        )

                if verbose or not all_valid:
                    self.add_success(
                        f"{dummy_col}: {len(mtf_response.data)}개 행 검증 완료"
                    )

            except Exception as e:
                self.add_error(f"{dummy_col} 검증 실패: {e}")
                all_valid = False

        return all_valid

    async def validate_train_test_split(self) -> bool:
        """Train/Test 분할 비율 및 시간 순서 검증"""
        logger.info("\n[3] Train/Test Split 검증 중...")

        try:
            # 분할 통계 조회
            stats_response = self.supabase.rpc("get_split_statistics").execute()

            if not stats_response.data:
                self.add_warning("train_test_split 플래그가 설정되지 않았습니다.")
                return True

            all_valid = True

            for row in stats_response.data:
                group = row["stratification_group"]
                train_count = row["train_count"]
                test_count = row["test_count"]
                total_count = row["total_count"]
                train_ratio = float(row["train_ratio"])

                # 비율 검증 (±5% 허용)
                if not (0.65 <= train_ratio <= 0.75):
                    self.add_warning(
                        f"{group}: Train 비율이 70%에서 벗어남 ({train_ratio*100:.1f}%)"
                    )
                    all_valid = False
                else:
                    logger.info(
                        f"  ✓ {group}: Train {train_count}개 ({train_ratio*100:.1f}%), "
                        f"Test {test_count}개"
                    )

            # 시간 순서 검증
            await self._validate_time_order()

            if all_valid:
                self.add_success("모든 계층의 Train/Test 비율이 적절합니다.")

            return all_valid

        except Exception as e:
            self.add_error(f"Train/Test Split 검증 실패: {e}")
            return False

    async def _validate_time_order(self):
        """시간 순서 검증: Test는 Train보다 미래여야 함"""
        try:
            # 모든 stratification_group 조회
            groups_response = (
                self.supabase.table("ml_training_features")
                .select("stratification_group")
                .execute()
            )

            groups = set(
                row["stratification_group"]
                for row in groups_response.data
                if row.get("stratification_group")
            )

            for group in groups:
                # Train 최대 날짜
                train_response = (
                    self.supabase.table("ml_training_features")
                    .select("period_date")
                    .eq("stratification_group", group)
                    .eq("train_test_split", "train")
                    .order("period_date", desc=True)
                    .limit(1)
                    .execute()
                )

                # Test 최소 날짜
                test_response = (
                    self.supabase.table("ml_training_features")
                    .select("period_date")
                    .eq("stratification_group", group)
                    .eq("train_test_split", "test")
                    .order("period_date", desc=False)
                    .limit(1)
                    .execute()
                )

                if train_response.data and test_response.data:
                    train_max = train_response.data[0]["period_date"]
                    test_min = test_response.data[0]["period_date"]

                    if train_max > test_min:
                        self.add_error(
                            f"{group}: Test에 Train보다 과거 데이터 포함 "
                            f"(Train 최대: {train_max}, Test 최소: {test_min})"
                        )
                    else:
                        logger.info(
                            f"  ✓ {group}: 시간 순서 OK "
                            f"(Train 최대: {train_max}, Test 최소: {test_min})"
                        )

        except Exception as e:
            self.add_error(f"시간 순서 검증 실패: {e}")

    async def validate_duplicates(self) -> bool:
        """중복 데이터 검증"""
        logger.info("\n[4] 중복 데이터 검증 중...")

        tables_to_check = [
            ("houses_data", ["complex_name", "contract_date", "price"]),
            ("ml_training_features", ["region", "period_date", "period_type"]),
        ]

        all_valid = True

        for table_name, unique_cols in tables_to_check:
            try:
                # 전체 데이터 조회
                response = self.supabase.table(table_name).select("*").execute()

                if not response.data:
                    continue

                # 중복 확인
                seen = set()
                duplicates = []

                for row in response.data:
                    key = tuple(str(row.get(col)) for col in unique_cols)
                    if key in seen:
                        duplicates.append(key)
                    seen.add(key)

                if duplicates:
                    self.add_error(
                        f"{table_name}: {len(duplicates)}개 중복 발견 "
                        f"(unique_cols={unique_cols})"
                    )
                    all_valid = False
                else:
                    self.add_success(f"{table_name}: 중복 없음")

            except Exception as e:
                self.add_error(f"{table_name} 중복 검증 실패: {e}")
                all_valid = False

        return all_valid

    async def validate_null_values(self) -> bool:
        """필수 컬럼의 NULL 값 검증"""
        logger.info("\n[5] NULL 값 검증 중...")

        validations = [
            ("houses_data", ["complex_name", "price", "contract_date"]),
            ("news_signals", ["title", "published_at"]),
            ("ml_training_features", ["period_date", "region", "avg_price"]),
            ("policy_events", ["event_date", "event_type", "event_name"]),
        ]

        all_valid = True

        for table_name, required_cols in validations:
            try:
                for col in required_cols:
                    # 컬럼명을 동적으로 지정하여 NULL 값 개수 조회
                    null_response = (
                        self.supabase.table(table_name)
                        .select("id")
                        .is_(col, "null")
                        .execute()
                    )

                    null_count = len(null_response.data) if null_response.data else 0

                    if null_count > 0:
                        self.add_error(
                            f"{table_name}.{col}: {null_count}개 NULL 값 발견"
                        )
                        all_valid = False

                self.add_success(f"{table_name}: 필수 컬럼 NULL 값 없음")

            except Exception as e:
                self.add_error(f"{table_name} NULL 검증 실패: {e}")
                all_valid = False

        return all_valid

    async def validate_price_ranges(self) -> bool:
        """가격 범위 검증 (음수, 비정상적으로 큰 값)"""
        logger.info("\n[6] 가격 범위 검증 중...")

        try:
            # houses_data 가격 검증
            houses_response = (
                self.supabase.table("houses_data").select("id, price").execute()
            )

            invalid_prices = [
                row
                for row in houses_response.data
                if row["price"] <= 0 or row["price"] > 10_000_000_000
            ]

            if invalid_prices:
                self.add_error(
                    f"houses_data: {len(invalid_prices)}개 비정상 가격 발견 "
                    f"(0 이하 또는 100억 초과)"
                )
                return False

            # ml_training_features 평균 가격 검증
            mtf_response = (
                self.supabase.table("ml_training_features")
                .select("id, avg_price")
                .execute()
            )

            invalid_avg_prices = [
                row
                for row in mtf_response.data
                if row["avg_price"] <= 0 or row["avg_price"] > 10_000_000_000
            ]

            if invalid_avg_prices:
                self.add_error(
                    f"ml_training_features: {len(invalid_avg_prices)}개 비정상 평균 가격 발견"
                )
                return False

            self.add_success("모든 가격 데이터가 정상 범위 내에 있습니다.")
            return True

        except Exception as e:
            self.add_error(f"가격 범위 검증 실패: {e}")
            return False

    async def validate_date_ranges(self) -> bool:
        """날짜 범위 검증 (미래 날짜, 비정상적으로 과거 날짜)"""
        logger.info("\n[7] 날짜 범위 검증 중...")

        today = datetime.now().date()
        min_valid_date = datetime(2020, 1, 1).date()

        try:
            # houses_data 날짜 검증
            houses_response = (
                self.supabase.table("houses_data")
                .select("id, contract_date")
                .execute()
            )

            invalid_dates = [
                row
                for row in houses_response.data
                if datetime.fromisoformat(row["contract_date"][:10]).date()
                > today
                or datetime.fromisoformat(row["contract_date"][:10]).date()
                < min_valid_date
            ]

            if invalid_dates:
                self.add_error(
                    f"houses_data: {len(invalid_dates)}개 비정상 날짜 발견 "
                    f"(2020년 이전 또는 미래)"
                )
                return False

            self.add_success("모든 날짜 데이터가 정상 범위 내에 있습니다.")
            return True

        except Exception as e:
            self.add_error(f"날짜 범위 검증 실패: {e}")
            return False

    async def validate_embeddings(self) -> bool:
        """news_signals의 임베딩 차원 검증"""
        logger.info("\n[8] 임베딩 차원 검증 중...")

        try:
            # 임베딩이 있는 뉴스 조회
            response = (
                self.supabase.table("news_signals")
                .select("id, embedding")
                .not_.is_("embedding", "null")
                .limit(10)
                .execute()
            )

            if not response.data:
                self.add_warning("임베딩이 생성된 뉴스가 없습니다.")
                return True

            # 차원 확인 (1536차원이어야 함)
            for row in response.data:
                embedding = row.get("embedding")
                if embedding and len(embedding) != 1536:
                    self.add_error(
                        f"news_signals (id={row['id']}): "
                        f"임베딩 차원이 1536이 아님 ({len(embedding)})"
                    )
                    return False

            self.add_success(
                f"임베딩 차원 검증 완료 ({len(response.data)}개 샘플)"
            )
            return True

        except Exception as e:
            self.add_error(f"임베딩 검증 실패: {e}")
            return False

    async def print_summary(self):
        """검증 결과 요약 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("검증 결과 요약")
        logger.info("=" * 80)

        if not self.errors and not self.warnings:
            logger.info("✓ 모든 검증 통과! 데이터 무결성이 정상입니다.")
        else:
            if self.errors:
                logger.error(f"\n에러: {len(self.errors)}개")
                for error in self.errors:
                    logger.error(f"  - {error}")

            if self.warnings:
                logger.warning(f"\n경고: {len(self.warnings)}개")
                for warning in self.warnings:
                    logger.warning(f"  - {warning}")

        logger.info("=" * 80)

    async def validate_all(self, verbose: bool = False, fix_orphans: bool = False) -> bool:
        """모든 검증 수행"""
        logger.info("데이터 무결성 검증 시작...\n")

        results = []

        # 순차 검증
        results.append(await self.validate_region_references(fix_orphans))
        results.append(await self.validate_event_dummies(verbose))
        results.append(await self.validate_train_test_split())
        results.append(await self.validate_duplicates())
        results.append(await self.validate_null_values())
        results.append(await self.validate_price_ranges())
        results.append(await self.validate_date_ranges())
        results.append(await self.validate_embeddings())

        # 요약 출력
        await self.print_summary()

        return all(results)


async def main():
    parser = argparse.ArgumentParser(description="데이터 무결성 검증")
    parser.add_argument(
        "--table",
        type=str,
        choices=[
            "houses_data",
            "news_signals",
            "ml_training_features",
            "policy_events",
            "predictions",
            "ai_predictions",
        ],
        default=None,
        help="특정 테이블만 검증",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력",
    )
    parser.add_argument(
        "--fix-orphans",
        action="store_true",
        help="고아 레코드 자동 삭제 (주의: 데이터 손실 가능)",
    )

    args = parser.parse_args()

    # Supabase 클라이언트
    supabase = get_supabase_client()
    validator = DataIntegrityValidator(supabase)

    try:
        if args.table:
            logger.info(f"테이블 '{args.table}' 검증 중...")
            # 테이블별 검증 (TODO: 구현)
            logger.warning("테이블별 검증은 아직 구현되지 않았습니다. 전체 검증을 수행합니다.")

        if args.fix_orphans:
            logger.warning("!!! --fix-orphans 플래그가 켜졌습니다. 잘못된 무결성 레코드가 강제 삭제될 수 있습니다. !!!")

        # 전체 검증 수행
        is_valid = await validator.validate_all(verbose=args.verbose, fix_orphans=args.fix_orphans)

        if is_valid:
            logger.info("\n✓ 데이터 무결성 검증 완료!")
            return 0
        else:
            logger.error("\n✗ 데이터 무결성 검증 실패!")
            return 1

    except Exception as e:
        logger.error(f"검증 실패: {e}")
        raise


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
