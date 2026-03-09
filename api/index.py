"""
Vercel Serverless Function Entry Point

This file serves as the entry point for Vercel's Python runtime.
It imports the FastAPI app from src.main and exposes it as 'app'.
"""

from src.main import app

# Vercel expects the ASGI app to be named 'app'
# This handler will be called by Vercel's Python runtime
