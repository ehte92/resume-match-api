"""
Pydantic schemas for resume validation and serialization.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    """Base schema for resume with common fields."""

    file_name: str = Field(..., description="Original filename", max_length=255)
    file_type: str = Field(..., description="File type (pdf or docx)", max_length=10)
    file_size: int = Field(..., description="File size in bytes", gt=0)


class ResumeUpload(ResumeBase):
    """
    Schema for resume upload request.
    Used when creating a new resume.
    """

    pass


class ResumeUpdate(BaseModel):
    """
    Schema for updating resume parsed data.
    Used after parsing to update text and structured data.
    """

    parsed_text: Optional[str] = Field(None, description="Raw text extracted from file")
    parsed_data: Optional[Dict[str, Any]] = Field(
        None, description="Structured data (sections, contact info, etc.)"
    )


class ResumeResponse(ResumeBase):
    """
    Schema for resume response.
    Returned when fetching resume data.
    """

    id: UUID = Field(..., description="Resume UUID")
    user_id: UUID = Field(..., description="User UUID who owns this resume")
    file_path: str = Field(..., description="Storage path or URL")
    parsed_text: Optional[str] = Field(None, description="Raw text extracted from file")
    parsed_data: Optional[Dict[str, Any]] = Field(
        None, description="Structured data (sections, contact info, etc.)"
    )
    storage_backend: str = Field(..., description="Storage backend (local or r2)")
    download_url: Optional[str] = Field(
        None,  # noqa: E501
        description="Presigned download URL (null for local storage, 1-hour expiration for R2)",
    )
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ResumeInDB(ResumeResponse):
    """
    Schema for resume as stored in database.
    Includes all fields from the database model.
    """

    pass


class ResumeListResponse(BaseModel):
    """
    Schema for paginated list of resumes.
    """

    resumes: list[ResumeResponse] = Field(..., description="List of resumes")
    total: int = Field(..., description="Total number of resumes")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

    model_config = ConfigDict(from_attributes=True)
