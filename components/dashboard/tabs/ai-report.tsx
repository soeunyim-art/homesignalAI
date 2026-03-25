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

interface SentimentSummary {
  positive: number;
  neutral: number;
  negative: number;
  overallScore: number;
  trend: string;
}

function calcSummary(news: NewsItem[]): SentimentSummary {
  const analyzed = news.filter((n) => n.sentiment_label);
  if (analyzed.length === 0) {
    return { positive: 0, neutral: 0, negative: 0, overallScore: 50, trend: "보합" };
  }
  const pos = analyzed.filter((n) => n.sentiment_label === "positive").length;
  const neu = analyzed.filter((n) => n.sentiment_label === "neutral").length;
  const neg = analyzed.filter((n) => n.sentiment_label === "negative").length;
  const total = analyzed.length;
  const avgScore = Math.round(
    analyzed.reduce((sum, n) => sum + (n.sentiment_score ?? 50), 0) / total
  );
  const trend = avgScore >= 60 ? "상승" : avgScore <= 40 ? "하락" : "보합";
  return {
    positive: Math.round((pos / total) * 100),
    neutral: Math.round((neu / total) * 100),
    negative: Math.round((neg / total) * 100),
    overallScore: avgScore,
    trend,
  };
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(hours / 24);
  if (hours < 1) return "방금 전";
  if (hours < 24) return `${hours}시간 전`;
  if (days < 7) return `${days}일 전`;
  return new Date(dateStr).toLocaleDateString("ko-KR");
}

interface AIReportProps {
  searchQuery: string;
}

export function AIReport({ searchQuery }: AIReportProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchNews = useCallback(() => {
    setLoading(true);
    const q = searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : "";
    fetch(`/api/news${q}`)
      .then((r) => r.json())
      .then((data) => setNews(Array.isArray(data) ? data : []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchQuery]);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const summary = calcSummary(news);

  const getSentimentIcon = (label: string | null) => {
    if (label === "positive") return <TrendingUp className="h-4 w-4 text-primary" />;
    if (label === "negative") return <TrendingDown className="h-4 w-4 text-destructive" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  const getSentimentColor = (label: string | null) => {
    if (label === "positive") return "border-primary text-primary";
    if (label === "negative") return "border-destructive text-destructive";
    return "border-muted-foreground text-muted-foreground";
  };

  const aiSummaryText = () => {
    const region = searchQuery || "서울";
    const { overallScore, trend, positive, negative } = summary;
    const dominant = positive >= negative ? "긍정적인 시그널이 우세" : "부정적인 시그널이 우세";
    return `최근 ${region} 부동산 관련 뉴스 ${news.length}건을 분석한 결과, ${dominant}합니다. 종합 감성 점수는 ${overallScore}점으로 단기적으로 ${trend} 흐름이 예상됩니다.`;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            {searchQuery || "서울"} AI 리포트
          </h2>
          <p className="text-sm text-muted-foreground">
            실시간 뉴스 감성 분석 및 시장 동향
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchNews} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          새로고침
        </Button>
      </div>

      {/* Sentiment Summary */}
      <Card className="bg-card border-border">
        <CardContent className="p-6">
          {loading ? (
            <p className="text-sm text-muted-foreground text-center py-4">로딩 중...</p>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-primary">{summary.overallScore}</p>
                  <p className="text-xs text-muted-foreground mt-1">종합 감성 점수</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-primary">{summary.positive}%</p>
                  <p className="text-xs text-muted-foreground mt-1">긍정 비율</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-muted-foreground">{summary.neutral}%</p>
                  <p className="text-xs text-muted-foreground mt-1">중립 비율</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-destructive">{summary.negative}%</p>
                  <p className="text-xs text-muted-foreground mt-1">부정 비율</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-accent">{summary.trend}</p>
                  <p className="text-xs text-muted-foreground mt-1">시장 전망</p>
                </div>
              </div>
              <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden flex">
                <div className="h-full bg-primary transition-all" style={{ width: `${summary.positive}%` }} />
                <div className="h-full bg-muted-foreground transition-all" style={{ width: `${summary.neutral}%` }} />
                <div className="h-full bg-destructive transition-all" style={{ width: `${summary.negative}%` }} />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* AI Summary */}
      {!loading && news.length > 0 && (
        <Card className="bg-gradient-to-br from-primary/10 to-accent/10 border-primary/30">
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                <Newspaper className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-foreground mb-2">AI 종합 분석</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{aiSummaryText()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* News Feed */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary" />
            실시간 뉴스 피드
            {!loading && <span className="text-xs text-muted-foreground font-normal">({news.length}건)</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[400px]">
            <div className="p-4 space-y-4">
              {loading ? (
                <p className="text-sm text-muted-foreground text-center py-8">로딩 중...</p>
              ) : news.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">뉴스 데이터가 없습니다</p>
              ) : (
                news.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-lg bg-muted/30 border border-border hover:border-primary/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getSentimentIcon(item.sentiment_label)}
                          <h4 className="font-medium text-foreground text-sm leading-tight line-clamp-2">
                            {item.title}
                          </h4>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs mt-3">
                          <span className="text-muted-foreground">{timeAgo(item.published_at)}</span>
                          {item.sentiment_score != null && (
                            <Badge variant="outline" className={getSentimentColor(item.sentiment_label)}>
                              감성 {item.sentiment_score}
                            </Badge>
                          )}
                          {(item.sentiment_tags ?? []).map((tag) => (
                            <Badge key={tag} variant="outline" className="border-accent/50 text-accent">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      {item.url && item.url !== "#" && (
                        <a href={item.url} target="_blank" rel="noopener noreferrer">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <ExternalLink className="h-4 w-4" />
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
        * 뉴스 감성 분석은 Claude AI 기반이며, 실제 시장 영향과 다를 수 있습니다.
      </p>
    </div>
  );
}
