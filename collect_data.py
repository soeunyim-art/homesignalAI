"""
HomeSignal AI - 데이터 수집 파이프라인
동대문구 아파트 매매가 예측을 위한 데이터 수집
- 국토교통부 아파트 매매 실거래가
- 국토교통부 아파트 전월세 실거래가
- 한국은행 기준금리 / 시장금리
"""

import os
import time
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

load_dotenv("homesignal.env")

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
PUBLIC_DATA_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")
ECOS_API_KEY        = os.getenv("ECOS_API_KEY")
SUPABASE_URL        = os.getenv("SUPABASE_URL")
SUPABASE_KEY        = os.getenv("SUPABASE_KEY")

# 수집 대상 구 (동대문구 + 가격대 유사 인접 4개구)
TARGET_DISTRICTS = {
    "동대문구": "11230",
    "성북구":   "11290",
    "중랑구":   "11260",
    "강북구":   "11305",
    "도봉구":   "11320",
}
COLLECT_FROM_YEAR  = 2020
COLLECT_FROM_MONTH = 1

MOLIT_TRADE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
MOLIT_RENT_URL  = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
ECOS_BASE_URL  = "https://ecos.bok.or.kr/api"


# ─────────────────────────────────────────
# Supabase REST API 헬퍼 (라이브러리 불필요)
# ─────────────────────────────────────────
def supabase_upsert(table: str, rows: list[dict], on_conflict: str) -> int:
    """Supabase PostgREST API로 upsert 수행"""
    if not rows:
        return 0

    # Postgres NUMERIC(10,2) 기준으로 dedup (부동소수점 정규화)
    conflict_cols = [c.strip() for c in on_conflict.split(",")]
    seen = {}
    for row in rows:
        key = tuple(
            round(row.get(c), 2) if isinstance(row.get(c), float) else row.get(c)
            for c in conflict_cols
        )
        seen[key] = row
    rows = list(seen.values())

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=ignore-duplicates,return=representation",
    }
    params = {"on_conflict": on_conflict}

    # 500건씩 나눠서 전송 (요청 크기 제한 방지)
    total = 0
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        try:
            resp = requests.post(url, headers=headers, params=params,
                                 data=json.dumps(chunk, ensure_ascii=False),
                                 timeout=30)
            if resp.status_code in (200, 201):
                total += len(resp.json()) if resp.text else len(chunk)
            else:
                print(f"    [ERROR] Supabase {resp.status_code}: {resp.text[:200]}")
        except requests.RequestException as e:
            print(f"    [ERROR] Supabase 연결 실패: {e}")

    return total


# ─────────────────────────────────────────
# 국토교통부 API 공통 파서
# ─────────────────────────────────────────
def fetch_molit_xml(endpoint: str, params: dict, lawd_cd: str = "11230") -> list[dict]:
    """국토교통부 API (XML) 호출 후 item 리스트 반환"""
    params.update({
        "serviceKey": PUBLIC_DATA_API_KEY,
        "LAWD_CD":    lawd_cd,
        "numOfRows":  1000,
        "pageNo":     1,
    })
    try:
        resp = requests.get(endpoint, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] API 호출 실패: {e}")
        return []

    root = ET.fromstring(resp.content)
    result_code = root.findtext(".//resultCode", "")
    if result_code not in ("00", "000"):
        msg = root.findtext(".//resultMsg", "")
        print(f"  [WARN] API 오류 코드 {result_code}: {msg}")
        return []

    items = []
    for item in root.findall(".//item"):
        row = {child.tag: (child.text or "").strip() for child in item}
        items.append(row)
    return items


# ─────────────────────────────────────────
# 아파트 매매 실거래가 수집
# ─────────────────────────────────────────
def collect_apt_trade(year: int, month: int, lawd_cd: str = "11230") -> int:
    deal_ymd = f"{year}{month:02d}"
    print(f"  매매 {year}-{month:02d} 수집 중... (코드:{lawd_cd})")

    items = fetch_molit_xml(MOLIT_TRADE_URL, {"DEAL_YMD": deal_ymd}, lawd_cd)
    if not items:
        return 0

    rows = []
    for it in items:
        try:
            rows.append({
                "deal_year":  int(it.get("dealYear",  it.get("년", 0))),
                "deal_month": int(it.get("dealMonth", it.get("월", 0))),
                "deal_day":   int((it.get("dealDay",  it.get("일", "0")) or "0").strip()),
                "dong":       it.get("umdNm",     it.get("법정동", "")).strip(),
                "apt_name":   it.get("aptNm",     it.get("아파트", "")).strip(),
                "build_year": int(it.get("buildYear", it.get("건축년도", 0)) or 0),
                "area":       float(it.get("excluUseAr", it.get("전용면적", 0)) or 0),
                "floor":      int(it.get("floor",    it.get("층", 0)) or 0),
                "price_10k":  int((it.get("dealAmount", it.get("거래금액", "0")) or "0").replace(",", "")),
                "deal_type":  it.get("dealingGbn", it.get("거래유형", "")).strip(),
            })
        except (ValueError, TypeError) as e:
            print(f"    [SKIP] 파싱 오류: {e}")
            continue

    count = supabase_upsert(
        "apt_trade", rows,
        "deal_year,deal_month,deal_day,dong,apt_name,area,floor"
    )
    print(f"    → {count}건 적재")
    return count


