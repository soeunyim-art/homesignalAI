#!/bin/bash

# Vercel 환경변수 설정 스크립트
# 사용법: ./scripts/setup_vercel_env.sh

set -e

echo "🚀 Vercel 환경변수 설정을 시작합니다..."
echo ""

# 필수 환경변수 목록
ENV_VARS=(
    "SUPABASE_URL"
    "SUPABASE_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
    "OPENAI_API_KEY"
    "APP_ENV"
    "DEBUG"
)

# 선택 환경변수
OPTIONAL_ENV_VARS=(
    "ANTHROPIC_API_KEY"
    "AI_PROVIDER"
    "REDIS_URL"
    "ALLOWED_ORIGINS"
)

echo "📝 필수 환경변수 설정"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for var in "${ENV_VARS[@]}"; do
    echo ""
    echo "🔹 $var 설정"

    # 기본값 제공
    case $var in
        "APP_ENV")
            default="production"
            ;;
        "DEBUG")
            default="false"
            ;;
        *)
            default=""
            ;;
    esac

    if [ -n "$default" ]; then
        echo "   (기본값: $default)"
        read -p "   값을 입력하세요 [Enter = 기본값 사용]: " value
        value=${value:-$default}
    else
        read -p "   값을 입력하세요: " value
    fi

    if [ -n "$value" ]; then
        echo "   ✅ Vercel에 설정 중..."
        vercel env add "$var" production <<< "$value"
        echo "   ✅ 완료"
    else
        echo "   ⚠️  값이 비어있습니다. 나중에 설정하세요."
    fi
done

echo ""
echo "📝 선택 환경변수 설정 (Enter로 건너뛰기)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for var in "${OPTIONAL_ENV_VARS[@]}"; do
    echo ""
    echo "🔹 $var (선택사항)"
    read -p "   값을 입력하세요 [Enter = 건너뛰기]: " value

    if [ -n "$value" ]; then
        echo "   ✅ Vercel에 설정 중..."
        vercel env add "$var" production <<< "$value"
        echo "   ✅ 완료"
    else
        echo "   ⏭️  건너뛰기"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 환경변수 설정 완료!"
echo ""
echo "📋 설정된 환경변수 목록:"
vercel env ls

echo ""
echo "🚀 다음 단계:"
echo "   1. vercel --prod (프로덕션 배포)"
echo "   2. curl https://your-backend.vercel.app/health (검증)"
echo ""
