"""
임베딩 생성 서비스 - OpenAI Embedding API

뉴스 텍스트를 벡터로 변환하여 Vector DB에서 유사도 검색 지원
"""

import logging
from typing import Any

import httpx
import openai

from src.config import settings

from .exceptions import AIAPIError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """OpenAI Embedding API 클라이언트"""

    def __init__(self):
        self._client: openai.AsyncOpenAI | None = None

    def _get_client(self) -> openai.AsyncOpenAI:
        """OpenAI 클라이언트 지연 초기화"""
        if self._client is None:
            self._client = openai.AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=httpx.Timeout(settings.ai_api_timeout),
            )
        return self._client

    async def generate_embedding(self, text: str) -> list[float]:
        """
        단일 텍스트에 대한 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            1536차원 벡터 (text-embedding-3-small 기준)

        Raises:
            AIAPIError: API 호출 실패 시
        """
        if not text or not text.strip():
            logger.warning("빈 텍스트에 대한 임베딩 요청")
            return [0.0] * settings.embedding_dimensions

        try:
            client = self._get_client()
            response = await client.embeddings.create(
                model=settings.embedding_model,
                input=text.strip(),
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise AIAPIError(
                message="임베딩 생성에 실패했습니다",
                details={"error": str(e), "text_length": len(text)},
            )

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        여러 텍스트에 대한 배치 임베딩 생성

        Args:
            texts: 임베딩할 텍스트 목록
            batch_size: 한 번에 처리할 텍스트 수 (OpenAI 제한 고려)

        Returns:
            각 텍스트에 대한 임베딩 벡터 목록

        Raises:
            AIAPIError: API 호출 실패 시
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        try:
            client = self._get_client()

            # 배치 단위로 처리
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]

                # 빈 텍스트 처리
                processed_texts = [
                    t.strip() if t and t.strip() else " " for t in batch_texts
                ]

                response = await client.embeddings.create(
                    model=settings.embedding_model,
                    input=processed_texts,
                )

                # 응답 순서대로 임베딩 추출
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(
                    f"임베딩 배치 처리: {i + len(batch_texts)}/{len(texts)} 완료"
                )

            return all_embeddings

        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            raise AIAPIError(
                message="배치 임베딩 생성에 실패했습니다",
                details={"error": str(e), "total_texts": len(texts)},
            )

    async def generate_embedding_for_news(
        self,
        title: str,
        content: str | None = None,
    ) -> list[float]:
        """
        뉴스 제목과 본문을 결합하여 임베딩 생성

        Args:
            title: 뉴스 제목
            content: 뉴스 본문 (선택)

        Returns:
            결합된 텍스트의 임베딩 벡터
        """
        # 제목과 본문 결합
        if content:
            # 본문이 너무 길면 앞부분만 사용 (토큰 제한 고려)
            max_content_length = 2000
            truncated_content = (
                content[:max_content_length] + "..."
                if len(content) > max_content_length
                else content
            )
            combined_text = f"{title}\n\n{truncated_content}"
        else:
            combined_text = title

        return await self.generate_embedding(combined_text)


# 싱글톤 인스턴스
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """임베딩 서비스 싱글톤 반환"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
