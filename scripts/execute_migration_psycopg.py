#!/usr/bin/env python3
"""psycopg로 마이그레이션 직접 실행"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from src.config import settings

def main():
    if not settings.database_url:
        print("[X] DATABASE_URL이 설정되지 않았습니다.")
        print("    .env에 DATABASE_URL을 추가하세요.")
        return 1
    
    print("=" * 60)
    print("ai_predictions 테이블 생성 (psycopg)")
    print("=" * 60)
    
    # 마이그레이션 SQL 읽기
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "migrations",
        "002_add_ai_predictions_only.sql"
    )
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"\n[INFO] 파일: {migration_file}")
    print(f"[INFO] DATABASE_URL: {settings.database_url[:50]}...")
    
    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                print("\n[실행] SQL 실행 중...")
                cur.execute(sql)
                conn.commit()
                print("[OK] ai_predictions 테이블 생성 완료")
                
                # 검증
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'ai_predictions'
                """)
                count = cur.fetchone()[0]
                if count > 0:
                    print("[OK] 테이블 존재 확인됨")
                else:
                    print("[!] 테이블이 생성되지 않았습니다")
                
        print("\n" + "=" * 60)
        print("[완료] 마이그레이션 성공")
        print("=" * 60)
        print("\n검증: uv run python scripts/verify_migration.py")
        return 0
        
    except Exception as e:
        print(f"\n[X] 실행 실패: {e}")
        print("\n대체 방법:")
        print("  1. Supabase SQL Editor에서 직접 실행")
        print("     https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new")
        print("  2. migrations/002_add_ai_predictions_only.sql 내용 복사")
        return 1

if __name__ == "__main__":
    sys.exit(main())
