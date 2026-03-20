import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

const GU_DONG_MAP: Record<string, string[]> = {
  동대문구: ["회기동","이문동","청량리동","전농동","답십리동","장안동","용두동","휘경동","제기동"],
  성북구:   ["길음동","돈암동","동소문동4가","동소문동5가","동소문동7가","보문동1가","보문동3가","보문동6가",
             "삼선동2가","삼선동3가","삼선동4가","석관동","안암동1가","안암동3가","장위동","정릉동","종암동",
             "하월곡동","상월곡동"],
  중랑구:   ["면목동","묵동","신내동","중화동","망우동","상봉동"],
  강북구:   ["번동","미아동","수유동"],
  도봉구:   ["방학동","창동","도봉동","쌍문동"],
};

const SUPA_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPA_KEY = process.env.SUPABASE_SERVICE_KEY!;

function dedup(data: any[]) {
  const seen = new Set<string>();
  return data.filter((r) => {
    const key = `${r.apt_name}_${r.dong}_${r.area}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// REST API 직접 호출 (supabase-js eq 한글 버그 우회)
async function getTradeCount(dongs: string[]): Promise<Record<string, number>> {
  // apt_trade에서 2025년 이후 거래 전체 조회 (dong 필터 없이, 후처리로 필터)
  const dongSet = new Set(dongs);
  const res = await fetch(
    `${SUPA_URL}/rest/v1/apt_trade?select=apt_name,dong&deal_year=gte.2025&price_10k=gt.0&limit=5000`,
    { headers: { apikey: SUPA_KEY, Authorization: `Bearer ${SUPA_KEY}` }, cache: "no-store" }
  );
  if (!res.ok) return {};
  const rows: { apt_name: string; dong: string }[] = await res.json();

  const countMap: Record<string, number> = {};
  for (const r of rows) {
    if (!dongSet.has(r.dong)) continue;
    const key = `${r.apt_name}__${r.dong}`;
    countMap[key] = (countMap[key] ?? 0) + 1;
  }
  return countMap;
}

async function getPredictionsForDongs(dongs: string[], runDate: string) {
  const results: any[] = [];
  for (const dong of dongs) {
    const { data } = await supabase
      .from("predictions_apt")
      .select("*")
      .ilike("dong", dong)
      .eq("run_date", runDate)
      .limit(20);
    if (data) results.push(...data);
  }
  return results;
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q  = searchParams.get("q")  ?? "";
  const gu = searchParams.get("gu") ?? "";

  // 이름 검색
  if (q.trim()) {
    const { data, error } = await supabase
      .from("predictions_apt")
      .select("*")
      .ilike("apt_name", `%${q}%`)
      .order("run_date", { ascending: false })
      .limit(50);
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json(dedup(data ?? []));
  }

  // 구 기준 기본 목록
  const dongs = gu ? (GU_DONG_MAP[gu] ?? []) : Object.values(GU_DONG_MAP).flat();

  // 최신 run_date
  const { data: latestRun } = await supabase
    .from("predictions_apt")
    .select("run_date")
    .order("run_date", { ascending: false })
    .limit(1);
  const runDate = latestRun?.[0]?.run_date;
  if (!runDate) return NextResponse.json([]);

  // predictions_apt 조회 + 거래량 카운트 병렬
  const [preds, countMap] = await Promise.all([
    getPredictionsForDongs(dongs, runDate),
    getTradeCount(dongs),
  ]);

  const deduped = dedup(preds);

  // 거래량 내림차순 정렬
  deduped.sort((a, b) => {
    const ka = `${a.apt_name}__${a.dong}`;
    const kb = `${b.apt_name}__${b.dong}`;
    return (countMap[kb] ?? 0) - (countMap[ka] ?? 0);
  });

  return NextResponse.json(deduped.slice(0, 20));
}
