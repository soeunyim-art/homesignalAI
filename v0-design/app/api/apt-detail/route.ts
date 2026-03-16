import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const aptName = (searchParams.get("apt_name") ?? "").trim();
  const dong = (searchParams.get("dong") ?? "").trim();
  const area = searchParams.get("area"); // 선택적: 전용면적 필터

  if (!aptName || !dong) {
    return NextResponse.json({ error: "apt_name and dong required" }, { status: 400 });
  }

  // 전체 거래 이력 조회 (2020년~)
  let query = supabase
    .from("apt_trade")
    .select("deal_year, deal_month, price_10k, area, floor")
    .eq("apt_name", aptName)
    .eq("dong", dong)
    .gte("deal_year", 2020)
    .gt("price_10k", 0)
    .order("deal_year")
    .order("deal_month");

  if (area) {
    query = query.eq("area", Number(area));
  }

  const { data: trades, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // 이 아파트에 존재하는 전용면적 목록
  const areaSet = [...new Set((trades ?? []).map((t) => Number(t.area)).filter(Boolean))].sort(
    (a, b) => a - b
  );

  // 월별 집계 (면적 필터 적용 후)
  const monthMap: Record<string, { sum: number; count: number; floors: number[] }> = {};
  for (const row of trades ?? []) {
    const ym = `${row.deal_year}-${String(row.deal_month).padStart(2, "0")}`;
    if (!monthMap[ym]) monthMap[ym] = { sum: 0, count: 0, floors: [] };
    monthMap[ym].sum += Number(row.price_10k);
    monthMap[ym].count += 1;
    if (row.floor) monthMap[ym].floors.push(Number(row.floor));
  }

  const history = Object.entries(monthMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ym, { sum, count }]) => ({
      ym,
      avg_price_10k: Math.round(sum / count),
      trade_count: count,
    }));

  // 전체 거래 목록 (최근 20건)
  const recentTrades = (trades ?? [])
    .slice(-20)
    .reverse()
    .map((t) => ({
      ym: `${t.deal_year}-${String(t.deal_month).padStart(2, "0")}`,
      price_10k: Number(t.price_10k),
      area: Number(t.area),
      floor: t.floor,
    }));

  // 통계
  const allPrices = (trades ?? []).map((t) => Number(t.price_10k));
  const stats =
    allPrices.length > 0
      ? {
          min: Math.min(...allPrices),
          max: Math.max(...allPrices),
          avg: Math.round(allPrices.reduce((s, v) => s + v, 0) / allPrices.length),
          total_trades: allPrices.length,
        }
      : null;

  return NextResponse.json({ history, recentTrades, areaSet, stats });
}
