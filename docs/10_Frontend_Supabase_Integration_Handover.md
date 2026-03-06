# HomeSignal AI — 프론트엔드·Supabase 연동 인수인계서

**문서 버전:** 1.0  
**작성일:** 2026-02-28  
**프로젝트:** 동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스  
**대상:** 프로젝트 총괄(프론트엔드 담당), 개발1(Supabase 담당), 후임 개발자

---

## 1. 한눈에 보기

### 1.1 핵심 질문과 답변

| 질문 | 답변 |
|------|------|
| 팀원(개발1)의 Supabase를 사용하고, 내가 만든 프론트엔드를 연동할 수 있는가? | **가능합니다.** 백엔드 API 경유 또는 Supabase 직접 연결 중 선택 가능. |
| 프론트엔드 기반 디자인은? | `design/b_7o90xjVvyA2-1772242489866` (Next.js + shadcn/ui) 기반으로 진행. |

### 1.2 연동 구조 요약

```
[프로젝트 총괄 프론트엔드]  ← design/b_7o90xjVvyA2-1772242489866 기반
         │
         ├── (권장) ──► [백엔드 API] ──► [개발1 Supabase]
         │
         └── (선택) ──► [개발1 Supabase] 직접 연결 (RLS 설정 필수)
```

---

## 2. 팀원 Supabase + 내 프론트엔드 연동

### 2.1 연동 방식 비교

| 방식 | 설명 | Supabase 키 위치 | 권장도 |
|------|------|------------------|--------|
| **A. 백엔드 API 경유** | 프론트 → 백엔드 API → Supabase | 백엔드 환경변수만 | ✅ 권장 |
| **B. Supabase 직접 연결** | 프론트에서 @supabase/supabase-js 직접 호출 | 프론트 `NEXT_PUBLIC_*` 환경변수 | 선택 시 가능 |

### 2.2 방식 A: 백엔드 API 경유 (권장)

#### 흐름

```
[내 프론트엔드]  →  fetch(NEXT_PUBLIC_API_URL/api/v1/forecast)  →  [백엔드]
                                                                    │
                                                                    └─► [개발1 Supabase]
```

#### 프론트엔드 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `NEXT_PUBLIC_API_URL` | 백엔드 API Base URL | `https://api.homesignal.example.com` 또는 `http://localhost:8000` |

#### 프론트엔드가 호출할 API

| 용도 | 엔드포인트 | 메서드 |
|------|-----------|--------|
| 시계열 예측 | `/api/v1/forecast` | GET, POST |
| RAG 챗봇 | `/api/v1/chat` | POST |
| 뉴스 인사이트 | `/api/v1/news/insights` | GET |

#### 개발1(팀원)이 해야 할 일

1. Supabase 프로젝트 생성, 테이블·데이터 적재
2. 백엔드에 `SUPABASE_URL`, `SUPABASE_KEY` 환경변수 설정
3. 백엔드 API가 Supabase에서 데이터 조회하도록 연동 완료

---

### 2.3 방식 B: Supabase 직접 연결 (선택)

#### 흐름

```
[내 프론트엔드]  →  createClient(SUPABASE_URL, SUPABASE_ANON_KEY)  →  [개발1 Supabase]
```

#### 프론트엔드 환경변수

| 변수명 | 설명 | 발급처 |
|--------|------|--------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | 개발1에게 요청 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon (공개) 키 | 개발1에게 요청 |

#### 개발1이 해야 할 일

1. Supabase 대시보드 → Settings → API에서 URL, anon key 공유
2. **RLS(Row Level Security)** 설정 — 읽기 전용이면 anon key 노출해도 안전

#### 보안 유의사항

- `service_role` 키는 **절대** 프론트엔드에 넣지 말 것
- anon key만 사용, RLS로 테이블별 접근 제어

---

## 3. design/b_7o90xjVvyA2-1772242489866 기반 프론트엔드 진행

### 3.1 디자인 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **경로** | `design/b_7o90xjVvyA2-1772242489866/` |
| **프레임워크** | Next.js 16, React 19 |
| **UI 라이브러리** | shadcn/ui (Radix UI), Tailwind CSS 4 |
| **차트** | Recharts |
| **상태** | Mock 데이터(`lib/data.ts`) 사용 중 — API/Supabase 연동 필요 |

### 3.2 화면 구조

| 경로 | 화면 | 현재 데이터 소스 |
|------|------|------------------|
| `/` | 메인 대시보드 | `lib/data.ts` Mock |
| `/apartments` | 아파트 목록 | `lib/data.ts` Mock |
| `/apartments/[id]` | 아파트 상세 | `lib/data.ts` Mock |
| `/apartments/[id]/prediction` | 예측 상세 | `lib/data.ts` Mock |
| `/compare` | 단지 비교 | `lib/data.ts` Mock |

### 3.3 데이터 모델 (`lib/data.ts` Apartment 인터페이스)

