'use client'

import type { Prediction } from '@/lib/supabase'

interface Props {
  prediction: Prediction
}

function formatPrice(val: number) {
  if (!val) return '-'
  const eok = Math.floor(val / 10000)
  const cheon = val % 10000
  if (cheon === 0) return `${eok}억`
  return `${eok}억 ${Math.round(cheon / 100) * 100}만`
}

function ChangeTag({ pct }: { pct: number }) {
  if (!pct && pct !== 0) return <span className="text-slate-400">-</span>
  const color = pct > 0 ? 'text-red-400' : pct < 0 ? 'text-blue-400' : 'text-slate-400'
  const sign = pct > 0 ? '+' : ''
  return <span className={`${color} font-semibold`}>{sign}{pct.toFixed(1)}%</span>
}

export default function PredictionCard({ prediction: p }: Props) {
  return (
    <div className="bg-slate-800 rounded-2xl p-5 border border-slate-700 hover:border-blue-500 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-bold text-white">{p.dong}</h3>
        <span className="text-xs text-slate-400 bg-slate-700 px-2 py-1 rounded">{p.base_ym}</span>
      </div>

      <div className="mb-4">
        <p className="text-xs text-slate-400 mb-1">현재 평균 매매가</p>
        <p className="text-2xl font-bold text-slate-100">{formatPrice(p.current_price_10k)}</p>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {[
          { label: '1개월 후', price: p.pred_1m_10k, pct: p.change_1m_pct },
          { label: '3개월 후', price: p.pred_3m_10k, pct: p.change_3m_pct },
          { label: '6개월 후', price: p.pred_6m_10k, pct: p.change_6m_pct },
        ].map(({ label, price, pct }) => (
          <div key={label} className="bg-slate-700 rounded-xl p-3 text-center">
            <p className="text-xs text-slate-400 mb-1">{label}</p>
            <p className="text-sm font-bold text-slate-100">{formatPrice(price)}</p>
            <ChangeTag pct={pct} />
          </div>
        ))}
      </div>
    </div>
  )
}
