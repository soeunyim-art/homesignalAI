"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Info } from "lucide-react";

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
  current_price_10k: number;
  change_1m_pct: number;
  change_3m_pct: number;
  base_ym: string;
  confidence_score: number | null;
};

type GuStat = {
  name: string;
  avgPrice: string;
  change: string;
  change3m: string;
  dongCount: number;
  confidence: number;
};

function ConfidenceBadge({ score }: { score: number }) {
  if (score >= 70) {
    return <Badge className="bg-primary/20 text-primary border-0 text-xs">높음</Badge>;
  }
  if (score >= 40) {
    return <Badge className="bg-yellow-500/20 text-yellow-400 border-0 text-xs">보통</Badge>;
  }
  return (
    <Badge className="bg-destructive/20 text-destructive border-0 text-xs gap-1">
      <AlertTriangle className="h-3 w-3" />
      낮음
    </Badge>
  );
}

interface RegionAnalysisProps {
  searchQuery: string;
}

export function RegionAnalysis({ searchQuery }: RegionAnalysisProps) {
  const [guStats, setGuStats] = useState<GuStat[]>([]);
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
          const gu = DONG_GU_MAP[p.dong] ?? p.dong;
          if (!guMap[gu]) guMap[gu] = [];
          guMap[gu].push(p);
        }

        const filtered = GU_ORDER.filter((gu) => {
          if (!guMap[gu]?.length) return false;
          if (!searchQuery) return true;
          return gu.includes(searchQuery);
        });

        const stats = filtered.map((gu) => {
          const rows = guMap[gu];
          const avgPrice = rows.reduce((s, r) => s + (r.current_price_10k ?? 0), 0) / rows.length;
          const change1m = rows.reduce((s, r) => s + (r.change_1m_pct ?? 0), 0) / rows.length;
          const change3m = rows.reduce((s, r) => s + (r.change_3m_pct ?? 0), 0) / rows.length;
          const scores = rows.map((r) => r.confidence_score ?? 50);
          const confidence = Math.round(scores.reduce((s, v) => s + v, 0) / scores.length);
          return {
            name: gu,
            avgPrice: `${(avgPrice / 10000).toFixed(1)}억`,
            change: `${change1m > 0 ? "+" : ""}${change1m.toFixed(1)}%`,
            change3m: `${change3m > 0 ? "+" : ""}${change3m.toFixed(1)}%`,
            dongCount: rows.length,
            confidence,
          };
        });

        setGuStats(stats);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchQuery]);

  const hasLowConfidence = guStats.some((s) => s.confidence < 40);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            {searchQuery || "분석 대상 5개 구"} 지역 분석
          </h2>
          <p className="text-sm text-muted-foreground">
            AI 기반 구별 매매가 및 변동률 분석
          </p>
        </div>
        {baseYm && (
          <Badge variant="outline" className="text-primary border-primary">
            분석 기준: {baseYm}
          </Badge>
        )}
      </div>

      {/* 면책 공지 */}
      <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/40 border border-border/50">
        <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          본 예측은 <strong className="text-foreground">참고용</strong>이며 실제 시장과 다를 수 있습니다.
          Ridge 회귀 모델 기반으로 월 거래량이 적은 지역은 신뢰도가 낮게 표시됩니다.
          투자 결정 시 반드시 전문가 상담을 권장합니다.
        </p>
      </div>

      {/* 신뢰도 낮음 경고 */}
      {hasLowConfidence && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
          <AlertTriangle className="h-4 w-4 text-destructive shrink-0" />
          <p className="text-xs text-destructive">
            일부 지역의 신뢰도가 낮습니다. 월 거래량 부족으로 예측 정확도가 떨어질 수 있습니다.
          </p>
        </div>
      )}

      {/* District Comparison Table */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-base font-medium">구별 비교</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground text-center py-8">로딩 중...</p>
          ) : guStats.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {searchQuery ? `"${searchQuery}" 데이터가 없습니다.` : "예측 데이터가 없습니다. predict_model.py를 먼저 실행해 주세요."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-muted-foreground font-medium">지역</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">평균 매매가</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">1개월 변동</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">3개월 예측</th>
                    <th className="text-center py-3 px-4 text-muted-foreground font-medium">신뢰도</th>
                    <th className="text-right py-3 px-4 text-muted-foreground font-medium">분석 동 수</th>
                  </tr>
                </thead>
                <tbody>
                  {guStats.map((stat) => (
                    <tr key={stat.name} className="border-b border-border/50 hover:bg-muted/30">
                      <td className="py-3 px-4 font-medium text-foreground">{stat.name}</td>
                      <td className="py-3 px-4 text-right text-foreground">{stat.avgPrice}</td>
                      <td className={`py-3 px-4 text-right font-medium ${stat.change.startsWith("+") ? "text-primary" : "text-destructive"}`}>
                        {stat.change}
                      </td>
                      <td className={`py-3 px-4 text-right font-medium ${stat.change3m.startsWith("+") ? "text-primary" : "text-destructive"}`}>
                        {stat.change3m}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <ConfidenceBadge score={stat.confidence} />
                      </td>
                      <td className="py-3 px-4 text-right text-muted-foreground">
                        {stat.dongCount}개 동
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">
        * 신뢰도는 해당 구의 월 평균 거래량 기반으로 산출됩니다 (높음 ≥70점 / 보통 40~69점 / 낮음 &lt;40점)
      </p>
    </div>
  );
}
