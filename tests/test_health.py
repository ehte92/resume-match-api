"""
Tests for health check endpoints.

This module tests the basic health check endpoint and the database
health check endpoint to ensure the API is operational.
"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test basic health endpoint.

    Verifies that the /health endpoint returns a 200 status
    and the expected healthy status message.

    Args:
        client: The test client fixture
    """
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_db(client: TestClient):
    """
    Test database health check endpoint.

    Verifies that the /health/db endpoint returns a 200 status
    and confirms the database connection is working.

    Args:
        client: The test client fixture
    """
    response = client.get("/health/db")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
