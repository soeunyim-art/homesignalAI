"use client";

import { WireframeBox } from "./wireframe-box";
import { ChevronLeft, AlertTriangle, Shield, TrendingDown, Building, Percent, FileText, Info } from "lucide-react";

export function Screen4Risk() {
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
            <span className="text-sm font-medium text-foreground">리스크 분석</span>
            <p className="text-[10px] text-muted-foreground">강남구 대치동</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="h-[520px] overflow-y-auto p-4 space-y-4">
        {/* Overall Risk Score */}
        <WireframeBox label="종합 리스크 점수" className="!p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground mb-1">현재 리스크 수준</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-amber-500">58</span>
                <span className="text-sm text-muted-foreground">/100</span>
              </div>
              <p className="text-xs text-amber-500 mt-1">보통 주의</p>
            </div>
            <div className="w-24 h-24 relative">
              {/* Gauge visualization */}
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50" cy="50" r="40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  className="text-muted"
                />
                <circle
                  cx="50" cy="50" r="40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  strokeDasharray={`${58 * 2.51} 251`}
                  className="text-amber-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <Shield className="w-8 h-8 text-amber-500" />
              </div>
            </div>
          </div>
          
          <div className="mt-4 flex gap-2">
            {[
              { label: "낮음", range: "0-30", color: "bg-primary" },
              { label: "보통", range: "31-60", color: "bg-amber-500" },
              { label: "높음", range: "61-100", color: "bg-destructive" },
            ].map((item) => (
              <div key={item.label} className="flex-1 text-center">
                <div className={`h-2 ${item.color} rounded-full mb-1`} />
                <p className="text-[10px] text-muted-foreground">{item.label}</p>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Individual Risk Factors */}
        <WireframeBox label="개별 리스크 요소" className="!p-3">
          <div className="space-y-3">
            {[
              { 
                icon: Building, 
                label: "공급 리스크", 
                value: 72, 
                desc: "향후 2년간 3,500세대 입주 예정",
                level: "높음"
              },
              { 
                icon: Percent, 
                label: "금리 민감도", 
                value: 55, 
                desc: "기준금리 변동 시 가격 영향도",
                level: "보통"
              },
              { 
                icon: TrendingDown, 
                label: "가격 하락 확률", 
                value: 28, 
                desc: "6개월 내 5% 이상 하락 확률",
                level: "낮음"
              },
              { 
                icon: FileText, 
                label: "정책 리스크", 
                value: 45, 
                desc: "규제 지역 지정 가능성",
                level: "보통"
              },
            ].map((item) => (
              <div key={item.label} className="p-3 bg-muted/20 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                      <item.icon className="w-4 h-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs font-medium text-foreground">{item.label}</p>
                      <p className="text-[10px] text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-foreground">{item.value}%</p>
                    <p className={`text-[10px] ${
                      item.level === "높음" ? "text-destructive" :
                      item.level === "보통" ? "text-amber-500" : "text-primary"
                    }`}>
                      {item.level}
                    </p>
                  </div>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.value > 60 ? "bg-destructive" :
                      item.value > 30 ? "bg-amber-500" : "bg-primary"
                    }`}
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Risk Mitigation Tips */}
        <WireframeBox label="리스크 대응 가이드" className="!p-3">
          <div className="space-y-2">
            {[
              "입주 물량 확인 후 매수 시점 조절 권장",
              "전세가율 변동 추이 모니터링 필요",
              "대출 금리 고정/변동 선택 신중히",
            ].map((tip, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-primary/10 rounded-lg">
                <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <p className="text-xs text-foreground">{tip}</p>
              </div>
            ))}
          </div>
        </WireframeBox>

        {/* Disclaimer */}
        <div className="p-3 bg-muted/30 border border-border rounded-lg flex gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            리스크 분석은 AI 모델 기반의 참고 정보입니다. 
            실제 투자 결정 시에는 다양한 요소를 종합적으로 검토하시기 바랍니다.
          </p>
        </div>
      </div>
    </div>
  );
}
