import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get("q") ?? "";

  if (!q.trim()) {
    return NextResponse.json([]);
  }

  const { data, error } = await supabase
    .from("predictions_apt")
    .select("*")
    .ilike("apt_name", `%${q}%`)
    .order("run_date", { ascending: false })
    .limit(30);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // 동일 아파트+면적 중 최신 run_date만 남기기
  const seen = new Set<string>();
  const latest = (data ?? []).filter((r) => {
    const key = `${r.apt_name}_${r.dong}_${r.area}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return NextResponse.json(latest);
}
