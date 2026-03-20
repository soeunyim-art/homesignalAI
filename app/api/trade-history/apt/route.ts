import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const aptName = searchParams.get("apt_name") ?? "";
  const dong    = searchParams.get("dong") ?? "";
  const area    = parseFloat(searchParams.get("area") ?? "0");

  if (!aptName || !dong) {
    return NextResponse.json({ error: "apt_name and dong required" }, { status: 400 });
  }

  // 면적 ±3㎡ 허용 (동일 타입 묶기) — ilike로 한글 eq 이슈 우회
  const { data: trades, error } = await supabase
    .from("apt_trade")
    .select("deal_year, deal_month, price_10k")
    .ilike("apt_name", aptName)
    .ilike("dong", dong)
    .gte("area", area - 3)
    .lte("area", area + 3)
    .gte("deal_year", 2025)
    .gt("price_10k", 0)
    .order("deal_year")
    .order("deal_month")
    .limit(10000);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // 월별 집계
  const monthMap: Record<string, { sum: number; count: number }> = {};
  for (const row of trades ?? []) {
    const ym = `${row.deal_year}-${String(row.deal_month).padStart(2, "0")}`;
    if (!monthMap[ym]) monthMap[ym] = { sum: 0, count: 0 };
    monthMap[ym].sum += Number(row.price_10k);
    monthMap[ym].count += 1;
  }

  const history = Object.entries(monthMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ym, { sum, count }]) => ({
      ym,
      avg_price_10k: Math.round(sum / count),
      trade_count: count,
    }));

  return NextResponse.json(history);
}
