"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield } from "lucide-react";

const riskData = [
  { factor: "공급 리스크", value: 72, fullMark: 100 },
  { factor: "금리 민감도", value: 85, fullMark: 100 },
  { factor: "거래 활동성", value: 58, fullMark: 100 },
  { factor: "정책 영향", value: 65, fullMark: 100 },
  { factor: "가격 변동성", value: 45, fullMark: 100 },
];

export function RiskRadar() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <CardTitle className="text-lg text-foreground">리스크 레이더</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={riskData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis
                dataKey="factor"
                tick={{ fill: "#9CA3AF", fontSize: 11 }}
                tickLine={{ stroke: "#374151" }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: "#6B7280", fontSize: 10 }}
                axisLine={false}
              />
              <Radar
                name="리스크 지수"
                dataKey="value"
                stroke="#4ADE80"
                strokeWidth={2}
                fill="#4ADE80"
                fillOpacity={0.2}
                dot={{ fill: "#4ADE80", strokeWidth: 0, r: 4 }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-border">
          {riskData.map((item) => (
            <div key={item.factor} className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{item.factor}</span>
              <span
                className={`font-medium ${
                  item.value >= 70
                    ? "text-destructive"
                    : item.value >= 50
                    ? "text-yellow-500"
                    : "text-primary"
                }`}
              >
                {item.value}%
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
