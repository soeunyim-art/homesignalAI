import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_KEY!;

export const supabase = createClient(supabaseUrl, supabaseKey);

export type Prediction = {
  run_date: string;
  dong: string;
  base_ym: string;
  current_price_10k: number;
  pred_1m_10k: number;
  pred_2m_10k: number;
  pred_3m_10k: number;
  change_1m_pct: number;
  change_2m_pct: number;
  change_3m_pct: number;
};

export type NewsSignal = {
  id: string;
  title: string;
  url: string;
  keywords: string[];
  published_at: string;
};
