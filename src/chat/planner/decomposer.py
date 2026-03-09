"""Query Decomposer - 복합 질문 분해 및 엔티티 추출"""

import logging
import re
from typing import Any

from src.config import settings
from src.shared.ai_client import AIClient
from src.shared.keyword_config import get_keyword_config

from .schemas import ExtractedEntities, QueryIntent, SubQuery

logger = logging.getLogger(__name__)


class EntityExtractor:
    """질문에서 엔티티(지역, 키워드, 시간 등)를 추출
    
    하이브리드 방식 지원:
    - Stage 1: 단순 매칭 (keywords.yaml)
    - Stage 2: NLP 형태소 분석 (선택)
    - Stage 3: AI 맥락 이해 (선택)
    """

    # 동대문구 세부 지역
    REGIONS = [
        "동대문구",
        "청량리",
        "이문동",
        "이문",
        "휘경동",
        "휘경",
        "전농동",
        "전농",
        "답십리",
        "장안동",
        "장안",
        "용두동",
        "용두",
        "제기동",
        "제기",
        "신설동",
        "신설",
        "회기동",
        "회기",
    ]

    def __init__(self, ai_client: AIClient | None = None):
        """
        Args:
            ai_client: AI 클라이언트 (AI 추출 사용 시 필수)
        """
        keyword_config = get_keyword_config()
        self.KEYWORDS = keyword_config.get_all_keywords()
        
        self.KEYWORDS.extend([
            "역세권",
            "전세",
            "월세",
            "매매",
            "실거래",
            "호가",
        ])
        
        # 하이브리드 추출기 초기화 (선택적)
        self.hybrid_extractor = None
        if settings.enable_nlp_extraction or settings.enable_ai_extraction:
            try:
                from src.chat.extractors import HybridKeywordExtractor
                self.hybrid_extractor = HybridKeywordExtractor(
                    ai_client=ai_client,
                    enable_nlp=settings.enable_nlp_extraction,
                    enable_ai=settings.enable_ai_extraction,
                    ai_min_confidence=settings.ai_extraction_min_confidence,
                )
                logger.info(
                    f"하이브리드 추출기 활성화: "
                    f"NLP={settings.enable_nlp_extraction}, "
                    f"AI={settings.enable_ai_extraction}"
                )
            except ImportError as e:
                logger.warning(
                    f"하이브리드 추출기 로드 실패: {e}. "
                    f"단순 매칭만 사용합니다."
                )
            except Exception as e:
                logger.error(f"하이브리드 추출기 초기화 실패: {e}")

    # 시간 표현 패턴
    TIME_PATTERNS = [
        (r"(\d{4})년", "year"),
        (r"(\d+)개월", "months"),
        (r"(\d+)년", "years"),
        (r"(내년|올해|작년|재작년)", "relative_year"),
        (r"(최근|요즘|지금|현재)", "recent"),
        (r"(상반기|하반기)", "half_year"),
        (r"(\d+)분기", "quarter"),
    ]

    # 부동산 유형
    PROPERTY_TYPES = [
        "아파트",
        "빌라",
        "오피스텔",
        "주택",
        "단독주택",
        "다세대",
        "다가구",
        "상가",
        "토지",
    ]

    async def extract(self, query: str) -> ExtractedEntities:
        """질문에서 엔티티를 추출합니다.
        
        하이브리드 추출기가 활성화된 경우 NLP/AI 기반 추출 사용
        """
        # 기본 추출 (지역, 시간, 부동산 유형)
        regions = self._find_regions(query)
        time_expressions = self._find_time_expressions(query)
        property_types = self._find_property_types(query)
        
        # 키워드 추출 (하이브리드 또는 단순)
        keywords = await self._extract_keywords(query)
        
        return ExtractedEntities(
            regions=regions,
            keywords=keywords,
            time_expressions=time_expressions,
            property_types=property_types,
        )
    
    async def _extract_keywords(self, query: str) -> list[str]:
        """키워드 추출 (하이브리드 또는 단순)
        
        Args:
            query: 사용자 질문
            
        Returns:
            추출된 키워드 목록
        """
        # 하이브리드 추출기 사용 가능 시
        if self.hybrid_extractor:
            try:
                result = await self.hybrid_extractor.extract(query)
                keywords = result.get("keywords", [])
                logger.debug(
                    f"하이브리드 추출: {len(keywords)}개 "
                    f"(신뢰도: {result.get('confidence', 0):.2f})"
                )
                return keywords
            except Exception as e:
                logger.error(f"하이브리드 추출 실패, 단순 매칭으로 대체: {e}")
        
        # 단순 매칭 (폴백)
        return self._find_keywords(query)

    def _find_regions(self, query: str) -> list[str]:
        """지역명 추출"""
        found = []
        for region in self.REGIONS:
            if region in query:
                found.append(region)
        return list(set(found))

    def _find_keywords(self, query: str) -> list[str]:
        """키워드 추출"""
        found = []
        query_upper = query.upper()
        for keyword in self.KEYWORDS:
            if keyword.upper() in query_upper:
                found.append(keyword)
        return list(set(found))

    def _find_time_expressions(self, query: str) -> list[str]:
        """시간 표현 추출"""
        found = []
        for pattern, _ in self.TIME_PATTERNS:
            matches = re.findall(pattern, query)
            found.extend(matches)
        return found

    def _find_property_types(self, query: str) -> list[str]:
        """부동산 유형 추출"""
        found = []
        for prop_type in self.PROPERTY_TYPES:
            if prop_type in query:
                found.append(prop_type)
        return list(set(found))


