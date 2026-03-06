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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(HomeSignalError)
async def homesignal_exception_handler(request: Request, exc: HomeSignalError):
    """HomeSignal 커스텀 예외 핸들러"""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "details": exc.details,
        },
    )


# 라우터 등록
app.include_router(forecast_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
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
