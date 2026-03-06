"""Supabase 마이그레이션 실행 스크립트"""

import os
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from dotenv import load_dotenv

# .env 로드
load_dotenv()


def run_migration():
    """마이그레이션 SQL 파일 실행"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    migration_file = project_root / "migrations" / "001_setup_pgvector.sql"
    if not migration_file.exists():
        print(f"❌ 마이그레이션 파일을 찾을 수 없습니다: {migration_file}")
        sys.exit(1)

    print("=" * 60)
    print("Supabase 마이그레이션 실행")
    print("=" * 60)
    print(f"데이터베이스: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
    print(f"마이그레이션 파일: {migration_file.name}")
    print()

    # SQL 파일 읽기
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # 데이터베이스 연결 및 실행
    conn = None
    try:
        print("📡 데이터베이스 연결 중...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print("🚀 마이그레이션 실행 중...")
        cursor.execute(sql)

        print()
        print("=" * 60)
        print("✅ 마이그레이션 성공!")
        print("=" * 60)
        print()
        print("생성된 항목:")
        print("  ✓ pgvector extension")
        print("  ✓ news_signals 테이블 (벡터 임베딩)")
        print("  ✓ houses_data 테이블 (실거래가)")
        print("  ✓ predictions 테이블 (모델 예측)")
        print("  ✓ match_news_documents() RPC 함수")
        print("  ✓ 자동 업데이트 트리거")
        print()

        # 테이블 확인
        print("📊 생성된 테이블 확인:")
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")

        cursor.close()

    except psycopg2.Error as e:
        print()
        print("=" * 60)
        print("❌ 마이그레이션 실패")
        print("=" * 60)
        print(f"오류: {e}")
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            print()
            print("🔌 데이터베이스 연결 종료")


if __name__ == "__main__":
    run_migration()
