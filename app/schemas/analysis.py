"""
Pydantic schemas for resume analysis validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisBase(BaseModel):
    """Base schema for analysis with common fields."""

    job_description: str = Field(..., description="Job description text for comparison")
    job_title: Optional[str] = Field(None, description="Job title", max_length=255)
    company_name: Optional[str] = Field(None, description="Company name", max_length=255)


class AnalysisRequest(AnalysisBase):
    """
    Schema for analysis request.
    Used when requesting a new resume analysis.
    """

    resume_id: UUID = Field(..., description="Resume UUID to analyze")


class ATSIssue(BaseModel):
    """Schema for ATS compatibility issue."""

    type: str = Field(..., description="Issue type (e.g., 'missing_section', 'formatting')")
    severity: str = Field(..., description="Severity level (high, medium, low)")
    message: str = Field(..., description="Issue description")
    recommendation: str = Field(..., description="How to fix this issue")


class AISuggestion(BaseModel):
    """Schema for AI-generated suggestion."""

    type: str = Field(..., description="Suggestion type (keyword, metric, format, etc.)")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    issue: str = Field(..., description="Issue description")
    suggestion: str = Field(..., description="Actionable advice")
    example: Optional[str] = Field(None, description="Concrete example")


class RewrittenBullet(BaseModel):
    """Schema for AI-rewritten bullet point."""

    original: str = Field(..., description="Original bullet point text")
    improved: str = Field(..., description="Improved version with metrics and keywords")
    reason: Optional[str] = Field(None, description="Why this improvement was suggested")


class AnalysisResponse(AnalysisBase):
    """
    Schema for analysis response.
    Returned when fetching analysis results.
    """

    id: UUID = Field(..., description="Analysis UUID")
    user_id: Optional[UUID] = Field(
        None, description="User UUID who requested this analysis (null for guest)"
    )
    resume_id: Optional[UUID] = Field(
        None, description="Resume UUID that was analyzed (null for guest)"
    )

    # Scores
    match_score: Optional[Decimal] = Field(
        None, description="Overall match score (0-100)", ge=0, le=100
    )
    ats_score: Optional[Decimal] = Field(
        None, description="ATS compatibility score (0-100)", ge=0, le=100
    )
    semantic_similarity: Optional[Decimal] = Field(
        None, description="Semantic similarity score (0-100)", ge=0, le=100
    )

    # Keywords
    matching_keywords: Optional[List[str]] = Field(
        None, description="Keywords found in both resume and job description"
    )
    missing_keywords: Optional[List[str]] = Field(
        None, description="Keywords in job description but missing from resume"
    )

    # Issues and suggestions
    ats_issues: Optional[List[Dict[str, Any]]] = Field(None, description="ATS compatibility issues")
    ai_suggestions: Optional[List[Dict[str, Any]]] = Field(
        None, description="AI-generated suggestions"
    )
    rewritten_bullets: Optional[List[Dict[str, Any]]] = Field(
        None, description="AI-rewritten bullet points"
    )

    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    created_at: datetime = Field(..., description="Analysis timestamp")

    model_config = ConfigDict(from_attributes=True)


class AnalysisInDB(AnalysisResponse):
    """
    Schema for analysis as stored in database.
    Includes all fields from the database model.
    """

    pass


class AnalysisListResponse(BaseModel):
    """
    Schema for paginated list of analyses.
    """

    analyses: list[AnalysisResponse] = Field(..., description="List of analyses")
    total: int = Field(..., description="Total number of analyses")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

    model_config = ConfigDict(from_attributes=True)


class AnalysisSummary(BaseModel):
    """
    Schema for analysis summary (lightweight version).
    Used for listing analyses without full details.
    """

    id: UUID = Field(..., description="Analysis UUID")
    resume_id: UUID = Field(..., description="Resume UUID")
    job_title: Optional[str] = Field(None, description="Job title")
    company_name: Optional[str] = Field(None, description="Company name")
    match_score: Optional[Decimal] = Field(None, description="Match score (0-100)")
    ats_score: Optional[Decimal] = Field(None, description="ATS score (0-100)")
    created_at: datetime = Field(..., description="Analysis timestamp")

    model_config = ConfigDict(from_attributes=True)
