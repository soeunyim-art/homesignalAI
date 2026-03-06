import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from supabase import Client

from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """검색된 문서 청크"""

    content: str
    source: str
    score: float
    metadata: dict | None = None


class VectorDBInterface(ABC):
    """Vector DB 인터페이스 (별도 담당자 구현 예정)"""

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[DocumentChunk]:
        """유사도 검색"""
        pass

    @abstractmethod
    async def upsert(
        self,
        documents: list[dict],
        embeddings: list[list[float]],
    ) -> bool:
        """문서 임베딩 저장"""
        pass


class MockVectorDB(VectorDBInterface):
    """개발용 Mock Vector DB"""

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[DocumentChunk]:
        # TODO: 실제 Vector DB 연동 시 교체
        return [
            DocumentChunk(
                content="GTX-C 청량리역 개통 예정으로 동대문구 부동산 시장에 긍정적 영향 전망",
                source="한국경제 2024-12-01",
                score=0.92,
            ),
            DocumentChunk(
                content="이문휘경뉴타운 재개발 사업 속도... 2025년 분양 예정",
                source="매일경제 2024-11-15",
                score=0.88,
            ),
        ]

    async def upsert(
        self,
        documents: list[dict],
        embeddings: list[list[float]],
    ) -> bool:
        return True


class SupabaseVectorDB(VectorDBInterface):
    """Supabase pgvector 기반 Vector DB 구현

    Supabase의 pgvector 확장을 사용하여 벡터 유사도 검색을 수행합니다.
    RPC 함수 `match_news_documents`를 호출하여 코사인 유사도 검색을 실행합니다.
    """

    def __init__(
        self,
        client: Client | None = None,
        embedding_service=None,
    ):
        """
        Args:
            client: Supabase 클라이언트 (None이면 지연 초기화)
            embedding_service: 임베딩 생성 서비스 (None이면 지연 초기화)
        """
        self._client = client
        self._embedding_service = embedding_service

    def _get_client(self) -> Client:
        """Supabase 클라이언트 지연 초기화 (upsert용 service_role)"""
        if self._client is None:
            from src.shared.database import get_supabase_client

            # VectorDB upsert는 INSERT를 수행하므로 service_role 키 사용
            self._client = get_supabase_client(use_service_role=True)
        return self._client

    def _get_embedding_service(self):
        """임베딩 서비스 지연 초기화"""
        if self._embedding_service is None:
            from src.shared.embedding import get_embedding_service

            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[DocumentChunk]:
        """pgvector 코사인 유사도 검색

        Args:
            query: 검색 쿼리 (텍스트)
            top_k: 반환할 최대 문서 수
            filters: 필터 조건 (keywords, date_from, date_to)

        Returns:
            유사도 순으로 정렬된 DocumentChunk 리스트
        """
        try:
            # 1. 쿼리를 임베딩으로 변환
            embedding_service = self._get_embedding_service()
            query_embedding = await embedding_service.generate_embedding(query)

            if not query_embedding or all(v == 0.0 for v in query_embedding):
                logger.warning("빈 쿼리 임베딩 생성됨")
                return []

            # 2. Supabase RPC 함수 호출
            client = self._get_client()

            # RPC 함수 파라미터 구성
            rpc_params = {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "match_threshold": 0.5,  # 최소 유사도 임계값
            }

            # 필터 조건 추가
            if filters:
                if "keywords" in filters:
                    rpc_params["filter_keywords"] = filters["keywords"]
                if "date_from" in filters:
                    rpc_params["filter_date_from"] = filters["date_from"]
                if "date_to" in filters:
                    rpc_params["filter_date_to"] = filters["date_to"]

            result = client.rpc("match_news_documents", rpc_params).execute()

            if not result.data:
                logger.debug(f"검색 결과 없음: query='{query[:50]}...'")
                return []

            # 3. DocumentChunk로 변환
            chunks = []
            for row in result.data:
                chunks.append(
                    DocumentChunk(
                        content=row.get("content") or row.get("title", ""),
                        source=self._format_source(row),
                        score=float(row.get("similarity", 0.0)),
                        metadata={
                            "id": row.get("id"),
                            "url": row.get("url"),
                            "keywords": row.get("keywords", []),
                            "published_at": row.get("published_at"),
                        },
                    )
                )

            logger.info(f"Vector 검색 완료: query='{query[:30]}...', results={len(chunks)}")
            return chunks

        except Exception as e:
            logger.error(f"Vector 검색 실패: {e}")
            # 폴백: Mock 결과 반환
            return await MockVectorDB().search(query, top_k, filters)

    async def upsert(
        self,
        documents: list[dict],
        embeddings: list[list[float]],
    ) -> bool:
        """문서와 임베딩을 news_signals 테이블에 저장

        Args:
            documents: 문서 목록 [{title, content, url, keywords, published_at}, ...]
            embeddings: 각 문서의 임베딩 벡터

        Returns:
            성공 여부
        """
        if len(documents) != len(embeddings):
            logger.error("문서 수와 임베딩 수가 일치하지 않음")
            return False

        try:
            client = self._get_client()

            for doc, embedding in zip(documents, embeddings):
                record = {
                    "title": doc.get("title"),
                    "content": doc.get("content"),
                    "url": doc.get("url"),
                    "keywords": doc.get("keywords", []),
                    "embedding": embedding,
                    "published_at": doc.get("published_at"),
                }

                # URL 기준으로 upsert
                if doc.get("url"):
                    client.table("news_signals").upsert(
                        record, on_conflict="url"
                    ).execute()
                else:
                    client.table("news_signals").insert(record).execute()

            logger.info(f"Vector upsert 완료: {len(documents)} documents")
            return True

        except Exception as e:
            logger.error(f"Vector upsert 실패: {e}")
            return False

    @staticmethod
    def _format_source(row: dict) -> str:
        """출처 문자열 포맷팅"""
        title = row.get("title", "알 수 없음")[:50]
        published_at = row.get("published_at", "")

        if published_at:
            # ISO 형식에서 날짜만 추출
            date_str = str(published_at)[:10]
            return f"{title} ({date_str})"
        return title


# 싱글톤 인스턴스
_vector_db: VectorDBInterface | None = None


def get_vector_db() -> VectorDBInterface:
    """Vector DB 클라이언트 반환

    환경에 따라 적절한 구현체를 반환합니다:
    - Mock: SUPABASE_URL이 placeholder이거나 debug 모드
    - Real: 프로덕션 환경
    """
    global _vector_db

    if _vector_db is not None:
        return _vector_db

    # Mock 조건 확인
    use_mock = (
        settings.debug
        or "placeholder" in settings.supabase_url.lower()
        or "your-" in settings.supabase_url.lower()
        or not settings.openai_api_key  # 임베딩 생성 불가
    )

    if use_mock:
        logger.info("Using MockVectorDB (dev mode)")
        _vector_db = MockVectorDB()
    else:
        logger.info("Using SupabaseVectorDB (production mode)")
        _vector_db = SupabaseVectorDB()

    return _vector_db


def reset_vector_db() -> None:
    """Vector DB 싱글톤 초기화 (테스트용)"""
    global _vector_db
    _vector_db = None
