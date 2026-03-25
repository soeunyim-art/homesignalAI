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
  sentiment_score: number | null;
  sentiment_label: Sentiment | null;
  sentiment_tags: string[] | null;
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

function SentimentBadge({ label, score }: { label: Sentiment | null; score: number | null }) {
  if (label === "positive") {
    return (
      <Badge className="bg-primary/20 text-primary border-0 gap-1">
        <TrendingUp className="h-3 w-3" />
        {score ?? "긍정"} 긍정 시그널
      </Badge>
    );
  }
  if (label === "negative") {
    return (
      <Badge className="bg-destructive/20 text-destructive border-0 gap-1">
        <TrendingDown className="h-3 w-3" />
        {score ?? "부정"} 부정 시그널
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
      .then((data) => setNews(Array.isArray(data) ? data : []))
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
          ) : (
            <div className="space-y-4">
              {news.map((item) => (
                <a
                  key={item.id}
                  href={item.url !== "#" ? item.url : undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 rounded-lg bg-secondary/50 border border-border hover:border-primary/30 transition-all cursor-pointer"
                >
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-foreground line-clamp-2 mb-2">
                      {item.title}
                    </h4>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                      <span>{timeAgo(item.published_at)}</span>
                    </div>
                    <SentimentBadge label={item.sentiment_label} score={item.sentiment_score} />
                  </div>
                </a>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
