"""
CoverLetter database model for SQLAlchemy ORM.
Stores AI-generated cover letters for job applications.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CoverLetter(Base):
    """
    CoverLetter model representing AI-generated cover letters.

    Fields:
        id: UUID primary key, auto-generated
        user_id: Foreign key to users table
        resume_id: Foreign key to resumes table
        job_title: Job title (optional)
        company_name: Company name (optional)
        job_description: The job description used for generation
        cover_letter_text: The generated cover letter content
        tone: Writing tone (professional, enthusiastic, balanced)
        length: Target length (short, medium, long)
        openai_tokens_used: AI tokens consumed during generation
        processing_time_ms: Time taken to generate
        word_count: Actual word count of generated text
        created_at: Timestamp when cover letter was created
        updated_at: Timestamp when cover letter was last updated

    Relationships:
        user: The user who owns this cover letter
        resume: The resume used for generation

    Example:
        >>> cover_letter = CoverLetter(
        ...     user_id=user.id,
        ...     resume_id=resume.id,
        ...     job_title="Senior Software Engineer",
        ...     company_name="Google",
        ...     job_description="We are seeking...",
        ...     cover_letter_text="Dear Hiring Manager...",
        ...     tone="professional",
        ...     length="medium",
        ...     word_count=350
        ... )
    """

    __tablename__ = "cover_letters"

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

    # Job details
    job_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=False)

    # Generated content
    cover_letter_text = Column(Text, nullable=False)

    # Generation parameters
    tone = Column(String(20), nullable=False, default="professional")
    length = Column(String(20), nullable=False, default="medium")

    # Metrics
    openai_tokens_used = Column(Integer, nullable=True, default=0)
    processing_time_ms = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="cover_letters")
    resume = relationship("Resume", back_populates="cover_letters")

    def __repr__(self) -> str:
        """String representation of CoverLetter for debugging."""
        return f"<CoverLetter {self.job_title} at {self.company_name} (user_id={self.user_id})>"
