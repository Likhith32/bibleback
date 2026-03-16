"""
Bible Study Workspace — FastAPI application entry point.
"""
from dotenv import load_dotenv
load_dotenv()  # MUST run before any app imports that read env vars

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logger import setup_logger
from app.routes import search, verse, ai, daily, export, suggestions
import uvicorn

# ── Initialize logger FIRST ────────────────────────────────────
setup_logger()
logger = logging.getLogger(__name__)

# ── App ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Galilee Workspace API",
    version="2.0.0",
    description="AI-powered Bible study backend with smart search, sermons, cross-references, and more.",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "https://biblefront.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ──────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info("📥 Request: %s %s", request.method, request.url)

    response = await call_next(request)

    duration_ms = (time.time() - start) * 1000
    logger.info(
        "📤 Response: %s %s → %s  (%.0f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Startup / Shutdown events ──────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Galilee Workspace API starting...")
    logger.info("🔎 Checking database connection...")

    from app.database.db import db_pool
    if db_pool:
        logger.info("✅ Database pool is ready")
    else:
        logger.warning("⚠️  Database pool is NOT available — check DATABASE_URL")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Galilee Workspace API shutting down...")

    from app.database.db import db_pool
    if db_pool:
        db_pool.closeall()
        logger.info("🔒 Database connections closed")


# ── Routes ──────────────────────────────────────────────────────
app.include_router(search.router,      tags=["Search"])
app.include_router(verse.router,       tags=["Verse"])
app.include_router(ai.router,          tags=["AI Features"])
app.include_router(daily.router,       tags=["Daily"])
app.include_router(export.router,      tags=["Export"])
app.include_router(suggestions.router, tags=["Suggestions"])


@app.get("/")
async def root():
    return {"message": "Galilee Workspace API is running", "version": "2.0.0"}


@app.get("/health")
async def health():
    from app.database.db import db_pool
    db_ok = db_pool is not None
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
