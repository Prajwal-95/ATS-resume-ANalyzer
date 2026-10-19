# ── Root Dockerfile for Antideploy single-origin deployment ──────────────────
# Multi-stage build: Node builds the React frontend, Python serves it via FastAPI.
# Antideploy detects and uses this Dockerfile because it lives at the repository
# root. The existing backend/Dockerfile and frontend/Dockerfile remain untouched
# for local docker-compose use.

# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build production assets
# VITE_API_URL is intentionally NOT set — produces a same-origin build where
# all API requests are relative (e.g., /auth/login instead of
# http://localhost:8000/auth/login).
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend + serve frontend ─────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

ENV FRONTEND_BUILD_DIR=/app/frontend/dist
# Install system dependencies (build-essential for PyMuPDF and other C extensions)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model at build time so it's baked into the image
# (the app gracefully falls back if this fails)
RUN python -m spacy download en_core_web_sm || true

# Copy backend application code
COPY backend/ .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create upload and report directories with proper permissions
RUN mkdir -p uploads reports && \
    chown -R 1000:1000 uploads reports frontend/dist

# Switch to non-root user
USER 1000:1000

# Expose port (Antideploy injects PORT at runtime)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/healthz')" || exit 1

# Run migrations then start uvicorn on the port Antideploy provides.
# ${PORT:-8000} falls back to 8000 for local development.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]