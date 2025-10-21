"""
Cover letter API endpoints.
Provides REST API for AI-powered cover letter generation and management.
"""

from typing import Any
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from fastapi.responses import Response

from app.constants.cover_letter_tags import TAG_CATEGORIES
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterListResponse,
    CoverLetterRefineRequest,
    CoverLetterRefineResponse,
    CoverLetterResponse,
    CoverLetterUpdateRequest,
    ExportFormat,
)
from app.services.cover_letter_exporter import CoverLetterExporter
from app.services.cover_letter_service import CoverLetterService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/tags",
    summary="Get available tags",
    description="Get all available predefined tags organized by category",
)
@limiter.limit("30/minute")
def get_available_tags(
    request: Request,
) -> Any:
    """
    Get all available predefined tags for cover letter categorization.

    Returns:
    - Dictionary of tag categories with their respective tags

    Rate limit: 30 requests per minute
    """
    return TAG_CATEGORIES


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
    description="Get paginated list of all cover letters for the current user with optional search and filters",
)
@limiter.limit("30/minute")
def list_cover_letters(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    tags: str | None = None,
    tone: str | None = None,
    length: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get paginated list of user's cover letters with optional search and filters.

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - search: Search text in job_title, company_name, and cover_letter_text
    - tags: Comma-separated list of tags to filter by (e.g., "Remote,Software Engineering")
    - tone: Filter by tone (professional, enthusiastic, balanced)
    - length: Filter by length (short, medium, long)
    - sort_by: Sort field (created_at, word_count, job_title, company_name) - default: created_at
    - sort_order: Sort order (asc, desc) - default: desc

    Returns:
    - List of cover letters matching the filters and search
    - Pagination metadata (total, page, page_size)

    Rate limit: 30 requests per minute
    """
    # Parse tags from comma-separated string
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

    cover_letters, total = CoverLetterService.list_cover_letters(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        tags=tag_list,
        tone=tone,
        length=length,
        sort_by=sort_by,
        sort_order=sort_order,
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


@router.get(
    "/{cover_letter_id}/export",
    summary="Export cover letter",
    description="Export cover letter in PDF, DOCX, or TXT format",
)
@limiter.limit("20/minute")
def export_cover_letter(
    request: Request,
    cover_letter_id: UUID,
    format: ExportFormat = "pdf",
    include_metadata: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export cover letter in specified format.

    Path parameters:
    - cover_letter_id: UUID of the cover letter

    Query parameters:
    - format: Export format (pdf, docx, txt) - default: pdf
    - include_metadata: Include generation metadata in export (PDF only) - default: false

    Returns:
    - File download with appropriate content-type

    Raises:
    - 404: If cover letter not found or doesn't belong to user

    Rate limit: 20 requests per minute
    """
    # Get cover letter and verify ownership
    cover_letter = CoverLetterService.get_cover_letter(db, cover_letter_id, current_user.id)

    if not cover_letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover letter not found",
        )

    # Generate export based on format
    exporter = CoverLetterExporter()

    if format == "pdf":
        file_bytes = exporter.export_to_pdf(cover_letter, include_metadata)
        media_type = "application/pdf"
    elif format == "docx":
        file_bytes = exporter.export_to_docx(cover_letter)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:  # txt
        file_bytes = exporter.export_to_txt(cover_letter)
        media_type = "text/plain"

    # Generate appropriate filename
    filename = exporter.get_filename(cover_letter, format)
    # URL-encode filename for RFC 2231/5987 compliance (handles Unicode safely)
    filename_utf8 = quote(filename.encode("utf-8"))

    # Return file download response with RFC 2231 encoding
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            # ASCII fallback + UTF-8 version for modern browsers
            "Content-Disposition": (
                f'attachment; filename="{filename}"; ' f"filename*=UTF-8''{filename_utf8}"
            ),
            "Content-Length": str(len(file_bytes)),
        },
    )


@router.post(
    "/{cover_letter_id}/refine",
    response_model=CoverLetterRefineResponse,
    summary="Refine cover letter with AI",
    description="Refine an existing cover letter based on specific instructions using AI",
)
@limiter.limit("3/minute")  # Lower rate limit for AI refinement
async def refine_cover_letter(
    request: Request,
    cover_letter_id: UUID,
    refine_request: CoverLetterRefineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Refine an existing cover letter with AI guidance.

    This endpoint allows users to iteratively improve their cover letters by
    providing specific instructions (e.g., "make it more concise", "emphasize
    leadership skills", "add more technical details").

    Path parameters:
    - cover_letter_id: UUID of the cover letter to refine

    Request body:
    - refinement_instruction: Instructions for refinement (10-500 characters)

    Returns:
    - Original cover letter for comparison
    - Refined cover letter text
    - Refinement metrics (tokens, processing time, word count)

    Raises:
    - 404: If cover letter not found or doesn't belong to user
    - 503: If AI service is unavailable
    - 500: If refinement fails

    Rate limit: 3 requests per minute

    Note: The refined version is NOT automatically saved. The frontend should
    present it to the user for review before accepting/rejecting the changes.
    """
    result = await CoverLetterService.refine_cover_letter(
        db, cover_letter_id, current_user.id, refine_request.refinement_instruction
    )

    return CoverLetterRefineResponse(
        original_cover_letter=result["original_cover_letter"],
        refined_cover_letter_text=result["refined_cover_letter_text"],
        refinement_instruction=result["refinement_instruction"],
        tokens_used=result["tokens_used"],
        processing_time_ms=result["processing_time_ms"],
        word_count=result["word_count"],
    )
