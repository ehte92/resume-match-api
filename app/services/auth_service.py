"""
Authentication service with business logic for user management.
Handles user creation, authentication, and retrieval.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user in the database.

    Args:
        db: Database session
        user_data: User registration data

    Returns:
        User: Created user object

    Raises:
        HTTPException: 400 if email already exists

    Example:
        >>> user = create_user(db, UserCreate(
        ...     email="john@example.com",
        ...     password="securepass123",
        ...     full_name="John Doe"
        ... ))
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create new user instance
    db_user = User(
        email=user_data.email, password_hash=hashed_password, full_name=user_data.full_name
    )

    # Add to database
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}",
        )


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email
        password: Plain text password to verify

    Returns:
        User: User object if authentication successful, None otherwise

    Example:
        >>> user = authenticate_user(db, "john@example.com", "securepass123")
        >>> if user:
        ...     print(f"Authenticated: {user.email}")
        ... else:
        ...     print("Authentication failed")
    """
    # Get user by email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        return None

    # Check if user is active
    if not user.is_active:
        return None

    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User: User object if found, None otherwise

    Example:
        >>> user = get_user_by_email(db, "john@example.com")
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User's UUID

    Returns:
        User: User object if found, None otherwise

    Example:
        >>> from uuid import UUID
        >>> user = get_user_by_id(db, UUID("550e8400-e29b-41d4-a716-446655440000"))
    """
    return db.query(User).filter(User.id == user_id).first()
