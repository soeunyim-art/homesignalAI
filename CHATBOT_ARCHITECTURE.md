# AI 챗봇 아키텍처 문서

## 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 (브라우저)                          │
│                    http://localhost:3000                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 1. 질문 입력
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js 16 + React 19)                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  components/dashboard/ai-chatbot.tsx                     │   │
│  │  - 챗봇 UI 컴포넌트                                        │   │
│  │  - 메시지 표시 및 입력                                      │   │
│  │  - 로딩 상태 관리                                          │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │ 2. POST /api/chat                 │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API (Next.js API Route)                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  app/api/chat/route.ts                                   │   │
│  │  - 요청 검증                                              │   │
│  │  - RAG 파이프라인 조율                                     │   │
│  │  - Claude API 호출                                        │   │
│  └──────┬────────────────────────────────────┬─────────────┘   │
│         │ 3. RAG 데이터 검색                  │ 5. AI 응답 생성  │
└─────────┼────────────────────────────────────┼─────────────────┘
          ↓                                    ↓
┌──────────────────────────────┐  ┌──────────────────────────────┐
│  RAG Utils (lib/rag-utils.ts) │  │  Anthropic Claude API         │
│                                │  │  (Claude Sonnet 4.5)          │
│  ┌──────────────────────────┐ │  │                               │
│  │ analyzeUserIntent()      │ │  │  Model:                       │
│  │ - 질문 의도 분석          │ │  │  claude-sonnet-4-5-20250929  │
│  │ - 지역/시간 추출          │ │  │                               │
│  └──────────────────────────┘ │  │  Context Window: 200K tokens │
│                                │  │  Max Output: 64K tokens       │
│  ┌──────────────────────────┐ │  │                               │
│  │ getRelevantData()        │ │  │  Pricing:                     │
│  │ - Supabase 쿼리 실행     │ │  │  - Input: $3/M tokens        │
│  │ - 병렬 데이터 조회        │ │  │  - Output: $15/M tokens      │
│  └──────────────────────────┘ │  └──────────────────────────────┘
│                                │
│  ┌──────────────────────────┐ │
│  │ buildContextPrompt()     │ │
│  │ - 프롬프트 구성           │ │
│  │ - 데이터 포맷팅           │ │
│  └──────────────────────────┘ │
│                                │
│  ┌──────────────────────────┐ │
│  │ calculateStats()         │ │
│  │ - 통계 계산               │ │
│  │ - 트렌드 분석             │ │
│  └──────────────────────────┘ │
└────────────┬───────────────────┘
             │ 4. 데이터베이스 쿼리
             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Supabase (PostgreSQL)                        │
│                                                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │  predictions         │  │  news_signals        │               │
│  │  - 동별 가격 예측     │  │  - 부동산 뉴스        │               │
│  │  - 1/2/3개월 예측     │  │  - 키워드, 감성      │               │
│  │  - 변동률, 신뢰도     │  │  - 발행일            │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │  apt_trade           │  │  apt_rent            │               │
│  │  - 실거래 데이터      │  │  - 전월세 데이터      │               │
│  │  - 2025년 이후        │  │  - 전세가율          │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │  dongs               │  │  apartments          │               │
│  │  - 동 마스터          │  │  - 아파트 마스터      │               │
│  └─────────────────────┘  └─────────────────────┘               │
└───────────────────────────────────────────────────────────────────┘
```

## 데이터 흐름 (RAG 파이프라인)

### 단계별 처리 과정

```
1️⃣ 사용자 질문 입력
   ↓
   예: "동대문구 아파트 가격 전망은?"

2️⃣ 의도 분석 (analyzeUserIntent)
   ↓
   {
     type: "prediction",
     gu: "동대문구",
     dong: undefined,
     timeframe: undefined
   }

3️⃣ 관련 데이터 검색 (getRelevantData)
   ↓
   ┌─────────────────────────────────────┐
   │ 병렬 Supabase 쿼리 (Promise.all)    │
   ├─────────────────────────────────────┤
   │ getPredictionData("동대문구")       │
   │ → predictions 테이블 조회            │
   │ → 50개 동의 최신 예측 데이터         │
   │                                     │
   │ getNewsSignals(5)                   │
   │ → news_signals 테이블 조회          │
   │ → 최근 5개 뉴스                      │
   │                                     │
   │ getTradeStats("동대문구")           │
   │ → apt_trade 테이블 조회              │
   │ → 2025년 이후 거래 100건             │
   └─────────────────────────────────────┘
   ↓
   {
     intent: { type: "prediction", gu: "동대문구" },
     predictions: [15개 동의 예측 데이터],
     news: [5개 뉴스],
     trades: [100건 거래],
     metadata: {
       predictionCount: 15,
       newsCount: 5,
       tradeCount: 100
     }
   }

