"""
Cover letter API endpoints.
Provides REST API for AI-powered cover letter generation and management.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterListResponse,
    CoverLetterResponse,
    CoverLetterUpdateRequest,
)
from app.services.cover_letter_service import CoverLetterService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/generate",
    response_model=CoverLetterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI-powered cover letter",
    description="Generate a personalized cover letter using AI based on resume and job description",
)
@limiter.limit("5/minute")  # Rate limit AI generation to prevent abuse
async def generate_cover_letter(
    request: Request,
    cover_letter_request: CoverLetterGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate AI-powered cover letter for a job application.

    Requires:
    - Valid resume_id from user's resume library
    - Job description (minimum 50 characters)
    - Optional: job_title, company_name, tone, length

    Returns:
    - Generated cover letter with metadata (tokens used, processing time, etc.)

    Rate limit: 5 requests per minute
    """
    cover_letter = await CoverLetterService.generate_cover_letter(
        db, current_user.id, cover_letter_request
    )
    return cover_letter


@router.get(
    "/",
    response_model=CoverLetterListResponse,
    summary="List user's cover letters",
    description="Get paginated list of all cover letters for the current user",
)
@limiter.limit("30/minute")
def list_cover_letters(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get paginated list of user's cover letters.

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

    Returns:
    - List of cover letters sorted by creation date (newest first)
    - Pagination metadata (total, page, page_size)

    Rate limit: 30 requests per minute
    """
    cover_letters, total = CoverLetterService.list_cover_letters(
        db, current_user.id, page, page_size
    )

    return CoverLetterListResponse(
        cover_letters=cover_letters, total=total, page=page, page_size=page_size
    )


@router.get(
    "/{cover_letter_id}",
    response_model=CoverLetterResponse,
    summary="Get cover letter by ID",
    description="Retrieve a specific cover letter by its ID",
)
@limiter.limit("30/minute")
def get_cover_letter(
    request: Request,
    cover_letter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get specific cover letter by ID.

    Path parameters:
    - cover_letter_id: UUID of the cover letter

    Returns:
    - Cover letter with full text and metadata

    Raises:
    - 404: If cover letter not found or doesn't belong to user

    Rate limit: 30 requests per minute
    """
    cover_letter = CoverLetterService.get_cover_letter(db, cover_letter_id, current_user.id)

    if not cover_letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover letter not found",
        )

    return cover_letter


@router.put(
    "/{cover_letter_id}",
    response_model=CoverLetterResponse,
    summary="Update cover letter text",
    description="Update the text of a generated cover letter (manual edits)",
)
@limiter.limit("10/minute")
def update_cover_letter(
    request: Request,
    cover_letter_id: UUID,
    update_data: CoverLetterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update cover letter text (manual edits after generation).

    Path parameters:
    - cover_letter_id: UUID of the cover letter

    Request body:
    - cover_letter_text: Updated cover letter text (minimum 100 characters)

    Returns:
    - Updated cover letter with recalculated word count

    Raises:
    - 404: If cover letter not found or doesn't belong to user

    Rate limit: 10 requests per minute
    """
    cover_letter = CoverLetterService.update_cover_letter(
        db, cover_letter_id, current_user.id, update_data
    )
    return cover_letter


@router.delete(
    "/{cover_letter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cover letter",
    description="Permanently delete a cover letter",
)
@limiter.limit("10/minute")
def delete_cover_letter(
    request: Request,
    cover_letter_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete cover letter permanently.

    Path parameters:
    - cover_letter_id: UUID of the cover letter

    Returns:
    - 204 No Content on success

    Raises:
    - 404: If cover letter not found or doesn't belong to user

    Rate limit: 10 requests per minute
    """
    CoverLetterService.delete_cover_letter(db, cover_letter_id, current_user.id)
