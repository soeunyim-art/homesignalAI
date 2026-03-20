"use client";

import { useState, useEffect } from "react";
import { Search, TrendingUp, MapPin, Building2, Sparkles, TrendingDown } from "lucide-react";
import { motion } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { HomeSignalLogo } from "./logo";

// 실제 분석 대상 5개 구만 표시
const GU_LIST = ["동대문구", "성북구", "중랑구", "강북구", "도봉구"];

type Prediction = {
  current_price_10k: number;
  change_1m_pct: number;
};

type NewsItem = {
  id: string;
  title: string;
  keywords: string[];
  published_at: string;
};

const POSITIVE_KW = ["완화", "상승", "회복", "활기", "호재", "인하", "재개발"];
const NEGATIVE_KW = ["하락", "규제", "위기", "침체", "강화", "제한"];

function getSentiment(keywords: string[], title: string): "positive" | "negative" | "neutral" {
  const text = [...(keywords ?? []), title].join(" ");
  const pos = POSITIVE_KW.filter((k) => text.includes(k)).length;
  const neg = NEGATIVE_KW.filter((k) => text.includes(k)).length;
  if (pos > neg) return "positive";
  if (neg > pos) return "negative";
  return "neutral";
}

interface HomeSearchProps {
  onSearch: (query: string) => void;
}

export function HomeSearch({ onSearch }: HomeSearchProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState<{ avgPrice: string; dongCount: number; change: string } | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);

  useEffect(() => {
    // 실제 predictions 데이터로 홈 통계 계산
    fetch("/api/predictions")
      .then((r) => r.json())
      .then((preds: Prediction[]) => {
        if (!preds || preds.length === 0) return;
        const avgPrice = preds.reduce((s, p) => s + (p.current_price_10k ?? 0), 0) / preds.length;
        const avgChange = preds.reduce((s, p) => s + (p.change_1m_pct ?? 0), 0) / preds.length;
        setStats({
          avgPrice: `${(avgPrice / 10000).toFixed(1)}억`,
          dongCount: preds.length,
          change: `${avgChange > 0 ? "+" : ""}${avgChange.toFixed(1)}%`,
        });
      })
      .catch(console.error);

    // 실제 뉴스 데이터
    fetch("/api/news")
      .then((r) => r.json())
      .then((data: NewsItem[]) => {
        if (data && data.length > 0) setNews(data.slice(0, 3));
      })
      .catch(console.error);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) onSearch(searchQuery);
  };

  const handleQuickSearch = (query: string) => {
    setSearchQuery(query);
    onSearch(query);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="fixed inset-0 pointer-events-none z-0">
        <svg className="w-full h-full opacity-[0.03]">
          <defs>
            <pattern id="homeDotGrid" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="#4ADE80" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#homeDotGrid)" />
        </svg>
      </div>

      <main className="flex-1 flex flex-col items-center justify-center px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-2xl text-center"
        >
          <div className="flex items-center justify-center mb-6">
            <HomeSignalLogo className="scale-125" />
          </div>

          <p className="text-lg text-muted-foreground mb-8">
            AI 기반 부동산 시장 분석 및 가격 예측 플랫폼
          </p>

          <form onSubmit={handleSubmit} className="relative mb-6">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="분석 지역을 입력하세요 (예: 동대문구, 성북구)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-14 pl-12 pr-32 text-base bg-card border-border rounded-xl focus:border-primary focus:ring-primary"
              />
              <Button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-10 px-6 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <Sparkles className="h-4 w-4 mr-2" />
                AI 분석
              </Button>
            </div>
          </form>

          {/* 분석 가능한 5개 구만 표시 */}
          <div className="mb-12">
            <p className="text-sm text-muted-foreground mb-3">분석 가능 지역</p>
            <div className="flex flex-wrap justify-center gap-2">
              {GU_LIST.map((term) => (
                <Badge
                  key={term}
                  variant="outline"
                  className="cursor-pointer hover:bg-primary/10 hover:border-primary transition-colors py-1.5 px-3"
                  onClick={() => handleQuickSearch(term)}
                >
                  <MapPin className="h-3 w-3 mr-1" />
                  {term}
                </Badge>
              ))}
            </div>
          </div>

          {/* 실제 데이터 기반 통계 - 데이터 없으면 카드 숨김 */}
          {stats && (
            <div className="grid grid-cols-3 gap-4 mb-12">
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <Card className="p-4 bg-card border-border">
                  <TrendingUp className="h-6 w-6 text-primary mx-auto mb-2" />
                  <p className="text-2xl font-bold text-foreground">{stats.avgPrice}</p>
                  <p className="text-xs text-muted-foreground">5개 구 평균 매매가</p>
                </Card>
              </motion.div>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                <Card className="p-4 bg-card border-border">
                  <Building2 className="h-6 w-6 text-accent mx-auto mb-2" />
                  <p className="text-2xl font-bold text-foreground">{stats.dongCount}개 동</p>
                  <p className="text-xs text-muted-foreground">분석 대상 동 수</p>
                </Card>
              </motion.div>
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                <Card className="p-4 bg-card border-border">
                  <Sparkles className="h-6 w-6 text-chart-3 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-foreground">{stats.change}</p>
                  <p className="text-xs text-muted-foreground">1개월 평균 변동률</p>
                </Card>
              </motion.div>
            </div>
          )}

          {/* 실제 뉴스 - 데이터 없으면 섹션 숨김 */}
          {news.length > 0 && (
            <div className="text-left">
              <p className="text-sm text-muted-foreground mb-3">실시간 부동산 뉴스</p>
              <div className="space-y-2">
                {news.map((item, index) => {
                  const sentiment = getSentiment(item.keywords ?? [], item.title);
                  return (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                      className="flex items-center gap-2 p-3 rounded-lg bg-card/50 border border-border/50"
                    >
                      <div className={`w-2 h-2 rounded-full shrink-0 ${sentiment === "positive" ? "bg-primary" : sentiment === "negative" ? "bg-destructive" : "bg-muted-foreground"}`} />
                      <span className="text-sm text-foreground line-clamp-1">{item.title}</span>
                      {sentiment === "positive" ? (
                        <TrendingUp className="h-3 w-3 text-primary shrink-0 ml-auto" />
                      ) : sentiment === "negative" ? (
                        <TrendingDown className="h-3 w-3 text-destructive shrink-0 ml-auto" />
                      ) : null}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}
        </motion.div>
      </main>

      <footer className="text-center py-4 text-xs text-muted-foreground border-t border-border">
        <p>본 서비스의 AI 예측은 참고용이며, 투자 결정은 전문가 상담 후 신중하게 판단하시기 바랍니다.</p>
      </footer>
    </div>
  );
}
