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
  Download,
  RefreshCw,
} from "lucide-react";

const newsData = [
  {
    id: 1,
    title: "서울 아파트 매매가 3개월 연속 상승세...강남권 주도",
    source: "경제일보",
    date: "2024.03.07",
    sentiment: "positive",
    score: 82,
    summary: "서울 아파트 매매가격이 3개월 연속 상승세를 이어가고 있으며, 특히 강남권이 상승세를 주도하고 있다.",
    impact: "가격 상승 요인",
  },
  {
    id: 2,
    title: "금리 인하 기대감 확산...부동산 시장 회복 신호",
    source: "부동산경제",
    date: "2024.03.06",
    sentiment: "positive",
    score: 75,
    summary: "한국은행의 금리 인하 가능성이 높아지면서 부동산 시장에 회복 기대감이 확산되고 있다.",
    impact: "거래량 증가 예상",
  },
  {
    id: 3,
    title: "2024년 수도권 입주 물량 역대 최대...전세가 하락 우려",
    source: "주택신문",
    date: "2024.03.06",
    sentiment: "negative",
    score: 68,
    summary: "올해 수도권 아파트 입주 물량이 역대 최대치를 기록할 전망이어서 전세가격 하락이 우려된다.",
    impact: "전세가 하락 리스크",
  },
  {
    id: 4,
    title: "정부, 재건축 규제 완화 검토...강남 노후단지 기대감",
    source: "정책뉴스",
    date: "2024.03.05",
    sentiment: "positive",
    score: 71,
    summary: "정부가 재건축 규제 완화를 검토 중이며, 강남권 노후 단지들의 기대감이 커지고 있다.",
    impact: "특정 지역 상승 가능",
  },
  {
    id: 5,
    title: "전세가율 68% 기록...2년 만에 최저치",
    source: "경제매일",
    date: "2024.03.05",
    sentiment: "negative",
    score: 45,
    summary: "서울 아파트 전세가율이 68%를 기록하며 2년 만에 최저치를 나타냈다.",
    impact: "갭투자 매력 감소",
  },
  {
    id: 6,
    title: "외국인 부동산 투자 규제 강화 논의",
    source: "국제경제",
    date: "2024.03.04",
    sentiment: "neutral",
    score: 50,
    summary: "외국인의 국내 부동산 투자에 대한 규제 강화가 논의되고 있다.",
    impact: "시장 영향 제한적",
  },
];

const sentimentSummary = {
  positive: 45,
  neutral: 30,
  negative: 25,
  overallScore: 72,
  trend: "상승",
};

interface AIReportProps {
  searchQuery: string;
}

export function AIReport({ searchQuery }: AIReportProps) {
  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <TrendingUp className="h-4 w-4 text-primary" />;
      case "negative":
        return <TrendingDown className="h-4 w-4 text-destructive" />;
      default:
        return <Minus className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "border-primary text-primary";
      case "negative":
        return "border-destructive text-destructive";
      default:
        return "border-muted-foreground text-muted-foreground";
    }
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
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            리포트 다운로드
          </Button>
        </div>
      </div>

      {/* Sentiment Summary */}
      <Card className="bg-card border-border">
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">{sentimentSummary.overallScore}</p>
              <p className="text-xs text-muted-foreground mt-1">종합 감성 점수</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">{sentimentSummary.positive}%</p>
              <p className="text-xs text-muted-foreground mt-1">긍정 비율</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-muted-foreground">{sentimentSummary.neutral}%</p>
              <p className="text-xs text-muted-foreground mt-1">중립 비율</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-destructive">{sentimentSummary.negative}%</p>
              <p className="text-xs text-muted-foreground mt-1">부정 비율</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-accent">{sentimentSummary.trend}</p>
              <p className="text-xs text-muted-foreground mt-1">시장 전망</p>
            </div>
          </div>
          <div className="mt-4 h-2 bg-muted rounded-full overflow-hidden flex">
            <div
              className="h-full bg-primary"
              style={{ width: `${sentimentSummary.positive}%` }}
            />
            <div
              className="h-full bg-muted-foreground"
              style={{ width: `${sentimentSummary.neutral}%` }}
            />
            <div
              className="h-full bg-destructive"
              style={{ width: `${sentimentSummary.negative}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* AI Summary Card */}
      <Card className="bg-gradient-to-br from-primary/10 to-accent/10 border-primary/30">
        <CardContent className="p-6">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <Newspaper className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-foreground mb-2">AI 종합 분석</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                최근 1주일간 {searchQuery || "서울"} 부동산 관련 뉴스를 분석한 결과, 
                <span className="text-primary font-medium"> 긍정적인 시그널이 우세</span>합니다. 
                금리 인하 기대감과 정책 완화 논의가 상승 요인으로 작용하고 있으나, 
                대규모 입주 물량으로 인한 전세가 하락 리스크는 주의가 필요합니다. 
                단기적으로 <span className="text-accent font-medium">완만한 상승세</span>가 예상되며, 
                모델 신뢰도는 <span className="text-primary font-medium">78%</span>입니다.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* News Feed */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary" />
            실시간 뉴스 피드
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[400px]">
            <div className="p-4 space-y-4">
              {newsData.map((news) => (
                <div
                  key={news.id}
                  className="p-4 rounded-lg bg-muted/30 border border-border hover:border-primary/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getSentimentIcon(news.sentiment)}
                        <h4 className="font-medium text-foreground text-sm leading-tight">
                          {news.title}
                        </h4>
                      </div>
                      <p className="text-xs text-muted-foreground mb-3">{news.summary}</p>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-muted-foreground">{news.source}</span>
                        <span className="text-muted-foreground">{news.date}</span>
                        <Badge variant="outline" className={getSentimentColor(news.sentiment)}>
                          감성 {news.score}
                        </Badge>
                        <Badge variant="outline" className="border-accent/50 text-accent">
                          {news.impact}
                        </Badge>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <p className="text-xs text-muted-foreground text-center">
        * 뉴스 감성 분석은 AI 자연어 처리 기반이며, 실제 시장 영향과 다를 수 있습니다.
      </p>
    </div>
  );
}
