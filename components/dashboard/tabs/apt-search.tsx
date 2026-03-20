"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type PredictionApt = {
  id: number;
  run_date: string;
  dong: string;
  apt_name: string;
  area: number;
  base_ym: string;
  current_price_10k: number;
  pred_1m_10k: number;
  pred_3m_10k: number;
  pred_6m_10k: number;
  change_1m_pct: number;
  change_3m_pct: number;
  change_6m_pct: number;
};

function formatPrice(val: number) {
  if (!val) return "-";
  const eok = Math.floor(val / 10000);
  const cheon = val % 10000;
  if (cheon === 0) return `${eok}억`;
  return `${eok}억 ${Math.round(cheon / 100) * 100}만`;
}

function ChangeTag({ pct }: { pct: number }) {
  if (pct == null) return <span className="text-muted-foreground text-xs">-</span>;
  const color = pct > 0 ? "text-primary" : pct < 0 ? "text-destructive" : "text-muted-foreground";
  return <span className={`${color} font-semibold text-xs`}>{pct > 0 ? "+" : ""}{pct.toFixed(1)}%</span>;
}

interface AptSearchProps {
  searchQuery: string;
}

export function AptSearch({ searchQuery: _ }: AptSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PredictionApt[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function search() {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(`/api/predictions/apt?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(data ?? []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-foreground">아파트별 예측 검색</h2>
        <p className="text-sm text-muted-foreground">아파트 이름으로 1·3·6개월 예측가를 조회합니다</p>
      </div>

      {/* 검색창 */}
      <div className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="아파트 이름 검색 (예: 래미안, 롯데캐슬, 힐스테이트)"
          className="flex-1"
        />
        <Button onClick={search} disabled={loading} className="gap-2">
          <Search className="h-4 w-4" />
          {loading ? "검색 중..." : "검색"}
        </Button>
      </div>

      {/* 결과 */}
      {loading ? (
        <p className="text-sm text-muted-foreground text-center py-12">검색 중...</p>
      ) : searched && results.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-12">
          &quot;{query}&quot; 검색 결과가 없습니다.
        </p>
      ) : results.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">{results.length}개 결과</p>
          {results.map((r) => (
            <Card key={r.id} className="bg-card border-border hover:border-primary/50 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="font-bold text-foreground">{r.apt_name}</span>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">{r.dong}</Badge>
                      <span className="text-xs text-muted-foreground">{r.area}㎡</span>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">{r.base_ym}</span>
                </div>

                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-muted/30 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground mb-1">현재</p>
                    <p className="text-sm font-bold text-foreground">{formatPrice(r.current_price_10k)}</p>
                  </div>
                  {[
                    { label: "1개월 후", price: r.pred_1m_10k, pct: r.change_1m_pct },
                    { label: "3개월 후", price: r.pred_3m_10k, pct: r.change_3m_pct },
                    { label: "6개월 후", price: r.pred_6m_10k, pct: r.change_6m_pct },
                  ].map(({ label, price, pct }) => (
                    <div key={label} className="bg-muted/30 rounded-lg p-3 text-center">
                      <p className="text-xs text-muted-foreground mb-1">{label}</p>
                      <p className="text-sm font-bold text-foreground">{formatPrice(price)}</p>
                      <ChangeTag pct={pct} />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-muted-foreground">
          <Search className="h-10 w-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">아파트 이름을 검색해보세요</p>
        </div>
      )}
    </div>
  );
}
