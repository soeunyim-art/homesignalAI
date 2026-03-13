"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

function addMonths(ym: string, n: number): string {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m - 1 + n);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

type Prediction = {
  dong: string;
  base_ym: string;
  current_price_10k: number;
  pred_1m_10k: number;
  pred_2m_10k: number;
  pred_3m_10k: number;
  change_1m_pct: number;
  change_3m_pct: number;
};

type ChartPoint = {
  month: string;
  actual: number | null;
  predicted: number | null;
  upper: number | null;
  lower: number | null;
};

interface PriceTrendsProps {
  searchQuery: string;
}

export function PriceTrends({ searchQuery }: PriceTrendsProps) {
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [baseLabel, setBaseLabel] = useState("");
  const [change1m, setChange1m] = useState<number | null>(null);
  const [change3m, setChange3m] = useState<number | null>(null);
  const [pred3Label, setPred3Label] = useState("");
  const [pred3Price, setPred3Price] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/predictions")
      .then((r) => r.json())
      .then((preds: Prediction[]) => {
        if (!preds || preds.length === 0) return;

        const avg = (key: keyof Prediction) =>
          preds.reduce((s, p) => s + ((p[key] as number) ?? 0), 0) / preds.length;

        const bym = preds[0].base_ym;
        const toEok = (v: number) => Math.round((v / 10000) * 10) / 10;
        const band = 0.3;

        const current = toEok(avg("current_price_10k"));
        const p1 = toEok(avg("pred_1m_10k"));
        const p2 = toEok(avg("pred_2m_10k"));
        const p3 = toEok(avg("pred_3m_10k"));

        const bl = addMonths(bym, 0);
        const p1l = addMonths(bym, 1);
        const p2l = addMonths(bym, 2);
        const p3l = addMonths(bym, 3);

        setBaseLabel(bl);
        setPred3Label(p3l);
        setPred3Price(p3);
        setChange1m(avg("change_1m_pct"));
        setChange3m(avg("change_3m_pct"));

        setChartData([
          { month: bl, actual: current, predicted: current, upper: current, lower: current },
          { month: p1l, actual: null, predicted: p1, upper: +(p1 + band).toFixed(1), lower: +(p1 - band).toFixed(1) },
          { month: p2l, actual: null, predicted: p2, upper: +(p2 + band * 1.5).toFixed(1), lower: +(p2 - band * 1.5).toFixed(1) },
          { month: p3l, actual: null, predicted: p3, upper: +(p3 + band * 2).toFixed(1), lower: +(p3 - band * 2).toFixed(1) },
        ]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchQuery]);

  const allVals = chartData.flatMap((d) => [d.actual, d.upper, d.lower].filter(Boolean) as number[]);
  const yMin = allVals.length ? Math.floor(Math.min(...allVals) - 0.5) : 5;
  const yMax = allVals.length ? Math.ceil(Math.max(...allVals) + 0.5) : 15;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            {searchQuery || "분석 대상 5개 구"} 가격 동향
          </h2>
          <p className="text-sm text-muted-foreground">
            AI 예측 가격 및 확률 밴드 분석
          </p>
        </div>
        {baseLabel && (
          <Badge variant="outline" className="text-primary border-primary">
            기준: {baseLabel}
          </Badge>
        )}
      </div>

      {/* Main Price Chart */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary" />
              AI 예측 가격 추이
            </CardTitle>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <div className="w-3 h-0.5 bg-primary" />
                <span className="text-muted-foreground">실거래가</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-0.5 bg-accent" />
                <span className="text-muted-foreground">AI 예측</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-accent/20 border border-accent/50" />
                <span className="text-muted-foreground">확률 밴드</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-[320px] flex items-center justify-center text-sm text-muted-foreground">
              로딩 중...
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-[320px] flex items-center justify-center text-sm text-muted-foreground">
              예측 데이터가 없습니다. predict_model.py를 먼저 실행해 주세요.
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="ptColorBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="month"
                    tick={{ fill: "#9CA3AF", fontSize: 11 }}
                    axisLine={{ stroke: "#374151" }}
                  />
                  <YAxis
                    domain={[yMin, yMax]}
                    tick={{ fill: "#9CA3AF", fontSize: 11 }}
                    axisLine={{ stroke: "#374151" }}
                    tickFormatter={(v) => `${v}억`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1F2937",
                      border: "1px solid #374151",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#E5E7EB" }}
                    formatter={(value: number, name: string) => {
                      if (!value) return ["-", name];
                      const labels: Record<string, string> = {
                        actual: "실거래가",
                        predicted: "AI 예측",
                        upper: "상한",
                        lower: "하한",
                      };
                      return [`${value}억`, labels[name] || name];
                    }}
                  />
                  {baseLabel && (
                    <ReferenceLine
                      x={baseLabel}
                      stroke="#4ADE80"
                      strokeDasharray="3 3"
                      label={{ value: "현재", fill: "#4ADE80", fontSize: 10 }}
                    />
                  )}
                  <Area
                    type="monotone"
                    dataKey="upper"
                    stroke="transparent"
                    fill="url(#ptColorBand)"
                    stackId="band"
                  />
                  <Area
                    type="monotone"
                    dataKey="lower"
                    stroke="transparent"
                    fill="transparent"
                    stackId="band"
                  />
                  <Area
                    type="monotone"
                    dataKey="actual"
                    stroke="#4ADE80"
                    strokeWidth={2}
                    fill="transparent"
                    dot={{ fill: "#4ADE80", strokeWidth: 2, r: 4 }}
                    connectNulls={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="predicted"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    fill="transparent"
                    dot={{ fill: "#3B82F6", strokeWidth: 2, r: 4 }}
                    connectNulls={false}
                  />
                </AreaChart>
              </ResponsiveContainer>

              {pred3Price !== null && (
                <div className="mt-4 flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div>
                    <p className="text-sm text-foreground font-medium">
                      3개월 후 예측 ({pred3Label}):{" "}
                      <span className="text-primary">{pred3Price}억</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      1개월 변동률: {change1m != null ? `${change1m > 0 ? "+" : ""}${change1m.toFixed(1)}%` : "-"} ·
                      3개월 변동률: {change3m != null ? `${change3m > 0 ? "+" : ""}${change3m.toFixed(1)}%` : "-"}
                    </p>
                  </div>
                  <Badge className="bg-primary/20 text-primary border-0">
                    AI 예측 기반
                  </Badge>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">
        * AI 예측은 과거 데이터 기반이며, 실제 가격과 다를 수 있습니다. 투자 결정 시 전문가 상담을 권장합니다.
      </p>
    </div>
  );
}