class QueryDecomposer:
    """복합 질문을 하위 질문으로 분해"""

    def __init__(self, ai_client: AIClient | None = None):
        """
        Args:
            ai_client: AI 클라이언트 (하이브리드 추출 사용 시)
        """
        self.extractor = EntityExtractor(ai_client=ai_client)

    def decompose(
        self,
        query: str,
        intents: list[QueryIntent],
        entities: ExtractedEntities | None = None,
    ) -> list[SubQuery]:
        """질문을 하위 질문으로 분해합니다.

        Args:
            query: 원본 질문
            intents: 분류된 의도들
            entities: 추출된 엔티티 (없으면 자동 추출)

        Returns:
            list[SubQuery]: 분해된 하위 질문들
        """
        if entities is None:
            entities = self.extractor.extract(query)

        sub_queries: list[SubQuery] = []

        # 비교 의도 + 다중 지역 → 지역별 분리
        if QueryIntent.COMPARISON in intents and len(entities.regions) > 1:
            sub_queries.extend(self._decompose_comparison(query, entities))

        # 뉴스 분석 의도 + 키워드 → 키워드별 검색
        elif QueryIntent.NEWS_ANALYSIS in intents and entities.keywords:
            sub_queries.extend(self._decompose_news_analysis(query, entities))

        # 예측 의도 + 다중 지역
        elif QueryIntent.FORECAST in intents and len(entities.regions) > 1:
            sub_queries.extend(self._decompose_forecast_multi_region(query, entities))

        # 추세 분석 + 예측 조합
        elif QueryIntent.TREND_ANALYSIS in intents and QueryIntent.FORECAST in intents:
            sub_queries.extend(self._decompose_trend_forecast(query, entities))

        # 단순 질문 - 분해 없이 원본 그대로
        if not sub_queries:
            primary_intent = intents[0] if intents else QueryIntent.GENERAL
            sub_queries.append(
                SubQuery(
                    intent=primary_intent,
                    query_text=query,
                    region=entities.regions[0] if entities.regions else None,
                    keywords=entities.keywords,
                    priority=1,
                )
            )

        return sub_queries

    def _decompose_comparison(
        self, query: str, entities: ExtractedEntities
    ) -> list[SubQuery]:
        """비교 질문 분해"""
        sub_queries = []

        # 각 지역별 예측 쿼리 생성
        for idx, region in enumerate(entities.regions):
            sub_queries.append(
                SubQuery(
                    intent=QueryIntent.FORECAST,
                    query_text=f"{region} 부동산 전망",
                    region=region,
                    keywords=entities.keywords,
                    priority=idx + 1,
                )
            )

        # 비교 집계 쿼리 추가
        sub_queries.append(
            SubQuery(
                intent=QueryIntent.COMPARISON,
                query_text=query,
                region=None,
                keywords=entities.keywords,
                priority=len(entities.regions) + 1,
            )
        )

        return sub_queries

    def _decompose_news_analysis(
        self, query: str, entities: ExtractedEntities
    ) -> list[SubQuery]:
        """뉴스 분석 질문 분해"""
        sub_queries = []
        region = entities.regions[0] if entities.regions else "동대문구"

        # 키워드별 뉴스 검색
        for idx, keyword in enumerate(entities.keywords):
            sub_queries.append(
                SubQuery(
                    intent=QueryIntent.NEWS_ANALYSIS,
                    query_text=f"{keyword} 관련 뉴스",
                    region=region,
                    keywords=[keyword],
                    priority=idx + 1,
                )
            )

        # 예측도 함께 필요하면 추가
        sub_queries.append(
            SubQuery(
                intent=QueryIntent.FORECAST,
                query_text=f"{region} 가격 전망",
                region=region,
                keywords=entities.keywords,
                priority=len(entities.keywords) + 1,
            )
        )

        return sub_queries

    def _decompose_forecast_multi_region(
        self, query: str, entities: ExtractedEntities
    ) -> list[SubQuery]:
        """다중 지역 예측 질문 분해"""
        sub_queries = []

        for idx, region in enumerate(entities.regions):
            sub_queries.append(
                SubQuery(
                    intent=QueryIntent.FORECAST,
                    query_text=f"{region} 부동산 가격 예측",
                    region=region,
                    keywords=entities.keywords,
                    priority=idx + 1,
                )
            )

        return sub_queries

    def _decompose_trend_forecast(
        self, query: str, entities: ExtractedEntities
    ) -> list[SubQuery]:
        """추세 + 예측 조합 질문 분해"""
        region = entities.regions[0] if entities.regions else "동대문구"

        return [
            SubQuery(
                intent=QueryIntent.TREND_ANALYSIS,
                query_text=f"{region} 최근 시세 추이",
                region=region,
                keywords=entities.keywords,
                priority=1,
            ),
            SubQuery(
                intent=QueryIntent.FORECAST,
                query_text=f"{region} 향후 가격 전망",
                region=region,
                keywords=entities.keywords,
                priority=2,
            ),
        ]

    def is_simple_query(self, sub_queries: list[SubQuery]) -> bool:
        """단순 쿼리인지 판단합니다.

        단순 쿼리: 하위 질문이 1개이고, 특별한 분해가 필요 없는 경우
        """
        return len(sub_queries) == 1
