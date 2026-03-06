#!/usr/bin/env python3
"""Supabase REST API로 테이블/스키마 정보 조회 (직접 DB 연결 불필요)"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.shared.database import get_supabase_client

# 마이그레이션에 정의된 예상 테이블 + 추가 확인용
EXPECTED_TABLES = [
    ("news_signals", ["id", "title", "content", "url", "keywords", "published_at", "embedding", "created_at", "updated_at"]),
    ("houses_data", ["id", "complex_name", "dong_name", "price", "contract_date", "sqft_living", "yr_built", "gu_name", "created_at", "updated_at"]),
    ("predictions", ["id", "region", "period", "horizon", "predictions", "confidence_interval", "model_name", "model_version", "created_at"]),
]
# Supabase 기본/커스텀 테이블 추가 탐색
EXTRA_TABLES = ["profiles", "users", "documents", "news", "house_transactions"]

def main():
    client = get_supabase_client()
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    print("=" * 60)
    print("Supabase 프로젝트: yietqoikdaqpwmmvamtv")
    print("URL:", settings.supabase_url)
    print("조회 시각:", checked_at)
    print("=" * 60)

    if "Mock" in type(client).__name__:
        print("\n[!] Mock 클라이언트 사용 중 - 실제 DB 연결 필요")
        return

    results = []
    print("\n[HomeSignal 예상 테이블]")
    print("-" * 60)
    for table_name, expected_cols in EXPECTED_TABLES:
        try:
            r = client.table(table_name).select("*").limit(5).execute()
            cnt = len(r.data) if r.data else 0
            cols = list(r.data[0].keys()) if r.data and len(r.data) > 0 else []
            col_str = ", ".join(cols[:6]) + ("..." if len(cols) > 6 else "")
            print(f"  [OK] {table_name}: 존재 (컬럼: {col_str})")
            results.append((table_name, True, cols, cnt))
        except Exception as e:
            err = str(e)
            if "Could not find the table" in err or "relation" in err.lower():
                print(f"  [X] {table_name}: 테이블 없음")
                results.append((table_name, False, [], 0))
            else:
                print(f"  [!] {table_name}: {err[:80]}")
                results.append((table_name, False, [], 0))

    print("\n[기타 테이블 탐색]")
    print("-" * 60)
    for table_name in EXTRA_TABLES:
        if table_name in [r[0] for r in results]:
            continue
        try:
            r = client.table(table_name).select("*").limit(1).execute()
            cols = list(r.data[0].keys()) if r.data and len(r.data) > 0 else []
            print(f"  [OK] {table_name}: 존재 (컬럼: {cols})")
            results.append((table_name, True, cols, len(r.data or [])))
        except Exception:
            pass  # 없으면 출력 생략

    print("\n" + "=" * 60)
    print("[TIP] 마이그레이션 미실행 시: migrations/001_setup_pgvector.sql")
    print("   Supabase SQL Editor에서 실행 필요")
    print("=" * 60)
    return results

if __name__ == "__main__":
    main()
