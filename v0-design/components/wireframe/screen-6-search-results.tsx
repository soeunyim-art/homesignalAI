"use client";

import { WireframeBox, WireframeText, WireframeDivider } from "./wireframe-box";
import { Search, MapPin, Building2, TrendingUp, TrendingDown, ChevronRight, Filter, SlidersHorizontal, X } from "lucide-react";

export function Screen6SearchResults() {
  const searchResults = [
    {
      id: 1,
      name: "래미안 크레시티",
      address: "동대문구 전농동 123-45",
      type: "아파트 · 2020년 · 1,200세대",
      price: "12.8억",
      prediction: "+3.2%",
      trend: "up",
      aiScore: 87,
      risk: "낮음",
    },
    {
      id: 2,
      name: "동대문 롯데캐슬",
      address: "동대문구 용두동 456-78",
      type: "아파트 · 2018년 · 890세대",
      price: "9.4억",
      prediction: "+1.8%",
      trend: "up",
      aiScore: 82,
      risk: "보통",
    },
    {
      id: 3,
      name: "휘경SK뷰",
      address: "동대문구 휘경동 789-12",
      type: "아파트 · 2015년 · 650세대",
      price: "7.2억",
      prediction: "-0.5%",
      trend: "down",
      aiScore: 74,
      risk: "보통",
    },
    {
      id: 4,
      name: "청량리 역세권 e편한세상",
      address: "동대문구 청량리동 234-56",
      type: "아파트 · 2022년 · 1,450세대",
      price: "14.2억",
      prediction: "+4.1%",
      trend: "up",
      aiScore: 91,
      risk: "낮음",
    },
    {
      id: 5,
      name: "이문 아이파크",
      address: "동대문구 이문동 567-89",
      type: "아파트 · 2019년 · 780세대",
      price: "10.6억",
      prediction: "+2.4%",
      trend: "up",
      aiScore: 85,
      risk: "낮음",
    },
  ];

  return (
    <div className="bg-[#1a1a2e] min-h-screen p-6">
      {/* Header */}
      <WireframeBox className="mb-4 p-4">
        <div className="flex items-center justify-between">
          <WireframeText size="lg" className="font-semibold">홈시그널AI</WireframeText>
          <div className="flex items-center gap-3">
            <WireframeBox variant="dashed" className="w-8 h-8 rounded-full" />
            <WireframeBox variant="dashed" className="w-8 h-8 rounded-full" />
          </div>
        </div>
      </WireframeBox>

      {/* Search Bar with Input */}
      <WireframeBox className="mb-4 p-3">
        <div className="flex items-center gap-3">
          <Search className="w-5 h-5 text-gray-500" />
          <div className="flex-1 flex items-center gap-2">
            <span className="text-white font-medium">동대문구</span>
            <X className="w-4 h-4 text-gray-500 cursor-pointer" />
          </div>
          <WireframeDivider vertical className="h-6" />
          <button className="flex items-center gap-1 text-gray-400 text-sm">
            <SlidersHorizontal className="w-4 h-4" />
            필터
          </button>
        </div>
      </WireframeBox>

      {/* Filter Tags */}
      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
        <WireframeBox className="px-3 py-1.5 rounded-full text-sm whitespace-nowrap">
          <span className="text-gray-300">전체 유형</span>
        </WireframeBox>
        <WireframeBox className="px-3 py-1.5 rounded-full text-sm whitespace-nowrap border-[#4ADE80] border">
          <span className="text-[#4ADE80]">아파트</span>
        </WireframeBox>
        <WireframeBox className="px-3 py-1.5 rounded-full text-sm whitespace-nowrap">
          <span className="text-gray-300">오피스텔</span>
        </WireframeBox>
        <WireframeBox className="px-3 py-1.5 rounded-full text-sm whitespace-nowrap">
          <span className="text-gray-300">빌라</span>
        </WireframeBox>
        <WireframeBox className="px-3 py-1.5 rounded-full text-sm whitespace-nowrap">
          <span className="text-gray-300">5억 이상</span>
        </WireframeBox>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-[#4ADE80]" />
          <WireframeText size="sm" className="text-gray-400">
            <span className="text-white font-medium">동대문구</span> 검색 결과 <span className="text-[#4ADE80] font-semibold">127개</span>
          </WireframeText>
        </div>
        <div className="flex items-center gap-2">
          <WireframeText size="xs" className="text-gray-500">정렬:</WireframeText>
          <WireframeBox variant="dashed" className="px-2 py-1 rounded text-xs">
            AI 점수순
          </WireframeBox>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-3">
        {searchResults.map((result) => (
          <WireframeBox key={result.id} className="p-4 hover:border-[#4ADE80]/50 transition-colors cursor-pointer">
            <div className="flex items-start justify-between">
              {/* Left: Property Info */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-white font-semibold">{result.name}</h3>
                  <WireframeBox 
                    className={`px-2 py-0.5 rounded text-xs ${
                      result.risk === "낮음" 
                        ? "bg-[#4ADE80]/20 text-[#4ADE80]" 
                        : "bg-yellow-500/20 text-yellow-400"
                    }`}
                  >
                    리스크 {result.risk}
                  </WireframeBox>
                </div>
                <div className="flex items-center gap-1 text-gray-400 text-sm mb-2">
                  <MapPin className="w-3 h-3" />
                  {result.address}
                </div>
                <div className="flex items-center gap-1 text-gray-500 text-xs">
                  <Building2 className="w-3 h-3" />
                  {result.type}
                </div>
              </div>

              {/* Right: Price & Prediction */}
              <div className="text-right flex flex-col items-end">
                <div className="text-white font-bold text-lg mb-1">{result.price}</div>
                <div className={`flex items-center gap-1 text-sm ${
                  result.trend === "up" ? "text-[#4ADE80]" : "text-red-400"
                }`}>
                  {result.trend === "up" ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  <span>{result.prediction}</span>
                  <span className="text-gray-500 text-xs">(6개월)</span>
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <span className="text-gray-500 text-xs">AI 점수</span>
                  <WireframeBox className="px-2 py-0.5 rounded bg-[#3B82F6]/20">
                    <span className="text-[#3B82F6] font-semibold text-sm">{result.aiScore}</span>
                  </WireframeBox>
                </div>
              </div>

              {/* Arrow */}
              <ChevronRight className="w-5 h-5 text-gray-600 ml-2 self-center" />
            </div>
          </WireframeBox>
        ))}
      </div>

      {/* Load More */}
      <div className="mt-4 text-center">
        <WireframeBox variant="dashed" className="inline-block px-6 py-2 rounded-lg">
          <WireframeText size="sm" className="text-gray-400">더보기 (122개 더)</WireframeText>
        </WireframeBox>
      </div>

      {/* Bottom Info */}
      <div className="mt-6 p-3 rounded-lg bg-[#0f0f1a] border border-gray-800">
        <div className="flex items-start gap-2">
          <div className="w-4 h-4 rounded-full bg-[#3B82F6]/30 flex items-center justify-center mt-0.5">
            <span className="text-[#3B82F6] text-xs">i</span>
          </div>
          <WireframeText size="xs" className="text-gray-500 leading-relaxed">
            AI 예측은 과거 데이터 기반 참고 정보입니다. 실제 가격은 다양한 요인에 의해 변동될 수 있으며, 투자 결정 시 전문가 상담을 권장합니다.
          </WireframeText>
        </div>
      </div>
    </div>
  );
}
