"""
AI 챗봇 상세 테스트 스크립트

이 스크립트는 챗봇의 모든 구성 요소를 테스트합니다:
1. 환경 변수 확인
2. Supabase 연결 테스트
3. 데이터 검색 테스트
4. Anthropic API 연결 테스트

실행 방법: python test_chatbot_detailed.py
"""

import os
import sys
import json
from dotenv import load_dotenv

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# .env 파일 로드
load_dotenv()

def check_env_vars():
    """환경 변수 확인"""
    print("=" * 70)
    print("1. 환경 변수 확인")
    print("=" * 70)

    required_vars = {
        "NEXT_PUBLIC_SUPABASE_URL": os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    }

    all_present = True
    for var_name, var_value in required_vars.items():
        if var_value:
            masked = var_value[:15] + "..." + var_value[-10:] if len(var_value) > 30 else var_value[:10] + "..."
            print(f"✅ {var_name}: {masked}")
        else:
            print(f"❌ {var_name}: 설정되지 않음")
            all_present = False

    print()
    return all_present


def test_supabase_connection():
    """Supabase 연결 테스트"""
    print("=" * 70)
    print("2. Supabase 연결 테스트")
    print("=" * 70)

    try:
        from supabase import create_client

        url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        if not url or not key:
            print("❌ Supabase 환경 변수가 설정되지 않았습니다.")
            return False

        supabase = create_client(url, key)

        # predictions 테이블 조회
        result = supabase.table("predictions").select("*").limit(1).execute()
        print(f"✅ predictions 테이블 연결 성공 ({len(result.data)}건)")

        # news_signals 테이블 조회
        result = supabase.table("news_signals").select("*").limit(1).execute()
        print(f"✅ news_signals 테이블 연결 성공 ({len(result.data)}건)")

        # apt_trade 테이블 조회
        result = supabase.table("apt_trade").select("*").limit(1).execute()
        print(f"✅ apt_trade 테이블 연결 성공 ({len(result.data)}건)")

        print()
        return True

    except ImportError:
        print("❌ supabase-py가 설치되지 않았습니다.")
        print("   설치: pip install supabase")
        print()
        return False
    except Exception as e:
        print(f"❌ Supabase 연결 오류: {e}")
        print()
        return False


def test_data_retrieval():
    """데이터 검색 테스트 (RAG)"""
    print("=" * 70)
    print("3. 데이터 검색 테스트 (RAG)")
    print("=" * 70)

    try:
        from supabase import create_client

        url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase = create_client(url, key)

        # 예측 데이터 검색
        print("📊 예측 데이터 검색 중...")
        predictions = supabase.table("predictions") \
            .select("*") \
            .order("run_date", desc=True) \
            .limit(10) \
            .execute()

        print(f"   검색된 예측 데이터: {len(predictions.data)}건")
        if predictions.data:
            sample = predictions.data[0]
            print(f"   샘플: {sample.get('dong', 'N/A')} - 현재가 {sample.get('current_price_10k', 0) / 10000:.1f}억원")

        # 뉴스 시그널 검색
        print("\n📰 뉴스 시그널 검색 중...")
        news = supabase.table("news_signals") \
            .select("*") \
            .order("published_at", desc=True) \
            .limit(5) \
            .execute()

        print(f"   검색된 뉴스: {len(news.data)}건")
        if news.data:
            sample = news.data[0]
            print(f"   샘플: {sample.get('title', 'N/A')[:40]}...")

        # 거래 통계 검색
        print("\n📈 거래 통계 검색 중...")
        trades = supabase.table("apt_trade") \
            .select("*") \
            .gte("deal_year", 2025) \
            .limit(10) \
            .execute()

        print(f"   검색된 거래: {len(trades.data)}건")

        print()
        return True

    except Exception as e:
        print(f"❌ 데이터 검색 오류: {e}")
        print()
        return False


def test_anthropic_api():
    """Anthropic API 연결 테스트"""
    print("=" * 70)
    print("4. Anthropic API 연결 테스트")
    print("=" * 70)

    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            return False

        client = anthropic.Anthropic(api_key=api_key)

        # 간단한 테스트 메시지
        print("🤖 Claude API 호출 중...")
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "안녕하세요. 간단히 인사해주세요."
                }
            ]
        )

        response_text = message.content[0].text
        print(f"✅ Claude API 연결 성공")
        print(f"   응답: {response_text[:80]}...")
        print(f"   토큰 사용: 입력 {message.usage.input_tokens}, 출력 {message.usage.output_tokens}")

        print()
        return True

    except ImportError:
        print("❌ anthropic 패키지가 설치되지 않았습니다.")
        print("   설치: pip install anthropic")
        print()
        return False
    except anthropic.AuthenticationError:
        print("❌ API 키가 유효하지 않습니다.")
        print()
        return False
    except anthropic.RateLimitError:
        print("❌ API 요청 한도를 초과했습니다.")
        print()
        return False
    except Exception as e:
        print(f"❌ Anthropic API 오류: {e}")
        print()
        return False


def main():
    print("\n" + "=" * 70)
    print("🧪 AI 챗봇 상세 진단 테스트")
    print("=" * 70 + "\n")

    results = []

    # 1. 환경 변수 확인
    results.append(("환경 변수", check_env_vars()))

    # 2. Supabase 연결 테스트
    results.append(("Supabase 연결", test_supabase_connection()))

    # 3. 데이터 검색 테스트
    results.append(("데이터 검색", test_data_retrieval()))

    # 4. Anthropic API 테스트
    results.append(("Anthropic API", test_anthropic_api()))

    # 결과 요약
    print("=" * 70)
    print("📋 테스트 결과 요약")
    print("=" * 70)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:20s} : {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 모든 테스트 통과! 챗봇이 정상 작동할 준비가 되었습니다.")
        print("\n다음 단계:")
        print("1. npm run dev로 Next.js 서버 시작")
        print("2. http://localhost:3000에서 챗봇 테스트")
        print("3. 또는 node test_chatbot.js로 API 직접 테스트")
    else:
        print("⚠️  일부 테스트 실패. 위의 오류 메시지를 확인하세요.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
