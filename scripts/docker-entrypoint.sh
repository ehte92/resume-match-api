#!/bin/bash
# ==========================================
# Docker Entrypoint Script
# ==========================================
# This script runs before the main application starts
#
# Responsibilities:
# 1. Run Alembic database migrations
# 2. Start the application with provided command
#
# Note: Database connectivity is handled by SQLAlchemy.
# If database is unavailable, migrations will fail with clear error.
#
# Usage: Called automatically by Dockerfile ENTRYPOINT

set -e  # Exit on error

echo "========================================"
echo "AI Resume Optimizer - Starting Backend"
echo "========================================"
echo "Environment: ${ENVIRONMENT:-development}"
echo "Python version: $(python --version)"
echo ""

# ==========================================
# Step 1: Run Database Migrations
# ==========================================
echo "🔄 Running database migrations..."

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "❌ ERROR: alembic not found in PATH"
    exit 1
fi

# Run migrations with error handling
if alembic upgrade head; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ ERROR: Migration failed"
    echo "   This may happen if:"
    echo "   - Database schema is corrupted"
    echo "   - Migration scripts have errors"
    echo "   - Database permissions are insufficient"
    exit 1
fi

echo ""

# ==========================================
# Step 2: Start Application
# ==========================================
echo "🚀 Starting application..."
echo "Command: $@"
echo "========================================"
echo ""

# Execute the main command (passed as arguments to this script)
# This will be either:
# - Development: uvicorn with --reload
# - Production: gunicorn with multiple workers
exec "$@"
