"""Intent Classifier - AI 기반 질문 의도 분류"""

import json
import logging

from src.shared.ai_client import AIClient

from .schemas import IntentClassificationResult, QueryIntent

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM_PROMPT = """당신은 부동산 관련 질문의 의도를 분류하는 전문가입니다.
사용자 질문을 분석하여 의도를 분류해주세요.

## 가능한 의도 (Intent)
- price_inquiry: 현재 또는 과거 시세/가격 조회 질문
- forecast: 미래 가격 예측, 전망 질문
- comparison: 지역 간 또는 시기 간 비교 질문
- news_analysis: 뉴스, 정책, 이슈가 시세에 미치는 영향 분석
- trend_analysis: 가격 추세, 변화 흐름 분석 질문
- investment: 투자 판단, 매수/매도 타이밍 관련 질문
- general: 일반 정보, 지역 특성 등 기타 질문

## 분류 규칙
1. primary_intent: 가장 핵심적인 의도 하나
2. secondary_intents: 추가로 포함된 의도들 (없으면 빈 배열)
3. confidence: 분류 확신도 (0.0 ~ 1.0)

## 예시

질문: "청량리 아파트 시세가 얼마인가요?"
{"primary_intent": "price_inquiry", "secondary_intents": [], "confidence": 0.95}

질문: "GTX-C 개통이 이문동 시세에 어떤 영향을 줄까요?"
{"primary_intent": "news_analysis", "secondary_intents": ["forecast"], "confidence": 0.90}

질문: "청량리와 이문동 중 어디가 더 오를까요?"
{"primary_intent": "comparison", "secondary_intents": ["forecast"], "confidence": 0.92}

질문: "최근 1년간 동대문구 아파트 가격 추이가 어떻게 되나요?"
{"primary_intent": "trend_analysis", "secondary_intents": [], "confidence": 0.93}

질문: "지금이 매수 타이밍인가요?"
{"primary_intent": "investment", "secondary_intents": ["forecast"], "confidence": 0.88}

반드시 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요."""


class IntentClassifier:
    """AI 기반 질문 의도 분류기"""

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def classify(self, query: str) -> IntentClassificationResult:
        """질문의 의도를 분류합니다.

        Args:
            query: 사용자 질문

        Returns:
            IntentClassificationResult: 분류 결과
        """
        try:
            response = await self.ai_client.generate(
                system_prompt=CLASSIFIER_SYSTEM_PROMPT,
                user_message=f"질문: {query}",
                temperature=0.1,  # 일관된 분류를 위해 낮은 temperature
                max_tokens=256,
            )

            # JSON 파싱
            result = self._parse_response(response)
            logger.debug(f"Intent classification: {query[:50]}... -> {result.primary_intent}")
            return result

        except Exception as e:
            logger.warning(f"Intent classification failed, using fallback: {e}")
            return self._fallback_classification(query)

    def _parse_response(self, response: str) -> IntentClassificationResult:
        """AI 응답을 파싱합니다."""
        # JSON 블록 추출 (```json ... ``` 형식도 처리)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        data = json.loads(cleaned)

        return IntentClassificationResult(
            primary_intent=QueryIntent(data["primary_intent"]),
            secondary_intents=[QueryIntent(i) for i in data.get("secondary_intents", [])],
            confidence=data.get("confidence", 0.8),
        )

    def _fallback_classification(self, query: str) -> IntentClassificationResult:
        """AI 분류 실패 시 규칙 기반 폴백"""
        query_lower = query.lower()

        # 예측/전망 키워드
        if any(kw in query for kw in ["예측", "전망", "예상", "앞으로", "향후", "될까", "오를까", "내릴까"]):
            return IntentClassificationResult(
                primary_intent=QueryIntent.FORECAST,
                secondary_intents=[],
                confidence=0.7,
            )

        # 비교 키워드
        if any(kw in query for kw in ["비교", "vs", "어디가", "뭐가", "중에서", "보다"]):
            return IntentClassificationResult(
                primary_intent=QueryIntent.COMPARISON,
                secondary_intents=[],
                confidence=0.7,
            )

        # 뉴스/이슈 키워드
        if any(kw in query for kw in ["GTX", "재개발", "뉴타운", "정책", "규제", "영향", "효과"]):
            return IntentClassificationResult(
                primary_intent=QueryIntent.NEWS_ANALYSIS,
                secondary_intents=[],
                confidence=0.7,
            )

        # 시세 조회 키워드
        if any(kw in query for kw in ["시세", "가격", "얼마", "매매가", "전세가"]):
            return IntentClassificationResult(
                primary_intent=QueryIntent.PRICE_INQUIRY,
                secondary_intents=[],
                confidence=0.7,
            )

        # 추세 키워드
        if any(kw in query for kw in ["추세", "추이", "흐름", "동향", "변화"]):
            return IntentClassificationResult(
                primary_intent=QueryIntent.TREND_ANALYSIS,
                secondary_intents=[],
                confidence=0.7,
            )

        # 투자 키워드
        if any(kw in query for kw in ["투자", "매수", "매도", "타이밍", "살까", "팔까"]):
            return IntentClassificationResult(
                primary_intent=QueryIntent.INVESTMENT,
                secondary_intents=[],
                confidence=0.7,
            )

        # 기본값
        return IntentClassificationResult(
            primary_intent=QueryIntent.GENERAL,
            secondary_intents=[],
            confidence=0.5,
        )
