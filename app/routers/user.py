"""
User profile and settings API endpoints.
Provides profile management, password changes, and account deletion.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.settings import (
    AccountDeleteRequest,
    AccountDeleteResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    UserProfileUpdate,
)
from app.schemas.user import UserResponse
from app.services import user_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get user profile",
    response_description="Current user's profile data",
)
@limiter.limit("100/minute")
def get_profile(request: Request, current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header:
    `Authorization: Bearer <access_token>`

    Returns complete user profile data.

    Raises:
        401: Invalid or missing token
        404: User not found
    """
    return current_user


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
    response_description="Updated user profile",
)
@limiter.limit("10/minute")
def update_profile(
    request: Request,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update current user's profile information.

    - **full_name**: Updated full name (optional)
    - **email**: Updated email address (optional, must be unique)

    At least one field must be provided for update.

    Returns updated user profile.

    Raises:
        400: Email already in use or no fields to update
        401: Invalid or missing token
        404: User not found
    """
    # Check if at least one field is being updated
    if profile_data.full_name is None and profile_data.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (full_name or email) must be provided for update",
        )

    updated_user = user_service.update_user_profile(db, current_user.id, profile_data)
    return updated_user


@router.put(
    "/password",
    response_model=PasswordChangeResponse,
    summary="Change password",
    response_description="Password successfully changed",
)
@limiter.limit("5/minute")
def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Change current user's password.

    - **old_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)

    New password must be different from current password.

    Returns success message.

    Raises:
        400: Incorrect current password or new password same as old
        401: Invalid or missing token
        404: User not found
    """
    user_service.change_password(
        db, current_user.id, password_data.old_password, password_data.new_password
    )

    return PasswordChangeResponse()


@router.delete(
    "/account",
    response_model=AccountDeleteResponse,
    summary="Delete user account",
    response_description="Account successfully deleted",
)
@limiter.limit("3/minute")
def delete_account(
    request: Request,
    delete_data: AccountDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete current user's account.

    This action is PERMANENT and cannot be undone.
    All user data including resumes and analyses will be deleted.

    - **password**: Current password for verification
    - **confirmation**: Must be exactly "DELETE" (case-sensitive)

    Returns success message.

    Raises:
        400: Incorrect password or invalid confirmation
        401: Invalid or missing token
        404: User not found
    """
    # Verify confirmation text
    if delete_data.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Confirmation must be exactly "DELETE" (case-sensitive)',
        )

    # Delete account (will verify password in service)
    user_service.delete_user_account(db, current_user.id, delete_data.password)

    return AccountDeleteResponse()
