"""
Pydantic schemas for authentication endpoints.
Defines request/response models for login, token refresh, etc.
"""

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.user import UserResponse


class Token(BaseModel):
    """
    Basic JWT token response.

    Used for simple token-only responses.
    """

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class TokenResponse(BaseModel):
    """
    Complete authentication response with tokens and user data.

    Returned by login endpoint after successful authentication.

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "created_at": "2025-10-14T10:30:00Z"
            }
        }
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """
    Request schema for token refresh endpoint.

    Example:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """

    refresh_token: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}}
    )


class LoginRequest(BaseModel):
    """
    Request schema for login endpoint.

    Example:
        {
            "email": "john@example.com",
            "password": "securepass123"
        }
    """

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "john@example.com", "password": "securepass123"}}
    )
