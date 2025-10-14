"""
Shared dependency functions for FastAPI routes.
Provides database sessions and user authentication.
"""

from typing import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.user import User

# Security scheme for JWT Bearer tokens
security = HTTPBearer()

# Get settings
settings = get_settings()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency function to get the current authenticated user.

    Extracts and validates JWT token from Authorization header,
    then retrieves the user from the database.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token
        token = credentials.credentials

        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Extract user ID from token
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Convert string UUID to UUID object
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Query user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency function to get the current active user.

    Ensures the authenticated user is active (not disabled).

    Args:
        current_user: The authenticated user from get_current_user

    Returns:
        User: The active user object

    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
