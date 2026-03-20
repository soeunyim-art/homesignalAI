"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Info, ChevronDown, ChevronUp } from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, ReferenceLine, CartesianGrid,
} from "recharts";

const DONG_GU_MAP: Record<string, string> = {
  회기동: "동대문구", 이문동: "동대문구", 청량리동: "동대문구", 전농동: "동대문구",
  답십리동: "동대문구", 장안동: "동대문구", 용두동: "동대문구", 신설동: "동대문구",
  휘경동: "동대문구", 제기동: "동대문구",
  길음동: "성북구", 동소문동: "성북구", 돈암동: "성북구", 안암동: "성북구",
  보문동: "성북구", 정릉동: "성북구", 석관동: "성북구", 장위동: "성북구",
  종암동: "성북구", 월곡동: "성북구",
  면목동: "중랑구", 묵동: "중랑구", 신내동: "중랑구", 중화동: "중랑구",
  망우동: "중랑구", 상봉동: "중랑구",
  번동: "강북구", 미아동: "강북구", 수유동: "강북구", 우이동: "강북구",
  방학동: "도봉구", 창동: "도봉구", 도봉동: "도봉구", 쌍문동: "도봉구",
};

const GU_ORDER = ["동대문구", "성북구", "중랑구", "강북구", "도봉구"];

type Prediction = {
  dong: string;
  base_ym: string;
  current_price_10k: number;
  pred_1m_10k: number;
  pred_3m_10k: number;
  pred_6m_10k: number;
  change_1m_pct: number;
  change_3m_pct: number;
  change_6m_pct: number;
  confidence_score: number | null;
};

function ChangeCell({ pct }: { pct: number }) {
  if (pct == null) return <span className="text-muted-foreground">-</span>;
  const color = pct > 0 ? "text-primary" : pct < 0 ? "text-destructive" : "text-muted-foreground";
  return <span className={`font-medium ${color}`}>{pct > 0 ? "+" : ""}{pct.toFixed(1)}%</span>;
}

function ConfidenceBadge({ score }: { score: number }) {
  if (score >= 70) return <Badge className="bg-primary/20 text-primary border-0 text-xs">높음</Badge>;
  if (score >= 40) return <Badge className="bg-yellow-500/20 text-yellow-400 border-0 text-xs">보통</Badge>;
  return (
    <Badge className="bg-destructive/20 text-destructive border-0 text-xs gap-1">
      <AlertTriangle className="h-3 w-3" />낮음
    </Badge>
  );
}

function formatPrice(val: number) {
  if (!val) return "-";
  const eok = Math.floor(val / 10000);
  const cheon = val % 10000;
  if (cheon === 0) return `${eok}억`;
  return `${eok}억 ${Math.round(cheon / 100) * 100}만`;
}

type ChartPoint = { ym: string; real_price?: number; pred_price?: number; trade_count?: number };

