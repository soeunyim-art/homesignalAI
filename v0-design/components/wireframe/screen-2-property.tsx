"use client";

import { WireframeBox } from "./wireframe-box";
import { ChevronLeft, Heart, Share2, MapPin, Building2, Calendar, TrendingUp, AlertCircle } from "lucide-react";

export function Screen2Property() {
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
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <ChevronLeft className="w-4 h-4 text-foreground" />
          </div>
          <span className="text-sm font-medium text-foreground">매물 상세</span>
        </div>
        <div className="flex gap-2">
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <Heart className="w-4 h-4 text-muted-foreground" />
          </div>
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <Share2 className="w-4 h-4 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="h-[520px] overflow-y-auto">
        {/* Property Image Placeholder */}
        <div className="h-48 bg-muted/50 flex items-center justify-center border-b border-border">
          <div className="text-center">
            <Building2 className="w-12 h-12 text-muted-foreground/50 mx-auto mb-2" />
            <span className="text-xs text-muted-foreground font-mono">[매물 이미지]</span>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* Basic Info */}
          <div>
            <div className="flex items-start justify-between mb-2">
              <div>
                <h2 className="text-lg font-semibold text-foreground">래미안 크레시티</h2>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <MapPin className="w-3 h-3" />
                  <span>강남구 대치동</span>
                </div>
              </div>
              <div className="px-2 py-1 bg-primary/20 rounded text-xs text-primary font-medium">
                AI 점수 92
              </div>
            </div>
            
            <div className="flex gap-4 mt-3">
              <div>
                <p className="text-xs text-muted-foreground">매매가</p>
                <p className="text-xl font-bold text-foreground">18.5억</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">전세가</p>
                <p className="text-xl font-bold text-foreground">12.2억</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">전세가율</p>
                <p className="text-xl font-bold text-primary">66%</p>
              </div>
            </div>
          </div>

          {/* AI Prediction Card */}
          <WireframeBox label="AI 가격 예측" className="!p-3">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-foreground">6개월 후 예측</span>
            </div>
            
            <div className="bg-muted/30 rounded-lg p-3 mb-3">
              <div className="flex justify-between items-baseline mb-1">
                <span className="text-xs text-muted-foreground">예측 가격</span>
                <span className="text-lg font-bold text-foreground">19.2억</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">변동 예측</span>
                <span className="text-sm font-medium text-primary">+3.8%</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">예측 신뢰구간 (95%)</span>
                <span className="font-mono text-foreground">18.7억 ~ 19.8억</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">모델 정확도</span>
                <span className="font-mono text-foreground">82.4%</span>
              </div>
            </div>

            <div className="mt-3 p-2 bg-amber-500/10 border border-amber-500/20 rounded-lg flex gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <p className="text-[10px] text-amber-200/80 leading-relaxed">
                AI 예측은 참고용이며 실제 시장 상황에 따라 달라질 수 있습니다. 투자 결정 시 전문가 상담을 권장합니다.
              </p>
            </div>
          </WireframeBox>

          {/* Property Details */}
          <WireframeBox label="기본 정보" className="!p-3">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "전용면적", value: "84㎡" },
                { label: "층수", value: "15층/25층" },
                { label: "입주년도", value: "2019년" },
                { label: "세대수", value: "1,240세대" },
              ].map((item) => (
                <div key={item.label} className="flex justify-between">
                  <span className="text-xs text-muted-foreground">{item.label}</span>
                  <span className="text-xs font-medium text-foreground">{item.value}</span>
                </div>
              ))}
            </div>
          </WireframeBox>

          {/* Price History Mini Chart */}
          <WireframeBox label="가격 추이" className="!p-3">
            <div className="h-20 flex items-end gap-1">
              {[40, 45, 42, 50, 55, 52, 60, 65, 70, 75, 72, 80].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 bg-primary/30 rounded-t"
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
              <span>2023.01</span>
              <span>2024.01</span>
            </div>
          </WireframeBox>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="p-4 border-t border-border bg-card">
        <button className="w-full py-3 bg-primary text-primary-foreground rounded-lg text-sm font-medium">
          상세 분석 보기
        </button>
      </div>
    </div>
  );
}
