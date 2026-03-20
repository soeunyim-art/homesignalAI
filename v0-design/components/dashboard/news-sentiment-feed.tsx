"use client";

import { Newspaper, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useEffect, useState } from "react";

type Sentiment = "positive" | "negative" | "neutral";

interface NewsItem {
  id: string;
  title: string;
  url: string;
  keywords: string[];
  published_at: string;
  sentiment: Sentiment;
  score: number;
}

const POSITIVE_KW = ["완화", "상승", "회복", "활기", "호재", "인하", "재개발", "상승세", "뉴타운"];
const NEGATIVE_KW = ["하락", "규제", "위기", "침체", "폭락", "강화", "제한", "세금"];

function getSentiment(keywords: string[], title: string): { sentiment: Sentiment; score: number } {
  const text = [...(keywords ?? []), title].join(" ");
  const pos = POSITIVE_KW.filter((k) => text.includes(k)).length;
  const neg = NEGATIVE_KW.filter((k) => text.includes(k)).length;
  if (pos > neg) return { sentiment: "positive", score: pos * 8 };
  if (neg > pos) return { sentiment: "negative", score: neg * -8 };
  return { sentiment: "neutral", score: 0 };
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


function SentimentBadge({ sentiment, score }: { sentiment: Sentiment; score: number }) {
  if (sentiment === "positive") {
    return (
      <Badge className="bg-primary/20 text-primary border-0 gap-1">
        <TrendingUp className="h-3 w-3" />
        +{Math.abs(score)}% 긍정 시그널
      </Badge>
    );
  }
  if (sentiment === "negative") {
    return (
      <Badge className="bg-destructive/20 text-destructive border-0 gap-1">
        <TrendingDown className="h-3 w-3" />
        {score}% 부정 시그널
      </Badge>
    );
  }
  return (
    <Badge className="bg-muted text-muted-foreground border-0 gap-1">
      <Minus className="h-3 w-3" />
      중립
    </Badge>
  );
}

export function NewsSentimentFeed() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/news")
      .then((r) => r.json())
      .then((data) => {
        const items: NewsItem[] = (data ?? []).map((d: { id: string; title: string; url: string; keywords: string[]; published_at: string }) => {
          const { sentiment, score } = getSentiment(d.keywords ?? [], d.title);
          return { ...d, sentiment, score };
        });
        setNews(items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Card className="bg-card border-border h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Newspaper className="h-5 w-5 text-primary" />
          <CardTitle className="text-lg text-foreground">뉴스 센티먼트</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="px-0">
        <ScrollArea className="h-[320px] px-6">
          {loading ? (
            <p className="text-sm text-muted-foreground text-center py-8">로딩 중...</p>
          ) : news.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">뉴스 데이터가 없습니다</p>
          ) : null}
          <div className="space-y-4">
            {news.map((item) => (
              <a
                key={item.id}
                href={item.url !== "#" ? item.url : undefined}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 rounded-lg bg-secondary/50 border border-border hover:border-primary/30 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-foreground line-clamp-2 mb-2">
                      {item.title}
                    </h4>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{timeAgo(item.published_at)}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-3">
                  <SentimentBadge sentiment={item.sentiment} score={item.score} />
                </div>
              </a>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
