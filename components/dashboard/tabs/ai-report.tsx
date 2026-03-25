"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Newspaper,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  RefreshCw,
  Building2,
} from "lucide-react";
import { useEffect, useState, useCallback } from "react";

interface NewsItem {
  id: string;
  title: string;
  url: string;
  keywords: string[];
  published_at: string;
  sentiment_score: number | null;
  sentiment_label: "positive" | "neutral" | "negative" | null;
  sentiment_tags: string[] | null;
}

interface PredictionData {
  base_ym: string;
  current: number;
  pred_1m: number;
  pred_3m: number;
  pred_6m: number;
}

function calcSentimentSummary(news: NewsItem[]) {
  const analyzed = news.filter((n) => n.sentiment_label);
  if (!analyzed.length) return { positive: 0, neutral: 0, negative: 0, overallScore: 50, trend: "보합" };
  const pos = analyzed.filter((n) => n.sentiment_label === "positive").length;
  const neu = analyzed.filter((n) => n.sentiment_label === "neutral").length;
  const neg = analyzed.filter((n) => n.sentiment_label === "negative").length;
  const total = analyzed.length;
  const avgScore = Math.round(analyzed.reduce((s, n) => s + (n.sentiment_score ?? 50), 0) / total);
  return {
    positive: Math.round((pos / total) * 100),
    neutral: Math.round((neu / total) * 100),
    negative: Math.round((neg / total) * 100),
    overallScore: avgScore,
    trend: avgScore >= 60 ? "상승" : avgScore <= 40 ? "하락" : "보합",
  };
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(hours / 24);
  if (hours < 1) return "방금 전";
  if (hours < 24) return `${hours}시간 전`;
  if (days < 7) return `${days}일 전`;
  return new Date(dateStr).toLocaleDateString("ko-KR");
}

function fmt억(val: number) {
  return `${(val / 10000).toFixed(1)}억`;
}

function fmtPct(val: number) {
  const sign = val >= 0 ? "+" : "";
  return `${sign}${val.toFixed(1)}%`;
}

interface AIReportProps {
  searchQuery: string;
}

const GU_LIST = ["동대문구", "성북구", "중랑구", "강북구", "도봉구"];

