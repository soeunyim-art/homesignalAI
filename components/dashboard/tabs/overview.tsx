"use client";

import { KPITicker } from "@/components/dashboard/kpi-ticker";
import { MapArea } from "@/components/dashboard/map-area";
import { PricePredictionChart } from "@/components/dashboard/price-prediction-chart";
import { NewsSentimentFeed } from "@/components/dashboard/news-sentiment-feed";
import { RiskRadar } from "@/components/dashboard/risk-radar";

interface OverviewProps {
  searchQuery: string;
}

export function Overview({ searchQuery }: OverviewProps) {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-foreground">
          {searchQuery ? `${searchQuery} 검색 결과` : "서울 동북권"} 종합 개요
        </h2>
        <p className="text-sm text-muted-foreground">
          실시간 시장 현황 및 AI 분석 요약
        </p>
      </div>

      {/* KPI Ticker Row */}
      <section>
        <p className="text-xs text-muted-foreground mb-2">
          · 아래 수치는 검색 구 무관하게 <span className="text-foreground font-medium">서울 동북권 5개 구 전체 평균</span>입니다
        </p>
        <KPITicker />
      </section>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column - Map (Takes 2 columns on XL) */}
        <div className="xl:col-span-2 space-y-6">
          <MapArea />
          <PricePredictionChart />
        </div>

        {/* Right Column - News & Risk */}
        <div className="space-y-6">
          <NewsSentimentFeed />
          <RiskRadar />
        </div>
      </div>
    </div>
  );
}
