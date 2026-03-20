-- HomeSignal AI - Supabase Schema (FK 포함 정규화)
-- SQL Editor 에 전체 붙여넣기 후 Run 실행
-- 주의: 기존 테이블을 DROP 후 재생성합니다 (apt_trade/apt_rent/interest_rate 는 건드리지 않음)

-- 기존 테이블 삭제 (의존성 역순)
DROP TABLE IF EXISTS predictions_apt CASCADE;
DROP TABLE IF EXISTS predictions     CASCADE;
DROP TABLE IF EXISTS apartments      CASCADE;
DROP TABLE IF EXISTS dongs           CASCADE;


-- 1단계: dongs 마스터 테이블
CREATE TABLE dongs (
    dong_name  TEXT PRIMARY KEY,
    gu_name    TEXT NOT NULL DEFAULT '',
    dong_code  TEXT
);

-- apt_trade 에서 동 목록 자동 추출
INSERT INTO dongs (dong_name, gu_name)
SELECT DISTINCT dong, ''
FROM apt_trade
WHERE dong IS NOT NULL AND dong <> ''
ON CONFLICT (dong_name) DO NOTHING;


-- 2단계: apartments 마스터 테이블 (FK -> dongs)
CREATE TABLE apartments (
    id        BIGSERIAL PRIMARY KEY,
    dong      TEXT    NOT NULL REFERENCES dongs(dong_name) ON DELETE CASCADE,
    apt_name  TEXT    NOT NULL,
    area      NUMERIC NOT NULL,
    UNIQUE (dong, apt_name, area)
);

-- apt_trade 에서 아파트 목록 자동 추출
INSERT INTO apartments (dong, apt_name, area)
SELECT DISTINCT dong, apt_name, area
FROM apt_trade
WHERE dong IS NOT NULL AND dong <> ''
  AND apt_name IS NOT NULL AND apt_name <> ''
  AND area IS NOT NULL
ON CONFLICT (dong, apt_name, area) DO NOTHING;


-- 3단계: predictions 동별 예측 테이블 (FK -> dongs)
CREATE TABLE predictions (
    id                BIGSERIAL PRIMARY KEY,
    run_date          DATE    NOT NULL,
    dong              TEXT    NOT NULL REFERENCES dongs(dong_name) ON DELETE RESTRICT,
    base_ym           TEXT,
    current_price_10k INT,
    pred_1m_10k       INT,
    pred_2m_10k       INT,
    pred_3m_10k       INT,
    change_1m_pct     NUMERIC,
    change_2m_pct     NUMERIC,
    change_3m_pct     NUMERIC,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (run_date, dong)
);


-- 4단계: predictions_apt 아파트별 예측 테이블 (FK -> dongs)
CREATE TABLE predictions_apt (
    id                BIGSERIAL PRIMARY KEY,
    run_date          DATE    NOT NULL,
    dong              TEXT    NOT NULL REFERENCES dongs(dong_name) ON DELETE RESTRICT,
    apt_name          TEXT    NOT NULL,
    area              NUMERIC NOT NULL,
    base_ym           TEXT,
    current_price_10k INT,
    pred_1m_10k       INT,
    pred_2m_10k       INT,
    pred_3m_10k       INT,
    change_1m_pct     NUMERIC,
    change_2m_pct     NUMERIC,
    change_3m_pct     NUMERIC,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);


-- 검증: 4개 테이블 존재 + dongs 행 수 확인
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('dongs', 'apartments', 'predictions', 'predictions_apt')
ORDER BY table_name;

SELECT COUNT(*) AS dong_count FROM dongs;
SELECT COUNT(*) AS apt_count  FROM apartments;
