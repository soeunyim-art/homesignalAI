"""Supabase 연결 테스트 스크립트"""
import sys

def main():
    from src.config import settings
    from src.shared.database import get_supabase_client

    client = get_supabase_client()
    print("Supabase URL:", settings.supabase_url[:50] + "...")
    print("Client type:", type(client).__name__)

    if type(client).__name__.startswith("Mock"):
        print("Mock client - placeholder URL was replaced with real URL?")
        return 0

    try:
        r = client.table("houses_data").select("id").limit(1).execute()
        print("houses_data OK, rows:", len(r.data))
    except Exception as e:
        print("houses_data error (table may not exist):", str(e)[:120])
    return 0

if __name__ == "__main__":
    sys.exit(main())