function addMonths(ym: string, n: number) {
  const [y, m] = ym.split("-").map(Number);
  const d = new Date(y, m - 1 + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function DongChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as ChartPoint;
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

function DongChart({ prediction: p }: { prediction: Prediction }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ChartPoint[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    if (!open && data === null) {
      setLoading(true);
      try {
        const res = await fetch(`/api/trade-history?dong=${encodeURIComponent(p.dong)}`);
        const json = await res.json();
        const raw: { ym: string; avg_price_10k: number; trade_count: number }[] = json.history ?? [];

        const pointMap: Record<string, ChartPoint> = {};
        for (const r of raw) {
          pointMap[r.ym] = { ym: r.ym, real_price: r.avg_price_10k, trade_count: r.trade_count };
        }
        const realYms = raw.map((r) => r.ym).sort();
        const lastRealYm = realYms[realYms.length - 1] ?? p.base_ym;
        const maxPredYm = addMonths(lastRealYm, 7);
        const predEntries: [string, number][] = ([
          [p.base_ym, p.current_price_10k],
          [addMonths(p.base_ym, 1), p.pred_1m_10k],
          [addMonths(p.base_ym, 3), p.pred_3m_10k],
          [addMonths(p.base_ym, 6), p.pred_6m_10k],
        ] as [string, number][]).filter(([ym]) => ym <= maxPredYm);
        for (const [ym, price] of predEntries) {
          if (!pointMap[ym]) pointMap[ym] = { ym };
          pointMap[ym].pred_price = price;
        }
        setData(Object.values(pointMap).sort((a, b) => a.ym.localeCompare(b.ym)));
      } catch {
        setData([]);
      } finally {
        setLoading(false);
      }
    }
    setOpen((v) => !v);
  }

  return (
    <td colSpan={6} className="p-0">
      <button
        onClick={toggle}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors px-4 py-2"
      >
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {open ? "차트 닫기" : "실거래가 추이 (2025.01~)"}
      </button>
      {open && (
        <div className="h-48 px-4 pb-3">
          {loading ? (
            <p className="text-xs text-muted-foreground text-center pt-10">로딩 중...</p>
          ) : !data?.length ? (
            <p className="text-xs text-muted-foreground text-center pt-10">거래 데이터가 없습니다.</p>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="ym" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => v.slice(2)} />
                <YAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => `${Math.round(v / 10000)}억`} width={36} domain={["auto", "auto"]} />
                <Tooltip content={<DongChartTooltip />} />
                <ReferenceLine x={p.base_ym} stroke="hsl(var(--primary))" strokeDasharray="4 2" label={{ value: "현재", fontSize: 10, fill: "hsl(var(--primary))" }} />
                <Line dataKey="real_price" stroke="#4ADE80" strokeWidth={2} dot={{ r: 3, fill: "#4ADE80", strokeWidth: 0 }} connectNulls={false} name="실거래" />
                <Line dataKey="pred_price" stroke="#3B82F6" strokeWidth={2} strokeDasharray="5 3" dot={{ r: 4, fill: "#3B82F6", strokeWidth: 0 }} connectNulls name="예측" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}
    </td>
  );
}

interface RegionAnalysisProps {
  searchQuery: string;
}

export function RegionAnalysis({ searchQuery }: RegionAnalysisProps) {
  const [grouped, setGrouped] = useState<Record<string, Prediction[]>>({});
  const [loading, setLoading] = useState(true);
  const [baseYm, setBaseYm] = useState("");

  useEffect(() => {
    fetch("/api/predictions")
      .then((r) => r.json())
      .then((preds: Prediction[]) => {
        if (!preds || preds.length === 0) return;
        if (preds[0].base_ym) {
          const [y, m] = preds[0].base_ym.split("-");
          setBaseYm(`${y}.${m.padStart(2, "0")}`);
        }

        const guMap: Record<string, Prediction[]> = {};
        for (const p of preds) {
          const gu = DONG_GU_MAP[p.dong] ?? "기타";
          if (!guMap[gu]) guMap[gu] = [];
          guMap[gu].push(p);
        }
        setGrouped(guMap);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchQuery]);

  const guList = GU_ORDER.filter((gu) => {
    if (!grouped[gu]?.length) return false;
    if (!searchQuery) return true;
    return gu.includes(searchQuery) || grouped[gu].some((p) => p.dong.includes(searchQuery));
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">동별 매매가 예측</h2>
          <p className="text-sm text-muted-foreground">구 단위로 구분된 동별 1·3·6개월 예측</p>
        </div>
        {baseYm && (
          <Badge variant="outline" className="text-primary border-primary">
            기준: {baseYm}
          </Badge>
        )}
      </div>

      {/* 면책 공지 */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/40 border border-border/50">
        <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          본 예측은 <strong className="text-foreground">참고용</strong>이며 Ridge 회귀 모델 기반입니다.
          월 거래량이 적은 동은 신뢰도가 낮습니다. 투자 결정 시 전문가 상담을 권장합니다.
        </p>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground text-center py-12">로딩 중...</p>
      ) : guList.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-12">
          {searchQuery ? `"${searchQuery}" 데이터가 없습니다.` : "예측 데이터가 없습니다."}
        </p>
      ) : (
        <div className="space-y-8">
          {guList.map((gu) => {
            const dongs = grouped[gu].filter((p) =>
              !searchQuery || p.dong.includes(searchQuery) || gu.includes(searchQuery)
            );
            return (
              <div key={gu}>
                {/* 구 구분선 헤더 */}
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-sm font-semibold text-muted-foreground">{gu}</span>
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-xs text-muted-foreground">{dongs.length}개 동</span>
                </div>

                {/* 동별 테이블 */}
                <Card className="bg-card border-border">
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-border bg-muted/20">
                            <th className="text-left py-2.5 px-4 text-muted-foreground font-medium">동</th>
                            <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">현재 매매가</th>
                            <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">1개월 예측</th>
                            <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">3개월 예측</th>
                            <th className="text-right py-2.5 px-4 text-muted-foreground font-medium">6개월 예측</th>
                            <th className="text-center py-2.5 px-4 text-muted-foreground font-medium">신뢰도</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dongs.map((p) => (
                            <React.Fragment key={p.dong}>
                              <tr className="border-b border-border/40 hover:bg-muted/20 transition-colors">
                                <td className="py-3 px-4 font-medium text-foreground">{p.dong}</td>
                                <td className="py-3 px-4 text-right text-foreground">{formatPrice(p.current_price_10k)}</td>
                                <td className="py-3 px-4 text-right">
                                  <div className="flex flex-col items-end gap-0.5">
                                    <span className="text-foreground text-xs">{formatPrice(p.pred_1m_10k)}</span>
                                    <ChangeCell pct={p.change_1m_pct} />
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-right">
                                  <div className="flex flex-col items-end gap-0.5">
                                    <span className="text-foreground text-xs">{formatPrice(p.pred_3m_10k)}</span>
                                    <ChangeCell pct={p.change_3m_pct} />
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-right">
                                  <div className="flex flex-col items-end gap-0.5">
                                    <span className="text-foreground text-xs">{formatPrice(p.pred_6m_10k)}</span>
                                    <ChangeCell pct={p.change_6m_pct} />
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-center">
                                  <ConfidenceBadge score={p.confidence_score ?? 50} />
                                </td>
                              </tr>
                              <tr className="border-b border-border/20 bg-muted/5">
                                <DongChart prediction={p} />
                              </tr>
                            </React.Fragment>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>
      )}

      <p className="text-xs text-muted-foreground text-center">
        * 신뢰도는 월 거래량 기반 (높음 ≥70점 / 보통 40~69점 / 낮음 &lt;40점)
      </p>
    </div>
  );
}
