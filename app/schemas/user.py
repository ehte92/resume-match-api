"""
Pydantic schemas for User data validation.
Used for API request/response serialization and validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Schema for creating a new user (registration).

    Used for POST /api/auth/register endpoint.

    Example:
        {
            "email": "john@example.com",
            "password": "securepass123",
            "full_name": "John Doe"
        }
    """

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john@example.com",
                "password": "securepass123",
                "full_name": "John Doe",
            }
        }
    )


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.

    Never includes password or password_hash for security.

    Example:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "john@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "created_at": "2025-10-14T10:30:00Z"
        }
    """

    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  # Allows creation from ORM models
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2025-10-14T10:30:00Z",
            }
        },
    )


class UserInDB(UserResponse):
    """
    Schema for user data with password hash (internal use only).

    This schema should NEVER be returned by API endpoints.
    Only used internally for database operations.
    """

    password_hash: str

    model_config = ConfigDict(from_attributes=True)
