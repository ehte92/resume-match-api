"""
User service with business logic for profile and settings management.
Handles user profile updates, password changes, and account deletion.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.settings import UserProfileUpdate
from app.utils.security import hash_password, verify_password


def get_user_profile(db: Session, user_id: UUID) -> Optional[User]:
    """
    Get user profile by ID.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        User: User object if found, None otherwise

    Example:
        >>> user = get_user_profile(db, user.id)
    """
    return db.query(User).filter(User.id == user_id).first()


def update_user_profile(
    db: Session, user_id: UUID, profile_data: UserProfileUpdate
) -> User:
    """
    Update user profile information.

    Args:
        db: Database session
        user_id: User's UUID
        profile_data: Profile update data (full_name, email)

    Returns:
        User: Updated user object

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if email already in use by another user

    Example:
        >>> updated_user = update_user_profile(
        ...     db,
        ...     user.id,
        ...     UserProfileUpdate(full_name="John Smith", email="john@new.com")
        ... )
    """
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update full_name if provided
    if profile_data.full_name is not None:
        user.full_name = profile_data.full_name

    # Update email if provided
    if profile_data.email is not None:
        # Check if new email is different from current email
        if profile_data.email != user.email:
            # Check if email already exists
            existing_user = (
                db.query(User).filter(User.email == profile_data.email).first()
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            user.email = profile_data.email

    # Save changes
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}",
        )


def change_password(
    db: Session, user_id: UUID, old_password: str, new_password: str
) -> User:
    """
    Change user password after verifying old password.

    Args:
        db: Database session
        user_id: User's UUID
        old_password: Current password for verification
        new_password: New password to set

    Returns:
        User: Updated user object

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if old password is incorrect
        HTTPException: 400 if new password same as old password

    Example:
        >>> user = change_password(db, user.id, "oldpass123", "newpass456")
    """
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify old password
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password"
        )

    # Check if new password is same as old password
    if verify_password(new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Hash and update password
    user.password_hash = hash_password(new_password)

    # Save changes
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}",
        )


def delete_user_account(db: Session, user_id: UUID, password: str) -> bool:
    """
    Delete user account after password verification.

    This performs a hard delete, removing the user and all associated data
    (resumes, analyses) due to cascade delete relationships.

    Args:
        db: Database session
        user_id: User's UUID
        password: Current password for verification

    Returns:
        bool: True if deletion successful

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if password is incorrect

    Example:
        >>> success = delete_user_account(db, user.id, "mypassword123")
    """
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify password
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password. Account deletion requires password verification.",
        )

    # Delete user (cascade will delete resumes and analyses)
    try:
        db.delete(user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}",
        )
