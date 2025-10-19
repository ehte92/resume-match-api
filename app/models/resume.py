"""
Resume database model for SQLAlchemy ORM.
Stores uploaded resume files and parsed data.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Resume(Base):
    """
    Resume model representing uploaded resume files.

    Fields:
        id: UUID primary key, auto-generated
        user_id: Foreign key to users table
        file_name: Original filename (e.g., "john_doe_resume.pdf")
        file_path: Storage path or URL (S3/local storage)
        file_type: File extension (pdf or docx)
        file_size: File size in bytes
        file_hash: SHA-256 hash of file content (for deduplication)
        parsed_text: Raw text extracted from the file
        parsed_data: Structured data (sections, contact info) as JSONB
        created_at: Timestamp when resume was uploaded
        updated_at: Timestamp when resume was last updated

    Relationships:
        user: The user who owns this resume
        analyses: Resume analyses performed on this resume

    Example:
        >>> resume = Resume(
        ...     user_id=user.id,
        ...     file_name="resume.pdf",
        ...     file_path="/uploads/uuid/resume.pdf",
        ...     file_type="pdf",
        ...     file_size=245678,
        ...     parsed_text="John Doe\\nSoftware Engineer...",
        ...     parsed_data={"sections": {...}, "contact": {...}}
        ... )
    """

    __tablename__ = "resumes"

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
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf or docx
    file_size = Column(Integer, nullable=False)  # bytes
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication
    parsed_text = Column(Text, nullable=True)  # Raw extracted text
    parsed_data = Column(JSONB, nullable=True)  # Structured data

    # Storage fields for R2/S3 integration
    storage_backend = Column(String(20), nullable=False, default="local")  # local or r2
    storage_url = Column(Text, nullable=True)  # R2 public URL
    storage_key = Column(Text, nullable=True)  # R2 object key (for deletion)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="resumes")
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
    cover_letters = relationship(
        "CoverLetter", back_populates="resume", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Resume for debugging."""
        return f"<Resume {self.file_name} (user_id={self.user_id})>"
