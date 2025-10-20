"""
Pydantic schemas for cover letter generation and management.
Defines request/response models for cover letter endpoints.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoverLetterGenerateRequest(BaseModel):
    """Request schema for generating a new cover letter."""

    resume_id: UUID = Field(..., description="ID of resume to use for generation")
    job_description: str = Field(..., min_length=50, description="Full job description text")
    job_title: Optional[str] = Field(None, max_length=255, description="Job title (optional)")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name (optional)")
    tone: Literal["professional", "enthusiastic", "balanced"] = Field(
        default="professional", description="Writing tone for the cover letter"
    )
    length: Literal["short", "medium", "long"] = Field(
        default="medium",
        description="Target length: short (~250 words), medium (~350 words), long (~500 words)",
    )
    tags: Optional[list[str]] = Field(
        default=None, description="Optional categorization tags for organizing cover letters"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_id": "123e4567-e89b-12d3-a456-426614174000",
                "job_description": "We are seeking a Senior Software Engineer with 5+ years of experience in Python and distributed systems...",
                "job_title": "Senior Software Engineer",
                "company_name": "Google",
                "tone": "professional",
                "length": "medium",
                "tags": ["Software Engineering", "Remote", "Senior"],
            }
        }
    )


class CoverLetterUpdateRequest(BaseModel):
    """Request schema for updating cover letter text."""

    cover_letter_text: str = Field(..., min_length=100, description="Updated cover letter text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cover_letter_text": "Dear Hiring Manager,\n\nI am writing to express my strong interest in the Senior Software Engineer position at Google..."
            }
        }
    )


class CoverLetterResponse(BaseModel):
    """Response schema for a single cover letter."""

    id: UUID
    user_id: UUID
    resume_id: UUID
    job_title: Optional[str]
    company_name: Optional[str]
    job_description: str
    cover_letter_text: str
    tone: str
    length: str
    tags: Optional[list[str]]
    openai_tokens_used: int
    processing_time_ms: int
    word_count: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CoverLetterListResponse(BaseModel):
    """Paginated list of cover letters."""

    cover_letters: list[CoverLetterResponse]
    total: int
    page: int
    page_size: int


class CoverLetterRefineRequest(BaseModel):
    """Request schema for refining an existing cover letter with AI."""

    refinement_instruction: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Instructions for how to refine the cover letter (e.g., 'make it more concise', 'emphasize leadership experience')",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refinement_instruction": "Make the cover letter more concise and emphasize my leadership experience in managing distributed teams"
            }
        }
    )


class CoverLetterRefineResponse(BaseModel):
    """Response schema for refined cover letter with comparison to original."""

    original_cover_letter: CoverLetterResponse
    refined_cover_letter_text: str = Field(
        ..., description="The refined version of the cover letter"
    )
    refinement_instruction: str = Field(..., description="The instruction used for refinement")
    tokens_used: int = Field(..., description="AI tokens used for refinement")
    processing_time_ms: int = Field(..., description="Time taken to refine in milliseconds")
    word_count: int = Field(..., description="Word count of refined version")

    model_config = ConfigDict(from_attributes=True)


# Export format type
ExportFormat = Literal["pdf", "docx", "txt"]
