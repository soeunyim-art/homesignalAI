import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get("q") ?? "").trim();

  if (!q || q.length < 2) {
    return NextResponse.json([]);
  }

  // apt_trade에서 apt_name 검색 (최근 2년치 기준으로 집계)
  const { data, error } = await supabase
    .from("apt_trade")
    .select("apt_name, dong, price_10k, deal_year, deal_month")
    .ilike("apt_name", `%${q}%`)
    .gte("deal_year", 2023)
    .gt("price_10k", 0)
    .order("deal_year", { ascending: false })
    .limit(500);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // apt_name + dong 기준으로 집계 (최근 평균가, 거래 건수)
  const aptMap: Record<string, { dong: string; sum: number; count: number; latestYm: string }> = {};

  for (const row of data ?? []) {
    const key = `${row.apt_name}__${row.dong}`;
    const ym = `${row.deal_year}-${String(row.deal_month).padStart(2, "0")}`;
    if (!aptMap[key]) {
      aptMap[key] = { dong: row.dong, sum: 0, count: 0, latestYm: ym };
    }
    aptMap[key].sum += Number(row.price_10k);
    aptMap[key].count += 1;
    if (ym > aptMap[key].latestYm) aptMap[key].latestYm = ym;
  }

  const results = Object.entries(aptMap)
    .map(([key, v]) => ({
      apt_name: key.split("__")[0],
      dong: v.dong,
      avg_price_10k: Math.round(v.sum / v.count),
      trade_count: v.count,
      latest_ym: v.latestYm,
    }))
    .sort((a, b) => b.trade_count - a.trade_count)
    .slice(0, 20);

  return NextResponse.json(results);
}
