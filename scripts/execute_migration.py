#!/usr/bin/env python3
"""Supabase에 마이그레이션 직접 실행 (service_role 키 사용)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.shared.database import get_supabase_client

def execute_sql(client, sql: str, description: str):
    """SQL 실행"""
    try:
        print(f"\n[실행] {description}")
        result = client.rpc('exec_sql', {'query': sql}).execute()
        print(f"  [OK] 성공")
        return True
    except Exception as e:
        # RPC 함수가 없으면 직접 실행 시도
        print(f"  [!] RPC 실패, 대체 방법 필요: {str(e)[:80]}")
        return False

def main():
    print("=" * 60)
    print("ai_predictions 테이블 생성")
    print("=" * 60)
    
    # service_role 키로 클라이언트 생성
    try:
        client = get_supabase_client(use_service_role=True)
        print(f"[OK] service_role 클라이언트 생성됨")
    except Exception as e:
        print(f"[X] 클라이언트 생성 실패: {e}")
        return 1
    
    # ai_predictions 테이블 생성 SQL
    sql = """
-- ai_predictions 테이블 생성
CREATE TABLE IF NOT EXISTS ai_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version TEXT NOT NULL,
    target_date DATE NOT NULL,
    predicted_price NUMERIC(15, 2) NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    features_used JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS ai_predictions_target_date_idx
ON ai_predictions (target_date DESC);

CREATE INDEX IF NOT EXISTS ai_predictions_model_version_idx
ON ai_predictions (model_version);

-- RLS 정책
ALTER TABLE ai_predictions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read ai_predictions" ON ai_predictions;
CREATE POLICY "Allow public read ai_predictions" ON ai_predictions FOR SELECT USING (true);
"""
    
    print("\n[INFO] Supabase Python 클라이언트는 직접 SQL 실행을 지원하지 않습니다.")
    print("[INFO] 다음 방법 중 하나를 선택하세요:")
    print("\n1. Supabase SQL Editor에서 실행 (권장):")
    print("   https://supabase.com/dashboard/project/yietqoikdaqpwmmvamtv/sql/new")
    print("   파일: migrations/002_add_ai_predictions_only.sql")
    print("\n2. psycopg로 직접 연결 (DATABASE_URL 필요):")
    print("   uv run python scripts/execute_migration_psycopg.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
