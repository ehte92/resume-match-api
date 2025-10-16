# ==========================================
# Multi-stage Dockerfile for FastAPI Backend
# ==========================================
# Stage 1: Builder - Install dependencies and download models
# Stage 2: Runtime - Minimal production image
#
# Features:
# - Python 3.11 slim (Debian-based)
# - Non-root user for security
# - Multi-stage build for smaller image (~400MB)
# - spaCy en_core_web_sm model pre-downloaded
# - Health check integration
# - Production-ready with gunicorn

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install system dependencies required for Python packages
# - gcc, g++: Compilation for psycopg2, bcrypt, etc.
# - libpq-dev: PostgreSQL client library
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies into /build/venv
RUN python -m venv /build/venv && \
    /build/venv/bin/pip install --upgrade pip && \
    /build/venv/bin/pip install --no-cache-dir -r requirements.txt

# Download spaCy English model (en_core_web_sm)
# This is required for NER in keyword_analyzer.py
RUN /build/venv/bin/python -m spacy download en_core_web_sm

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH" \
    ENVIRONMENT=production

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /build/venv /venv

# Copy application code
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY scripts/docker-entrypoint.sh /app/docker-entrypoint.sh

# Make entrypoint script and venv binaries executable
RUN chmod +x /app/docker-entrypoint.sh && \
    chmod +x /venv/bin/* 2>/dev/null || true

# Change ownership to non-root user
RUN chown -R appuser:appuser /app /venv

# Switch to non-root user
USER appuser

# Expose port 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
# Entrypoint will run migrations first, then start the server
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