4️⃣ 컨텍스트 프롬프트 구성 (buildContextPrompt)
   ↓
   ```
   # 사용자 질문
   동대문구 아파트 가격 전망은?

   # 질문 유형: prediction
   # 검색 구: 동대문구

   ## 📊 AI 예측 데이터 (2026-03-20 기준)

   ### 전체 시장 요약
   - 분석 동 수: 15개
   - 평균 매매가: 8.5억원
   - 1개월 평균 변동률: +1.2%
   - 상승 예상 동: 12/15개

   ### 상승률 상위 5개 동
   1. 휘경동: 8.2억 → 8.4억 (+2.3%)
   2. 답십리동: 9.1억 → 9.3억 (+1.8%)
   ...

   ## 📰 최신 뉴스 시그널
   1. 4000세대 단지에 전세는 '단 3개'... (2026-03-20)
   ...

   ## 📈 최근 거래 통계 (2025년~)
   - 최근 거래 건수: 100건
   - 평균 거래가: 8.3억원

   ## 답변 가이드
   위 데이터를 바탕으로 정확하고 구체적인 답변을 제공하세요.
   ```

5️⃣ Claude API 호출
   ↓
   POST https://api.anthropic.com/v1/messages
   {
     model: "claude-sonnet-4-5-20250929",
     max_tokens: 2048,
     system: "당신은 HomeSignal AI의 부동산 분석 전문가입니다...",
     messages: [
       {
         role: "user",
         content: [컨텍스트 프롬프트]
       }
     ]
   }

6️⃣ AI 응답 생성
   ↓
   Claude가 컨텍스트 데이터를 분석하여
   정확하고 구체적인 답변 생성

7️⃣ 사용자에게 응답 전달
   ↓
   {
     message: "동대문구 아파트 시장 분석...",
     usage: {
       inputTokens: 1500,
       outputTokens: 600
     }
   }

8️⃣ UI에 표시
   ↓
   챗봇 화면에 답변 표시
   (타이핑 애니메이션 포함)
```

## 핵심 컴포넌트 설명

### 1. Frontend: ai-chatbot.tsx

**역할**: 챗봇 UI 및 사용자 인터랙션

**주요 기능**:
- 채팅 창 열기/닫기
- 메시지 입력 및 전송
- 로딩 상태 표시
- 자동 스크롤
- 제안 질문 버튼

**상태 관리**:
```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [input, setInput] = useState("");
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**API 호출**:
```typescript
const response = await fetch("/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [...messages, userMessage]
  })
});
```

### 2. Backend: route.ts

**역할**: API 엔드포인트 및 RAG 파이프라인 조율

**처리 순서**:
1. 요청 검증 (`messages` 배열 확인)
2. RAG 데이터 검색 (`getRelevantData`)
3. 컨텍스트 구성 (`buildContextPrompt`)
4. Claude API 호출
5. 응답 반환

**에러 처리**:
- 401: API 키 오류
- 429: Rate limit 초과
- 500: 일반 오류

### 3. RAG Utils: rag-utils.ts

**역할**: RAG 시스템의 핵심 로직

#### analyzeUserIntent()
사용자 질문에서 의도와 파라미터 추출

```typescript
입력: "동대문구 휘경동 집값 전망"
출력: {
  type: "prediction",
  gu: "동대문구",
  dong: "휘경동"
}
```

#### getRelevantData()
병렬로 관련 데이터 조회

```typescript
const [predictions, news, trades] = await Promise.all([
  getPredictionData(dong, gu),
  getNewsSignals(5),
  getTradeStats(dong)
]);
```

#### buildContextPrompt()
검색된 데이터를 Claude가 이해할 수 있는 프롬프트로 구성

**프롬프트 구조**:
1. 사용자 질문 명시
2. 질문 유형 및 파라미터
3. 예측 데이터 (표 형식)
4. 뉴스 시그널
5. 거래 통계
6. 답변 가이드

#### calculateStats()
예측 데이터의 통계 계산

```typescript
- avgPrice: 평균 매매가
- avgChange1m: 1개월 평균 변동률
- risingCount: 상승 예상 동 개수
- maxChange: 최대 변동률
- minChange: 최소 변동률
```

### 4. Database: Supabase

**테이블 구조**:

