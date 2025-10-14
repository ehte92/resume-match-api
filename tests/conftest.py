"""
Pytest configuration and shared fixtures for testing.

This module provides test fixtures for database setup, test client,
and authentication helpers used across all test files.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, SessionLocal
from app.models.user import User
from app.utils.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """
    Clean up test users from database before test session starts.

    This fixture runs once before all tests to ensure a clean state.
    It removes any users with email addresses ending in 'example.com'.
    """
    db = SessionLocal()
    try:
        # Delete all test users from previous runs
        test_users = db.query(User).filter(User.email.like("%example.com%")).all()
        for user in test_users:
            db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """
    Provide clean database session for each test.

    This fixture creates a new database session for each test.
    The session is used within a transaction context that gets
    rolled back after the test, ensuring test isolation.

    Yields:
        Session: A SQLAlchemy database session
    """
    session = SessionLocal()

    yield session

    # Clean up test users after each test
    try:
        test_users = session.query(User).filter(User.email.like("%example.com%")).all()
        for user in test_users:
            session.delete(user)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Provide test client with overridden database dependency.

    This fixture creates a FastAPI TestClient with the get_db
    dependency overridden to use the test database session.

    Args:
        db_session: The test database session fixture

    Yields:
        TestClient: A FastAPI test client
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """
    Create a test user with known credentials.

    This fixture creates a user that can be used for authentication
    testing. The credentials are:
    - email: test@example.com
    - password: testpassword123

    Args:
        db_session: The test database session fixture

    Returns:
        User: The created test user object
    """
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """
    Get authentication headers for test user.

    This fixture logs in as the test user and returns the
    authorization headers needed for authenticated requests.

    Args:
        client: The test client fixture
        test_user: The test user fixture

    Returns:
        dict: Authorization headers with Bearer token
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
