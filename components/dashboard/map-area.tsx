"use client";

import { useEffect, useState } from "react";
import { MapPin, TrendingUp, TrendingDown, AlertTriangle, Info, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GuDetailSheet } from "./gu-detail-sheet";

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
  pred_1m_10k: number;
  confidence_score: number | null;
};

type GuStat = {
  gu: string;
  avgPrice: number;
  change1m: number;
  dongCount: number;
  avgConfidence: number;
};

function ConfidenceBadge({ score }: { score: number }) {
  if (score >= 70) {
    return <Badge className="bg-primary/20 text-primary border-0 text-xs">신뢰도 높음</Badge>;
  }
  if (score >= 40) {
    return <Badge className="bg-yellow-500/20 text-yellow-400 border-0 text-xs">신뢰도 보통</Badge>;
  }
  return (
    <Badge className="bg-destructive/20 text-destructive border-0 text-xs gap-1">
      <AlertTriangle className="h-3 w-3" />
      신뢰도 낮음
    </Badge>
  );
}

export function MapArea() {
  const [guStats, setGuStats] = useState<GuStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGu, setSelectedGu] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/predictions")
      .then((r) => r.json())
      .then((preds: Prediction[]) => {
        if (!preds || preds.length === 0) return;

        const guMap: Record<string, Prediction[]> = {};
        for (const p of preds) {
          const gu = DONG_GU_MAP[p.dong] ?? p.dong;
          if (!guMap[gu]) guMap[gu] = [];
          guMap[gu].push(p);
        }

        const stats = GU_ORDER
          .filter((gu) => guMap[gu]?.length > 0)
          .map((gu) => {
            const rows = guMap[gu];
            const avgPrice = rows.reduce((s, r) => s + (r.current_price_10k ?? 0), 0) / rows.length;
            const change1m = rows.reduce((s, r) => s + (r.change_1m_pct ?? 0), 0) / rows.length;
            const confidenceScores = rows.map((r) => r.confidence_score ?? 50);
            const avgConfidence = confidenceScores.reduce((s, v) => s + v, 0) / confidenceScores.length;
            return { gu, avgPrice, change1m, dongCount: rows.length, avgConfidence };
          });

        setGuStats(stats);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Card className="h-[500px] bg-card border-border flex items-center justify-center">
        <p className="text-sm text-muted-foreground">데이터 로딩 중...</p>
      </Card>
    );
  }

  if (guStats.length === 0) {
    return (
      <Card className="h-[500px] bg-card border-border flex items-center justify-center">
        <p className="text-sm text-muted-foreground">
          예측 데이터가 없습니다. predict_model.py를 먼저 실행해 주세요.
        </p>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border p-6">
      <div className="flex items-center gap-2 mb-2">
        <MapPin className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold text-foreground">분석 대상 구별 현황</h3>
        <Badge variant="outline" className="text-primary border-primary ml-auto">
          {guStats.length}개 구 분석 중
        </Badge>
      </div>

      {/* 면책 공지 */}
      <div className="flex items-start gap-2 mb-5 p-3 rounded-lg bg-muted/40 border border-border/50">
        <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          본 예측은 2020년~현재 실거래 데이터 기반 Ridge 회귀 모델의 결과입니다.
          월 거래량이 적은 동은 신뢰도가 낮을 수 있으며, <strong className="text-foreground">투자 결정 시 반드시 전문가 상담을 받으시기 바랍니다.</strong>
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {guStats.map((stat, index) => (
          <motion.div
            key={stat.gu}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => setSelectedGu(stat.gu)}
            className={`p-4 rounded-xl border transition-all cursor-pointer ${
              stat.avgConfidence < 40
                ? "bg-destructive/5 border-destructive/20 hover:border-destructive/40"
                : "bg-secondary/50 border-border hover:border-primary/40"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <MapPin className="h-4 w-4 text-primary" />
                </div>
                <span className="text-base font-semibold text-foreground">{stat.gu}</span>
              </div>
              <div className={`flex items-center gap-1 text-sm font-medium ${stat.change1m >= 0 ? "text-primary" : "text-destructive"}`}>
                {stat.change1m >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                {stat.change1m > 0 ? "+" : ""}{stat.change1m.toFixed(1)}%
              </div>
            </div>

            <div className="space-y-1 mb-3">
              <p className="text-2xl font-bold text-foreground">
                {(stat.avgPrice / 10000).toFixed(1)}억
              </p>
              <p className="text-xs text-muted-foreground">
                평균 매매가 · {stat.dongCount}개 동 분석
              </p>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-border/50">
              <p className="text-xs text-muted-foreground">
                1개월 예측:{" "}
                <span className={stat.change1m >= 0 ? "text-primary font-medium" : "text-destructive font-medium"}>
                  {stat.change1m > 0 ? "+" : ""}{stat.change1m.toFixed(2)}%
                </span>
              </p>
              <ConfidenceBadge score={stat.avgConfidence} />
            </div>

            <div className="flex items-center justify-end mt-2 pt-2">
              <span className="text-xs text-muted-foreground flex items-center gap-1 hover:text-primary transition-colors">
                매매가 추이 보기 <ChevronRight className="h-3 w-3" />
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      <GuDetailSheet
        gu={selectedGu}
        open={!!selectedGu}
        onClose={() => setSelectedGu(null)}
      />
    </Card>
  );
}
