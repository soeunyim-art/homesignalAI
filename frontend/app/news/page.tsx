'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Newspaper, TrendingUp, Calendar } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getNewsInsights } from '@/lib/api-client'

export default function NewsPage() {
  const [keywords, setKeywords] = useState(['GTX', '재개발', '청량리'])
  const [useRisePoints, setUseRisePoints] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['news-insights', keywords, useRisePoints],
    queryFn: () => getNewsInsights(keywords, useRisePoints),
  })

  const availableKeywords = [
    'GTX',
    'GTX-C',
    '청량리역',
    '재개발',
    '뉴타운',
    '이문휘경뉴타운',
    '분양',
    '입주',
    '금리',
    '대출',
  ]

  const toggleKeyword = (keyword: string) => {
    setKeywords((prev) =>
      prev.includes(keyword)
        ? prev.filter((k) => k !== keyword)
        : [...prev, keyword]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Newspaper className="w-8 h-8 mr-3 text-primary-600" />
          뉴스 이슈 분석
        </h1>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="space-y-4">
          {/* Keyword Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              분석 키워드 선택
            </label>
            <div className="flex flex-wrap gap-2">
              {availableKeywords.map((keyword) => (
                <button
                  key={keyword}
                  onClick={() => toggleKeyword(keyword)}
                  className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                    keywords.includes(keyword)
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400'
                  }`}
                >
                  {keyword}
                </button>
              ))}
            </div>
          </div>

          {/* Rise Points Toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="useRisePoints"
              checked={useRisePoints}
              onChange={(e) => setUseRisePoints(e.target.checked)}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <label
              htmlFor="useRisePoints"
              className="text-sm font-medium text-gray-700 flex items-center"
            >
              <TrendingUp className="w-4 h-4 mr-1" />
              상승 시점 전후 뉴스만 분석
            </label>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {isLoading && (
          <div className="flex items-center justify-center h-64">
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
          <div className="space-y-6">
            {/* Summary */}
            <div>
              <h2 className="text-xl font-semibold mb-4">키워드 빈도 분석</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.keyword_frequencies}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="keyword" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="frequency" fill="#0ea5e9" name="빈도" />
                  <Bar
                    dataKey="impact_score"
                    fill="#f59e0b"
                    name="영향도"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top Keywords */}
            <div>
              <h3 className="text-lg font-semibold mb-3">주요 키워드</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {data.keyword_frequencies.slice(0, 4).map((item: any) => (
                  <div key={item.keyword} className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">{item.keyword}</p>
                    <p className="text-2xl font-semibold">{item.frequency}</p>
                    <p className="text-xs text-gray-500">
                      영향도: {item.impact_score?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent News */}
            {data.recent_news && data.recent_news.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center">
                  <Calendar className="w-5 h-5 mr-2" />
                  최근 뉴스
                </h3>
                <div className="space-y-3">
                  {data.recent_news.slice(0, 5).map((news: any, index: number) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <h4 className="font-medium mb-1">{news.title}</h4>
                      {news.content && (
                        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                          {news.content}
                        </p>
                      )}
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{news.published_at}</span>
                        {news.keywords && (
                          <div className="flex gap-1">
                            {news.keywords.slice(0, 3).map((kw: string) => (
                              <span
                                key={kw}
                                className="px-2 py-1 bg-primary-100 text-primary-700 rounded"
                              >
                                {kw}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analysis Summary */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold mb-2">분석 요약</h3>
              <p className="text-sm text-gray-700">
                {data.summary ||
                  '선택한 키워드에 대한 뉴스 빈도와 영향도를 분석했습니다. 상승 시점 전후 분석을 활성화하면 가격 변동과 연관된 이슈를 더 정확히 파악할 수 있습니다.'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          📊 현재 13개의 뉴스 데이터가 수집되어 있습니다. 더 많은 데이터 수집을
          위해 크롤링을 실행하세요.
        </p>
      </div>
    </div>
  )
}
