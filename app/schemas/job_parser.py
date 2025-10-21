"""
Pydantic schemas for job description parsing.
Defines request/response models for the AI-powered job parser.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobParseRequest(BaseModel):
    """Request schema for parsing job descriptions."""

    source_type: Literal["text", "url"] = Field(
        ..., description="Whether the content is raw text or a URL to fetch"
    )
    content: str = Field(..., min_length=10, description="Job description text or URL to parse")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_type": "url",
                "content": "https://www.linkedin.com/jobs/view/3845729183",
            }
        }
    )


class ParsedJobData(BaseModel):
    """Response schema containing extracted job information."""

    job_title: Optional[str] = Field(None, description="Extracted job title")
    company_name: Optional[str] = Field(None, description="Extracted company name")
    location: Optional[str] = Field(None, description="Job location if mentioned")
    key_skills: list[str] = Field(
        default_factory=list, description="List of required technical skills"
    )
    responsibilities: list[str] = Field(
        default_factory=list, description="Main job responsibilities"
    )
    qualifications: list[str] = Field(default_factory=list, description="Required qualifications")
    nice_to_have: list[str] = Field(
        default_factory=list, description="Preferred/bonus qualifications"
    )
    tone: Literal["professional", "enthusiastic", "balanced"] = Field(
        default="professional", description="Inferred tone of the job posting"
    )
    experience_level: Optional[Literal["junior", "mid", "senior", "lead"]] = Field(
        None, description="Inferred experience level from requirements"
    )
    raw_text: str = Field(..., description="The full extracted/provided job description text")
    source_url: Optional[str] = Field(None, description="Original URL if provided")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_title": "Senior Software Engineer",
                "company_name": "Google",
                "location": "Mountain View, CA",
                "key_skills": ["Python", "Kubernetes", "Distributed Systems"],
                "responsibilities": [
                    "Design and implement scalable backend systems",
                    "Collaborate with cross-functional teams",
                ],
                "qualifications": ["5+ years of software engineering experience"],
                "nice_to_have": ["Experience with Google Cloud Platform"],
                "tone": "professional",
                "experience_level": "senior",
                "raw_text": "We are seeking a Senior Software Engineer...",
                "source_url": "https://careers.google.com/jobs/...",
            }
        }
    )
