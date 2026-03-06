#!/usr/bin/env python3
"""마이그레이션 검증 스크립트"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.database import get_supabase_client

def main():
    client = get_supabase_client()
    
    tables = [
        'news_signals',
        'houses_data', 
        'predictions',
        'ai_predictions'
    ]
    
    print("=" * 60)
    print("마이그레이션 검증")
    print("=" * 60)
    
    all_ok = True
    for table in tables:
        try:
            r = client.table(table).select("*").limit(0).execute()
            print(f"  [OK] {table}: 존재")
        except Exception as e:
            err = str(e)
            if "Could not find" in err:
                print(f"  [X] {table}: 없음")
                all_ok = False
            else:
                print(f"  [!] {table}: {err[:50]}")
                all_ok = False
    
    print("\n" + "=" * 60)
    print("service_role 키 확인")
    print("=" * 60)
    
    from src.config import settings
    if settings.supabase_service_role_key:
        print("  [OK] SUPABASE_SERVICE_ROLE_KEY 설정됨")
    else:
        print("  [X] SUPABASE_SERVICE_ROLE_KEY 미설정")
        all_ok = False
    
    # houses_data 컬럼 확인 (선택적)
    print("\n" + "=" * 60)
    print("houses_data 확장 컬럼 확인")
    print("=" * 60)
    
    required_columns = [
        'bedrooms', 'bathrooms', 'sqft_lot', 'floors',
        'waterfront', 'view', 'condition', 
        'sqft_above', 'sqft_basement', 'yr_renovated'
    ]
    
    try:
        # 더미 데이터로 컬럼 존재 확인 (실제 INSERT는 안함)
        test_record = {col: None for col in required_columns}
        test_record.update({
            'complex_name': 'test',
            'price': 100000000,
            'contract_date': '2024-01-01'
        })
        # 실제로는 INSERT 안하고 스키마만 확인
        print("  [INFO] 컬럼 확인을 위해서는 SQL Editor에서 직접 확인 권장")
        print("  SELECT column_name FROM information_schema.columns")
        print("  WHERE table_name = 'houses_data';")
    except Exception as e:
        print(f"  [!] 컬럼 확인 실패: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] 모든 검증 통과")
    else:
        print("[X] 일부 항목 실패 - 마이그레이션 실행 필요")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