#### predictions
```sql
- run_date: 예측 생성 날짜
- dong: 동 이름
- current_price_10k: 현재가 (만원 단위)
- pred_1m_10k: 1개월 후 예측가
- pred_2m_10k: 2개월 후 예측가
- pred_3m_10k: 3개월 후 예측가
- change_1m_pct: 1개월 변동률 (%)
- change_2m_pct: 2개월 변동률 (%)
- change_3m_pct: 3개월 변동률 (%)
```

#### news_signals
```sql
- id: UUID
- title: 뉴스 제목
- url: 뉴스 URL
- keywords: 키워드 배열
- published_at: 발행일
```

#### apt_trade
```sql
- deal_year: 거래 연도
- deal_month: 거래 월
- price_10k: 거래가 (만원 단위)
- area: 전용면적
- dong: 동 이름
```

## 성능 최적화

### 1. 병렬 쿼리
```typescript
// ✅ 좋은 예: 병렬 실행 (빠름)
const [predictions, news, trades] = await Promise.all([...]);

// ❌ 나쁜 예: 순차 실행 (느림)
const predictions = await getPredictionData();
const news = await getNewsSignals();
const trades = await getTradeStats();
```

### 2. 쿼리 제한
- predictions: 최대 50개 동
- news_signals: 최대 5개 뉴스
- apt_trade: 최대 100건 거래

### 3. 인덱스 (Supabase)
```sql
-- 필수 인덱스
CREATE INDEX idx_predictions_run_date ON predictions(run_date DESC);
CREATE INDEX idx_news_published_at ON news_signals(published_at DESC);
CREATE INDEX idx_trade_year_month ON apt_trade(deal_year DESC, deal_month DESC);
```

## 보안

### 환경 변수 관리
```bash
# Frontend (공개 가능)
NEXT_PUBLIC_SUPABASE_URL=...

# Backend (비공개)
SUPABASE_SERVICE_KEY=...
ANTHROPIC_API_KEY=...
```

### API 키 보호
- API 라우트는 서버 사이드에서만 실행
- 클라이언트에 API 키 노출 안됨
- Next.js의 `process.env`는 빌드 타임에 주입

### Rate Limiting (권장)
```typescript
// 향후 추가 권장
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15분
  max: 100 // 최대 100번 요청
});
```

## 모니터링 및 로깅

### 현재 로깅
```typescript
console.log("[RAG] 데이터 검색 시작:", userMessage);
console.log("[RAG] 검색 완료:", {
  predictions: metadata.predictionCount,
  news: metadata.newsCount,
  trades: metadata.tradeCount
});
console.error("Claude API Error:", error);
```

### 개선 가능 사항
- Sentry 통합 (에러 추적)
- 응답 시간 측정
- 토큰 사용량 모니터링
- 사용자 질문 패턴 분석

## 확장 가능성

### 1. 대화 히스토리
```typescript
// chat_history 테이블 추가
CREATE TABLE chat_history (
  id UUID PRIMARY KEY,
  session_id UUID,
  role TEXT,
  content TEXT,
  created_at TIMESTAMP
);

// API에서 이전 대화 포함
messages: [
  ...previousMessages,
  { role: "user", content: userMessage }
]
```

### 2. 스트리밍 응답
```typescript
const stream = await anthropic.messages.stream({
  model: "claude-sonnet-4-5-20250929",
  messages: [...]
});

for await (const chunk of stream) {
  // 실시간 전송
}
```

### 3. 멀티모달 (이미지)
```typescript
// 차트 이미지 생성 후 전송
content: [
  { type: "text", text: "가격 추이를 분석해줘" },
  { type: "image", source: { type: "base64", data: chartBase64 }}
]
```

## 비용 예측

### Claude Sonnet 4.5 가격
- 입력: $3 / 백만 토큰
- 출력: $15 / 백만 토큰

### 예상 사용량 (질문당)
- 입력: 약 1,500 토큰 (컨텍스트 포함)
- 출력: 약 600 토큰 (답변)

### 계산
```
입력 비용: 1,500 / 1,000,000 × $3 = $0.0045
출력 비용: 600 / 1,000,000 × $15 = $0.009
질문당 총 비용: $0.0135 (약 ₩18)

월 1,000번 질문: $13.5 (약 ₩18,000)
월 10,000번 질문: $135 (약 ₩180,000)
```

## 참고 자료

- [Anthropic Claude API Docs](https://platform.claude.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Next.js API Routes](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [RAG 패턴 가이드](https://www.anthropic.com/research/retrieval-augmented-generation)

---

**작성일**: 2026-03-25
**버전**: 1.0
**문서 상태**: 최신
