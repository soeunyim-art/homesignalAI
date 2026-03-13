"use client";

import { TrendingUp, TrendingDown, BarChart3, Percent, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { useEffect, useState } from "react";

type Prediction = {
  current_price_10k: number;
  pred_1m_10k: number;
  change_1m_pct: number;
  change_3m_pct: number;
};

export function KPITicker() {
  const [preds, setPreds] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/predictions")
      .then((r) => r.json())
      .then(setPreds)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const avg = (key: keyof Prediction) =>
    preds.length > 0
      ? preds.reduce((s, p) => s + ((p[key] as number) ?? 0), 0) / preds.length
      : null;

  const avgPrice = avg("current_price_10k");
  const avgChange1m = avg("change_1m_pct");
  const avgChange3m = avg("change_3m_pct");
  const risingCount = preds.filter((p) => (p.change_1m_pct ?? 0) > 0).length;

  const fmt억 = (v: number) => `${(v / 10000).toFixed(1)}억`;
  const fmtPct = (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;

  const kpiData = [
    {
      label: "동북권 평균 매매가",
      value: loading ? "..." : avgPrice ? fmt억(avgPrice) : "-",
      change: avgChange1m != null ? fmtPct(avgChange1m) : "-",
      trend: (avgChange1m ?? 0) >= 0 ? "up" : "down",
      icon: BarChart3,
    },
    {
      label: "분석 구 수",
      value: loading ? "..." : preds.length > 0 ? "5개 구" : "-",
      change: preds.length > 0 ? `${preds.length}개 동` : "-",
      trend: "up",
      icon: Activity,
    },
    {
      label: "1개월 후 상승 예상",
      value: loading ? "..." : preds.length > 0 ? `${risingCount}/${preds.length}개 동` : "-",
      change: avgChange1m != null ? fmtPct(avgChange1m) : "-",
      trend: (avgChange1m ?? 0) >= 0 ? "up" : "down",
      icon: TrendingDown,
    },
    {
      label: "3개월 예상 변동률",
      value: loading ? "..." : avgChange3m != null ? fmtPct(avgChange3m) : "-",
      change: "AI 예측 기반",
      trend: (avgChange3m ?? 0) >= 0 ? "up" : "down",
      icon: Percent,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {kpiData.map((kpi, index) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <Card className="p-4 bg-card border-border hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground mb-1">{kpi.label}</p>
                <p className="text-2xl font-bold text-foreground">{kpi.value}</p>
              </div>
              <div className="p-2 rounded-lg bg-secondary">
                <kpi.icon className="h-4 w-4 text-primary" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-2">
              {kpi.trend === "up" ? (
                <TrendingUp className="h-3 w-3 text-primary" />
              ) : (
                <TrendingDown className="h-3 w-3 text-destructive" />
              )}
              <span
                className={`text-xs font-medium ${
                  kpi.trend === "up" ? "text-primary" : "text-destructive"
                }`}
              >
                {kpi.change}
              </span>
              <span className="text-xs text-muted-foreground ml-1">전월 대비</span>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