| 필드 | 타입 | 백엔드/Supabase 대응 |
|------|------|---------------------|
| `id` | string | `houses_data` id 또는 단지 식별자 |
| `name`, `nameKo` | string | `complex_name`, `dong_name` |
| `currentPrice` | number | `price` (최신) 또는 매매가 지수 |
| `change3m` | number | 3개월 변동률 (계산) |
| `predictedPrice` | number | forecast API `value` |
| `confidenceMin`, `confidenceMax` | number | forecast API `lower_bound`, `upper_bound` |
| `historicalPrices` | array | forecast API `forecast` 배열 |
| `predictionFactors` | object | `news_weights`, `model_version` 등 |
| `jeonseRatio` | number | (선택) 전세비율 — 별도 데이터 필요 |

### 3.4 Mock → 실제 데이터 교체 시 작업

| # | 작업 | 담당 | 상세 |
|---|------|------|------|
| 1 | API 클라이언트 생성 | 프론트엔드 | `fetch` 또는 `axios`로 백엔드 API 호출 |
| 2 | `lib/data.ts` 수정 | 프론트엔드 | `apartments` 대신 API 호출 결과 변환 |
| 3 | API 응답 → Apartment 매핑 | 프론트엔드 | `forecast` 배열을 `historicalPrices` 형식으로 변환 |
| 4 | 에러·로딩 처리 | 프론트엔드 | Fallback 메시지, 스켈레톤 UI |

### 3.5 API 응답 → 프론트엔드 매핑 예시

**Forecast API 응답 (예시)**

```json
{
  "region": "동대문구",
  "trend": "상승",
  "confidence": 0.85,
  "forecast": [
    { "date": "2026-03-29", "value": 105.5, "lower_bound": 103.5, "upper_bound": 107.5 }
  ],
  "news_weights": [
    { "keyword": "GTX", "frequency": 45, "impact_score": 0.8 }
  ],
  "model_version": "v1.0"
}
```

**Apartment 형식으로 변환**

- `predictedPrice` ← `forecast` 마지막 `value` 또는 지수→금액 환산
- `confidenceMin/Max` ← `forecast` 마지막 `lower_bound`, `upper_bound`
- `historicalPrices` ← `forecast` 배열을 `{ date, price, volume }[]` 형태로 변환
- `predictionFactors` ← `news_weights`, `trend`, `confidence` 조합

---

## 4. 진행 체크리스트

### 4.1 개발1(Supabase 담당) 체크리스트

- [ ] Supabase 프로젝트 생성
- [ ] `db_Schema(Sql)_mokdb.md` DDL 실행 (4개 테이블)
- [ ] pgvector 확장, 인덱스, RLS 설정
- [ ] 국토교통부 API 데이터 → `houses_data` 적재
- [ ] 백엔드에 `SUPABASE_URL`, `SUPABASE_KEY` 전달
- [ ] (방식 B 선택 시) `SUPABASE_URL`, `SUPABASE_ANON_KEY`를 프로젝트 총괄에게 공유

### 4.2 프로젝트 총괄(프론트엔드 담당) 체크리스트

- [ ] `design/b_7o90xjVvyA2-1772242489866` 복사 또는 해당 디렉터리에서 개발 진행
- [ ] 백엔드 API URL 확보 후 `NEXT_PUBLIC_API_URL` 설정
- [ ] `lib/data.ts` Mock 제거, API 호출 로직으로 교체
- [ ] 예측·챗봇·뉴스 API 연동
- [ ] 에러·Fallback 상태 UI 구현
- [ ] (선택) Vercel 배포

### 4.3 백엔드 담당 체크리스트

- [ ] Supabase 실제 연결 (개발1 연결 정보 수령)
- [ ] Forecast API Mock → 실제 `houses_data` 조회로 교체
- [ ] CORS에 프론트엔드 도메인(로컬/Vercel) 추가
- [ ] API 문서(`/docs`) 최신 유지

---

## 5. 참조 문서

| 문서 | 용도 |
|------|------|
| `docs/02_Architecture_Design.md` | 배포(Vercel), 보안, CORS |
| `docs/07_Handover_Document.md` | API 응답 구조 (§6.2) |
| `docs/09_Organization_Roles.md` | 역할별 협업, Supabase 담당(개발1) |
| `db_Schema(Sql)_mokdb.md` | 테이블 스키마 |

---

*본 인수인계서는 2026-02-28 기준으로 작성되었습니다. Supabase·프론트엔드 연동 진행 시 본 문서를 우선 참고해 주세요.*

---

## 6. Supabase 연동 적용 내역 (2026-02-28)

| 구분 | 적용 내용 |
|------|-----------|
| **백엔드** | `.env`에 `SUPABASE_URL`, `SUPABASE_KEY` 설정 완료 |
| **백엔드** | `DataRepository`가 placeholder URL이 아닐 때 `SupabaseDataRepository` 사용 |
| **프론트엔드** | `design/.../lib/supabase.ts` 클라이언트 추가, `.env.local` 설정 |
| **프론트엔드** | `@supabase/supabase-js` 패키지 추가 |
| **설정** | `DATABASE_URL`(PostgreSQL 직접 연결) 옵션 추가 (마이그레이션/ingest용) |
