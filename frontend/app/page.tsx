import Link from 'next/link'
import { Home, TrendingUp, MessageSquare, Newspaper } from 'lucide-react'

export default function HomePage() {
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
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          동대문구 부동산 AI 분석
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          시계열 예측과 뉴스 분석으로 부동산 시장을 이해하세요
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <Link
          href="/forecast"
          className="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center mb-4">
            <TrendingUp className="w-8 h-8 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold">가격 예측</h2>
          </div>
          <p className="text-gray-600">
            Prophet + LightGBM 앙상블 모델로 부동산 가격을 예측합니다
          </p>
        </Link>

        <Link
          href="/chat"
          className="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center mb-4">
            <MessageSquare className="w-8 h-8 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold">AI 챗봇</h2>
          </div>
          <p className="text-gray-600">
            RAG 기반 챗봇으로 부동산 관련 질문에 답변받으세요
          </p>
        </Link>

        <Link
          href="/news"
          className="block p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center mb-4">
            <Newspaper className="w-8 h-8 text-primary-600 mr-3" />
            <h2 className="text-xl font-semibold">뉴스 분석</h2>
          </div>
          <p className="text-gray-600">
            GTX, 재개발 등 주요 이슈의 영향을 분석합니다
          </p>
        </Link>
      </div>

      {/* Region Selector */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold mb-4 flex items-center">
          <Home className="w-6 h-6 mr-2 text-primary-600" />
          지역 선택
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {regions.map((region) => (
            <Link
              key={region}
              href={`/forecast?region=${encodeURIComponent(region)}`}
              className="p-4 border-2 border-gray-200 rounded-lg text-center hover:border-primary-500 hover:bg-primary-50 transition-colors"
            >
              <span className="font-medium">{region}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-2">현재 상태</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li>• Mock 모드로 운영 중 (실제 예측 모델 구현 예정)</li>
          <li>• 13개 뉴스 데이터 수집 완료</li>
          <li>• Supabase 데이터베이스 연동 완료</li>
          <li>• 상승 시점 키워드 추출 시스템 구축 완료</li>
        </ul>
      </div>
    </div>
  )
}
