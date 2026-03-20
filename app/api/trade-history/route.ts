import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

const GU_DONG_MAP: Record<string, string[]> = {
  동대문구: ["회기동", "이문동", "청량리동", "전농동", "답십리동", "장안동", "용두동", "신설동", "휘경동", "제기동"],
  성북구:   ["길음동", "동소문동", "돈암동", "안암동", "보문동", "정릉동", "석관동", "장위동", "종암동", "월곡동"],
  중랑구:   ["면목동", "묵동", "신내동", "중화동", "망우동", "상봉동"],
  강북구:   ["번동", "미아동", "수유동", "우이동"],
  도봉구:   ["방학동", "창동", "도봉동", "쌍문동"],
};

const SUPA_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPA_KEY = process.env.SUPABASE_SERVICE_KEY!;

// Supabase PostgREST max 1000행 제한 우회 — 동별 개별 조회 후 합산
async function fetchTradesByDong(dong: string): Promise<{ deal_year: number; deal_month: number; price_10k: number }[]> {
  const encoded = encodeURIComponent(dong);
  const res = await fetch(
    `${SUPA_URL}/rest/v1/apt_trade?select=deal_year,deal_month,price_10k&dong=eq.${encoded}&deal_year=gte.2025&price_10k=gt.0&order=deal_year.asc,deal_month.asc&limit=1000`,
    { headers: { apikey: SUPA_KEY, Authorization: `Bearer ${SUPA_KEY}` }, cache: "no-store" }
  );
  if (!res.ok) return [];
  return res.json();
}

function aggregateMonthly(rows: { deal_year: number; deal_month: number; price_10k: number }[]) {
  const monthMap: Record<string, { sum: number; count: number }> = {};
  for (const row of rows) {
    const ym = `${row.deal_year}-${String(row.deal_month).padStart(2, "0")}`;
    if (!monthMap[ym]) monthMap[ym] = { sum: 0, count: 0 };
    monthMap[ym].sum += Number(row.price_10k);
    monthMap[ym].count += 1;
  }
  return Object.entries(monthMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ym, { sum, count }]) => ({
      ym,
      avg_price_10k: Math.round(sum / count),
      trade_count: count,
    }));
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const gu   = searchParams.get("gu")   ?? "";
  const dong = searchParams.get("dong") ?? "";

  // dong 단위 조회 (단일 동은 1000행 이내라 REST 직접 호출)
  if (dong) {
    const rows = await fetchTradesByDong(dong);
    return NextResponse.json({ history: aggregateMonthly(rows) });
  }

  const dongs = GU_DONG_MAP[gu];
  if (!dongs || dongs.length === 0) {
    return NextResponse.json({ error: "unknown gu or dong" }, { status: 400 });
  }

  // 구 단위: 동별 개별 조회 후 월별 합산 (1000행 제한 우회)
  const allRows = (await Promise.all(dongs.map(fetchTradesByDong))).flat();

  // 월별 합산 집계
  const monthMap: Record<string, { sum: number; count: number }> = {};
  for (const row of allRows) {
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

  // 예측 데이터 (최신 run)
  const { data: preds } = await supabase
    .from("predictions")
    .select("dong, base_ym, current_price_10k, pred_1m_10k, pred_3m_10k, pred_6m_10k")
    .in("dong", dongs)
    .order("run_date", { ascending: false })
    .limit(dongs.length * 2);

  const latestPreds = preds?.filter(
    (p, i, arr) => arr.findIndex((x) => x.dong === p.dong) === i
  ) ?? [];

  const avg = (key: keyof typeof latestPreds[0]) =>
    latestPreds.length
      ? latestPreds.reduce((s, p) => s + (Number(p[key]) || 0), 0) / latestPreds.length
      : null;

  const baseYm = latestPreds[0]?.base_ym ?? null;
  const predictions = baseYm
    ? {
        base_ym: baseYm,
        current: Math.round(avg("current_price_10k") ?? 0),
        pred_1m: Math.round(avg("pred_1m_10k") ?? 0),
        pred_3m: Math.round(avg("pred_3m_10k") ?? 0),
        pred_6m: Math.round(avg("pred_6m_10k") ?? 0),
      }
    : null;

  return NextResponse.json({ history, predictions });
}
