"""
Pydantic schemas for user settings and profile management.
Defines request/response models for profile updates, password changes, etc.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileUpdate(BaseModel):
    """
    Schema for updating user profile information.

    Used for PUT /api/users/profile endpoint.

    Fields can be omitted if not being updated.

    Example:
        {
            "full_name": "John Smith",
            "email": "john.smith@example.com"
        }
    """

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Smith",
                "email": "john.smith@example.com",
            }
        }
    )


class PasswordChangeRequest(BaseModel):
    """
    Schema for changing user password.

    Used for PUT /api/users/password endpoint.

    Requires old password for verification before changing to new password.

    Example:
        {
            "old_password": "currentpass123",
            "new_password": "newsecurepass456"
        }
    """

    old_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(
        ..., min_length=8, description="New password (minimum 8 characters)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "currentpass123",
                "new_password": "newsecurepass456",
            }
        }
    )


class PasswordChangeResponse(BaseModel):
    """
    Response schema for successful password change.

    Example:
        {
            "message": "Password updated successfully"
        }
    """

    message: str = "Password updated successfully"

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Password updated successfully"}}
    )


class AccountDeleteRequest(BaseModel):
    """
    Schema for account deletion request.

    Requires password confirmation for security.

    Example:
        {
            "password": "mypassword123",
            "confirmation": "DELETE"
        }
    """

    password: str = Field(..., description="Current password for verification")
    confirmation: str = Field(
        ...,
        description="Must be exactly 'DELETE' (case-sensitive) to confirm deletion",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"password": "mypassword123", "confirmation": "DELETE"}}
    )


class AccountDeleteResponse(BaseModel):
    """
    Response schema for successful account deletion.

    Example:
        {
            "message": "Account deleted successfully"
        }
    """

    message: str = "Account deleted successfully"

    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Account deleted successfully"}}
    )
