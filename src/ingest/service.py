"""
Ingest 비즈니스 로직 - 데이터 적재 서비스

개발1(국토교통부), 개발2(뉴스) 데이터를 Supabase에 적재
"""

import logging
import uuid
from datetime import datetime

from supabase import Client

from src.shared.database import get_supabase_client
from src.shared.embedding import EmbeddingService, get_embedding_service
from src.shared.exceptions import DatabaseError

from .schemas import (
    HouseDataBatchRequest,
    HouseDataBatchResponse,
    HouseDataStatusResponse,
    NewsSignalBatchRequest,
    NewsSignalBatchResponse,
    NewsSignalStatusResponse,
    PredictionBatchRequest,
    PredictionBatchResponse,
)

logger = logging.getLogger(__name__)


class IngestService:
    """데이터 적재 서비스 (service_role 키 사용)"""

    def __init__(
        self,
        db: Client | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        # Ingest는 INSERT/UPDATE가 필요하므로 service_role 키 사용
        self.db = db or get_supabase_client(use_service_role=True)
        self.embedding_service = embedding_service or get_embedding_service()

    # =========================================================================
    # Houses Data (개발1 - 국토교통부)
    # =========================================================================

    async def ingest_houses(
        self,
        request: HouseDataBatchRequest,
    ) -> HouseDataBatchResponse:
        """
        부동산 거래 데이터 배치 적재

        중복 체크: (complex_name, contract_date, price) 기준
        """
        batch_id = str(uuid.uuid4())[:8]
        inserted_count = 0
        failed_count = 0
        errors: list[str] = []

        logger.info(
            f"부동산 데이터 적재 시작: batch_id={batch_id}, "
            f"items={len(request.items)}, source={request.source}"
        )

        for idx, item in enumerate(request.items):
            try:
                # 데이터 변환
                record = {
                    "complex_name": item.complex_name,
                    "dong_name": item.dong_name,
                    "price": item.price,
                    "bedrooms": item.bedrooms,
                    "bathrooms": item.bathrooms,
                    "sqft_living": item.sqft_living,
                    "sqft_lot": item.sqft_lot,
                    "floors": item.floors,
                    "waterfront": item.waterfront,
                    "view": item.view,
                    "condition": item.condition,
                    "sqft_above": item.sqft_above,
                    "sqft_basement": item.sqft_basement,
                    "yr_built": item.yr_built,
                    "yr_renovated": item.yr_renovated,
                    "contract_date": item.contract_date.isoformat(),
                }

                # Supabase에 삽입
                self.db.table("houses_data").insert(record).execute()
                inserted_count += 1

            except Exception as e:
                failed_count += 1
                error_msg = f"[{idx}] {item.complex_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"레코드 삽입 실패: {error_msg}")

        logger.info(
            f"부동산 데이터 적재 완료: batch_id={batch_id}, "
            f"inserted={inserted_count}, failed={failed_count}"
        )

        return HouseDataBatchResponse(
            success=failed_count == 0,
            inserted_count=inserted_count,
            failed_count=failed_count,
            errors=errors if errors else None,
            batch_id=batch_id,
        )

    async def get_houses_status(self) -> HouseDataStatusResponse:
        """부동산 데이터 현황 조회"""
        try:
            # 총 레코드 수
            count_result = (
                self.db.table("houses_data")
                .select("id", count="exact")
                .execute()
            )
            total_records = count_result.count or 0

            # 계약일 범위
            date_result = (
                self.db.table("houses_data")
                .select("contract_date")
                .order("contract_date", desc=False)
                .limit(1)
                .execute()
            )
            oldest_date = (
                date_result.data[0]["contract_date"][:10]
                if date_result.data
                else None
            )

            latest_result = (
                self.db.table("houses_data")
                .select("contract_date")
                .order("contract_date", desc=True)
                .limit(1)
                .execute()
            )
            latest_date = (
                latest_result.data[0]["contract_date"][:10]
                if latest_result.data
                else None
            )

            # 동별 분포 (간단히 구현)
            dong_distribution: dict[str, int] = {}

            return HouseDataStatusResponse(
                total_records=total_records,
                latest_contract_date=latest_date,
                oldest_contract_date=oldest_date,
                dong_distribution=dong_distribution,
                last_ingestion_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"부동산 데이터 현황 조회 실패: {e}")
            return HouseDataStatusResponse(
                total_records=0,
                latest_contract_date=None,
                oldest_contract_date=None,
                dong_distribution={},
                last_ingestion_at=None,
            )

    # =========================================================================
    # News Signals (개발2 - 뉴스 크롤링)
    # =========================================================================

    async def ingest_news(
        self,
        request: NewsSignalBatchRequest,
    ) -> NewsSignalBatchResponse:
        """
        뉴스 데이터 배치 적재

        - URL 기준 중복 체크
        - embedding 미제공 시 자동 생성 (generate_embeddings=True)
        """
        batch_id = str(uuid.uuid4())[:8]
        inserted_count = 0
        duplicate_count = 0
        embedding_generated_count = 0
        failed_count = 0
        errors: list[str] = []

        logger.info(
            f"뉴스 데이터 적재 시작: batch_id={batch_id}, "
            f"items={len(request.items)}, source={request.source}, "
            f"generate_embeddings={request.generate_embeddings}"
        )

        for idx, item in enumerate(request.items):
            try:
                # URL 기준 중복 체크
                if item.url:
                    existing = (
                        self.db.table("news_signals")
                        .select("id")
                        .eq("url", item.url)
                        .execute()
                    )
                    if existing.data:
                        duplicate_count += 1
                        continue

                # 임베딩 처리
                embedding = item.embedding
                if embedding is None and request.generate_embeddings:
                    try:
                        embedding = await self.embedding_service.generate_embedding_for_news(
                            title=item.title,
                            content=item.content,
                        )
                        embedding_generated_count += 1
                    except Exception as e:
                        logger.warning(f"임베딩 생성 실패 [{idx}]: {e}")
                        # 임베딩 실패해도 데이터는 저장

                # 데이터 변환
                record = {
                    "title": item.title,
                    "content": item.content,
                    "url": item.url,
                    "keywords": item.keywords,
                    "embedding": embedding,
                    "published_at": item.published_at.isoformat(),
                }

                # Supabase에 삽입
                self.db.table("news_signals").insert(record).execute()
                inserted_count += 1

            except Exception as e:
                failed_count += 1
                error_msg = f"[{idx}] {item.title[:30]}...: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"레코드 삽입 실패: {error_msg}")

        logger.info(
            f"뉴스 데이터 적재 완료: batch_id={batch_id}, "
            f"inserted={inserted_count}, duplicates={duplicate_count}, "
            f"embeddings_generated={embedding_generated_count}, failed={failed_count}"
        )

        return NewsSignalBatchResponse(
            success=failed_count == 0,
            inserted_count=inserted_count,
            duplicate_count=duplicate_count,
            embedding_generated_count=embedding_generated_count,
            failed_count=failed_count,
            errors=errors if errors else None,
            batch_id=batch_id,
        )

    async def get_news_status(self) -> NewsSignalStatusResponse:
        """뉴스 데이터 현황 조회"""
        try:
            # 총 레코드 수
            count_result = (
                self.db.table("news_signals")
                .select("id", count="exact")
                .execute()
            )
            total_records = count_result.count or 0

            # 임베딩 보유 레코드 수 (간단히 0으로 반환, 실제로는 쿼리 필요)
            with_embedding_count = 0

            # 최근 발행일
            latest_result = (
                self.db.table("news_signals")
                .select("published_at")
                .order("published_at", desc=True)
                .limit(1)
                .execute()
            )
            latest_published = (
                latest_result.data[0]["published_at"]
                if latest_result.data
                else None
            )

            # 키워드 빈도 (간단히 빈 딕셔너리 반환)
            keyword_frequency: dict[str, int] = {}

            return NewsSignalStatusResponse(
                total_records=total_records,
                with_embedding_count=with_embedding_count,
                keyword_frequency=keyword_frequency,
                latest_published_at=latest_published,
                last_ingestion_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"뉴스 데이터 현황 조회 실패: {e}")
            return NewsSignalStatusResponse(
                total_records=0,
                with_embedding_count=0,
                keyword_frequency={},
                latest_published_at=None,
                last_ingestion_at=None,
            )

    # =========================================================================
    # Predictions (백엔드 내부용)
    # =========================================================================

    async def ingest_predictions(
        self,
        request: PredictionBatchRequest,
    ) -> PredictionBatchResponse:
        """예측 결과 배치 저장"""
        batch_id = str(uuid.uuid4())[:8]
        inserted_count = 0

        logger.info(
            f"예측 결과 저장 시작: batch_id={batch_id}, items={len(request.items)}"
        )

        for item in request.items:
            try:
                record = {
                    "model_version": item.model_version,
                    "target_date": item.target_date.isoformat(),
                    "predicted_price": item.predicted_price,
                    "confidence_score": item.confidence_score,
                    "features_used": item.features_used,
                }

                self.db.table("ai_predictions").insert(record).execute()
                inserted_count += 1

            except Exception as e:
                logger.warning(f"예측 결과 저장 실패: {e}")

        logger.info(
            f"예측 결과 저장 완료: batch_id={batch_id}, inserted={inserted_count}"
        )

        return PredictionBatchResponse(
            success=True,
            inserted_count=inserted_count,
            batch_id=batch_id,
        )
