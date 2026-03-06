#!/usr/bin/env python3
"""
뉴스 데이터 임베딩 생성 및 벡터 DB 적재 스크립트

사용법:
    # 전체 뉴스 임베딩 생성 (임베딩 없는 뉴스만)
    uv run python scripts/generate_embeddings.py

    # 특정 날짜 이후 뉴스만 처리
    uv run python scripts/generate_embeddings.py --date-from 2024-01-01

    # 배치 크기 지정 (기본: 100)
    uv run python scripts/generate_embeddings.py --batch-size 50

    # Dry run (실제 업데이트 없이 테스트)
    uv run python scripts/generate_embeddings.py --dry-run
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, date
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.shared.database import get_supabase_client
from src.shared.embedding import get_embedding_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def fetch_news_without_embeddings(
    date_from: date | None = None,
    limit: int | None = None,
) -> list[dict]:
    """임베딩이 없는 뉴스 조회

    Args:
        date_from: 시작 날짜 (None이면 전체)
        limit: 최대 조회 개수 (None이면 전체)

    Returns:
        뉴스 레코드 목록
    """
    client = get_supabase_client()

    query = client.table("news_signals").select("*").is_("embedding", "null")

    if date_from:
        query = query.gte("published_at", date_from.isoformat())

    query = query.order("published_at", desc=True)

    if limit:
        query = query.limit(limit)

    result = query.execute()
    return result.data


async def generate_and_update_embeddings(
    news_items: list[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> dict[str, int]:
    """뉴스 아이템의 임베딩 생성 및 DB 업데이트

    Args:
        news_items: 뉴스 레코드 목록
        batch_size: 한 번에 처리할 뉴스 수
        dry_run: True면 실제 업데이트 없이 테스트만

    Returns:
        통계 정보 {processed, success, failed}
    """
    if not news_items:
        logger.warning("처리할 뉴스가 없습니다")
        return {"processed": 0, "success": 0, "failed": 0}

    embedding_service = get_embedding_service()
    client = get_supabase_client()

    stats = {"processed": 0, "success": 0, "failed": 0}

    logger.info(f"총 {len(news_items)}개 뉴스 임베딩 생성 시작 (배치 크기: {batch_size})")

    for i in range(0, len(news_items), batch_size):
        batch = news_items[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(news_items) + batch_size - 1) // batch_size

        logger.info(f"배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개 뉴스)")

        # 1. 텍스트 준비 (제목 + 본문)
        texts = []
        for item in batch:
            title = item.get("title", "")
            content = item.get("content") or ""

            # 본문이 너무 길면 앞부분만 사용
            if content and len(content) > 2000:
                content = content[:2000] + "..."

            combined_text = f"{title}\n\n{content}" if content else title
            texts.append(combined_text)

        # 2. 배치 임베딩 생성
        try:
            embeddings = await embedding_service.generate_embeddings_batch(
                texts, batch_size=batch_size
            )

            if len(embeddings) != len(batch):
                logger.error(
                    f"임베딩 수({len(embeddings)})와 뉴스 수({len(batch)})가 일치하지 않음"
                )
                stats["failed"] += len(batch)
                continue

            # 3. DB 업데이트
            for item, embedding in zip(batch, embeddings):
                try:
                    if dry_run:
                        logger.debug(
                            f"[DRY RUN] {item['id']}: {item['title'][:50]}..."
                        )
                    else:
                        client.table("news_signals").update(
                            {"embedding": embedding}
                        ).eq("id", item["id"]).execute()

                    stats["success"] += 1
                    stats["processed"] += 1

                except Exception as e:
                    logger.error(f"뉴스 {item['id']} 업데이트 실패: {e}")
                    stats["failed"] += 1
                    stats["processed"] += 1

            logger.info(
                f"배치 {batch_num} 완료: 성공 {stats['success']}, 실패 {stats['failed']}"
            )

        except Exception as e:
            logger.error(f"배치 {batch_num} 임베딩 생성 실패: {e}")
            stats["failed"] += len(batch)
            stats["processed"] += len(batch)
            continue

        # Rate limiting: 짧은 대기
        if i + batch_size < len(news_items):
            await asyncio.sleep(1)

    return stats


async def verify_embeddings(sample_size: int = 5) -> None:
    """임베딩이 제대로 생성되었는지 검증

    Args:
        sample_size: 검증할 샘플 수
    """
    client = get_supabase_client()

    # 임베딩이 있는 뉴스 샘플 조회
    result = (
        client.table("news_signals")
        .select("id, title, embedding")
        .not_.is_("embedding", "null")
        .limit(sample_size)
        .execute()
    )

    if not result.data:
        logger.warning("임베딩이 있는 뉴스가 없습니다")
        return

    logger.info(f"\n{'='*60}")
    logger.info(f"임베딩 검증 (샘플 {len(result.data)}개)")
    logger.info(f"{'='*60}")

    for item in result.data:
        embedding = item.get("embedding")
        embedding_dim = len(embedding) if embedding else 0
        embedding_sample = (
            f"[{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]"
            if embedding and len(embedding) > 2
            else "None"
        )

        logger.info(f"\nID: {item['id']}")
        logger.info(f"Title: {item['title'][:60]}...")
        logger.info(f"Embedding Dimension: {embedding_dim}")
        logger.info(f"Embedding Sample: {embedding_sample}")

    logger.info(f"\n{'='*60}\n")


async def main() -> int:
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="뉴스 데이터 임베딩 생성 및 벡터 DB 적재",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--date-from",
        type=str,
        help="시작 날짜 (YYYY-MM-DD 형식, 예: 2024-01-01)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="배치 크기 (기본: 100)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="최대 처리 개수 (테스트용)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 업데이트 없이 테스트만 수행",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="임베딩 검증만 수행 (생성 안 함)",
    )

    args = parser.parse_args()

    # 환경 변수 검증
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다")
        return 1

    if "placeholder" in settings.supabase_url:
        logger.error("실제 SUPABASE_URL이 필요합니다 (placeholder URL 감지)")
        return 1

    # 날짜 파싱
    date_from = None
    if args.date_from:
        try:
            date_from = datetime.strptime(args.date_from, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"잘못된 날짜 형식: {args.date_from} (YYYY-MM-DD 필요)")
            return 1

    # 검증만 수행
    if args.verify_only:
        await verify_embeddings(sample_size=10)
        return 0

    # 임베딩 없는 뉴스 조회
    logger.info("임베딩 없는 뉴스 조회 중...")
    news_items = await fetch_news_without_embeddings(
        date_from=date_from,
        limit=args.limit,
    )

    if not news_items:
        logger.info("처리할 뉴스가 없습니다 (모든 뉴스에 이미 임베딩 존재)")
        return 0

    logger.info(f"발견: {len(news_items)}개 뉴스 (임베딩 없음)")

    if args.dry_run:
        logger.info("DRY RUN 모드: 실제 업데이트는 수행되지 않습니다")

    # 임베딩 생성 및 업데이트
    stats = await generate_and_update_embeddings(
        news_items=news_items,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    # 결과 출력
    logger.info(f"\n{'='*60}")
    logger.info("임베딩 생성 완료")
    logger.info(f"{'='*60}")
    logger.info(f"총 처리: {stats['processed']}")
    logger.info(f"성공: {stats['success']}")
    logger.info(f"실패: {stats['failed']}")
    logger.info(f"{'='*60}\n")

    # 검증
    if stats["success"] > 0 and not args.dry_run:
        await verify_embeddings(sample_size=5)

    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
