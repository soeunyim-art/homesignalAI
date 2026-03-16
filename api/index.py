"""
Vercel Serverless Function Entry Point for FastAPI

This file serves as the entry point for Vercel's Python runtime.
It imports the FastAPI app from src/main.py and exports it for Vercel.

Official Vercel FastAPI guide:
https://vercel.com/docs/frameworks/fastapi
"""
import os
import sys
from pathlib import Path

# Add project root to Python path (CRITICAL for imports)
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# 환경변수 기본값 설정 (MUST be set BEFORE importing app)
# This prevents ValidationError during Settings initialization
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://placeholder.supabase.co"
if not os.getenv("SUPABASE_KEY"):
    os.environ["SUPABASE_KEY"] = "placeholder-key"
if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "placeholder-service-key"
if not os.getenv("APP_ENV"):
    os.environ["APP_ENV"] = "production"

# Debug logging for Vercel deployment
print("[Vercel] Initializing HomeSignal AI FastAPI app...")
print(f"[Vercel] Python version: {sys.version}")
print(f"[Vercel] Environment check:")
print(f"  - SUPABASE_URL: {'✓' if os.getenv('SUPABASE_URL') else '✗'}")
print(f"  - SUPABASE_KEY: {'✓' if os.getenv('SUPABASE_KEY') else '✗'}")
print(f"  - APP_ENV: {os.getenv('APP_ENV', 'not set')}")

try:
    # Import the FastAPI app instance from src.main
    # This MUST succeed for Vercel to recognize the entrypoint
    from src.main import app

    print("[Vercel] ✓ FastAPI app loaded successfully from src.main")
    print(f"[Vercel] ✓ App title: {app.title}")

except Exception as e:
    print(f"[Vercel] ✗ CRITICAL ERROR: Failed to load app from src.main")
    print(f"[Vercel] ✗ Error: {e}")
    import traceback
    traceback.print_exc()

    # Fallback: Create minimal emergency app
    print("[Vercel] Creating fallback emergency app...")
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(
        title="HomeSignal AI (Emergency Fallback)",
        description="App failed to load - check logs"
    )

    @app.get("/")
    @app.get("/health")
    async def emergency_health():
        """Emergency health check when main app fails to load"""
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Application failed to initialize - check Vercel logs",
                "error": str(e),
                "troubleshooting": {
                    "check_env_vars": "Verify SUPABASE_URL, SUPABASE_KEY in Vercel dashboard",
                    "check_dependencies": "Ensure all requirements.txt packages installed",
                    "check_logs": "View detailed logs in Vercel deployment panel"
                },
                "env_check": {
                    "SUPABASE_URL": "✓" if os.getenv("SUPABASE_URL") else "✗ MISSING",
                    "SUPABASE_KEY": "✓" if os.getenv("SUPABASE_KEY") else "✗ MISSING",
                    "APP_ENV": os.getenv("APP_ENV", "NOT SET"),
                }
            }
        )

    print("[Vercel] ✓ Fallback app created")

# This is the CRITICAL line for Vercel to find the app
# The module MUST have 'app' as a top-level variable
print(f"[Vercel] Exporting app object: {type(app)}")
print(f"[Vercel] App is callable: {callable(app)}")

# Explicit export for Python's import system
__all__ = ["app"]
