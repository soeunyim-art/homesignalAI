"""뉴스 크롤러 CLI 진입점"""

import argparse
import asyncio
import logging
import sys

from .runner import CrawlerRunner, create_crawler_runner
from .schemas import CrawlConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def run_crawl(args: argparse.Namespace) -> int:
    """크롤링 실행

    Args:
        args: CLI 인자

    Returns:
        종료 코드 (0: 성공, 1: 실패)
    """
    config = CrawlConfig(
        queries=args.queries or CrawlConfig().queries,
        max_results_per_query=args.max_results,
        date_range_days=args.date_range,
        generate_embeddings=not args.no_embeddings,
        extract_content=not args.no_content,
        content_max_length=args.content_max_length,
    )

    runner = create_crawler_runner(
        requests_per_minute=args.rate_limit,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
    )

    try:
        result = await runner.run(config, dry_run=args.dry_run)

        print("\n" + "=" * 50)
        print("크롤링 결과")
        print("=" * 50)
        print(f"총 크롤링:      {result.total_crawled}")
        print(f"본문 추출:      {result.content_extracted}")
        print(f"신규 삽입:      {result.inserted}")
        print(f"중복 스킵:      {result.duplicates}")
        print(f"실패:          {result.errors}")
        print(f"소요 시간:      {result.duration_seconds}초")
        if result.batch_id:
            print(f"배치 ID:        {result.batch_id}")
        print("=" * 50)

        return 0 if result.errors == 0 else 1

    except KeyboardInterrupt:
        print("\n크롤링 중단됨")
        return 130
    except Exception as e:
        logger.error(f"크롤링 실패: {e}")
        return 1
    finally:
        await runner.close()


def main() -> None:
    """CLI 메인 진입점"""
    parser = argparse.ArgumentParser(
        description="HomeSignal AI 뉴스 크롤러",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 실행
  uv run python -m src.crawler.cli crawl

  # 커스텀 쿼리
  uv run python -m src.crawler.cli crawl -q "GTX-C 청량리" "동대문구 재개발"

  # 옵션 조합
  uv run python -m src.crawler.cli crawl --max-results 50 --date-range 14 --dry-run
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # crawl 서브커맨드
    crawl_parser = subparsers.add_parser("crawl", help="뉴스 크롤링 실행")

    # 쿼리 옵션
    crawl_parser.add_argument(
        "--queries",
        "-q",
        nargs="+",
        help="검색 쿼리 (기본: 동대문구 부동산, 청량리 재개발 등)",
    )
    crawl_parser.add_argument(
        "--max-results",
        "-n",
        type=int,
        default=20,
        help="쿼리당 최대 결과 수 (기본: 20)",
    )
    crawl_parser.add_argument(
        "--date-range",
        "-d",
        type=int,
        default=7,
        help="검색 기간 (일, 기본: 7)",
    )

    # Rate limiting 옵션
    crawl_parser.add_argument(
        "--rate-limit",
        "-r",
        type=int,
        default=10,
        help="분당 요청 수 (기본: 10)",
    )
    crawl_parser.add_argument(
        "--min-delay",
        type=float,
        default=1.0,
        help="최소 딜레이 초 (기본: 1.0)",
    )
    crawl_parser.add_argument(
        "--max-delay",
        type=float,
        default=3.0,
        help="최대 딜레이 초 (기본: 3.0)",
    )

    # 본문/임베딩 옵션
    crawl_parser.add_argument(
        "--no-content",
        action="store_true",
        help="본문 추출 비활성화",
    )
    crawl_parser.add_argument(
        "--content-max-length",
        type=int,
        default=2000,
        help="본문 최대 길이 (기본: 2000)",
    )
    crawl_parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="임베딩 생성 비활성화",
    )

    # 기타 옵션
    crawl_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 적재 없이 테스트",
    )
    crawl_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세 로그 출력",
    )

    args = parser.parse_args()

    # verbose 모드
    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.command == "crawl":
        exit_code = asyncio.run(run_crawl(args))
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
