"""
User database model for SQLAlchemy ORM.
Defines the users table schema with UUID primary key.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """
    User model representing application users.

    Fields:
        id: UUID primary key, auto-generated
        email: User's email address (unique, indexed)
        password_hash: Bcrypt hashed password
        full_name: User's full name (optional)
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated

    Example:
        >>> user = User(
        ...     email="john@example.com",
        ...     password_hash="$2b$12$...",
        ...     full_name="John Doe"
        ... )
    """

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("ResumeAnalysis", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of User for debugging."""
        return f"<User {self.email}>"
