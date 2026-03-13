"""
Vercel Serverless Function Entry Point

This file serves as the entry point for Vercel's Python runtime.
It imports the FastAPI app from src.main and exposes it as 'app'.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
# This allows 'from src.main import app' to work correctly
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Import FastAPI app from src.main
from src.main import app

# Export app for Vercel
# Vercel expects the ASGI app to be named 'app'
__all__ = ["app"]
