"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Building2, MapPin, TrendingUp, TrendingDown, Info, X, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from "recharts";

// ── 타입 ──────────────────────────────────────────────
type SearchResult = {
  apt_name: string;
  dong: string;
  avg_price_10k: number;
  trade_count: number;
  latest_ym: string;
};

type HistoryPoint = {
  ym: string;
  avg_price_10k: number;
  trade_count: number;
};

type RecentTrade = {
  ym: string;
  price_10k: number;
  area: number;
  floor: number;
};

type Stats = {
  min: number;
  max: number;
  avg: number;
  total_trades: number;
};

type AptDetail = {
  history: HistoryPoint[];
  recentTrades: RecentTrade[];
  areaSet: number[];
  stats: Stats | null;
};

type ChartPoint = {
  label: string;
  price: number | null;
  trade_count?: number;
};

// ── 헬퍼 ──────────────────────────────────────────────
function ymToLabel(ym: string) {
  const [y, m] = ym.split("-");
  return `${y.slice(2)}.${m}`;
}

function toEok(val: number) {
  return Math.round((val / 10000) * 100) / 100;
}

function formatPrice(val: number) {
  const eok = Math.floor(val / 10000);
  const man = Math.round((val % 10000) / 1000) * 1000;
  if (eok > 0 && man > 0) return `${eok}억 ${(man / 1000).toFixed(0)}천`;
  if (eok > 0) return `${eok}억`;
  return `${val.toLocaleString()}만`;
}

