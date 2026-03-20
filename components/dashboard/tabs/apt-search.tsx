"use client";

import { useState, useEffect } from "react";
import { Search, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts";

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

type HistoryPoint = {
  ym: string;
  real_price?: number;
  pred_price?: number;
  trade_count?: number;
};

function formatPrice(val: number) {
  if (!val) return "-";
  const eok = Math.floor(val / 10000);
  const cheon = val % 10000;
  if (cheon === 0) return `${eok}억`;
  return `${eok}억 ${Math.round(cheon / 100) * 100}만`;
}

function addMonths(ym: string, n: number) {
  const [y, m] = ym.split("-").map(Number);
  const date = new Date(y, m - 1 + n);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function ChangeTag({ pct }: { pct: number }) {
  if (pct == null) return <span className="text-muted-foreground text-xs">-</span>;
  const color = pct > 0 ? "text-primary" : pct < 0 ? "text-destructive" : "text-muted-foreground";
  return <span className={`${color} font-semibold text-xs`}>{pct > 0 ? "+" : ""}{pct.toFixed(1)}%</span>;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as HistoryPoint;
  const price = d.real_price ?? d.pred_price;
  const isPred = d.pred_price != null && d.real_price == null;
  return (
    <div className="bg-popover border border-border rounded-lg p-3 text-xs shadow-lg">
      <p className="font-semibold text-foreground mb-1">{label}</p>
      <p className="text-muted-foreground">
        {isPred ? "예측가" : "실거래 평균"}:{" "}
        <span className="text-foreground font-medium">{formatPrice(price!)}</span>
      </p>
      {!isPred && d.trade_count != null && (
        <p className="text-muted-foreground">거래량: {d.trade_count}건</p>
      )}
    </div>
  );
}

function AptChart({ apt }: { apt: PredictionApt }) {
  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [open, setOpen] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setHistory(null);
    fetch(`/api/trade-history/apt?apt_name=${encodeURIComponent(apt.apt_name)}&dong=${encodeURIComponent(apt.dong)}&area=${apt.area}`)
      .then((r) => r.json())
      .then((raw: { ym: string; avg_price_10k: number; trade_count: number }[]) => {
        const pointMap: Record<string, HistoryPoint> = {};
        for (const r of raw) {
          pointMap[r.ym] = { ym: r.ym, real_price: r.avg_price_10k, trade_count: r.trade_count };
        }
        // 실거래 마지막 월 기준 7개월 이내 예측만 표시 (base_ym 오류로 인한 먼 미래 포인트 제거)
        const realYms = raw.map((r) => r.ym).sort();
        const lastRealYm = realYms[realYms.length - 1] ?? apt.base_ym;
        const maxPredYm = addMonths(lastRealYm, 7);
        const predEntries: [string, number][] = [
          [apt.base_ym, apt.current_price_10k],
          [addMonths(apt.base_ym, 1), apt.pred_1m_10k],
          [addMonths(apt.base_ym, 3), apt.pred_3m_10k],
          [addMonths(apt.base_ym, 6), apt.pred_6m_10k],
        ].filter(([ym]) => ym <= maxPredYm) as [string, number][];
        for (const [ym, price] of predEntries) {
          if (!pointMap[ym]) pointMap[ym] = { ym };
          pointMap[ym].pred_price = price;
        }
        setHistory(Object.values(pointMap).sort((a, b) => a.ym.localeCompare(b.ym)));
      })
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [apt.id]);

  const baseYm = apt.base_ym;

  return (
    <div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors mt-3"
      >
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {open ? "차트 닫기" : "실거래가 추이 (2025.01~)"}
      </button>

      {open && (
        <div className="mt-3 h-52">
          {loading ? (
            <p className="text-xs text-muted-foreground text-center pt-10">로딩 중...</p>
          ) : history && history.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center pt-10">거래 데이터가 없습니다.</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history ?? []} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="ym"
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={(v) => v.slice(2)}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                  tickFormatter={(v) => `${Math.round(v / 10000)}억`}
                  width={36}
                  domain={["auto", "auto"]}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine x={baseYm} stroke="hsl(var(--primary))" strokeDasharray="4 2" label={{ value: "현재", fontSize: 10, fill: "hsl(var(--primary))" }} />

                {/* 실거래 이력 */}
                <Line
                  dataKey="real_price"
                  stroke="#4ADE80"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#4ADE80", strokeWidth: 0 }}
                  connectNulls={false}
                  name="실거래"
                />
                {/* 예측 구간 */}
                <Line
                  dataKey="pred_price"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  strokeDasharray="5 3"
                  dot={{ r: 4, fill: "#3B82F6", strokeWidth: 0 }}
                  connectNulls
                  name="예측"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}
    </div>
  );
}

function AptGroupCard({ apts }: { apts: PredictionApt[] }) {
  const areas = apts.map((a) => a.area).sort((a, b) => a - b);
  const [selectedArea, setSelectedArea] = useState(areas[0]);
  const r = apts.find((a) => a.area === selectedArea) ?? apts[0];

  return (
    <Card className="bg-card border-border hover:border-primary/50 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <span className="font-bold text-foreground">{r.apt_name}</span>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="text-xs">{r.dong}</Badge>
            </div>
          </div>
          <span className="text-xs text-muted-foreground">{r.base_ym}</span>
        </div>

        {/* 면적 타입 선택 */}
        {areas.length > 1 && (
          <div className="flex gap-1 mb-3 flex-wrap">
            {areas.map((a) => (
              <button
                key={a}
                onClick={() => setSelectedArea(a)}
                className={`px-2 py-0.5 rounded text-xs border transition-colors ${
                  a === selectedArea
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border text-muted-foreground hover:border-primary/50"
                }`}
              >
                {a}㎡
              </button>
            ))}
          </div>
        )}
        {areas.length === 1 && (
          <p className="text-xs text-muted-foreground mb-3">{r.area}㎡</p>
        )}

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

        <AptChart apt={r} />
      </CardContent>
    </Card>
  );
}

interface AptSearchProps {
  searchQuery: string;
}

const KNOWN_GU = ["동대문구","성북구","중랑구","강북구","도봉구"];

export function AptSearch({ searchQuery }: AptSearchProps) {
  const guFromSearch = KNOWN_GU.find((g) => searchQuery.includes(g)) ?? "";

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PredictionApt[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [defaultGu, setDefaultGu] = useState("__none__");

  // 구 변경 또는 초기 로드 시 기본 목록 로드
  useEffect(() => {
    if (guFromSearch === defaultGu) return;
    setDefaultGu(guFromSearch);
    setQuery("");
    setSearched(false);
    setLoading(true);
    const url = guFromSearch
      ? `/api/predictions/apt?gu=${encodeURIComponent(guFromSearch)}`
      : `/api/predictions/apt?gu=`;
    fetch(url)
      .then((r) => r.json())
      .then((d) => setResults(d ?? []))
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [guFromSearch]);

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

  const isDefaultView = !searched && !!guFromSearch;

  // apt_name + dong 기준으로 그룹화
  const aptGroups = (() => {
    const groupMap = new Map<string, PredictionApt[]>();
    for (const r of results) {
      const key = `${r.apt_name}__${r.dong}`;
      if (!groupMap.has(key)) groupMap.set(key, []);
      groupMap.get(key)!.push(r);
    }
    return Array.from(groupMap.values());
  })();

  const subtitle = isDefaultView
    ? `${guFromSearch} 거래량 상위 아파트 · 아파트 이름으로 직접 검색도 가능합니다`
    : "아파트 이름으로 실거래 추이 및 1·3·6개월 예측가를 조회합니다";

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <h2 className="text-xl font-semibold text-foreground">아파트별 예측 검색</h2>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>

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

      {loading ? (
        <p className="text-sm text-muted-foreground text-center py-12">검색 중...</p>
      ) : searched && results.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-12">
          &quot;{query}&quot; 검색 결과가 없습니다.
        </p>
      ) : results.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">
            {isDefaultView ? `${guFromSearch} 거래량 상위 ${aptGroups.length}개 단지` : `${aptGroups.length}개 단지`}
          </p>
          {aptGroups.map((apts) => (
            <AptGroupCard key={`${apts[0].apt_name}__${apts[0].dong}`} apts={apts} />
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