def _parse_contract_term(val) -> int:
    """계약기간 파싱: 숫자('24') 또는 범위('24.12~26.12') → 개월 수"""
    val = str(val).strip()
    if not val:
        return 0
    if "~" in val:
        # 'YY.MM~YY.MM' 형식 → 개월 수 계산
        try:
            start, end = val.split("~")
            sy, sm = [int(x) for x in start.split(".")]
            ey, em = [int(x) for x in end.split(".")]
            return (ey - sy) * 12 + (em - sm)
        except Exception:
            return 0
    try:
        return int(val)
    except ValueError:
        return 0


# ─────────────────────────────────────────
# 아파트 전월세 실거래가 수집
# ─────────────────────────────────────────
def collect_apt_rent(year: int, month: int, lawd_cd: str = "11230") -> int:
    deal_ymd = f"{year}{month:02d}"
    print(f"  전월세 {year}-{month:02d} 수집 중... (코드:{lawd_cd})")

    items = fetch_molit_xml(MOLIT_RENT_URL, {"DEAL_YMD": deal_ymd}, lawd_cd)
    if not items:
        return 0

    rows = []
    for it in items:
        try:
            monthly = (it.get("monthlyRent", it.get("월세금액", "0")) or "0").replace(",", "")
            deposit = (it.get("deposit",     it.get("보증금액", "0")) or "0").replace(",", "")
            ct_raw  = it.get("contractType", it.get("계약유형", "")).strip()
            contract_type = ct_raw if ct_raw else ("월세" if int(monthly) > 0 else "전세")

            rows.append({
                "deal_year":        int(it.get("dealYear",    it.get("년", 0))),
                "deal_month":       int(it.get("dealMonth",   it.get("월", 0))),
                "deal_day":         int((it.get("dealDay",    it.get("일", "0")) or "0").strip()),
                "dong":             it.get("umdNm",           it.get("법정동", "")).strip(),
                "apt_name":         it.get("aptNm",           it.get("아파트", "")).strip(),
                "build_year":       int(it.get("buildYear",   it.get("건축년도", 0)) or 0),
                "area":             float(it.get("excluUseAr",it.get("전용면적", 0)) or 0),
                "floor":            int(it.get("floor",       it.get("층", 0)) or 0),
                "contract_type":    contract_type,
                "deposit_10k":      int(deposit),
                "monthly_rent_10k": int(monthly),
                "contract_term":    _parse_contract_term(it.get("contractTerm", it.get("계약기간", ""))),
            })
        except (ValueError, TypeError) as e:
            print(f"    [SKIP] 파싱 오류: {e}")
            continue

    count = supabase_upsert(
        "apt_rent", rows,
        "deal_year,deal_month,deal_day,dong,apt_name,area,floor,contract_type"
    )
    print(f"    → {count}건 적재")
    return count


# ─────────────────────────────────────────
# 금리 정보 수집 (한국은행 ECOS)
# ─────────────────────────────────────────
# (stat_code, item_code, cycle)
# cycle='M': 월별 직접 조회 / cycle='D': 일별 조회 후 월평균 계산
ECOS_RATE_TYPES = {
    "기준금리":    ("722Y001", "0101000",  "M"),
    "CD금리(91일)":("817Y002", "010502000","D"),
    "국고채(3년)": ("817Y002", "010200000","D"),
}

