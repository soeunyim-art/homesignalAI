import { supabase } from "@/lib/supabase";

/**
 * 사용자 질문 의도 분석
 */
export function analyzeUserIntent(query: string): {
  type: "prediction" | "news" | "comparison" | "trend" | "general";
  dong?: string;
  gu?: string;
  timeframe?: "1m" | "2m" | "3m";
} {
  const lowerQuery = query.toLowerCase();

  // 동 이름 추출
  const dongMatch = lowerQuery.match(/([\w가-힣]+동)/);
  const dong = dongMatch ? dongMatch[1] : undefined;

  // 구 이름 추출
  const guMatch = lowerQuery.match(/(동대문구|성북구|중랑구|강북구|도봉구)/);
  const gu = guMatch ? guMatch[1] : undefined;

  // 의도 분류
  if (lowerQuery.includes("예측") || lowerQuery.includes("전망") || lowerQuery.includes("오를") || lowerQuery.includes("떨어질")) {
    return { type: "prediction", dong, gu };
  }

  if (lowerQuery.includes("뉴스") || lowerQuery.includes("소식") || lowerQuery.includes("기사")) {
    return { type: "news", dong, gu };
  }

  if (lowerQuery.includes("비교") || lowerQuery.includes("차이") || lowerQuery.includes("vs")) {
    return { type: "comparison", dong, gu };
  }

  if (lowerQuery.includes("상승") || lowerQuery.includes("하락") || lowerQuery.includes("변화") || lowerQuery.includes("트렌드")) {
    return { type: "trend", dong, gu };
  }

  return { type: "general", dong, gu };
}

/**
 * 예측 데이터 조회
 */
export async function getPredictionData(dong?: string, gu?: string) {
  let query = supabase
    .from("predictions")
    .select("*")
    .order("run_date", { ascending: false });

  if (dong) {
    query = query.ilike("dong", `%${dong}%`);
  }

  const { data, error } = await query.limit(dong ? 1 : 50);

  if (error) {
    console.error("Prediction query error:", error);
    return null;
  }

  return data;
}

/**
 * 뉴스 시그널 조회
 */
export async function getNewsSignals(limit: number = 10) {
  const { data, error } = await supabase
    .from("news_signals")
    .select("*")
    .order("published_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("News query error:", error);
    return null;
  }

  return data;
}

/**
 * 거래 통계 조회
 */
export async function getTradeStats(dong?: string) {
  let query = supabase
    .from("apt_trade")
    .select("deal_year, deal_month, price_10k, area, dong")
    .gte("deal_year", 2025)
    .order("deal_year", { ascending: false })
    .order("deal_month", { ascending: false });

  if (dong) {
    query = query.ilike("dong", `%${dong}%`);
  }

  const { data, error } = await query.limit(100);

  if (error) {
    console.error("Trade stats query error:", error);
    return null;
  }

  return data;
}

/**
 * 종합 데이터 검색 (RAG)
 */
export async function getRelevantData(query: string) {
  const intent = analyzeUserIntent(query);

  // 병렬로 데이터 조회
  const [predictions, news, trades] = await Promise.all([
    getPredictionData(intent.dong, intent.gu),
    getNewsSignals(5),
    getTradeStats(intent.dong),
  ]);

  return {
    intent,
    predictions,
    news,
    trades,
    metadata: {
      predictionCount: predictions?.length || 0,
      newsCount: news?.length || 0,
      tradeCount: trades?.length || 0,
    },
  };
}

/**
 * 컨텍스트 프롬프트 구성
 */
