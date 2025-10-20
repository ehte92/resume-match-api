"""
CoverLetterTemplate database model for SQLAlchemy ORM.
Stores reusable cover letter templates for quick generation.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CoverLetterTemplate(Base):
    """
    CoverLetterTemplate model representing reusable cover letter templates.

    Templates can be system-created (curated by admins) or user-created.
    They include placeholders that get filled in during generation.

    Fields:
        id: UUID primary key, auto-generated
        name: Template display name
        description: What this template is for (optional)
        category: Template category (e.g., "Software Engineering")
        tone: Writing tone (professional, enthusiastic, balanced)
        length: Target length (short, medium, long)
        template_text: The cover letter template with {{placeholders}}
        is_system: Whether this is a system/admin template
        user_id: Foreign key to users table (null for system templates)
        usage_count: Track how many times this template was used
        created_at: Timestamp when template was created
        updated_at: Timestamp when template was last updated

    Relationships:
        user: The user who owns this template (null for system templates)

    Example:
        >>> template = CoverLetterTemplate(
        ...     name="Software Engineering - Professional",
        ...     description="Perfect for senior software engineering roles",
        ...     category="Software Engineering",
        ...     tone="professional",
        ...     length="medium",
        ...     template_text="Dear Hiring Manager,\\n\\n...",
        ...     is_system=True,
        ...     user_id=None,
        ...     usage_count=0
        ... )
    """

    __tablename__ = "cover_letter_templates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    # Template metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)

    # Generation parameters
    tone = Column(String(20), nullable=False, index=True)
    length = Column(String(20), nullable=False)

    # Template content
    template_text = Column(Text, nullable=False)

    # Template type and ownership
    is_system = Column(Boolean, nullable=False, default=False, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user = relationship("User", back_populates="cover_letter_templates")

    def __repr__(self) -> str:
        """String representation of CoverLetterTemplate for debugging."""
        template_type = "System" if self.is_system else f"User({self.user_id})"
        return f"<CoverLetterTemplate '{self.name}' ({template_type}, category={self.category})>"
