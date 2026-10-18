"""
ATS Resume Score Checker - FastAPI Backend
Main application entry point.
"""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.database.connection import engine, Base
from app.api import auth, resume, analysis
from app.config import settings

# Register all models on Base.metadata so schema initialization
# (create_all) sees every table, including the analyses tables.
import app.models.models  # noqa: F401

logger = logging.getLogger("ats_resume_checker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("Starting up ATS Resume Score Checker API")

    # Initialize NLP model (Sentence Transformer)
    from app.nlp.semantic_matcher import initialize_model
    model_ok = initialize_model()
    if not model_ok:
        logger.warning("Sentence Transformer model not loaded; using TF-IDF fallback for semantic matching")

    # Verify database connectivity on startup and ensure all tables exist.
    # Alembic owns schema migrations in production (render.yaml runs
    # `alembic upgrade head` before start); create_all is idempotent and only
    # creates tables that are missing, so it is safe alongside alembic and
    # guarantees local/dev databases are usable without a manual migration step.
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connection verified and schema initialized")
    except Exception as e:
        logger.error(f"Database connection failed on startup: {e}")
        # Don't crash — readiness endpoint will report the issue

    yield

    logger.info("Shutting down ATS Resume Score Checker API")
    await engine.dispose()


app = FastAPI(
    title="ATS Resume Score Checker API",
    description="API for analyzing resumes against job descriptions and calculating ATS compatibility scores.",
    version="1.0.0",
    lifespan=lifespan,
)

# Request ID middleware for tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start_time = time.monotonic()
    response = await call_next(request)
    elapsed = (time.monotonic() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({elapsed:.1f}ms)")
    return response


from app.middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration — explicit origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])


@app.get("/healthz", tags=["Health"])
async def healthz():
    """Lightweight liveness probe. Does not check dependencies."""
    return {"status": "ok"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Full health check including database connectivity."""
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/readyz", tags=["Health"])
async def readyz():
    """Readiness probe — checks database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}, 503
