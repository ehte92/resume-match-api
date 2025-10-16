#!/bin/bash
# ==========================================
# Docker Entrypoint Script
# ==========================================
# This script runs before the main application starts
#
# Responsibilities:
# 1. Wait for PostgreSQL database to be ready
# 2. Run Alembic database migrations
# 3. Start the application with provided command
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
# Step 1: Wait for Database to be Ready
# ==========================================
echo "🔍 Checking database connection..."

# Extract database host from DATABASE_URL
# Format: postgresql://user:pass@host:port/dbname
DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:]+).*/\1/')
DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+)\/.*/\1/')

# Default to 5432 if port not found in URL
if [ -z "$DB_PORT" ] || [ "$DB_PORT" = "$DATABASE_URL" ]; then
    DB_PORT=5432
fi

echo "Database host: $DB_HOST:$DB_PORT"

# Wait for PostgreSQL to accept connections
MAX_RETRIES=30
RETRY_COUNT=0
RETRY_INTERVAL=2

until PGPASSWORD=$PGPASSWORD psql -h "$DB_HOST" -U "postgres" -p "$DB_PORT" -c '\q' 2>/dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "⏳ Waiting for database... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ ERROR: Could not connect to database after $MAX_RETRIES attempts"
    echo "   Please check:"
    echo "   - DATABASE_URL is correct"
    echo "   - Database server is running"
    echo "   - Network connectivity"
    exit 1
fi

echo "✅ Database is ready!"
echo ""

# ==========================================
# Step 2: Run Database Migrations
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
# Step 3: Start Application
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
