"""
Cover letter template API endpoints.
Provides REST API for managing cover letter templates (system and user-created).
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.cover_letter_template import (
    CoverLetterTemplateCreate,
    CoverLetterTemplateListResponse,
    CoverLetterTemplateResponse,
    CoverLetterTemplateUpdate,
)
from app.services.cover_letter_template_service import CoverLetterTemplateService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/categories",
    summary="Get available template categories",
    description="Get list of all unique template categories for filtering",
)
@limiter.limit("30/minute")
def get_template_categories(
    request: Request,
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Get all unique template categories.

    Returns:
    - List of category names (e.g., ["Software Engineering", "Marketing", "Data Science"])

    Rate limit: 30 requests per minute
    """
    return CoverLetterTemplateService.get_categories(db)


@router.post(
    "/",
    response_model=CoverLetterTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new template",
    description="Create a new user-owned cover letter template",
)
@limiter.limit("10/minute")
def create_template(
    request: Request,
    template_request: CoverLetterTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new cover letter template.

    Requires:
    - name: Template display name
    - category: Template category
    - tone: Writing tone (professional, enthusiastic, balanced)
    - length: Target length (short, medium, long)
    - template_text: Template content with {{placeholders}}

    Optional:
    - description: What this template is for

    Returns:
    - Created template with metadata

    Rate limit: 10 requests per minute
    """
    template = CoverLetterTemplateService.create_template(db, current_user.id, template_request)
    return template


@router.get(
    "/",
    response_model=CoverLetterTemplateListResponse,
    summary="List templates",
    description="Get paginated list of templates (system + user's own) with optional filters",
)
@limiter.limit("30/minute")
def list_templates(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    tone: str | None = None,
    is_system: bool | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get paginated list of templates with optional filters.

    Returns system templates and user's own templates.

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - category: Filter by category
    - tone: Filter by tone (professional, enthusiastic, balanced)
    - is_system: Filter by template type (true = system only, false = user only, null = all)
    - search: Search text in template name and description
    - sort_by: Sort field (created_at, usage_count, name) - default: created_at
    - sort_order: Sort order (asc, desc) - default: desc

    Returns:
    - List of templates matching the filters
    - Pagination metadata (total, page, page_size)

    Rate limit: 30 requests per minute
    """
    templates, total = CoverLetterTemplateService.list_templates(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        category=category,
        tone=tone,
        is_system=is_system,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return CoverLetterTemplateListResponse(
        templates=templates, total=total, page=page, page_size=page_size
    )


@router.get(
    "/{template_id}",
    response_model=CoverLetterTemplateResponse,
    summary="Get template by ID",
    description="Retrieve a specific template by its ID",
)
@limiter.limit("30/minute")
def get_template(
    request: Request,
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get specific template by ID.

    System templates are accessible to all users.
    User templates are only accessible to their owner.

    Path parameters:
    - template_id: UUID of the template

    Returns:
    - Template with full text and metadata

    Raises:
    - 404: If template not found or not accessible to user

    Rate limit: 30 requests per minute
    """
    template = CoverLetterTemplateService.get_template(db, template_id, current_user.id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or not accessible",
        )

    return template


@router.put(
    "/{template_id}",
    response_model=CoverLetterTemplateResponse,
    summary="Update template",
    description="Update a user-owned template (cannot update system templates)",
)
@limiter.limit("10/minute")
def update_template(
    request: Request,
    template_id: UUID,
    update_data: CoverLetterTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a user-owned template.

    Only the template owner can update their templates.
    System templates cannot be updated via API.

    Path parameters:
    - template_id: UUID of the template

    Request body (all fields optional):
    - name: Updated template name
    - description: Updated description
    - category: Updated category
    - tone: Updated tone
    - length: Updated length
    - template_text: Updated template text

    Returns:
    - Updated template

    Raises:
    - 404: If template not found or doesn't belong to user
    - 403: If trying to update a system template

    Rate limit: 10 requests per minute
    """
    template = CoverLetterTemplateService.update_template(
        db, template_id, current_user.id, update_data
    )
    return template


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    description="Permanently delete a user-owned template (cannot delete system templates)",
)
@limiter.limit("10/minute")
def delete_template(
    request: Request,
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a user-owned template permanently.

    Only the template owner can delete their templates.
    System templates cannot be deleted via API.

    Path parameters:
    - template_id: UUID of the template

    Returns:
    - 204 No Content on success

    Raises:
    - 404: If template not found or doesn't belong to user
    - 403: If trying to delete a system template

    Rate limit: 10 requests per minute
    """
    CoverLetterTemplateService.delete_template(db, template_id, current_user.id)
