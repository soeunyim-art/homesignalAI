"use client";

import { WireframeBox } from "./wireframe-box";
import { ChevronLeft, Info, TrendingUp, TrendingDown, Minus } from "lucide-react";

export function Screen3Prediction() {
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
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <ChevronLeft className="w-4 h-4 text-foreground" />
          </div>
          <div>
            <span className="text-sm font-medium text-foreground">AI 가격 예측</span>
            <p className="text-[10px] text-muted-foreground">래미안 크레시티 84㎡</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="h-[520px] overflow-y-auto p-4 space-y-4">
        {/* Main Prediction */}
        <WireframeBox label="예측 결과" className="!p-4">
          <div className="text-center mb-4">
            <p className="text-xs text-muted-foreground mb-1">6개월 후 예측 가격</p>
            <p className="text-3xl font-bold text-foreground">19.2억</p>
            <div className="inline-flex items-center gap-1 mt-1 px-2 py-1 bg-primary/20 rounded-full">
              <TrendingUp className="w-3 h-3 text-primary" />
              <span className="text-sm text-primary font-medium">+3.8%</span>
            </div>
          </div>

          {/* Probability Distribution */}
          <div className="mb-4">
            <div className="flex justify-between text-xs text-muted-foreground mb-2">
              <span>확률 분포</span>
              <span className="flex items-center gap-1">
                <Info className="w-3 h-3" />
                95% 신뢰구간
              </span>
            </div>
            
            <div className="relative h-16 bg-muted/30 rounded-lg overflow-hidden">
              {/* Distribution curve visualization */}
              <div className="absolute inset-0 flex items-end justify-center">
                <div className="w-full h-full flex items-end">
                  {[10, 20, 35, 55, 80, 100, 80, 55, 35, 20, 10].map((h, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-primary/40 mx-px"
                      style={{ height: `${h}%` }}
                    />
                  ))}
                </div>
              </div>
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 px-2 py-1 bg-background/80 rounded text-xs font-mono">
                19.2억
              </div>
            </div>
            
            <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
              <span>18.7억</span>
              <span>19.8억</span>
            </div>
          </div>

          {/* Prediction Metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-2 bg-muted/30 rounded-lg text-center">
              <p className="text-[10px] text-muted-foreground">모델 정확도</p>
              <p className="text-lg font-bold text-foreground">82.4%</p>
            </div>
            <div className="p-2 bg-muted/30 rounded-lg text-center">
              <p className="text-[10px] text-muted-foreground">예측 신뢰도</p>
              <p className="text-lg font-bold text-foreground">78%</p>
            </div>
          </div>
        </WireframeBox>

        {/* Scenarios */}
        <WireframeBox label="시나리오별 예측" className="!p-3">
          <div className="space-y-3">
            {[
              { scenario: "낙관적", price: "20.1억", change: "+8.6%", prob: "15%", icon: TrendingUp, color: "text-primary" },
              { scenario: "기본", price: "19.2억", change: "+3.8%", prob: "70%", icon: Minus, color: "text-foreground" },
              { scenario: "보수적", price: "18.3억", change: "-1.1%", prob: "15%", icon: TrendingDown, color: "text-destructive" },
            ].map((item) => (
              <div key={item.scenario} className="flex items-center justify-between p-2 bg-muted/20 rounded-lg">
                <div className="flex items-center gap-2">
                  <item.icon className={`w-4 h-4 ${item.color}`} />
                  <div>
                    <p className="text-xs font-medium text-foreground">{item.scenario}</p>
                    <p className="text-[10px] text-muted-foreground">확률 {item.prob}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground">{item.price}</p>
                  <p className={`text-[10px] ${item.color}`}>{item.change}</p>
                </div>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Key Factors */}
        <WireframeBox label="예측 영향 요인" className="!p-3">
          <div className="space-y-2">
            {[
              { factor: "금리 전망", impact: "긍정적", weight: 30 },
              { factor: "지역 개발", impact: "긍정적", weight: 25 },
              { factor: "공급 물량", impact: "부정적", weight: 20 },
              { factor: "거래량 추이", impact: "중립", weight: 15 },
              { factor: "정책 영향", impact: "부정적", weight: 10 },
            ].map((item) => (
              <div key={item.factor} className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-20 shrink-0">{item.factor}</span>
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.impact === "긍정적" ? "bg-primary" :
                      item.impact === "부정적" ? "bg-destructive" : "bg-muted-foreground"
                    }`}
                    style={{ width: `${item.weight * 2}%` }}
                  />
                </div>
                <span className={`text-[10px] w-12 text-right ${
                  item.impact === "긍정적" ? "text-primary" :
                  item.impact === "부정적" ? "text-destructive" : "text-muted-foreground"
                }`}>
                  {item.impact}
                </span>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Disclaimer */}
        <div className="p-3 bg-muted/30 border border-border rounded-lg">
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            <strong>면책조항:</strong> 본 예측은 AI 모델을 활용한 참고 정보이며, 
            실제 시장 상황과 다를 수 있습니다. 모든 투자 결정은 본인 책임하에 
            이루어져야 하며, 필요시 전문가 상담을 권장합니다.
          </p>
        </div>
      </div>
    </div>
  );
}
