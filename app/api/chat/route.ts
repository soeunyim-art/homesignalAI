import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { getRelevantData, buildContextPrompt, calculateStats } from "@/lib/rag-utils";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();

    if (!messages || messages.length === 0) {
      return NextResponse.json(
        { error: "메시지가 필요합니다." },
        { status: 400 }
      );
    }

    // 최신 사용자 메시지 추출
    const userMessage = messages[messages.length - 1].content;

    // RAG: 관련 데이터 검색
    console.log("[RAG] 데이터 검색 시작:", userMessage);
    const relevantData = await getRelevantData(userMessage);
    console.log("[RAG] 검색 완료:", {
      predictions: relevantData.metadata.predictionCount,
      news: relevantData.metadata.newsCount,
      trades: relevantData.metadata.tradeCount,
    });

    // 컨텍스트 프롬프트 구성
    const contextPrompt = buildContextPrompt(relevantData, userMessage);

    // 통계 계산
    const stats = calculateStats(relevantData.predictions || []);

    // Claude API 호출 (컨텍스트 포함)
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-5-20250929",
      max_tokens: 2048,
      messages: [
        {
          role: "user",
          content: contextPrompt,
        },
      ],
      system: `당신은 HomeSignal AI의 부동산 분석 전문가입니다.

**담당 지역**: 서울 동북권 5개 구
- 동대문구 (이문·장안·답십리 재개발)
- 성북구 (길음·장위 뉴타운)
- 중랑구 (면목·신내 개발)
- 강북구 (미아·수유 재정비)
- 도봉구 (창동 GTX-C)

**역할**:
- 아파트 매매가 예측 및 시장 분석 제공
- 투자 전략 및 리스크 평가
- 부동산 뉴스 및 트렌드 분석
- 친절하고 전문적인 톤으로 답변

**답변 원칙**:
1. 정확한 데이터 기반 답변
2. 명확하고 이해하기 쉬운 설명
3. 투자 결정은 사용자 책임임을 안내
4. 데이터가 없을 경우 솔직하게 고지`,
    });

    const content = response.content[0];
    const text = content.type === "text" ? content.text : "";

    return NextResponse.json({
      message: text,
      usage: {
        inputTokens: response.usage.input_tokens,
        outputTokens: response.usage.output_tokens,
      },
    });
  } catch (error: any) {
    console.error("Claude API Error:", error);

    // API 키 오류 처리
    if (error.status === 401) {
      return NextResponse.json(
        { error: "API 키가 유효하지 않습니다." },
        { status: 401 }
      );
    }

    // Rate limit 오류 처리
    if (error.status === 429) {
      return NextResponse.json(
        { error: "API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요." },
        { status: 429 }
      );
    }

    return NextResponse.json(
      { error: error.message || "챗봇 응답 생성 중 오류가 발생했습니다." },
      { status: 500 }
    );
  }
}
