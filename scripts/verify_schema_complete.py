#!/usr/bin/env python3
"""Phase 2: 스키마 완전성 검증"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.database import get_supabase_client

def main():
    client = get_supabase_client()
    
    print("=" * 60)
    print("Phase 2: 스키마 검증")
    print("=" * 60)
    
    all_ok = True
    
    # 1. houses_data 확장 컬럼 확인
    print("\n[1] houses_data 확장 컬럼 확인")
    print("-" * 60)
    
    required_columns = [
        'bedrooms', 'bathrooms', 'sqft_lot', 'floors',
        'waterfront', 'view', 'condition',
        'sqft_above', 'sqft_basement', 'yr_renovated'
    ]
    
    try:
        # 샘플 데이터로 컬럼 존재 확인
        r = client.table('houses_data').select('*').limit(1).execute()
        
        if r.data and len(r.data) > 0:
            existing_cols = list(r.data[0].keys())
            print(f"  기존 컬럼 수: {len(existing_cols)}")
            
            missing = [col for col in required_columns if col not in existing_cols]
            if missing:
                print(f"  [X] 누락 컬럼: {missing}")
                print(f"  -> migrations/003_add_houses_data_columns.sql 실행 필요")
                all_ok = False
            else:
                print(f"  [OK] 확장 컬럼 10개 모두 존재")
        else:
            print("  [INFO] 데이터 없음 - 컬럼 확인 불가")
            print("  [INFO] SQL Editor에서 직접 확인:")
            print("    SELECT column_name FROM information_schema.columns")
            print("    WHERE table_name = 'houses_data';")
    except Exception as e:
        print(f"  [!] 확인 실패: {str(e)[:80]}")
        all_ok = False
    
    # 2. RPC 함수 확인
    print("\n[2] RPC 함수 확인")
    print("-" * 60)
    
    try:
        # match_news_documents 함수 테스트 (빈 임베딩으로)
        test_embedding = [0.0] * 1536
        result = client.rpc(
            'match_news_documents',
            {
                'query_embedding': test_embedding,
                'match_count': 1,
                'match_threshold': 0.0
            }
        ).execute()
        
        print("  [OK] match_news_documents 함수 존재")
    except Exception as e:
        err = str(e)
        if "function" in err.lower() or "does not exist" in err.lower():
            print("  [X] match_news_documents 함수 없음")
            print("  -> migrations/001_setup_pgvector.sql 재실행 필요")
            all_ok = False
        else:
            print(f"  [OK] 함수 존재 (실행 결과: {err[:50]})")
    
    # 3. 테이블 존재 확인
    print("\n[3] 필수 테이블 확인")
    print("-" * 60)
    
    tables = ['news_signals', 'houses_data', 'predictions', 'ai_predictions']
    for table in tables:
        try:
            client.table(table).select('id').limit(0).execute()
            print(f"  [OK] {table}")
        except Exception:
            print(f"  [X] {table}")
            all_ok = False
    
    # 결과
    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] Phase 2 검증 완료 - Phase 3 진행 가능")
    else:
        print("[X] 일부 항목 실패 - 수정 필요")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
