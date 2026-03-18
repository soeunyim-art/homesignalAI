"use client";

import { useState } from "react";
import { Screen1Dashboard } from "@/components/wireframe/screen-1-dashboard";
import { Screen2Property } from "@/components/wireframe/screen-2-property";
import { Screen3Prediction } from "@/components/wireframe/screen-3-prediction";
import { Screen4Risk } from "@/components/wireframe/screen-4-risk";
import { Screen5Compare } from "@/components/wireframe/screen-5-compare";
import { Screen6SearchResults } from "@/components/wireframe/screen-6-search-results";
import { cn } from "@/lib/utils";

const screens = [
  { id: 1, name: "홈 대시보드", component: Screen1Dashboard },
  { id: 2, name: "검색 결과", component: Screen6SearchResults },
  { id: 3, name: "매물 상세", component: Screen2Property },
  { id: 4, name: "AI 가격 예측", component: Screen3Prediction },
  { id: 5, name: "리스크 분석", component: Screen4Risk },
  { id: 6, name: "매물 비교", component: Screen5Compare },
];

export default function WireframePage() {
  const [activeScreen, setActiveScreen] = useState(1);
  const ActiveComponent = screens.find((s) => s.id === activeScreen)?.component || Screen1Dashboard;

  return (
    <div className="min-h-screen bg-[#0a0a0a] p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <h1 className="text-2xl font-bold text-foreground mb-2">
          홈시그널AI - MVP 와이어프레임
        </h1>
        <p className="text-sm text-muted-foreground">
          Low-fidelity 설계 | 예측, 확률, 리스크를 명확히 보여주는 신뢰 중심 UX
        </p>
      </div>

      {/* Screen Navigation */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex flex-wrap gap-2">
          {screens.map((screen) => (
            <button
              key={screen.id}
              onClick={() => setActiveScreen(screen.id)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                activeScreen === screen.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border border-border text-muted-foreground hover:text-foreground hover:border-primary/50"
              )}
            >
              {screen.id}. {screen.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-8 items-start">
          {/* Active Screen Preview */}
          <div className="flex justify-center">
            <ActiveComponent />
          </div>

          {/* Screen Description */}
          <div className="space-y-6">
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                화면 {activeScreen}: {screens.find((s) => s.id === activeScreen)?.name}
              </h2>
              
              {activeScreen === 1 && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p><strong className="text-foreground">목적:</strong> 사용자가 앱 진입 시 가장 먼저 보는 화면. 핵심 지표와 AI 예측 요약을 한눈에 파악.</p>
                  <div>
                    <strong className="text-foreground">핵심 요소:</strong>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>시장 요약 (서울 평균, 거래량)</li>
                      <li>AI 예측 요약 (6개월 전망 + 신뢰도)</li>
                      <li>리스크 지표 바 차트</li>
                      <li>빠른 탐색 버튼</li>
                    </ul>
                  </div>
                  <p><strong className="text-foreground">신뢰 UX:</strong> 모든 예측에 신뢰도 표시, 면책 문구 포함</p>
                </div>
              )}

              {activeScreen === 2 && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p><strong className="text-foreground">목적:</strong> 지역/단지명 검색 시 결과 리스트 제공. 예: 동대문구 검색 결과</p>
                  <div>
                    <strong className="text-foreground">핵심 요소:</strong>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>검색어 표시 및 필터 태그</li>
                      <li>결과 개수 및 정렬 옵션</li>
                      <li>매물 카드 (이름, 주소, 가격, AI 예측)</li>
                      <li>AI 점수 및 리스크 수준 배지</li>
                      <li>6개월 예측 수치 (상승/하락)</li>
                    </ul>
                  </div>
                  <p><strong className="text-foreground">신뢰 UX:</strong> AI 예측은 참고 정보임을 명시, 전문가 상담 권장 문구</p>
                </div>
              )}

              {activeScreen === 3 && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p><strong className="text-foreground">목적:</strong> 개별 매물의 상세 정보와 AI 분석 결과 제공</p>
                  <div>
                    <strong className="text-foreground">핵심 요소:</strong>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>매물 기본 정보 (가격, 면적, 층수)</li>
                      <li>AI 점수 배지</li>
                      <li>6개월 예측 가격 + 신뢰구간</li>
                      <li>가격 추이 미니 차트</li>
                      <li>모델 정확도 명시</li>
                    </ul>
                  </div>
                  <p><strong className="text-foreground">신뢰 UX:</strong> 예측은 참고용임을 명시, 전문가 상담 권장 문구</p>
                </div>
              )}

              {activeScreen === 3 && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p><strong className="text-foreground">목적:</strong> AI 가격 예측의 상세 분석 및 확률 분포 시각화</p>
                  <div>
                    <strong className="text-foreground">핵심 요소:</strong>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>예측 가격 + 95% 신뢰구간</li>
                      <li>확률 분포 히스토그램</li>
                      <li>3가지 시나리오 (낙관/기본/보수)</li>
                      <li>예측 영향 요인 분석</li>
                      <li>모델 정확도 / 신뢰도 수치</li>
                    </ul>
                  </div>
                  <p><strong className="text-foreground">신뢰 UX:</strong> 확률 기반 표현, 다양한 시나리오 제시, 명확한 면책조항</p>
                </div>
              )}

              {activeScreen === 4 && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p><strong className="text-foreground">목적:</strong> 투자 리스크를 다각도로 분석하여 신중한 의사결정 지원</p>
                  <div>
                    <strong className="text-foreground">핵심 요소:</strong>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>종합 리스크 점수 (게이지)</li>
                      <li>개별 리스크 요소 (공급/금리/정책/변동성)</li>
                      <li>리스크 수준 컬러 코딩 (낮음/보통/높음)</li>
                      <li>리스크 대응 가이드</li>
                    </ul>
                  </div>
                  <p><strong className="text-foreground">신뢰 UX:</strong> 과장 없는 객관적 수치, 대응 방안 제시</p>
                </div>
              )}

              {activeScreen === 5 && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <p><strong className="text-foreground">목적:</strong> 여러 매물을 직접 비교하여 합리적인 선택 지원</p>
                  <div>
                    <strong className="text-foreground">핵심 요소:</strong>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>가격 비교 테이블</li>
                      <li>AI 예측 비교 (상승률/신뢰도)</li>
                      <li>리스크 비교 바 차트</li>
                      <li>AI 추천 요약</li>
                    </ul>
                  </div>
                  <p><strong className="text-foreground">신뢰 UX:</strong> 장단점 균형있게 표시, 최종 결정은 사용자 몫임을 명시</p>
                </div>
              )}
            </div>

            {/* Design Principles */}
            <div className="bg-card border border-border rounded-xl p-6">
              <h3 className="text-sm font-semibold text-foreground mb-3">설계 원칙</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { title: "투명성", desc: "모든 예측에 신뢰도/정확도 표시" },
                  { title: "확률 기반", desc: "단정적 표현 대신 범위와 확률 제시" },
                  { title: "리스크 명시", desc: "긍정적 정보와 함께 위험 요소 강조" },
                  { title: "면책 명확", desc: "AI 한계를 솔직하게 고지" },
                ].map((item) => (
                  <div key={item.title} className="p-3 bg-muted/30 rounded-lg">
                    <p className="text-xs font-medium text-primary mb-1">{item.title}</p>
                    <p className="text-[10px] text-muted-foreground">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* All Screens Overview */}
      <div className="max-w-7xl mx-auto mt-12">
        <h2 className="text-lg font-semibold text-foreground mb-6">전체 화면 개요</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {screens.map((screen) => {
            const Component = screen.component;
            return (
              <button
                key={screen.id}
                onClick={() => setActiveScreen(screen.id)}
                className={cn(
                  "relative rounded-xl overflow-hidden border-2 transition-all",
                  activeScreen === screen.id
                    ? "border-primary shadow-lg shadow-primary/20"
                    : "border-border hover:border-primary/50"
                )}
              >
                <div className="transform scale-[0.28] origin-top-left w-[357%] h-[357%] pointer-events-none">
                  <Component />
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background to-transparent p-2">
                  <p className="text-[10px] font-medium text-foreground text-center">
                    {screen.id}. {screen.name}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