export function buildContextPrompt(data: any, userQuery: string): string {
  const { intent, predictions, news, trades } = data;

  let contextSections: string[] = [];

  // 1. 기본 정보
  contextSections.push(`# 사용자 질문\n${userQuery}\n`);
  contextSections.push(`# 질문 유형: ${intent.type}`);
  if (intent.dong) contextSections.push(`# 검색 동: ${intent.dong}`);
  if (intent.gu) contextSections.push(`# 검색 구: ${intent.gu}`);

  // 2. 예측 데이터
  if (predictions && predictions.length > 0) {
    contextSections.push("\n## 📊 AI 예측 데이터 (2026-03-20 기준)\n");

    if (intent.dong && predictions.length === 1) {
      // 특정 동 상세 정보
      const p = predictions[0];
      contextSections.push(`### ${p.dong} 상세 예측`);
      contextSections.push(`- 현재 평균가: ${(p.current_price_10k / 10000).toFixed(1)}억원`);
      contextSections.push(`- 1개월 후: ${(p.pred_1m_10k / 10000).toFixed(1)}억원 (${p.change_1m_pct > 0 ? '+' : ''}${p.change_1m_pct?.toFixed(1)}%)`);
      contextSections.push(`- 2개월 후: ${(p.pred_2m_10k / 10000).toFixed(1)}억원 (${p.change_2m_pct > 0 ? '+' : ''}${p.change_2m_pct?.toFixed(1)}%)`);
      contextSections.push(`- 3개월 후: ${(p.pred_3m_10k / 10000).toFixed(1)}억원 (${p.change_3m_pct > 0 ? '+' : ''}${p.change_3m_pct?.toFixed(1)}%)`);
    } else {
      // 전체 동 요약
      const avgPrice = predictions.reduce((s: number, p: any) => s + p.current_price_10k, 0) / predictions.length;
      const avgChange1m = predictions.reduce((s: number, p: any) => s + (p.change_1m_pct || 0), 0) / predictions.length;
      const risingCount = predictions.filter((p: any) => (p.change_1m_pct || 0) > 0).length;

      contextSections.push(`### 전체 시장 요약`);
      contextSections.push(`- 분석 동 수: ${predictions.length}개`);
      contextSections.push(`- 평균 매매가: ${(avgPrice / 10000).toFixed(1)}억원`);
      contextSections.push(`- 1개월 평균 변동률: ${avgChange1m > 0 ? '+' : ''}${avgChange1m.toFixed(1)}%`);
      contextSections.push(`- 상승 예상 동: ${risingCount}/${predictions.length}개`);

      // 상위 5개 동
      const top5 = [...predictions]
        .sort((a, b) => (b.change_1m_pct || 0) - (a.change_1m_pct || 0))
        .slice(0, 5);

      contextSections.push(`\n### 상승률 상위 5개 동`);
      top5.forEach((p, idx) => {
        contextSections.push(
          `${idx + 1}. ${p.dong}: ${(p.current_price_10k / 10000).toFixed(1)}억 → ${(p.pred_1m_10k / 10000).toFixed(1)}억 (${p.change_1m_pct > 0 ? '+' : ''}${p.change_1m_pct?.toFixed(1)}%)`
        );
      });
    }
  }

  // 3. 뉴스 시그널
  if (news && news.length > 0) {
    contextSections.push("\n## 📰 최신 뉴스 시그널\n");
    news.slice(0, 3).forEach((n: any, idx: number) => {
      const date = n.published_at?.split('T')[0] || '';
      contextSections.push(`${idx + 1}. ${n.title} (${date})`);
      if (n.keywords && n.keywords.length > 0) {
        contextSections.push(`   키워드: ${n.keywords.slice(0, 3).join(', ')}`);
      }
    });
  }

  // 4. 거래 통계
  if (trades && trades.length > 0) {
    contextSections.push("\n## 📈 최근 거래 통계 (2025년~)\n");
    const avgTradePrice = trades.reduce((s: number, t: any) => s + (t.price_10k || 0), 0) / trades.length;
    contextSections.push(`- 최근 거래 건수: ${trades.length}건`);
    contextSections.push(`- 평균 거래가: ${(avgTradePrice / 10000).toFixed(1)}억원`);
  }

  // 5. 답변 가이드
  contextSections.push(`\n## 답변 가이드\n`);
  contextSections.push(`위 데이터를 바탕으로 정확하고 구체적인 답변을 제공하세요.`);
  contextSections.push(`- 숫자는 반올림하여 표현 (예: 10.5억원)`);
  contextSections.push(`- 변동률은 소수점 1자리까지 (예: +2.3%)`);
  contextSections.push(`- 데이터가 없는 내용은 추측하지 말고 "데이터가 없습니다"라고 명시`);
  contextSections.push(`- 투자 결정은 사용자 책임임을 마지막에 한 줄로 간단히 안내`);

  return contextSections.join("\n");
}

/**
 * 간단한 통계 계산
 */
export function calculateStats(predictions: any[]) {
  if (!predictions || predictions.length === 0) {
    return null;
  }

  const avgPrice = predictions.reduce((s, p) => s + p.current_price_10k, 0) / predictions.length;
  const avgChange1m = predictions.reduce((s, p) => s + (p.change_1m_pct || 0), 0) / predictions.length;
  const avgChange3m = predictions.reduce((s, p) => s + (p.change_3m_pct || 0), 0) / predictions.length;
  const risingCount = predictions.filter((p) => (p.change_1m_pct || 0) > 0).length;

  const maxChange = Math.max(...predictions.map((p) => p.change_1m_pct || 0));
  const minChange = Math.min(...predictions.map((p) => p.change_1m_pct || 0));

  return {
    avgPrice: (avgPrice / 10000).toFixed(1),
    avgChange1m: avgChange1m.toFixed(1),
    avgChange3m: avgChange3m.toFixed(1),
    risingCount,
    totalCount: predictions.length,
    maxChange: maxChange.toFixed(1),
    minChange: minChange.toFixed(1),
  };
}
