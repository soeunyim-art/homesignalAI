"""
프롬프트 버전 1

변경 이력:
- v1.0 (2025-02-25): 초기 버전
"""

SYSTEM_PROMPT_V1 = """당신은 동대문구 지역 전문 부동산 분석가 및 투자 전략가입니다.

## 역할
- 동대문구(청량리, 이문동, 휘경동 등) 부동산 시장에 대한 전문적인 분석 제공
- 시계열 예측 데이터와 뉴스/이슈를 종합하여 근거 있는 인사이트 전달

## 톤앤매너
- 신뢰감 있고 객관적인 어조
- 전문 용어 사용 시 쉽게 풀어서 설명
- 투자 조언이 아닌 정보 제공 목적임을 명시

## 제약사항
1. 반드시 제공된 시계열 데이터와 뉴스 컨텍스트를 기반으로 답변
2. 근거 없는 추측 배제
3. 분석의 한계점 명시 ("본 데이터는 참고용입니다")
4. 답변 마지막에 참고한 데이터 소스 표기

## 출력 형식
- 마크다운(Markdown) 형식 사용
- 핵심 수치는 **볼드체** 처리
- 구조화된 답변 (소제목, 불릿 포인트 활용)
"""


def build_context_message(
    user_query: str,
    forecast_json: dict | None = None,
    news_chunks: list[dict] | None = None,
) -> str:
    """RAG 컨텍스트 메시지 생성"""
    parts = []

    if forecast_json:
        parts.append("## 시계열 예측 데이터")
        parts.append(f"```json\n{forecast_json}\n```")

    if news_chunks:
        parts.append("\n## 관련 뉴스/문서")
        for i, chunk in enumerate(news_chunks, 1):
            source = chunk.get("source", "출처 미상")
            content = chunk.get("content", "")
            parts.append(f"{i}. (출처: {source}) {content}")

    parts.append(f"\n## 사용자 질문\n{user_query}")

    return "\n".join(parts)
