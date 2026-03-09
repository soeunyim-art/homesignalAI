"""AI 기반 키워드 추출기

GPT/Claude를 사용한 맥락 이해 기반 키워드 추출
"""

import json
import logging
from typing import Any

from src.shared.ai_client import AIClient
from src.shared.exceptions import AIAPIError

logger = logging.getLogger(__name__)


# AI 키워드 추출 프롬프트
KEYWORD_EXTRACTION_PROMPT = """다음 사용자 질문에서 부동산 관련 핵심 키워드를 추출하세요.

질문: {query}

가능한 키워드 카테고리:
- 지역: 청량리, 이문동, 회기동, 동대문구 등
- 교통: GTX, GTX-C, 지하철, 버스, 역세권 등
- 개발: 재개발, 뉴타운, 분양, 입주, 착공 등
- 정책: 금리, 대출, 규제, 청약, 세금 등
- 경제: 집값, 전세가, 매매가, 시세 등
- 사회: 학군, 학교, 공원, 교육환경 등

추출 규칙:
1. 질문의 핵심 의도를 파악하여 관련 키워드만 추출
2. 동의어나 유사어는 대표 키워드로 통일 (예: "아파트 가격" → "집값")
3. 형태소 변형 처리 (예: "재개발하다" → "재개발")
4. 최소 1개, 최대 10개의 키워드 추출

JSON 형식으로 반환:
{{
  "keywords": ["키워드1", "키워드2", ...],
  "categories": ["transport", "redevelopment", ...],
  "intent": "forecast" | "comparison" | "news_analysis" | "general",
  "confidence": 0.0-1.0
}}"""


class AIKeywordExtractor:
    """AI 기반 키워드 추출기
    
    GPT/Claude를 사용하여 사용자 질문의 맥락을 이해하고
    핵심 키워드를 추출합니다.
    """

    def __init__(self, ai_client: AIClient):
        """
        Args:
            ai_client: AI API 클라이언트
        """
        self.ai_client = ai_client

    async def extract(
        self, 
        query: str,
        min_confidence: float = 0.5,
    ) -> dict[str, Any]:
        """AI 기반 키워드 추출
        
        Args:
            query: 사용자 질문
            min_confidence: 최소 신뢰도 (이하면 빈 결과 반환)
            
        Returns:
            {
                "keywords": [...],
                "categories": [...],
                "intent": "...",
                "confidence": 0.0-1.0
            }
        """
        try:
            prompt = KEYWORD_EXTRACTION_PROMPT.format(query=query)
            
            response = await self.ai_client.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # 일관성을 위해 낮은 temperature
                max_tokens=500,
            )
            
            # JSON 파싱
            result = self._parse_response(response)
            
            # 신뢰도 체크
            confidence = result.get("confidence", 0.0)
            if confidence < min_confidence:
                logger.warning(
                    f"AI 추출 신뢰도 낮음: {confidence:.2f} < {min_confidence}"
                )
                return {
                    "keywords": [],
                    "categories": [],
                    "intent": "general",
                    "confidence": confidence,
                }
            
            logger.info(
                f"AI 키워드 추출 완료: {len(result['keywords'])}개 "
                f"(신뢰도: {confidence:.2f})"
            )
            return result
            
        except AIAPIError as e:
            logger.error(f"AI API 오류: {e}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"AI 키워드 추출 실패: {e}")
            return self._empty_result()

    def _parse_response(self, response: str) -> dict[str, Any]:
        """AI 응답 파싱
        
        Args:
            response: AI 응답 텍스트
            
        Returns:
            파싱된 결과 딕셔너리
        """
        try:
            # JSON 블록 추출 (```json ... ``` 또는 {...})
            import re
            
            # 코드 블록에서 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 직접 JSON 찾기
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다")
            
            result = json.loads(json_str)
            
            # 필수 필드 검증
            if "keywords" not in result:
                result["keywords"] = []
            if "categories" not in result:
                result["categories"] = []
            if "intent" not in result:
                result["intent"] = "general"
            if "confidence" not in result:
                result["confidence"] = 0.8  # 기본값
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            logger.debug(f"응답 내용: {response[:200]}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"응답 파싱 실패: {e}")
            return self._empty_result()

    def _empty_result(self) -> dict[str, Any]:
        """빈 결과 반환"""
        return {
            "keywords": [],
            "categories": [],
            "intent": "general",
            "confidence": 0.0,
        }

    async def extract_keywords_only(self, query: str) -> list[str]:
        """키워드만 추출 (간단한 인터페이스)
        
        Args:
            query: 사용자 질문
            
        Returns:
            추출된 키워드 목록
        """
        result = await self.extract(query)
        return result.get("keywords", [])
