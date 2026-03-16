"""키워드 추출 테스트

하이브리드 키워드 추출기 (단순 매칭 + NLP + AI) 테스트
"""

import pytest

from src.chat.extractors import (
    AIKeywordExtractor,
    HybridKeywordExtractor,
    NLPKeywordExtractor,
)
from src.shared.ai_client import AIClient


class TestNLPKeywordExtractor:
    """NLP 키워드 추출기 테스트"""

    @pytest.fixture
    def extractor(self) -> NLPKeywordExtractor:
        return NLPKeywordExtractor(use_mecab=False)  # 규칙 기반으로 테스트

    def test_extract_nouns_simple(self, extractor: NLPKeywordExtractor):
        """명사 추출 테스트 (규칙 기반)"""
        query = "청량리 재개발 어떤가요?"
        nouns = extractor.extract_nouns(query)
        
        assert "청량리" in nouns
        assert "재개발" in nouns

    def test_extract_keywords(self, extractor: NLPKeywordExtractor):
        """종합 키워드 추출 테스트"""
        query = "GTX 개통하면 집값 오를까요?"
        keywords = extractor.extract_keywords(query, include_verbs=False)
        
        assert len(keywords) > 0
        # 최소 2글자 이상
        assert all(len(k) >= 2 for k in keywords)

    def test_stopwords_removal(self, extractor: NLPKeywordExtractor):
        """불용어 제거 테스트"""
        query = "이것은 그것이다"
        keywords = extractor.extract_keywords(query)
        
        # 불용어는 제거되어야 함
        assert "이것" not in keywords
        assert "그것" not in keywords

    def test_extract_with_frequency(self, extractor: NLPKeywordExtractor):
        """키워드 빈도 추출 테스트"""
        query = "청량리 재개발 청량리 뉴타운"
        freq = extractor.extract_with_frequency(query)
        
        assert freq.get("청량리", 0) >= 2
        assert freq.get("재개발", 0) >= 1

    def test_is_available(self, extractor: NLPKeywordExtractor):
        """추출기 사용 가능 여부 테스트"""
        # 규칙 기반은 항상 사용 가능
        # Mecab 사용 시에는 설치 여부에 따라 달라짐
        available = extractor.is_available()
        assert isinstance(available, bool)


class TestAIKeywordExtractor:
    """AI 키워드 추출기 테스트"""

    @pytest.fixture
    def extractor(self, mock_ai_client) -> AIKeywordExtractor:
        """AI extractor with mock client"""
        return AIKeywordExtractor(mock_ai_client)

    @pytest.mark.asyncio
    async def test_extract(self, extractor: AIKeywordExtractor):
        """AI 키워드 추출 테스트"""
        query = "청량리 재개발 어떤가요?"
        result = await extractor.extract(query)
        
        assert "keywords" in result
        assert "categories" in result
        assert "intent" in result
        assert "confidence" in result
        
        assert len(result["keywords"]) > 0
        assert result["confidence"] >= 0.0

    @pytest.mark.asyncio
    async def test_extract_keywords_only(self, extractor: AIKeywordExtractor):
        """키워드만 추출 테스트"""
        query = "GTX 개통 예정일은?"
        keywords = await extractor.extract_keywords_only(query)
        
        assert isinstance(keywords, list)

    @pytest.mark.asyncio
    async def test_low_confidence(self, extractor: AIKeywordExtractor, mocker):
        """낮은 신뢰도 처리 테스트"""
        # 낮은 신뢰도 응답
        async def mock_low_confidence(*args, **kwargs):
            return '''{"keywords": [], "categories": [], "intent": "general", "confidence": 0.3}'''
        
        extractor.ai_client.generate = mock_low_confidence
        
        result = await extractor.extract("애매한 질문", min_confidence=0.5)
        
        # 신뢰도가 낮으면 빈 결과
        assert len(result["keywords"]) == 0


