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

# Use python -m instead of alembic binary to avoid execution issues
if python -m alembic upgrade head 2>&1; then
    echo "✅ Migrations applied successfully"
else
    echo "⚠️  WARNING: Migration failed, but continuing startup"
    echo "   The application will attempt to connect to the database."
    echo "   If tables don't exist, API calls will fail."
fi

echo ""

# ==========================================
# Step 2: Start Application
# ==========================================
echo "🚀 Starting application..."
echo "Command: $@"
echo "========================================"
echo ""

# Execute the main command
# Use python -m for gunicorn to avoid binary execution issues
if [ "$1" = "gunicorn" ]; then
    shift  # Remove 'gunicorn' from arguments
    exec python -m gunicorn "$@"
else
    exec "$@"
fi
