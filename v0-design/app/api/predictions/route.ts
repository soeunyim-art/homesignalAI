import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET() {
  const { data, error } = await supabase
    .from("predictions")
    .select("*")
    .order("run_date", { ascending: false })
    .limit(200);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // 최신 run_date만 필터
  if (!data || data.length === 0) {
    return NextResponse.json([]);
  }

  const latestDate = data[0].run_date;
  const latest = data.filter((r) => r.run_date === latestDate);

  return NextResponse.json(latest);
}
