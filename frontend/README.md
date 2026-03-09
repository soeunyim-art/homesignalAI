# HomeSignal AI Frontend

Next.js 15 기반 프론트엔드 애플리케이션

## 시작하기

### 설치

```bash
npm install
# or
yarn install
# or
pnpm install
```

### 개발 서버 실행

```bash
npm run dev
```

http://localhost:3000 에서 애플리케이션을 확인할 수 있습니다.

### 환경 변수 설정

`.env.local` 파일을 생성하고 다음 변수를 설정하세요:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 페이지 구조

- `/` - 홈 (지역 선택)
- `/forecast` - 시계열 예측 차트
- `/chat` - RAG 챗봇
- `/news` - 뉴스 이슈 분석

## 기술 스택

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- React Query
- Recharts
- Supabase Client
- Lucide Icons

## 빌드

```bash
npm run build
```

## Vercel 배포

```bash
vercel --prod
```