export function AIReport({ searchQuery }: AIReportProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(() => {
    setLoading(true);
    const gu = GU_LIST.find((g) => searchQuery.includes(g)) ?? "동대문구";
    const q = searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : "";

    Promise.all([
      fetch(`/api/news${q}`).then((r) => r.json()),
      fetch(`/api/trade-history?gu=${encodeURIComponent(gu)}`).then((r) => r.json()),
    ])
      .then(([newsData, tradeData]) => {
        setNews(Array.isArray(newsData) ? newsData : []);
        setPrediction(tradeData?.predictions ?? null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchQuery]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const sentiment = calcSentimentSummary(news);
  const priceTrend = prediction
    ? fmtPct(((prediction.pred_1m - prediction.current) / prediction.current) * 100)
    : null;

  const gu = GU_LIST.find((g) => searchQuery.includes(g)) ?? "동대문구";

  return (
    <div className="space-y-6 animate-in fade-in duration-300">

      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">{searchQuery || gu} AI 리포트</h2>
          <p className="text-sm text-muted-foreground">뉴스 감성 · 매매가 예측 종합 분석</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchAll} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          새로고침
        </Button>
      </div>

      {/* 종합 시장 신호 */}
      <Card className="bg-gradient-to-r from-primary/10 via-accent/5 to-primary/10 border-primary/30">
        <CardContent className="p-5">
          <p className="text-xs text-muted-foreground mb-3 font-medium uppercase tracking-wide">종합 시장 신호</p>
          {loading ? (
            <p className="text-sm text-muted-foreground">로딩 중...</p>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className={`text-2xl font-bold ${sentiment.overallScore >= 60 ? "text-primary" : sentiment.overallScore <= 40 ? "text-destructive" : "text-muted-foreground"}`}>
                  {sentiment.overallScore}점
                </p>
                <p className="text-xs text-muted-foreground mt-1">뉴스 감성</p>
                <Badge className={`mt-1 text-xs border-0 ${sentiment.overallScore >= 60 ? "bg-primary/20 text-primary" : sentiment.overallScore <= 40 ? "bg-destructive/20 text-destructive" : "bg-muted text-muted-foreground"}`}>
                  {sentiment.trend}
                </Badge>
              </div>
              <div className="text-center border-l border-border">
                <p className={`text-2xl font-bold ${priceTrend && !priceTrend.startsWith("-") ? "text-primary" : "text-destructive"}`}>
                  {priceTrend ?? "–"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">1개월 예측 변화율</p>
                <p className="text-xs text-muted-foreground">{gu} 평균</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 2-패널 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* 뉴스 감성 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Newspaper className="h-4 w-4 text-primary" />
              뉴스 감성 분석
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <p className="text-xs text-muted-foreground">로딩 중...</p> : (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-primary">긍정 {sentiment.positive}%</span>
                  <span className="text-muted-foreground">중립 {sentiment.neutral}%</span>
                  <span className="text-destructive">부정 {sentiment.negative}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden flex">
                  <div className="h-full bg-primary" style={{ width: `${sentiment.positive}%` }} />
                  <div className="h-full bg-muted-foreground" style={{ width: `${sentiment.neutral}%` }} />
                  <div className="h-full bg-destructive" style={{ width: `${sentiment.negative}%` }} />
                </div>
                <p className="text-xs text-muted-foreground">분석 기사 {news.filter((n) => n.sentiment_label).length}건</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 매매가 예측 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Building2 className="h-4 w-4 text-primary" />
              매매가 예측 ({gu})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <p className="text-xs text-muted-foreground">로딩 중...</p> : !prediction ? (
              <p className="text-xs text-muted-foreground">데이터 없음</p>
            ) : (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">현재 ({prediction.base_ym})</span>
                  <span className="font-semibold">{fmt억(prediction.current)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">1개월 후</span>
                  <span className={`font-semibold ${prediction.pred_1m >= prediction.current ? "text-primary" : "text-destructive"}`}>
                    {fmt억(prediction.pred_1m)}
                    <span className="text-xs ml-1 font-normal">{fmtPct(((prediction.pred_1m - prediction.current) / prediction.current) * 100)}</span>
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">3개월 후</span>
                  <span className={`font-semibold ${prediction.pred_3m >= prediction.current ? "text-primary" : "text-destructive"}`}>
                    {fmt억(prediction.pred_3m)}
                    <span className="text-xs ml-1 font-normal">{fmtPct(((prediction.pred_3m - prediction.current) / prediction.current) * 100)}</span>
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">6개월 후</span>
                  <span className={`font-semibold ${prediction.pred_6m >= prediction.current ? "text-primary" : "text-destructive"}`}>
                    {fmt억(prediction.pred_6m)}
                    <span className="text-xs ml-1 font-normal">{fmtPct(((prediction.pred_6m - prediction.current) / prediction.current) * 100)}</span>
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* AI 종합 분석 */}
      {!loading && (
        <Card className="bg-gradient-to-br from-primary/10 to-accent/10 border-primary/30">
          <CardContent className="p-5">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <Newspaper className="h-4 w-4 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-1 text-sm">AI 종합 분석</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {gu} 부동산 시장은 뉴스 감성{" "}
                  <span className="text-foreground font-medium">{sentiment.overallScore}점({sentiment.trend})</span>
                  {prediction && (
                    <>
                      , 1개월 후 매매가 예측{" "}
                      <span className={`font-medium ${prediction.pred_1m >= prediction.current ? "text-primary" : "text-destructive"}`}>
                        {fmt억(prediction.pred_1m)} ({fmtPct(((prediction.pred_1m - prediction.current) / prediction.current) * 100)})
                      </span>
                    </>
                  )}
                  {" "}을 종합하면{" "}
                  <span className={`font-medium ${sentiment.trend === "상승" ? "text-primary" : sentiment.trend === "하락" ? "text-destructive" : "text-muted-foreground"}`}>
                    {sentiment.trend} 흐름
                  </span>
                  이 예상됩니다.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 뉴스 피드 */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary" />
            실시간 뉴스 피드
            {!loading && <span className="text-xs text-muted-foreground font-normal">({news.length}건)</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[380px]">
            <div className="p-4 space-y-3">
              {loading ? (
                <p className="text-sm text-muted-foreground text-center py-8">로딩 중...</p>
              ) : news.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">뉴스 데이터가 없습니다</p>
              ) : (
                news.map((item) => (
                  <div key={item.id} className="p-3 rounded-lg bg-muted/30 border border-border hover:border-primary/30 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {item.sentiment_label === "positive" ? (
                            <TrendingUp className="h-3 w-3 text-primary shrink-0" />
                          ) : item.sentiment_label === "negative" ? (
                            <TrendingDown className="h-3 w-3 text-destructive shrink-0" />
                          ) : (
                            <Minus className="h-3 w-3 text-muted-foreground shrink-0" />
                          )}
                          <h4 className="font-medium text-foreground text-sm leading-tight line-clamp-2">{item.title}</h4>
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5 mt-2 text-xs">
                          <span className="text-muted-foreground">{timeAgo(item.published_at)}</span>
                          {item.sentiment_score != null && (
                            <Badge variant="outline" className={`text-xs ${item.sentiment_label === "positive" ? "border-primary text-primary" : item.sentiment_label === "negative" ? "border-destructive text-destructive" : "border-muted-foreground text-muted-foreground"}`}>
                              감성 {item.sentiment_score}
                            </Badge>
                          )}
                          {(item.sentiment_tags ?? []).map((tag) => (
                            <Badge key={tag} variant="outline" className="border-accent/50 text-accent text-xs">{tag}</Badge>
                          ))}
                        </div>
                      </div>
                      {item.url && item.url !== "#" && (
                        <a href={item.url} target="_blank" rel="noopener noreferrer" className="shrink-0">
                          <Button variant="ghost" size="icon" className="h-7 w-7">
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </a>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">
        * 뉴스 감성 분석은 Claude AI 기반이며, 예측 모델은 과거 데이터 기반으로 실제 시장과 다를 수 있습니다.
      </p>
    </div>
  );
}
