"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, BarChart2, Info } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

type HistoryPoint = {
  ym: string;
  avg_price_10k: number;
  trade_count: number;
};

type Predictions = {
  base_ym: string;
  current: number;
  pred_1m: number;
  pred_2m: number;
  pred_3m: number;
};

type ChartPoint = {
  label: string;
  actual: number | null;
  predicted: number | null;
  trade_count?: number;
  isPred?: boolean;
};

function addMonths(ym: string, n: number): string {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m - 1 + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function ymToLabel(ym: string): string {
  const [y, m] = ym.split("-");
  return `${y.slice(2)}.${m}`;
}

interface GuDetailSheetProps {
  gu: string | null;
  open: boolean;
  onClose: () => void;
}

export function GuDetailSheet({ gu, open, onClose }: GuDetailSheetProps) {
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [baseYm, setBaseYm] = useState("");
  const [change, setChange] = useState<number | null>(null);

  useEffect(() => {
    if (!gu || !open) return;
    setLoading(true);
    setChartData([]);

    fetch(`/api/trade-history?gu=${encodeURIComponent(gu)}`)
      .then((r) => r.json())
      .then((data: { history: HistoryPoint[]; predictions: Predictions | null }) => {
        const { history, predictions } = data;

        // 실거래 포인트
        const actuals: ChartPoint[] = (history ?? []).map((h) => ({
          label: ymToLabel(h.ym),
          actual: Math.round((h.avg_price_10k / 10000) * 10) / 10,
          predicted: null,
          trade_count: h.trade_count,
          isPred: false,
        }));

        // 예측 포인트
        const predPoints: ChartPoint[] = [];
        if (predictions) {
          setBaseYm(predictions.base_ym);
          const toEok = (v: number) => Math.round((v / 10000) * 10) / 10;
          const cur = toEok(predictions.current);
          const p1 = toEok(predictions.pred_1m);
          const p3 = toEok(predictions.pred_3m);
          setChange(p3 > 0 ? ((p3 - cur) / cur) * 100 : null);

          // base_ym이 history에 없으면 현재가 포인트 추가
          const baseLabel = ymToLabel(predictions.base_ym);
          if (!actuals.find((a) => a.label === baseLabel)) {
            predPoints.push({ label: baseLabel, actual: cur, predicted: cur, isPred: false });
          } else {
            // 기존 실거래 포인트에 predicted 연결
            const idx = actuals.findIndex((a) => a.label === baseLabel);
            if (idx >= 0) actuals[idx].predicted = actuals[idx].actual;
          }

          predPoints.push({
            label: ymToLabel(addMonths(predictions.base_ym, 1)),
            actual: null,
            predicted: toEok(predictions.pred_1m),
            isPred: true,
          });
          predPoints.push({
            label: ymToLabel(addMonths(predictions.base_ym, 2)),
            actual: null,
            predicted: Math.round((toEok(predictions.pred_1m) + toEok(predictions.pred_2m)) / 2 * 10) / 10,
            isPred: true,
          });
          predPoints.push({
            label: ymToLabel(addMonths(predictions.base_ym, 3)),
            actual: null,
            predicted: toEok(predictions.pred_3m),
            isPred: true,
          });
        }

        setChartData([...actuals, ...predPoints]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [gu, open]);

  const allVals = chartData.flatMap((d) =>
    [d.actual, d.predicted].filter((v): v is number => v !== null)
  );
  const yMin = allVals.length ? Math.floor(Math.min(...allVals) - 0.5) : 5;
  const yMax = allVals.length ? Math.ceil(Math.max(...allVals) + 0.5) : 15;
  const baseLabel = baseYm ? ymToLabel(baseYm) : null;

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="right" className="w-full sm:max-w-2xl bg-card border-border overflow-y-auto">
        <SheetHeader className="mb-6">
          <div className="flex items-center gap-3">
            <BarChart2 className="h-5 w-5 text-primary" />
            <SheetTitle className="text-foreground text-lg">
              {gu} 매매가 추이
            </SheetTitle>
            {change !== null && (
              <Badge className={`ml-auto ${change >= 0 ? "bg-primary/20 text-primary" : "bg-destructive/20 text-destructive"} border-0`}>
                {change >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                3개월 예측 {change > 0 ? "+" : ""}{change.toFixed(1)}%
              </Badge>
            )}
          </div>
        </SheetHeader>

        {loading ? (
          <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
            데이터 로딩 중...
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
            2025년 이후 거래 데이터가 없습니다.
          </div>
        ) : (
          <>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gActual" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4ADE80" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#4ADE80" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gPred" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="label" tick={{ fill: "#9CA3AF", fontSize: 11 }} axisLine={{ stroke: "#374151" }} tickLine={false} />
                  <YAxis
                    domain={[yMin, yMax]}
                    tick={{ fill: "#9CA3AF", fontSize: 11 }}
                    axisLine={{ stroke: "#374151" }}
                    tickLine={false}
                    tickFormatter={(v) => `${v}억`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: "8px" }}
                    labelStyle={{ color: "#9CA3AF" }}
                    formatter={(value: number, name: string) => {
                      if (value == null) return ["-", name];
                      return [`${value}억`, name === "actual" ? "실거래 평균" : "AI 예측"];
                    }}
                  />
                  {baseLabel && (
                    <ReferenceLine
                      x={baseLabel}
                      stroke="#4ADE80"
                      strokeDasharray="4 4"
                      label={{ value: "현재", fill: "#4ADE80", fontSize: 10 }}
                    />
                  )}
                  <Area
                    type="monotone"
                    dataKey="actual"
                    stroke="#4ADE80"
                    strokeWidth={2}
                    fill="url(#gActual)"
                    dot={{ fill: "#4ADE80", r: 3, strokeWidth: 0 }}
                    connectNulls={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="predicted"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fill="url(#gPred)"
                    dot={{ fill: "#3B82F6", r: 3, strokeWidth: 0 }}
                    connectNulls={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* 범례 */}
            <div className="flex items-center gap-6 mt-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-6 h-0.5 bg-primary rounded" />
                <span className="text-xs text-muted-foreground">실거래 평균</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-6 h-0.5 bg-accent rounded" style={{ borderTop: "2px dashed #3B82F6", background: "none" }} />
                <span className="text-xs text-muted-foreground">AI 예측 (1~3개월)</span>
              </div>
            </div>

            {/* 거래량 표 */}
            {chartData.some((d) => d.trade_count) && (
              <div className="border border-border rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border bg-muted/30">
                      <th className="text-left py-2 px-3 text-muted-foreground">월</th>
                      <th className="text-right py-2 px-3 text-muted-foreground">평균 매매가</th>
                      <th className="text-right py-2 px-3 text-muted-foreground">거래 건수</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chartData.filter((d) => d.actual !== null).map((d) => (
                      <tr key={d.label} className="border-b border-border/50 hover:bg-muted/20">
                        <td className="py-2 px-3 text-foreground">{d.label}</td>
                        <td className="py-2 px-3 text-right text-foreground">{d.actual}억</td>
                        <td className="py-2 px-3 text-right text-muted-foreground">{d.trade_count ?? "-"}건</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex items-start gap-2 mt-4 p-3 rounded-lg bg-muted/30">
              <Info className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground">
                실거래가는 국토부 실거래 데이터 기준이며, AI 예측은 참고용입니다. 투자 결정 시 전문가 상담을 권장합니다.
              </p>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