def collect_interest_rates(start_date: str, end_date: str) -> int:
    """금리 수집: 월별 series는 직접, 일별 series는 월평균으로 집계"""
    print(f"  금리 {start_date} ~ {end_date} 수집 중...")

    # 일별 조회용 날짜 확장 (월 초~말)
    start_m = start_date[:6]  # 'YYYYMM'
    end_m   = end_date[:6]
    # 일별 조회는 YYYYMMDD 형식 필요 → 해당 범위의 전체 일자
    start_d = start_m + "01"
    # 말일: 다음달 1일 - 1일
    _end_dt    = datetime.strptime(end_m, "%Y%m")
    _next      = _end_dt.replace(day=1) + relativedelta(months=1)
    end_d      = (_next - timedelta(days=1)).strftime("%Y%m%d")

    rows = []

    for rate_name, (stat_code, item_code, cycle) in ECOS_RATE_TYPES.items():
        if cycle == "M":
            url = (
                f"{ECOS_BASE_URL}/StatisticSearch/{ECOS_API_KEY}/json/kr/1/1000"
                f"/{stat_code}/M/{start_m}/{end_m}/{item_code}"
            )
            try:
                data = requests.get(url, timeout=30).json()
            except Exception as e:
                print(f"    [ERROR] {rate_name}: {e}")
                continue

            for item in data.get("StatisticSearch", {}).get("row", []):
                t, v = item.get("TIME",""), item.get("DATA_VALUE","")
                if not t or not v:
                    continue
                try:
                    d = datetime.strptime(t, "%Y%m").date()
                    # 월말일로 저장
                    d = (d.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)
                    rows.append({"stat_date": d.isoformat(), "rate_type": rate_name, "rate": float(v)})
                except (ValueError, TypeError):
                    continue

        else:  # cycle == "D" → 일별 조회 후 월평균
            url = (
                f"{ECOS_BASE_URL}/StatisticSearch/{ECOS_API_KEY}/json/kr/1/10000"
                f"/{stat_code}/D/{start_d}/{end_d}/{item_code}"
            )
            try:
                data = requests.get(url, timeout=30).json()
            except Exception as e:
                print(f"    [ERROR] {rate_name}: {e}")
                continue

            # 월별로 그룹화 → 평균
            monthly: dict = {}
            for item in data.get("StatisticSearch", {}).get("row", []):
                t, v = item.get("TIME",""), item.get("DATA_VALUE","")
                if not t or not v or len(t) < 6:
                    continue
                try:
                    ym = t[:6]  # 'YYYYMM'
                    monthly.setdefault(ym, []).append(float(v))
                except (ValueError, TypeError):
                    continue

            for ym, vals in monthly.items():
                try:
                    d = datetime.strptime(ym, "%Y%m").date()
                    d = (d.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)
                    rows.append({"stat_date": d.isoformat(), "rate_type": rate_name, "rate": round(sum(vals)/len(vals), 3)})
                except Exception:
                    continue

        time.sleep(0.3)

    count = supabase_upsert("interest_rate", rows, "stat_date,rate_type")
    print(f"    → {count}건 적재")
    return count


# ─────────────────────────────────────────
# 메인 파이프라인
# ─────────────────────────────────────────
def run_full_collection():
    now   = datetime.now()
    start = date(COLLECT_FROM_YEAR, COLLECT_FROM_MONTH, 1)
    end   = date(now.year, now.month, 1) - relativedelta(months=1)

    district_names = ", ".join(TARGET_DISTRICTS.keys())
    print("=" * 55)
    print("HomeSignal AI 데이터 수집 시작")
    print(f"수집 범위: {start} ~ {end}")
    print(f"수집 구: {district_names}")
    print("=" * 55)

    total_trade = total_rent = 0
    for gu_name, lawd_cd in TARGET_DISTRICTS.items():
        print(f"\n{'='*30}")
        print(f"[{gu_name} ({lawd_cd})] 수집 시작")
        print(f"{'='*30}")
        cur = start
        while cur <= end:
            print(f"\n[{cur.year}-{cur.month:02d}]")
            total_trade += collect_apt_trade(cur.year, cur.month, lawd_cd)
            time.sleep(0.5)
            total_rent  += collect_apt_rent(cur.year, cur.month, lawd_cd)
            time.sleep(0.5)
            cur += relativedelta(months=1)

    print("\n[금리 정보]")
    total_rate = collect_interest_rates(
        start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    )

    print("\n" + "=" * 55)
    print(f"수집 완료!")
    print(f"  매매 실거래: {total_trade:,}건")
    print(f"  전월세 실거래: {total_rent:,}건")
    print(f"  금리 데이터: {total_rate:,}건")
    print("=" * 55)


def run_monthly_update():
    now        = datetime.now()
    prev_month = date(now.year, now.month, 1) - relativedelta(months=1)
    y, m       = prev_month.year, prev_month.month
    print(f"증분 업데이트: {y}-{m:02d} ({', '.join(TARGET_DISTRICTS.keys())})")
    for gu_name, lawd_cd in TARGET_DISTRICTS.items():
        print(f"\n[{gu_name}]")
        collect_apt_trade(y, m, lawd_cd)
        collect_apt_rent(y, m, lawd_cd)
    collect_interest_rates(prev_month.strftime("%Y%m%d"), prev_month.strftime("%Y%m%d"))


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "update":
        run_monthly_update()
    else:
        run_full_collection()
