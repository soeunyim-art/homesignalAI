"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Calendar } from "lucide-react";
import { useEffect, useState } from "react";


type ChartPoint = {
  month: string;
  actual: number | null;
  predicted: number | null;
  upper: number | null;
  lower: number | null;
};

function addMonths(ym: string, n: number): string {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m - 1 + n);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function PricePredictionChart() {
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [dateLabel, setDateLabel] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/predictions")
      .then((r) => r.json())
      .then((preds) => {
        if (!preds || preds.length === 0) return;

        const avg = (key: string) =>
          preds.reduce((s: number, p: Record<string, number>) => s + (p[key] ?? 0), 0) / preds.length;

        const bym: string = preds[0].base_ym;
        const toEok = (v: number) => Math.round((v / 10000) * 10) / 10;

        const current = toEok(avg("current_price_10k"));
        const p1 = toEok(avg("pred_1m_10k"));
        const p2 = toEok(avg("pred_2m_10k"));
        const p3 = toEok(avg("pred_3m_10k"));
        const band = 0.3; // 예측 밴드 ±0.3억

        const baseLabel = addMonths(bym, 0);
        const p1Label = addMonths(bym, 1);
        const p2Label = addMonths(bym, 2);
        const p3Label = addMonths(bym, 3);

        setDateLabel(`${baseLabel} - ${p3Label} (예측)`);
        setChartData([
          { month: baseLabel, actual: current, predicted: current, upper: current, lower: current },
          { month: p1Label, actual: null, predicted: p1, upper: +(p1 + band).toFixed(1), lower: +(p1 - band).toFixed(1) },
          { month: p2Label, actual: null, predicted: p2, upper: +(p2 + band * 1.5).toFixed(1), lower: +(p2 - band * 1.5).toFixed(1) },
          { month: p3Label, actual: null, predicted: p3, upper: +(p3 + band * 2).toFixed(1), lower: +(p3 - band * 2).toFixed(1) },
        ]);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const allVals = chartData.flatMap((d) => [d.actual, d.upper, d.lower].filter(Boolean) as number[]);
  const yMin = allVals.length ? Math.floor(Math.min(...allVals) - 0.5) : 10;
  const yMax = allVals.length ? Math.ceil(Math.max(...allVals) + 0.5) : 15;

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg text-foreground">AI 가격 예측</CardTitle>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            <span>{loading ? "로딩 중..." : dateLabel || "데이터 없음"}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!loading && chartData.length === 0 ? (
          <div className="h-[280px] flex items-center justify-center text-sm text-muted-foreground">
            예측 데이터가 없습니다. predict_model.py를 먼저 실행해 주세요.
          </div>
        ) : (
          <>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4ADE80" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#4ADE80" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                  <XAxis dataKey="month" tick={{ fill: "#9CA3AF", fontSize: 11 }} tickLine={{ stroke: "#374151" }} axisLine={{ stroke: "#374151" }} />
                  <YAxis domain={[yMin, yMax]} tick={{ fill: "#9CA3AF", fontSize: 11 }} tickLine={{ stroke: "#374151" }} axisLine={{ stroke: "#374151" }} tickFormatter={(v) => `${v}억`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: "8px", color: "#E5E7EB" }}
                    labelStyle={{ color: "#9CA3AF" }}
                    formatter={(value: number, name: string) => {
                      const labels: Record<string, string> = { actual: "실거래", predicted: "예측 중위", upper: "상한", lower: "하한" };
                      return [`${value}억`, labels[name] || name];
                    }}
                  />
                  <Legend
                    verticalAlign="top"
                    height={36}
                    formatter={(value) => {
                      const labels: Record<string, string> = { actual: "실거래", predicted: "예측 중위", upper: "확률 밴드" };
                      return <span style={{ color: "#9CA3AF", fontSize: 12 }}>{labels[value] || value}</span>;
                    }}
                  />
                  <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#colorBand)" stackId="band" />
                  <Area type="monotone" dataKey="lower" stroke="transparent" fill="transparent" stackId="band" />
                  <Area type="monotone" dataKey="actual" stroke="#4ADE80" strokeWidth={2} fill="url(#colorActual)" dot={{ fill: "#4ADE80", strokeWidth: 0, r: 3 }} activeDot={{ r: 5, fill: "#4ADE80" }} />
                  <Area type="monotone" dataKey="predicted" stroke="#3B82F6" strokeWidth={2} strokeDasharray="5 5" fill="url(#colorPredicted)" dot={{ fill: "#3B82F6", strokeWidth: 0, r: 3 }} activeDot={{ r: 5, fill: "#3B82F6" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-border">
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-primary rounded" />
                <span className="text-xs text-muted-foreground">실거래</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-accent rounded" />
                <span className="text-xs text-muted-foreground">예측 중위</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-3 bg-accent/20 rounded" />
                <span className="text-xs text-muted-foreground">확률 밴드</span>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
