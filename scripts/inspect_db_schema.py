#!/usr/bin/env python3
"""Supabase PostgreSQL 스키마/테이블 정보 조회 스크립트"""
import os
import sys

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from psycopg.rows import dict_row

def main():
    from src.config import settings
    db_url = settings.database_url
    if not db_url:
        print("DATABASE_URL이 .env에 설정되지 않았습니다.")
        sys.exit(1)

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # 1. 확장(Extensions) 목록
            cur.execute("""
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname NOT IN ('plpgsql')
                ORDER BY extname;
            """)
            extensions = cur.fetchall()
            print("=" * 60)
            print("📦 Extensions (확장)")
            print("=" * 60)
            for ext in extensions:
                print(f"  - {ext['extname']} (v{ext['extversion']})")
            print()

            # 2. 스키마 목록
            cur.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schema_name;
            """)
            schemas = cur.fetchall()
            print("=" * 60)
            print("📁 Schemas (스키마)")
            print("=" * 60)
            for s in schemas:
                print(f"  - {s['schema_name']}")
            print()

            # 3. public 스키마의 테이블 목록 및 상세
            cur.execute("""
                SELECT t.table_name, t.table_type
                FROM information_schema.tables t
                WHERE t.table_schema = 'public'
                ORDER BY t.table_type, t.table_name;
            """)
            tables = cur.fetchall()
            print("=" * 60)
            print("📋 Tables (테이블) - public 스키마")
            print("=" * 60)

            for tbl in tables:
                name = tbl['table_name']
                tbl_type = tbl['table_type']
                print(f"\n  [{tbl_type}] {name}")
                print("  " + "-" * 50)

                # 컬럼 정보
                cur.execute("""
                    SELECT column_name, data_type, character_maximum_length,
                           is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """, (name,))
                cols = cur.fetchall()
                for col in cols:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                    print(f"    - {col['column_name']}: {col['data_type']}{length} {nullable}{default}")

                # 행 수 (테이블인 경우)
                if tbl_type == 'BASE TABLE':
                    try:
                        cur.execute(f'SELECT COUNT(*) as cnt FROM public."{name}"')
                        cnt = cur.fetchone()['cnt']
                        print(f"    [행 수: {cnt:,}건]")
                    except Exception:
                        pass

            # 4. RPC/함수 목록
            cur.execute("""
                SELECT routine_name, routine_type
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                ORDER BY routine_name;
            """)
            routines = cur.fetchall()
            print("\n" + "=" * 60)
            print("⚙️ Functions/RPC (함수)")
            print("=" * 60)
            for r in routines:
                print(f"  - {r['routine_name']} ({r['routine_type']})")
            print()

            # 5. 인덱스 목록
            cur.execute("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            indexes = cur.fetchall()
            print("=" * 60)
            print("🔍 Indexes (인덱스)")
            print("=" * 60)
            for idx in indexes:
                print(f"  - {idx['indexname']} (on {idx['tablename']})")
            print()

if __name__ == "__main__":
    main()
