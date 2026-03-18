"use client";

import { WireframeBox } from "./wireframe-box";
import { ChevronLeft, Plus, X, TrendingUp, TrendingDown, Minus, Check, AlertCircle } from "lucide-react";

export function Screen5Compare() {
  return (
    <div className="w-full max-w-[375px] mx-auto bg-background border border-border rounded-2xl overflow-hidden shadow-xl">
      {/* Status Bar */}
      <div className="h-6 bg-card flex items-center justify-between px-4">
        <span className="text-[10px] text-muted-foreground font-mono">9:41</span>
        <div className="flex gap-1">
          <div className="w-4 h-2 bg-muted-foreground/30 rounded-sm" />
          <div className="w-4 h-2 bg-muted-foreground/30 rounded-sm" />
          <div className="w-6 h-2 bg-primary/50 rounded-sm" />
        </div>
      </div>

      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
              <ChevronLeft className="w-4 h-4 text-foreground" />
            </div>
            <span className="text-sm font-medium text-foreground">매물 비교</span>
          </div>
          <button className="flex items-center gap-1 px-3 py-1.5 bg-primary/20 rounded-full text-xs text-primary">
            <Plus className="w-3 h-3" />
            추가
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="h-[520px] overflow-y-auto p-4 space-y-4">
        {/* Selected Properties */}
        <div className="flex gap-2">
          {[
            { name: "래미안 크레시티", area: "84㎡" },
            { name: "아크로 리버파크", area: "84㎡" },
          ].map((prop, i) => (
            <div key={i} className="flex-1 p-2 bg-card border border-border rounded-lg">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-foreground truncate">{prop.name}</p>
                  <p className="text-[10px] text-muted-foreground">{prop.area}</p>
                </div>
                <button className="w-5 h-5 rounded-full bg-muted flex items-center justify-center">
                  <X className="w-3 h-3 text-muted-foreground" />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Price Comparison */}
        <WireframeBox label="가격 비교" className="!p-3">
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div />
              <div className="text-[10px] text-muted-foreground">래미안 크레시티</div>
              <div className="text-[10px] text-muted-foreground">아크로 리버파크</div>
            </div>
            
            {[
              { label: "매매가", v1: "18.5억", v2: "24.2억" },
              { label: "전세가", v1: "12.2억", v2: "15.8억" },
              { label: "전세가율", v1: "66%", v2: "65%" },
              { label: "평당가", v1: "7,280만", v2: "9,520만" },
            ].map((row) => (
              <div key={row.label} className="grid grid-cols-3 gap-2 items-center">
                <span className="text-xs text-muted-foreground">{row.label}</span>
                <span className="text-xs font-medium text-foreground text-center">{row.v1}</span>
                <span className="text-xs font-medium text-foreground text-center">{row.v2}</span>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* AI Prediction Comparison */}
        <WireframeBox label="AI 예측 비교" className="!p-3">
          <div className="grid grid-cols-2 gap-3">
            {[
              { name: "래미안 크레시티", pred: "+3.8%", conf: "82%", trend: "up" },
              { name: "아크로 리버파크", pred: "+2.1%", conf: "79%", trend: "up" },
            ].map((item) => (
              <div key={item.name} className="p-3 bg-muted/30 rounded-lg text-center">
                <p className="text-[10px] text-muted-foreground mb-2 truncate">{item.name}</p>
                <div className="flex items-center justify-center gap-1 mb-1">
                  {item.trend === "up" ? (
                    <TrendingUp className="w-4 h-4 text-primary" />
                  ) : item.trend === "down" ? (
                    <TrendingDown className="w-4 h-4 text-destructive" />
                  ) : (
                    <Minus className="w-4 h-4 text-muted-foreground" />
                  )}
                  <span className={`text-lg font-bold ${
                    item.trend === "up" ? "text-primary" :
                    item.trend === "down" ? "text-destructive" : "text-foreground"
                  }`}>
                    {item.pred}
                  </span>
                </div>
                <p className="text-[10px] text-muted-foreground">신뢰도 {item.conf}</p>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Risk Comparison */}
        <WireframeBox label="리스크 비교" className="!p-3">
          <div className="space-y-2">
            {[
              { label: "공급 리스크", v1: 72, v2: 45 },
              { label: "금리 민감도", v1: 55, v2: 60 },
              { label: "가격 변동성", v1: 38, v2: 42 },
            ].map((item) => (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">{item.label}</span>
                  <div className="flex gap-4">
                    <span className="text-foreground w-8 text-right">{item.v1}%</span>
                    <span className="text-foreground w-8 text-right">{item.v2}%</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.v1 > 60 ? "bg-destructive" : item.v1 > 30 ? "bg-amber-500" : "bg-primary"
                      }`}
                      style={{ width: `${item.v1}%` }}
                    />
                  </div>
                  <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        item.v2 > 60 ? "bg-destructive" : item.v2 > 30 ? "bg-amber-500" : "bg-primary"
                      }`}
                      style={{ width: `${item.v2}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Quick Summary */}
        <WireframeBox label="AI 추천 요약" className="!p-3">
          <div className="space-y-2">
            <div className="flex items-start gap-2 p-2 bg-primary/10 rounded-lg">
              <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <p className="text-xs text-foreground">
                <strong>래미안 크레시티:</strong> 상대적으로 높은 상승 예측, 공급 리스크 주의 필요
              </p>
            </div>
            <div className="flex items-start gap-2 p-2 bg-muted/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-xs text-foreground">
                <strong>아크로 리버파크:</strong> 안정적인 예측, 금리 변동에 민감
              </p>
            </div>
          </div>
          <p className="text-[10px] text-muted-foreground mt-3 leading-relaxed">
            * AI 분석 결과는 참고용이며 실제 투자 결정은 신중히 판단하세요
          </p>
        </WireframeBox>
      </div>
    </div>
  );
}
