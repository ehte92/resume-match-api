"""
Service layer for cover letter template management.
Handles business logic for creating, retrieving, updating, and deleting templates.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cover_letter_template import CoverLetterTemplate
from app.schemas.cover_letter_template import (
    CoverLetterTemplateCreate,
    CoverLetterTemplateUpdate,
)

logger = logging.getLogger(__name__)


class CoverLetterTemplateService:
    """Service for cover letter template operations."""

    @staticmethod
    def create_template(
        db: Session, user_id: UUID, request: CoverLetterTemplateCreate
    ) -> CoverLetterTemplate:
        """
        Create a new cover letter template.

        Args:
            db: Database session
            user_id: Current user's ID
            request: Template creation request

        Returns:
            Created CoverLetterTemplate database object
        """
        template = CoverLetterTemplate(
            user_id=user_id,
            name=request.name,
            description=request.description,
            category=request.category,
            tone=request.tone,
            length=request.length,
            template_text=request.template_text,
            is_system=False,  # User templates are never system templates
            usage_count=0,
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        logger.info(f"Created template {template.id} for user {user_id}: '{template.name}'")

        return template

    @staticmethod
    def get_template(
        db: Session, template_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[CoverLetterTemplate]:
        """
        Get single template by ID.

        Args:
            db: Database session
            template_id: Template ID
            user_id: Current user's ID (optional, for ownership check on user templates)

        Returns:
            CoverLetterTemplate object or None if not found

        Note:
            System templates (is_system=True) are accessible to all users.
            User templates are only accessible to their owner.
        """
        query = db.query(CoverLetterTemplate).filter(CoverLetterTemplate.id == template_id)

        # If user_id provided, filter to system templates OR templates owned by user
        if user_id:
            query = query.filter(
                (CoverLetterTemplate.is_system == True)
                | (CoverLetterTemplate.user_id == user_id)
            )

        return query.first()

    @staticmethod
    def list_templates(
        db: Session,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        tone: Optional[str] = None,
        is_system: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[CoverLetterTemplate], int]:
        """
        List templates with pagination, search, and filters.

        Args:
            db: Database session
            user_id: Current user's ID
            page: Page number (1-indexed)
            page_size: Items per page (max 100)
            category: Filter by category
            tone: Filter by tone
            is_system: Filter by system/user templates (None = all, True = system only, False = user only)
            search: Search text in name and description
            sort_by: Field to sort by (created_at, usage_count, name)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple of (list of CoverLetterTemplate objects, total count)
        """
        # Limit page_size to prevent abuse
        page_size = min(page_size, 100)

        # Start with base query: system templates OR user's own templates
        query = db.query(CoverLetterTemplate).filter(
            (CoverLetterTemplate.is_system == True) | (CoverLetterTemplate.user_id == user_id)
        )

        # Apply category filter
        if category:
            query = query.filter(CoverLetterTemplate.category == category)

        # Apply tone filter
        if tone:
            query = query.filter(CoverLetterTemplate.tone == tone)

        # Apply is_system filter
        if is_system is not None:
            query = query.filter(CoverLetterTemplate.is_system == is_system)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (CoverLetterTemplate.name.ilike(search_pattern))
                | (CoverLetterTemplate.description.ilike(search_pattern))
            )

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(CoverLetterTemplate, sort_by, CoverLetterTemplate.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        templates = query.offset((page - 1) * page_size).limit(page_size).all()

        return templates, total

    @staticmethod
    def update_template(
        db: Session,
        template_id: UUID,
        user_id: UUID,
        update_data: CoverLetterTemplateUpdate,
    ) -> CoverLetterTemplate:
        """
        Update a user's template.

        Args:
            db: Database session
            template_id: Template ID
            user_id: Current user's ID (for ownership check)
            update_data: Updated template data

        Returns:
            Updated CoverLetterTemplate object

        Raises:
            HTTPException 404: If template not found
            HTTPException 403: If user tries to update a system template
        """
        template = (
            db.query(CoverLetterTemplate)
            .filter(
                CoverLetterTemplate.id == template_id, CoverLetterTemplate.user_id == user_id
            )
            .first()
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or doesn't belong to user",
            )

        if template.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update system templates",
            )

        # Update fields if provided
        if update_data.name is not None:
            template.name = update_data.name
        if update_data.description is not None:
            template.description = update_data.description
        if update_data.category is not None:
            template.category = update_data.category
        if update_data.tone is not None:
            template.tone = update_data.tone
        if update_data.length is not None:
            template.length = update_data.length
        if update_data.template_text is not None:
            template.template_text = update_data.template_text

        db.commit()
        db.refresh(template)

        logger.info(f"Updated template {template_id}: '{template.name}'")

        return template

    @staticmethod
    def delete_template(db: Session, template_id: UUID, user_id: UUID) -> bool:
        """
        Delete a user's template permanently.

        Args:
            db: Database session
            template_id: Template ID
            user_id: Current user's ID (for ownership check)

        Returns:
            True if deleted successfully

        Raises:
            HTTPException 404: If template not found
            HTTPException 403: If user tries to delete a system template
        """
        template = (
            db.query(CoverLetterTemplate)
            .filter(
                CoverLetterTemplate.id == template_id, CoverLetterTemplate.user_id == user_id
            )
            .first()
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or doesn't belong to user",
            )

        if template.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete system templates",
            )

        db.delete(template)
        db.commit()

        logger.info(f"Deleted template {template_id}")

        return True

    @staticmethod
    def increment_usage_count(db: Session, template_id: UUID) -> None:
        """
        Increment the usage count for a template (called when generating a cover letter from it).

        Args:
            db: Database session
            template_id: Template ID
        """
        template = db.query(CoverLetterTemplate).filter(CoverLetterTemplate.id == template_id).first()

        if template:
            template.usage_count += 1
            db.commit()
            logger.info(f"Incremented usage count for template {template_id} to {template.usage_count}")

    @staticmethod
    def get_categories(db: Session) -> list[str]:
        """
        Get list of unique template categories (for frontend dropdown).

        Args:
            db: Database session

        Returns:
            List of unique category names
        """
        categories = (
            db.query(CoverLetterTemplate.category)
            .distinct()
            .order_by(CoverLetterTemplate.category)
            .all()
        )

        return [cat[0] for cat in categories]
