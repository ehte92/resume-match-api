"""
Health check endpoints for system monitoring.
Provides basic server health and database connectivity checks.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_db

router = APIRouter()


@router.get(
    "/health",
    summary="Basic health check",
    response_description="Server is healthy",
    tags=["health"],
)
def health_check() -> Any:
    """
    Basic health check endpoint.

    Returns a simple status message indicating the server is running.

    Always returns 200 OK if server is responsive.

    Returns:
        dict: {"status": "healthy"}
    """
    return {"status": "healthy"}


@router.get(
    "/health/db",
    summary="Database health check",
    response_description="Database connection healthy",
    tags=["health"],
)
def health_check_db(db: Session = Depends(get_db)) -> Any:
    """
    Database connectivity health check.

    Executes a simple query to verify database connection.

    Returns:
        dict: {"status": "healthy", "database": "connected"}

    Raises:
        503: Service Unavailable if database connection fails
    """
    try:
        # Execute simple query to check database connectivity
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}",
        )
