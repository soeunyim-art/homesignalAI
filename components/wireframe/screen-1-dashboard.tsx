"use client";

import { WireframeBox, WireframePlaceholder, WireframeText } from "./wireframe-box";
import { Home, Search, Bell, User, TrendingUp, AlertTriangle, MapPin, BarChart3 } from "lucide-react";

export function Screen1Dashboard() {
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
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs text-muted-foreground">안녕하세요, 김서울님</p>
            <h1 className="text-lg font-semibold text-foreground">홈시그널 AI</h1>
          </div>
          <div className="flex gap-2">
            <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center">
              <Bell className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center">
              <User className="w-4 h-4 text-muted-foreground" />
            </div>
          </div>
        </div>
        
        {/* Search */}
        <WireframeBox className="!p-3 flex items-center gap-2">
          <Search className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">아파트, 지역 검색...</span>
        </WireframeBox>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4 h-[480px] overflow-y-auto">
        {/* Quick Stats */}
        <WireframeBox label="시장 요약" className="!p-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-2 bg-muted/30 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">서울 평균</p>
              <p className="text-lg font-bold text-foreground">12.4억</p>
              <p className="text-xs text-primary">+2.3%</p>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">거래량</p>
              <p className="text-lg font-bold text-foreground">8,420</p>
              <p className="text-xs text-destructive">-12.4%</p>
            </div>
          </div>
        </WireframeBox>

        {/* AI Prediction Summary */}
        <WireframeBox label="AI 예측 요약" className="!p-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">6개월 전망</p>
              <p className="text-xs text-muted-foreground">신뢰도 78%</p>
            </div>
          </div>
          <div className="bg-muted/30 rounded-lg p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-muted-foreground">예측 범위</span>
              <span className="text-xs font-mono text-primary">+1.2% ~ +3.8%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full w-[65%] bg-gradient-to-r from-primary/50 to-primary rounded-full" />
            </div>
            <p className="text-[10px] text-muted-foreground mt-2 leading-relaxed">
              * 예측은 과거 데이터 기반이며 실제 결과와 다를 수 있습니다
            </p>
          </div>
        </WireframeBox>

        {/* Risk Indicators */}
        <WireframeBox label="리스크 지표" className="!p-3">
          <div className="space-y-2">
            {[
              { label: "공급 리스크", value: 65, color: "bg-amber-500" },
              { label: "금리 민감도", value: 45, color: "bg-blue-500" },
              { label: "가격 변동성", value: 30, color: "bg-primary" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-20">{item.label}</span>
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${item.color} rounded-full`}
                    style={{ width: `${item.value}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-foreground w-8">{item.value}%</span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground mt-3">
            수치가 높을수록 주의가 필요합니다
          </p>
        </WireframeBox>

        {/* Quick Actions */}
        <div className="grid grid-cols-4 gap-2">
          {[
            { icon: MapPin, label: "지도" },
            { icon: BarChart3, label: "분석" },
            { icon: TrendingUp, label: "예측" },
            { icon: AlertTriangle, label: "리스크" },
          ].map((item) => (
            <div key={item.label} className="flex flex-col items-center gap-1 p-3 bg-card rounded-lg border border-border">
              <item.icon className="w-5 h-5 text-muted-foreground" />
              <span className="text-[10px] text-muted-foreground">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Nav */}
      <div className="h-16 border-t border-border bg-card flex items-center justify-around px-4">
        {[
          { icon: Home, label: "홈", active: true },
          { icon: Search, label: "검색", active: false },
          { icon: BarChart3, label: "분석", active: false },
          { icon: User, label: "마이", active: false },
        ].map((item) => (
          <div key={item.label} className="flex flex-col items-center gap-1">
            <item.icon className={`w-5 h-5 ${item.active ? "text-primary" : "text-muted-foreground"}`} />
            <span className={`text-[10px] ${item.active ? "text-primary" : "text-muted-foreground"}`}>
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