// ── 메인 컴포넌트 ──────────────────────────────────────
export function AptSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [selectedApt, setSelectedApt] = useState<SearchResult | null>(null);
  const [detail, setDetail] = useState<AptDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedArea, setSelectedArea] = useState<number | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 검색어 디바운스
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      setLoading(true);
      fetch(`/api/apt-search?q=${encodeURIComponent(query)}`)
        .then((r) => r.json())
        .then((data: SearchResult[]) => {
          setResults(Array.isArray(data) ? data : []);
          setShowDropdown(true);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }, 350);
  }, [query]);

  // 아파트 선택 → 상세 조회
  function handleSelect(apt: SearchResult) {
    setSelectedApt(apt);
    setShowDropdown(false);
    setQuery(apt.apt_name);
    setSelectedArea(null);
    setDetailLoading(true);
    fetch(`/api/apt-detail?apt_name=${encodeURIComponent(apt.apt_name)}&dong=${encodeURIComponent(apt.dong)}`)
      .then((r) => r.json())
      .then((data: AptDetail) => {
        setDetail(data);
        if (data.areaSet?.length > 0) setSelectedArea(null); // null = 전체
      })
      .catch(console.error)
      .finally(() => setDetailLoading(false));
  }

  // 면적 필터 변경
  function handleAreaChange(area: number | null) {
    if (!selectedApt) return;
    setSelectedArea(area);
    setDetailLoading(true);
    const areaParam = area !== null ? `&area=${area}` : "";
    fetch(
      `/api/apt-detail?apt_name=${encodeURIComponent(selectedApt.apt_name)}&dong=${encodeURIComponent(
        selectedApt.dong
      )}${areaParam}`
    )
      .then((r) => r.json())
      .then((data: AptDetail) => setDetail(data))
      .catch(console.error)
      .finally(() => setDetailLoading(false));
  }

  function handleClear() {
    setQuery("");
    setSelectedApt(null);
    setDetail(null);
    setResults([]);
    setShowDropdown(false);
    inputRef.current?.focus();
  }

  // 차트 데이터 가공
  const chartData: ChartPoint[] = (detail?.history ?? []).map((h) => ({
    label: ymToLabel(h.ym),
    price: toEok(h.avg_price_10k),
    trade_count: h.trade_count,
  }));

  const allVals = chartData.map((d) => d.price).filter((v): v is number => v !== null);
  const yMin = allVals.length ? Math.max(0, Math.floor(Math.min(...allVals) - 1)) : 0;
  const yMax = allVals.length ? Math.ceil(Math.max(...allVals) + 1) : 20;

  // 최근 변화율 계산 (처음 vs 마지막)
  const firstPrice = allVals[0] ?? null;
  const lastPrice = allVals[allVals.length - 1] ?? null;
  const totalChange =
    firstPrice && lastPrice ? ((lastPrice - firstPrice) / firstPrice) * 100 : null;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* 헤더 */}
      <div>
        <h2 className="text-xl font-semibold text-foreground">아파트 검색</h2>
        <p className="text-sm text-muted-foreground">
          아파트 이름으로 검색해 실거래 가격 히스토리를 확인하세요
        </p>
      </div>

      {/* 검색 박스 */}
      <div className="relative max-w-2xl">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results.length > 0 && setShowDropdown(true)}
            placeholder="아파트 이름 입력 (예: 이문 현대, 길음 뉴타운, 창동 주공)"
            className="h-12 pl-11 pr-10 text-sm bg-card border-border rounded-xl focus:border-primary"
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* 드롭다운 결과 */}
        <AnimatePresence>
          {showDropdown && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
              className="absolute z-50 w-full mt-1 bg-card border border-border rounded-xl shadow-xl overflow-hidden"
            >
              {loading ? (
                <div className="p-4 text-sm text-muted-foreground text-center">검색 중...</div>
              ) : results.length === 0 ? (
                <div className="p-4 text-sm text-muted-foreground text-center">
                  검색 결과가 없습니다
                </div>
              ) : (
                <ul className="max-h-72 overflow-y-auto divide-y divide-border/50">
                  {results.map((r, i) => (
                    <li key={i}>
                      <button
                        onClick={() => handleSelect(r)}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors text-left"
                      >
                        <Building2 className="h-4 w-4 text-primary shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">
                            {r.apt_name}
                          </p>
                          <p className="text-xs text-muted-foreground flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {r.dong}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-sm font-semibold text-foreground">
                            {formatPrice(r.avg_price_10k)}
                          </p>
                          <p className="text-xs text-muted-foreground">{r.trade_count}건</p>
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 아파트 미선택 상태 안내 */}
      {!selectedApt && !loading && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Building2 className="h-12 w-12 text-muted-foreground/30 mb-4" />
          <p className="text-muted-foreground text-sm">
            아파트를 검색하면 2020년부터의 실거래가 추이를 확인할 수 있습니다
          </p>
          <p className="text-muted-foreground/60 text-xs mt-1">
            서울 동북권 5개 구 (동대문·성북·중랑·강북·도봉) 데이터 제공
          </p>
        </div>
      )}

      {/* 상세 영역 */}
      <AnimatePresence>
        {selectedApt && (
          <motion.div
            key={selectedApt.apt_name + selectedApt.dong}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="space-y-4"
          >
            {/* 아파트 헤더 카드 */}
            <Card className="p-5 bg-card border-border">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Building2 className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">{selectedApt.apt_name}</h3>
                    <p className="text-sm text-muted-foreground flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {selectedApt.dong}
                    </p>
                  </div>
                </div>

                {/* 통계 뱃지 */}
                {detail?.stats && (
                  <div className="flex flex-wrap gap-2 justify-end">
                    <Badge variant="outline" className="text-xs">
                      총 {detail.stats.total_trades}건 거래
                    </Badge>
                    {totalChange !== null && (
                      <Badge
                        className={`text-xs border-0 ${
                          totalChange >= 0
                            ? "bg-primary/20 text-primary"
                            : "bg-destructive/20 text-destructive"
                        }`}
                      >
                        {totalChange >= 0 ? (
                          <TrendingUp className="h-3 w-3 mr-1" />
                        ) : (
                          <TrendingDown className="h-3 w-3 mr-1" />
                        )}
                        2020 대비 {totalChange > 0 ? "+" : ""}
                        {totalChange.toFixed(1)}%
                      </Badge>
                    )}
                  </div>
                )}
              </div>

              {/* 면적 필터 */}
              {detail && detail.areaSet.length > 1 && (
                <div className="flex items-center gap-2 mt-4 flex-wrap">
                  <span className="text-xs text-muted-foreground">전용면적:</span>
                  <Button
                    size="sm"
                    variant={selectedArea === null ? "default" : "outline"}
                    className="h-7 px-3 text-xs"
                    onClick={() => handleAreaChange(null)}
                  >
                    전체
                  </Button>
                  {detail.areaSet.map((a) => (
                    <Button
                      key={a}
                      size="sm"
                      variant={selectedArea === a ? "default" : "outline"}
                      className="h-7 px-3 text-xs"
                      onClick={() => handleAreaChange(a)}
                    >
                      {a}㎡
                    </Button>
                  ))}
                </div>
              )}
            </Card>

            {/* 가격 통계 요약 */}
            {detail?.stats && (
              <div className="grid grid-cols-3 gap-3">
                <Card className="p-4 bg-card border-border text-center">
                  <p className="text-xs text-muted-foreground mb-1">최저 거래가</p>
                  <p className="text-base font-semibold text-foreground">
                    {formatPrice(detail.stats.min)}
                  </p>
                </Card>
                <Card className="p-4 bg-card border-border text-center">
                  <p className="text-xs text-muted-foreground mb-1">평균 거래가</p>
                  <p className="text-base font-semibold text-primary">
                    {formatPrice(detail.stats.avg)}
                  </p>
                </Card>
                <Card className="p-4 bg-card border-border text-center">
                  <p className="text-xs text-muted-foreground mb-1">최고 거래가</p>
                  <p className="text-base font-semibold text-foreground">
                    {formatPrice(detail.stats.max)}
                  </p>
                </Card>
              </div>
            )}

            {/* 가격 추이 차트 */}
            <Card className="p-5 bg-card border-border">
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm font-medium text-foreground">
                  월별 평균 실거래가 추이
                  {selectedArea ? ` (${selectedArea}㎡)` : ""}
                </p>
                <p className="text-xs text-muted-foreground">2020년~ 국토부 실거래 기준</p>
              </div>

              {detailLoading ? (
                <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
                  로딩 중...
                </div>
              ) : chartData.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
                  거래 데이터가 없습니다
                </div>
              ) : (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="gAptPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#4ADE80" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#4ADE80" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#9CA3AF", fontSize: 10 }}
                        axisLine={{ stroke: "#374151" }}
                        tickLine={false}
                        interval="preserveStartEnd"
                      />
                      <YAxis
                        domain={[yMin, yMax]}
                        tick={{ fill: "#9CA3AF", fontSize: 10 }}
                        axisLine={{ stroke: "#374151" }}
                        tickLine={false}
                        tickFormatter={(v) => `${v}억`}
                        width={40}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#111827",
                          border: "1px solid #374151",
                          borderRadius: "8px",
                          fontSize: "12px",
                        }}
                        labelStyle={{ color: "#9CA3AF" }}
                        formatter={(value: number, _name: string, props) => [
                          `${value}억  (${props.payload.trade_count ?? "-"}건)`,
                          "평균 매매가",
                        ]}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#4ADE80"
                        strokeWidth={2}
                        fill="url(#gAptPrice)"
                        dot={{ fill: "#4ADE80", r: 2, strokeWidth: 0 }}
                        activeDot={{ r: 5, fill: "#4ADE80" }}
                        connectNulls={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>

            {/* 최근 거래 내역 테이블 */}
            {detail && detail.recentTrades.length > 0 && (
              <Card className="bg-card border-border overflow-hidden">
                <div className="px-5 py-3 border-b border-border">
                  <p className="text-sm font-medium text-foreground">최근 실거래 내역 (최대 20건)</p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border bg-muted/20">
                        <th className="text-left py-2.5 px-4 text-muted-foreground font-medium">거래월</th>
                        <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">매매가</th>
                        <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">전용면적</th>
                        <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">층</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.recentTrades.map((t, i) => (
                        <tr key={i} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                          <td className="py-2.5 px-4 text-foreground">{t.ym}</td>
                          <td className="py-2.5 px-4 text-right font-medium text-foreground">
                            {formatPrice(t.price_10k)}
                          </td>
                          <td className="py-2.5 px-4 text-right text-muted-foreground">
                            {t.area ? `${t.area}㎡` : "-"}
                          </td>
                          <td className="py-2.5 px-4 text-right text-muted-foreground">
                            {t.floor ? `${t.floor}층` : "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {/* 면책 공지 */}
            <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/30">
              <Info className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground">
                본 데이터는 국토교통부 실거래가 공개시스템 기준이며, 동일 아파트 내 면적·층수에 따라 실거래가가 다를 수 있습니다.
                전용면적 필터로 원하는 평형대를 선택하세요.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
