"""
Authentication API endpoints.
Provides user registration, login, token refresh, and profile access.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service
from app.utils.security import create_access_token, create_refresh_token, verify_token

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    response_description="User successfully created with authentication tokens",
)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register a new user account and return authentication tokens.

    - **email**: Valid email address (unique)
    - **password**: Password (minimum 8 characters)
    - **full_name**: User's full name (optional)

    Returns authentication tokens and user data (auto-login after registration).

    Raises:
        400: Email already registered
    """
    user = auth_service.create_user(db, user_data)

    # Create tokens for auto-login
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Return tokens and user data
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access token",
    response_description="Authentication successful",
)
@limiter.limit("5/minute")
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns:
        - access_token: Short-lived JWT (15 minutes)
        - refresh_token: Long-lived JWT (7 days)
        - user: User profile data

    Raises:
        401: Invalid email or password
    """
    # Authenticate user
    user = auth_service.authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Return tokens and user data
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    response_description="New tokens generated",
)
@limiter.limit("10/minute")
def refresh_token(
    request: Request, token_request: RefreshTokenRequest, db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token from login

    Returns new access and refresh tokens.

    Raises:
        401: Invalid or expired refresh token
    """
    # Verify refresh token
    payload = verify_token(token_request.refresh_token)

    # Check token type
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = auth_service.get_user_by_id(db, UUID(user_id_str))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    response_description="Current user data",
)
@limiter.limit("100/minute")
def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header:
    `Authorization: Bearer <access_token>`

    Returns current user data.

    Raises:
        401: Invalid or missing token
        403: Token valid but user not found
    """
    return current_user
