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
# Step 1: Run Database Migrations (Optional)
# ==========================================
echo "🔄 Running database migrations..."

# Try to run migrations, but don't fail if it doesn't work
# This allows the app to start even if migrations fail
if command -v alembic &> /dev/null; then
    if alembic upgrade head 2>&1; then
        echo "✅ Migrations applied successfully"
    else
        echo "⚠️  WARNING: Migration failed, but continuing startup"
        echo "   The application will attempt to connect to the database."
        echo "   If tables don't exist, API calls will fail."
    fi
else
    echo "⚠️  WARNING: alembic not found, skipping migrations"
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
