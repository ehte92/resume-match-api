"""
Pydantic schemas for cover letter template management.
Defines request/response models for template endpoints.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoverLetterTemplateCreate(BaseModel):
    """Request schema for creating a new cover letter template."""

    name: str = Field(..., min_length=1, max_length=255, description="Template display name")
    description: Optional[str] = Field(None, description="What this template is for")
    category: str = Field(
        ..., min_length=1, max_length=50, description="Template category (e.g., 'Software Engineering')"
    )
    tone: Literal["professional", "enthusiastic", "balanced"] = Field(
        default="professional", description="Writing tone for the template"
    )
    length: Literal["short", "medium", "long"] = Field(
        default="medium",
        description="Target length: short (~250 words), medium (~350 words), long (~500 words)",
    )
    template_text: str = Field(
        ...,
        min_length=100,
        description="The cover letter template with {{placeholders}} like {{job_title}}, {{company_name}}, etc.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Software Engineering - Professional",
                "description": "Perfect for senior software engineering roles",
                "category": "Software Engineering",
                "tone": "professional",
                "length": "medium",
                "template_text": "Dear Hiring Manager at {{company_name}},\n\nI am writing to express my interest in the {{job_title}} position...",
            }
        }
    )


class CoverLetterTemplateUpdate(BaseModel):
    """Request schema for updating an existing template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template display name")
    description: Optional[str] = Field(None, description="What this template is for")
    category: Optional[str] = Field(
        None, min_length=1, max_length=50, description="Template category"
    )
    tone: Optional[Literal["professional", "enthusiastic", "balanced"]] = Field(
        None, description="Writing tone for the template"
    )
    length: Optional[Literal["short", "medium", "long"]] = Field(
        None, description="Target length"
    )
    template_text: Optional[str] = Field(
        None, min_length=100, description="The cover letter template text"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Software Engineering - Professional (Updated)",
                "description": "Updated description",
                "template_text": "Dear Hiring Manager at {{company_name}},\n\nI am excited to apply for the {{job_title}} position...",
            }
        }
    )


class CoverLetterTemplateResponse(BaseModel):
    """Response schema for a single cover letter template."""

    id: UUID
    name: str
    description: Optional[str]
    category: str
    tone: str
    length: str
    template_text: str
    is_system: bool
    user_id: Optional[UUID]
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CoverLetterTemplateListResponse(BaseModel):
    """Paginated list of cover letter templates."""

    templates: list[CoverLetterTemplateResponse]
    total: int
    page: int
    page_size: int


class CoverLetterGenerateFromTemplateRequest(BaseModel):
    """Request schema for generating a cover letter from a template."""

    template_id: UUID = Field(..., description="ID of the template to use")
    resume_id: UUID = Field(..., description="ID of resume to use for generation")
    job_description: str = Field(..., min_length=50, description="Full job description text")
    job_title: Optional[str] = Field(None, max_length=255, description="Job title (optional)")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name (optional)")
    tags: Optional[list[str]] = Field(
        default=None, description="Optional categorization tags for organizing cover letters"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "resume_id": "123e4567-e89b-12d3-a456-426614174001",
                "job_description": "We are seeking a Senior Software Engineer with 5+ years of experience...",
                "job_title": "Senior Software Engineer",
                "company_name": "Google",
                "tags": ["Software Engineering", "Remote", "Senior"],
            }
        }
    )
