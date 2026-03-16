"""
HomeSignal AI - 동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스

실행 방법:
    uv run uvicorn src.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.chat import router as chat_router
from src.config import settings
from src.forecast import router as forecast_router
from src.ingest import router as ingest_router
from src.news import router as news_router
from src.shared.exceptions import HomeSignalError

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 로직"""
    logger.info(f"HomeSignal AI 시작 (환경: {settings.app_env})")
    
    # 설정 검증 결과 로그 루틴
    if "placeholder" in settings.supabase_url:
        logger.warning("WARNING: Supabase URL is still using placeholder. Check Vercel environment variables.")
    if settings.supabase_key == "placeholder-key":
        logger.warning("WARNING: Supabase Key is still using placeholder. Check Vercel environment variables.")
        
    yield
    logger.info("HomeSignal AI 종료")


app = FastAPI(
    title="HomeSignal AI",
    description="동대문구 부동산 시계열 예측 및 RAG 챗봇 서비스 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS 설정
# debug 모드: 모든 오리진 허용
# production 모드: ALLOWED_ORIGINS 환경변수로 지정된 도메인만 허용
cors_origins = ["*"] if settings.debug else settings.allowed_origins

if not settings.debug and not cors_origins:
    logger.warning(
        "프로덕션 환경에서 ALLOWED_ORIGINS가 설정되지 않았습니다. "
        "프론트엔드에서 API 호출이 차단될 수 있습니다."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(HomeSignalError)
async def homesignal_exception_handler(request: Request, exc: HomeSignalError):
    """HomeSignal 커스텀 예외 핸들러
    
    표준 에러 응답 포맷:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "사용자용 메시지",
            "details": {}
        }
    }
    
    참조: docs/07_API_Contract_Rules.md
    """
    from src.shared.exceptions import (
        AIAPIError,
        DatabaseError,
        NotFoundError,
        ValidationError,
    )

    # 예외 타입별 HTTP 상태 코드 및 에러 코드 매핑
    status_code = 500
    error_code = "INTERNAL_SERVER_ERROR"

    if isinstance(exc, ValidationError):
        status_code = 400
        error_code = "VALIDATION_ERROR"
    elif isinstance(exc, NotFoundError):
        status_code = 404
        error_code = "NOT_FOUND"
    elif isinstance(exc, DatabaseError):
        status_code = 500
        error_code = "DATABASE_ERROR"
    elif isinstance(exc, AIAPIError):
        status_code = 500
        error_code = "AI_API_ERROR"

    # 에러 메시지에서 특정 코드 추출 (선택)
    if "forecast" in exc.message.lower() and "not found" in exc.message.lower():
        error_code = "FORECAST_NOT_FOUND"
    elif "region" in exc.message.lower() and "지원" in exc.message.lower():
        error_code = "REGION_NOT_SUPPORTED"
    elif "rate limit" in exc.message.lower():
        error_code = "RATE_LIMIT_EXCEEDED"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러 (예상치 못한 오류)"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "내부 서버 오류가 발생했습니다.",
                "details": {"error": str(exc)} if settings.debug else {},
            }
        },
    )


# 라우터 등록
app.include_router(forecast_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    """헬스체크 엔드포인트 - 설정 유효성 포함"""
    config_ok = "placeholder" not in settings.supabase_url and settings.supabase_key != "placeholder-key"
    
    return {
        "status": "healthy" if config_ok else "degraded",
        "configuration": "OK" if config_ok else "Missing Supabase Credentials",
        "environment": settings.app_env,
        "version": "0.1.0",
    }


@app.get("/", tags=["root"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "HomeSignal AI API",
        "docs": "/docs" if settings.debug else "Disabled in production",
        "endpoints": {
            "forecast": "/api/v1/forecast",
            "chat": "/api/v1/chat",
            "news": "/api/v1/news/insights",
            "ingest_houses": "/api/v1/ingest/houses",
            "ingest_news": "/api/v1/ingest/news",
            "health": "/health",
        },
    }
