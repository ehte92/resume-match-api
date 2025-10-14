"""
Tests for authentication endpoints.

This module tests all authentication-related endpoints including
user registration, login, token refresh, and protected routes.
"""

import pytest
from fastapi.testclient import TestClient
from app.models.user import User


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_user(self, client: TestClient):
        """
        Test successful user registration.

        Verifies that a new user can be registered with valid data
        and that sensitive information is not returned.
        """
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify user data is returned
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True

        # Verify sensitive data is NOT returned
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """
        Test registration with existing email fails.

        Verifies that attempting to register with an already
        registered email returns a 400 error.
        """
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "anotherpassword123",
                "full_name": "Another User",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """
        Test registration with invalid email format fails.

        Verifies that Pydantic email validation rejects
        invalid email formats.
        """
        response = client.post(
            "/api/auth/register",
            json={
                "email": "notanemail",
                "password": "password123",
                "full_name": "Test User",
            },
        )

        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client: TestClient, test_user: User):
        """
        Test successful login with correct credentials.

        Verifies that valid credentials return JWT tokens
        and user information.
        """
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        # Verify user data is returned
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """
        Test login with wrong password fails.

        Verifies that incorrect passwords are rejected with a 401 error.
        """
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """
        Test login with non-existent email fails.

        Verifies that attempting to login with an email that
        doesn't exist returns a 401 error.
        """
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "somepassword123"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


class TestProtectedEndpoints:
    """Tests for protected endpoints requiring authentication."""

    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """
        Test getting current user info with valid token.

        Verifies that the /me endpoint returns user information
        when provided with a valid authentication token.
        """
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify user data is returned
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data

        # Verify sensitive data is NOT returned
        assert "password" not in data
        assert "password_hash" not in data

    def test_get_current_user_no_auth(self, client: TestClient):
        """
        Test getting current user without authentication fails.

        Verifies that accessing the /me endpoint without
        an Authorization header returns a 403 error.
        """
        response = client.get("/api/auth/me")

        assert response.status_code == 403

    def test_get_current_user_invalid_token(self, client: TestClient):
        """
        Test getting current user with invalid token fails.

        Verifies that an invalid authentication token
        is rejected with a 401 error.
        """
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """
        Test successful token refresh.

        Verifies that a valid refresh token can be used to
        obtain new access and refresh tokens.
        """
        # First, login to get a refresh token
        login_response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new tokens
        response = client.post(
            "/api/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify new tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        # Verify new tokens are different from original
        assert data["access_token"] != login_response.json()["access_token"]
        assert data["refresh_token"] != refresh_token

    def test_refresh_token_invalid(self, client: TestClient):
        """
        Test token refresh with invalid token fails.

        Verifies that attempting to refresh with an invalid
        or malformed token returns a 401 error.
        """
        response = client.post(
            "/api/auth/refresh", json={"refresh_token": "invalid_token_here"}
        )

        assert response.status_code == 401

    def test_refresh_token_with_access_token(self, client: TestClient, test_user: User):
        """
        Test that access token cannot be used for refresh.

        Verifies that using an access token instead of a refresh token
        for the refresh endpoint is rejected.
        """
        # Login to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Try to use access token for refresh (should fail)
        response = client.post(
            "/api/auth/refresh", json={"refresh_token": access_token}
        )

        assert response.status_code == 401
