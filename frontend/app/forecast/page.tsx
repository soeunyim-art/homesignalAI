'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, Calendar, MapPin } from 'lucide-react'
import { getForecast } from '@/lib/api-client'

export default function ForecastPage() {
  const [region, setRegion] = useState('청량리동')
  const [period, setPeriod] = useState<'week' | 'month'>('week')
  const [horizon, setHorizon] = useState(12)

  const { data, isLoading, error } = useQuery({
    queryKey: ['forecast', region, period, horizon],
    queryFn: () => getForecast({ region, period, horizon }),
  })

  const regions = [
    '청량리동',
    '회기동',
    '휘경동',
    '이문동',
    '용두동',
    '제기동',
    '전농동',
    '답십리동',
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <TrendingUp className="w-8 h-8 mr-3 text-primary-600" />
          부동산 가격 예측
        </h1>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Region Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
              <MapPin className="w-4 h-4 mr-1" />
              지역
            </label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Period Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
              <Calendar className="w-4 h-4 mr-1" />
              기간
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value as 'week' | 'month')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="week">주간</option>
              <option value="month">월간</option>
            </select>
          </div>

          {/* Horizon Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              예측 기간
            </label>
            <input
              type="number"
              value={horizon}
              onChange={(e) => setHorizon(parseInt(e.target.value))}
              min="1"
              max="52"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              {period === 'week' ? '주' : '개월'}
            </p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {isLoading && (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              데이터를 불러오는 중 오류가 발생했습니다.
            </p>
          </div>
        )}

        {data && (
          <>
            <div className="mb-4">
              <h2 className="text-xl font-semibold">{region} 가격 예측</h2>
              <p className="text-sm text-gray-600">
                모델: {data.model_name} | 버전: {data.model_version}
              </p>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data.predictions}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) =>
                    `${(value / 100000000).toFixed(1)}억`
                  }
                />
                <Tooltip
                  formatter={(value: number) =>
                    `${(value / 100000000).toFixed(2)}억 원`
                  }
                  labelFormatter={(label) => `날짜: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="predicted_price"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  name="예측 가격"
                  dot={{ r: 4 }}
                />
                {data.confidence_interval && (
                  <>
                    <Line
                      type="monotone"
                      dataKey="lower_bound"
                      stroke="#94a3b8"
                      strokeDasharray="5 5"
                      name="하한"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="upper_bound"
                      stroke="#94a3b8"
                      strokeDasharray="5 5"
                      name="상한"
                      dot={false}
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>

            {/* Summary Stats */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">현재 가격</p>
                <p className="text-xl font-semibold">
                  {(data.predictions[0]?.predicted_price / 100000000).toFixed(
                    2
                  )}
                  억
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">예측 가격</p>
                <p className="text-xl font-semibold">
                  {(
                    data.predictions[data.predictions.length - 1]
                      ?.predicted_price / 100000000
                  ).toFixed(2)}
                  억
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">변동률</p>
                <p className="text-xl font-semibold text-green-600">
                  +
                  {(
                    ((data.predictions[data.predictions.length - 1]
                      ?.predicted_price -
                      data.predictions[0]?.predicted_price) /
                      data.predictions[0]?.predicted_price) *
                    100
                  ).toFixed(2)}
                  %
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">신뢰도</p>
                <p className="text-xl font-semibold">
                  {data.confidence_score
                    ? `${(data.confidence_score * 100).toFixed(0)}%`
                    : 'N/A'}
                </p>
              </div>
            </div>

            {/* Warning */}
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                ⚠️ 현재 Mock 데이터를 사용하고 있습니다. 실제 Prophet/LightGBM
                모델은 추후 구현 예정입니다.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