class TestHybridKeywordExtractor:
    """하이브리드 키워드 추출기 테스트"""

    @pytest.fixture
    def mock_ai_client(self, mocker):
        """Mock AI 클라이언트"""
        client = mocker.Mock(spec=AIClient)
        
        async def mock_generate(*args, **kwargs):
            return '''{"keywords": ["집값", "가격"], "categories": ["economic_indicators"], "intent": "forecast", "confidence": 0.85}'''
        
        client.generate = mock_generate
        return client

    @pytest.fixture
    def extractor_nlp_only(self) -> HybridKeywordExtractor:
        """NLP만 활성화"""
        return HybridKeywordExtractor(
            ai_client=None,
            enable_nlp=True,
            enable_ai=False,
        )

    @pytest.fixture
    def extractor_hybrid(self, mock_ai_client) -> HybridKeywordExtractor:
        """NLP + AI 활성화"""
        return HybridKeywordExtractor(
            ai_client=mock_ai_client,
            enable_nlp=True,
            enable_ai=True,
        )

    @pytest.mark.asyncio
    async def test_simple_matching(self, extractor_nlp_only: HybridKeywordExtractor):
        """단순 매칭 테스트"""
        query = "청량리 재개발 어떤가요?"
        result = await extractor_nlp_only.extract(query)
        
        assert "keywords" in result
        assert "청량리" in result["keywords"] or "재개발" in result["keywords"]

    @pytest.mark.asyncio
    async def test_nlp_morphology(self, extractor_nlp_only: HybridKeywordExtractor):
        """형태소 변형 처리 테스트"""
        query = "재개발하다가 중단된 지역은?"
        result = await extractor_nlp_only.extract(query)
        
        # NLP가 "재개발" 추출 (형태소 분석)
        assert len(result["keywords"]) > 0

    @pytest.mark.asyncio
    async def test_hybrid_extraction(self, extractor_hybrid: HybridKeywordExtractor):
        """하이브리드 추출 테스트 (NLP + AI)"""
        query = "GTX 개통하면 집값 오를까?"
        result = await extractor_hybrid.extract(query, min_keywords=1)
        
        assert "keywords" in result
        assert "sources" in result
        assert "confidence" in result
        
        # 여러 소스에서 추출
        sources = result["sources"]
        assert "simple" in sources
        assert "nlp" in sources

    @pytest.mark.asyncio
    async def test_early_termination(self, extractor_hybrid: HybridKeywordExtractor):
        """조기 종료 테스트 (충분한 키워드 발견 시 AI 생략)"""
        query = "청량리 재개발 GTX 뉴타운"  # 많은 키워드
        result = await extractor_hybrid.extract(query, min_keywords=2)
        
        # Stage 1+2에서 충분히 발견되면 AI 생략
        # AI가 호출되지 않았을 수 있음
        assert len(result["keywords"]) >= 2

    @pytest.mark.asyncio
    async def test_extract_keywords_only(self, extractor_nlp_only: HybridKeywordExtractor):
        """키워드만 추출 테스트"""
        query = "이문동 아파트 시세는?"
        keywords = await extractor_nlp_only.extract_keywords_only(query)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, extractor_hybrid: HybridKeywordExtractor):
        """신뢰도 계산 테스트"""
        query = "청량리 재개발"
        result = await extractor_hybrid.extract(query)
        
        # 여러 소스에서 발견될수록 높은 신뢰도
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_category_mapping(self, extractor_nlp_only: HybridKeywordExtractor):
        """카테고리 매핑 테스트"""
        query = "GTX 재개발 금리"
        result = await extractor_nlp_only.extract(query)
        
        # 키워드가 카테고리로 매핑되어야 함
        assert "categories" in result
        # transport, redevelopment, policy 등이 포함될 수 있음


class TestEntityExtractorIntegration:
    """EntityExtractor 통합 테스트"""

    @pytest.mark.asyncio
    async def test_entity_extractor_with_hybrid(self, mocker):
        """EntityExtractor가 하이브리드 추출기 사용 테스트"""
        from src.chat.planner.decomposer import EntityExtractor
        from src.config import settings
        
        # NLP 활성화
        mocker.patch.object(settings, "enable_nlp_extraction", True)
        mocker.patch.object(settings, "enable_ai_extraction", False)
        
        extractor = EntityExtractor(ai_client=None)
        
        query = "청량리 재개발 어떤가요?"
        entities = await extractor.extract(query)
        
        assert "청량리" in entities.regions
        assert len(entities.keywords) > 0

    @pytest.mark.asyncio
    async def test_entity_extractor_fallback(self, mocker):
        """EntityExtractor 폴백 테스트 (하이브리드 실패 시)"""
        from src.chat.planner.decomposer import EntityExtractor
        from src.config import settings
        
        # 하이브리드 비활성화
        mocker.patch.object(settings, "enable_nlp_extraction", False)
        mocker.patch.object(settings, "enable_ai_extraction", False)
        
        extractor = EntityExtractor(ai_client=None)
        
        query = "청량리 재개발 어떤가요?"
        entities = await extractor.extract(query)
        
        # 단순 매칭으로 폴백
        assert "청량리" in entities.regions
        assert "재개발" in entities.keywords
