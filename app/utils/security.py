"""
Security utilities for password hashing and JWT token management.
Uses bcrypt for password hashing and python-jose for JWT tokens.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import get_settings

# Get settings
settings = get_settings()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Bcrypt hashed password

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> print(hashed)
        $2b$12$...
    """
    # Convert password to bytes and hash with bcrypt
    # Truncate to 72 bytes (bcrypt limit) to avoid errors
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password from database

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    # Convert both password and hash to bytes
    # Truncate to 72 bytes (bcrypt limit) to match hash_password behavior
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims (must include "sub" for user_id)
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token(data={"sub": "user-uuid-here"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: Dict[str, str]) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens are long-lived (7 days by default) and used to generate new access tokens.

    Args:
        data: Dictionary containing claims (must include "sub" for user_id)

    Returns:
        str: Encoded JWT refresh token with "type": "refresh" claim

    Example:
        >>> token = create_refresh_token(data={"sub": "user-uuid-here"})
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})  # Distinguish from access tokens

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, str]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: 401 if token is invalid or expired

    Example:
        >>> token = create_access_token(data={"sub": "user-uuid"})
        >>> payload = verify_token(token)
        >>> print(payload["sub"])
        user-uuid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
