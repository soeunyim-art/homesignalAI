import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q");

  let query = supabase
    .from("news_signals")
    .select("id, title, url, keywords, published_at, sentiment_score, sentiment_label, sentiment_tags")
    .order("published_at", { ascending: false })
    .limit(30);

  if (q) {
    query = query.ilike("title", `%${q}%`);
  }

  const { data, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data ?? []);
}
