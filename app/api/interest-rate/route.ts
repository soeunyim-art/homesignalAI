import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET() {
  // 최신 2개월치 데이터 조회
  const { data, error } = await supabase
    .from("interest_rate")
    .select("stat_date, rate_type, rate")
    .order("stat_date", { ascending: false })
    .limit(9); // 3가지 금리 × 3개월

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  if (!data || data.length === 0) {
    return NextResponse.json([]);
  }

  // stat_date별로 그룹핑 → rate_base / rate_cd / rate_bond3y 형태로 변환
  const grouped: Record<string, { rate_base?: number; rate_cd?: number; rate_bond3y?: number }> = {};
  for (const row of data) {
    if (!grouped[row.stat_date]) grouped[row.stat_date] = {};
    const t: string = row.rate_type ?? "";
    if (t.includes("기준")) grouped[row.stat_date].rate_base = row.rate;
    else if (t.includes("CD")) grouped[row.stat_date].rate_cd = row.rate;
    else if (t.includes("국고") || t.includes("채")) grouped[row.stat_date].rate_bond3y = row.rate;
  }

  const result = Object.entries(grouped)
    .sort(([a], [b]) => b.localeCompare(a)) // 최신순
    .map(([stat_date, rates]) => ({
      stat_date,
      year: parseInt(stat_date.slice(0, 4)),
      month: parseInt(stat_date.slice(5, 7)),
      ...rates,
    }));

  return NextResponse.json(result);
}
