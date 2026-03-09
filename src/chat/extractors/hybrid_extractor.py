"""하이브리드 키워드 추출기

단순 매칭 + NLP + AI를 조합한 고도화된 키워드 추출
"""

import logging
from typing import Any

from src.shared.ai_client import AIClient
from src.shared.keyword_config import get_keyword_config

from .ai_extractor import AIKeywordExtractor
from .nlp_extractor import NLPKeywordExtractor

logger = logging.getLogger(__name__)


class HybridKeywordExtractor:
    """하이브리드 키워드 추출기
    
    3단계 파이프라인으로 키워드 추출:
    1. Stage 1: 단순 매칭 (keywords.yaml 기반)
    2. Stage 2: NLP 분석 (형태소 분석)
    3. Stage 3: AI 검증 (맥락 이해) - 필요시만
    """

    def __init__(
        self,
        ai_client: AIClient | None = None,
        enable_nlp: bool = True,
        enable_ai: bool = False,
        ai_min_confidence: float = 0.5,
    ):
        """
        Args:
            ai_client: AI API 클라이언트 (AI 추출 사용 시 필수)
            enable_nlp: NLP 추출 활성화 여부
            enable_ai: AI 추출 활성화 여부
            ai_min_confidence: AI 추출 최소 신뢰도
        """
        self.keyword_config = get_keyword_config()
        self.all_keywords = set(self.keyword_config.get_all_keywords())
        
        self.enable_nlp = enable_nlp
        self.enable_ai = enable_ai and ai_client is not None
        self.ai_min_confidence = ai_min_confidence
        
        # NLP 추출기 초기화
        self.nlp_extractor = NLPKeywordExtractor() if enable_nlp else None
        
        # AI 추출기 초기화
        self.ai_extractor = (
            AIKeywordExtractor(ai_client) if self.enable_ai else None
        )
        
        logger.info(
            f"하이브리드 추출기 초기화: "
            f"NLP={enable_nlp}, AI={self.enable_ai}"
        )

    async def extract(
        self, 
        query: str,
        min_keywords: int = 2,
    ) -> dict[str, Any]:
        """하이브리드 키워드 추출
        
        Args:
            query: 사용자 질문
            min_keywords: Stage 1+2에서 이 개수 이상 발견 시 AI 생략
            
        Returns:
            {
                "keywords": [...],
                "categories": [...],
                "sources": {
                    "simple": [...],
                    "nlp": [...],
                    "ai": [...]
                },
                "confidence": 0.0-1.0
            }
        """
        sources: dict[str, list[str]] = {
            "simple": [],
            "nlp": [],
            "ai": [],
        }
        
        # Stage 1: 단순 매칭
        simple_keywords = self._simple_match(query)
        sources["simple"] = simple_keywords
        logger.debug(f"Stage 1 (단순): {len(simple_keywords)}개")
        
        # Stage 2: NLP 분석
        nlp_keywords: list[str] = []
        if self.enable_nlp and self.nlp_extractor:
            nlp_keywords = self._nlp_extract(query)
            sources["nlp"] = nlp_keywords
            logger.debug(f"Stage 2 (NLP): {len(nlp_keywords)}개")
        
        # 조기 종료 체크
        combined = list(set(simple_keywords + nlp_keywords))
        if len(combined) >= min_keywords:
            logger.info(
                f"충분한 키워드 발견 ({len(combined)}개), AI 생략"
            )
            return self._build_result(sources, combined, 0.8)
        
        # Stage 3: AI 검증 (필요시)
        ai_keywords: list[str] = []
        ai_confidence = 0.0
        
        if self.enable_ai and self.ai_extractor:
            logger.debug("Stage 3 (AI) 실행")
            ai_result = await self.ai_extractor.extract(
                query, 
                min_confidence=self.ai_min_confidence
            )
            ai_keywords = ai_result.get("keywords", [])
            ai_confidence = ai_result.get("confidence", 0.0)
            sources["ai"] = ai_keywords
            logger.debug(
                f"Stage 3 (AI): {len(ai_keywords)}개 "
                f"(신뢰도: {ai_confidence:.2f})"
            )
        
        # 최종 병합
        all_keywords = list(set(simple_keywords + nlp_keywords + ai_keywords))
        final_confidence = self._calculate_confidence(sources, ai_confidence)
        
        return self._build_result(sources, all_keywords, final_confidence)

    def _simple_match(self, query: str) -> list[str]:
        """Stage 1: 단순 문자열 매칭
        
        Args:
            query: 사용자 질문
            
        Returns:
            발견된 키워드 목록
        """
        found = []
        query_upper = query.upper()
        
        for keyword in self.all_keywords:
            if keyword.upper() in query_upper:
                found.append(keyword)
        
        return found

    def _nlp_extract(self, query: str) -> list[str]:
        """Stage 2: NLP 형태소 분석
        
        Args:
            query: 사용자 질문
            
        Returns:
            추출된 키워드 목록
        """
        if not self.nlp_extractor:
            return []
        
        try:
            # 명사 + 동사 추출
            keywords = self.nlp_extractor.extract_keywords(
                query, 
                include_verbs=True,
                min_length=2,
            )
            
            # keywords.yaml에 있는 것만 필터링 (선택적)
            # 또는 모든 명사를 키워드로 간주
            # 여기서는 모든 명사를 반환
            return keywords
            
        except Exception as e:
            logger.error(f"NLP 추출 실패: {e}")
            return []

    def _calculate_confidence(
        self, 
        sources: dict[str, list[str]], 
        ai_confidence: float,
    ) -> float:
        """신뢰도 계산
        
        여러 소스에서 발견된 키워드일수록 높은 신뢰도
        
        Args:
            sources: 소스별 키워드 목록
            ai_confidence: AI 추출 신뢰도
            
        Returns:
            최종 신뢰도 (0.0-1.0)
        """
        # 소스 개수
        active_sources = sum(1 for kws in sources.values() if kws)
        
        if active_sources == 0:
            return 0.0
        elif active_sources == 1:
            # 단일 소스
            if sources["ai"]:
                return ai_confidence
            return 0.6
        elif active_sources == 2:
            # 2개 소스 일치
            return 0.8
        else:
            # 3개 소스 모두 일치
            return 0.95

    def _build_result(
        self,
        sources: dict[str, list[str]],
        keywords: list[str],
        confidence: float,
    ) -> dict[str, Any]:
        """결과 딕셔너리 생성
        
        Args:
            sources: 소스별 키워드
            keywords: 최종 키워드 목록
            confidence: 신뢰도
            
        Returns:
            결과 딕셔너리
        """
        # 카테고리 매핑
        categories = self._map_categories(keywords)
        
        return {
            "keywords": keywords,
            "categories": categories,
            "sources": sources,
            "confidence": confidence,
        }

    def _map_categories(self, keywords: list[str]) -> list[str]:
        """키워드를 카테고리로 매핑
        
        Args:
            keywords: 키워드 목록
            
        Returns:
            카테고리 목록
        """
        categories = set()
        
        for category_name, category_obj in self.keyword_config.get_all_categories().items():
            category_keywords = category_obj.all_keywords()
            
            # 키워드가 이 카테고리에 속하는지 확인
            if any(kw in category_keywords for kw in keywords):
                categories.add(category_name)
        
        return list(categories)

    async def extract_keywords_only(self, query: str) -> list[str]:
        """키워드만 추출 (간단한 인터페이스)
        
        Args:
            query: 사용자 질문
            
        Returns:
            추출된 키워드 목록
        """
        result = await self.extract(query)
        return result.get("keywords", [])
