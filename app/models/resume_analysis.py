"""
ResumeAnalysis database model for SQLAlchemy ORM.
Stores analysis results comparing resume against job descriptions.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ResumeAnalysis(Base):
    """
    ResumeAnalysis model representing a resume analysis against a job description.

    Fields:
        id: UUID primary key, auto-generated
        user_id: Foreign key to users table
        resume_id: Foreign key to resumes table
        job_description: The job description text used for comparison
        job_title: Job title (optional, extracted or provided)
        company_name: Company name (optional, extracted or provided)
        match_score: Overall match score (0-100)
        ats_score: ATS compatibility score (0-100)
        semantic_similarity: Semantic similarity score (0-100)
        matching_keywords: Keywords found in both resume and job description
        missing_keywords: Keywords in job description but missing from resume
        ats_issues: ATS compatibility issues found
        ai_suggestions: AI-generated improvement suggestions
        rewritten_bullets: AI-rewritten bullet points
        processing_time_ms: Time taken to process the analysis
        created_at: Timestamp when analysis was created

    Relationships:
        user: The user who requested this analysis
        resume: The resume that was analyzed

    Example:
        >>> analysis = ResumeAnalysis(
        ...     user_id=user.id,
        ...     resume_id=resume.id,
        ...     job_description="We are looking for...",
        ...     job_title="Senior Software Engineer",
        ...     match_score=78.5,
        ...     ats_score=85.0,
        ...     matching_keywords=["python", "django", "aws"],
        ...     missing_keywords=["kubernetes", "docker"]
        ... )
    """

    __tablename__ = "resume_analyses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_description = Column(Text, nullable=False)
    job_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)

    # Scores (0-100 decimal values)
    match_score = Column(Numeric(5, 2), nullable=True)  # e.g., 78.50
    ats_score = Column(Numeric(5, 2), nullable=True)  # e.g., 85.00
    semantic_similarity = Column(Numeric(5, 2), nullable=True)  # e.g., 72.30

    # JSONB fields for flexible data storage
    matching_keywords = Column(JSONB, nullable=True)  # ["python", "django", ...]
    missing_keywords = Column(JSONB, nullable=True)  # ["kubernetes", "docker", ...]
    ats_issues = Column(JSONB, nullable=True)  # [{"type": "...", "message": "...", ...}]
    ai_suggestions = Column(JSONB, nullable=True)  # [{"type": "...", "suggestion": "...", ...}]
    rewritten_bullets = Column(JSONB, nullable=True)  # [{"original": "...", "improved": "..."}]

    processing_time_ms = Column(Integer, nullable=True)  # Time in milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")

    def __repr__(self) -> str:
        """String representation of ResumeAnalysis for debugging."""
        return f"<ResumeAnalysis resume_id={self.resume_id} match_score={self.match_score}>"
