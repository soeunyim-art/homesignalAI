Figma ver. 

[Project Overview and Planning](https://www.figma.com/make/0qBIBjmvNdUXTnTVeNDGOH/Project-Overview-and-Planning?fullscreen=1&t=dXZPoPt0gjnh1Qrb-1)

# 🎨 1. Design Tokens 정의 완료

## Color

- [ ]  Background Primary (#0B1220)
- [ ]  Card Background (#111827)
- [ ]  Border / Divider 정의
- [ ]  Text Primary / Secondary / Muted 정의
- [ ]  Status Color (Positive / Negative / Warning / Info) 정의
- [ ]  Chart 전용 컬러 정의 (과거/예측/신뢰구간)

![image.png](attachment:feba812e-581c-4a46-85f0-bb983d3c0a78:image.png)

---

## 1. 목적

본 문서는 REZON 아파트 시세 예측 웹 서비스의

UI 구현 기준을 정의합니다.

목표는:

- 예측 결과를 신뢰감 있게 표현
- 불확실성을 투명하게 전달
- 개발과 디자인 간 해석 차이 최소화

---

# 2. Design Tokens

## 🎨 Color System

### Base

- `-bg-primary`: #0B1220
- `-bg-card`: #111827
- `-border-default`: #1F2937
- `-divider`: #323946

### Text

- `-text-primary`: #FFFFFF
- `-text-secondary`: #9CA3AF
- `-text-muted`: #6B7280

### Status

- `-positive`: #22C55E
- `-negative`: #EF4444
- `-warning`: #F59E0B
- `-info`: #3B82F6

### Chart

- 과거선: #FFFFFF (Solid)
- 예측선: #60A5FA (Dashed)
- 신뢰구간: rgba(96,165,250,0.2)

---

# 3. Typography

## Font

Pretendard / Inter

## Type Scale

| Type | Size | Weight |
| --- | --- | --- |
| H1 | 28px | 700 |
| H2 | 22px | 600 |
| H3 | 18px | 600 |
| Body | 16px | 400 |
| Caption | 13px | 400 |

Line-height

- Heading: 1.3
- Body: 1.5

---

# 4. Grid & Spacing

## Grid

- 12 column layout
- Max width: 1200px
- Gutter: 24px

## Spacing System

8px 단위만 사용

4 / 8 / 16 / 24 / 32 / 40 / 48 / 64

임의 값 사용 금지

---

# 5. Core Components

---

## 5.1 Button

### Primary

- Height: 44px
- Radius: 8px
- Padding: 0 20px
- Background: Accent
- Text: White

States:

- Hover: brightness +5%
- Disabled: opacity 0.5

---

## 5.2 Card

- Background: Card Color
- Radius: 12px
- Padding: 24px
- Border: 1px solid default border

사용 영역:

- SummaryCard
- DataCard
- AlertCard

---

## 5.3 SummaryCard (예측 핵심 카드)

Props:

- title
- value
- subtext
- status(optional)

사용 예:

- 예측가
- 신뢰구간
- 상승확률
- 변동성 등급

---

## 5.4 Badge (등급 표시)

| Grade | 의미 | 색상 |
| --- | --- | --- |
| A | 높음 | Positive |
| B | 보통 | Warning |
| C | 낮음 | Negative |

형태:

- Pill shape
- Height: 28px

---

## 5.5 Alert

유형:

- Info
- Warning
- Error

사용 예:

- 데이터 부족
- 예측 실패
- 변동성 확대 안내

---

## 5.6 Accordion (예측 근거 영역)

- Default: Collapsed
- Animation: 200ms
- 드라이버 목록 표시

---

# 6. Chart 규칙

## Historical

- Solid line
- 2px

## Forecast

- Dashed line
- 2px

## Confidence Band

- Fill only
- Opacity 20%

## Tooltip

- Dark background
- 가격 단위: 억 단위 + 콤마 표기

---

# 7. 상태 정의 (필수 구현)

| 상태 | UI 처리 방식 |
| --- | --- |
| Default | 기본 화면 |
| Loading | Skeleton UI |
| Error | Alert + Retry |
| Data 부족 | Alert + 신뢰도 C |
| 예측 하락 | Warning tone 사용 (과도한 빨강 금지) |

---

# 8. 카피 가이드 (중요)

❌ 사용 금지 문구

- “매수 추천”
- “지금 사세요”
- “확실한 상승”

✔ 사용 가능 문구

- “상승 확률”
- “예측 범위”
- “변동성 확대 구간”

---

## 디스클레이머 (Prediction 화면 하단 고정)

> 본 서비스는 투자 권유가 아니며 정보 제공 목적입니다.
> 

---

# 9. Screen Structure (개발 구조 기준)

### PredictionScreen

PredictionScreen

├ SummaryGrid

│   ├ PredictedPriceCard

│   ├ ConfidenceIntervalCard

│   ├ UpwardProbabilityCard

│   └ VolatilityGradeCard

├ ForecastChart

├ DriverAccordion

└ ActionRow

---

# 10. Naming Convention

컴포넌트명: PascalCase

- SummaryCard.tsx
- ForecastChart.tsx
- DriverAccordion.tsx
- RiskBadge.tsx
- StatusAlert.tsx
- LoadingSkeleton.tsx

---

# 11. MVP Scope 제한

이번 버전에서는 제외:

- 실시간 업데이트
- AI 자동 매수 판단
- 복잡한 애니메이션
- 개인 맞춤 추천