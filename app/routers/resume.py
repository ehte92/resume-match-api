"""
Resume API endpoints for upload, retrieval, and management.
All endpoints require JWT authentication.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new resume",
    description="Upload a PDF or DOCX resume file. The file will be parsed and stored in R2.",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX, max 5MB)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a new resume file.

    **Workflow:**
    1. Validates file type (PDF/DOCX only)
    2. Validates file size (max 5MB)
    3. Uploads to R2 storage
    4. Parses resume content (text extraction, contact info, sections)
    5. Saves to database with parsed data

    **Returns:**
    - 201: Resume created successfully with parsed data
    - 400: Invalid file type or size
    - 401: Unauthorized (invalid/missing token)
    - 500: Server error during processing
    """
    resume_service = ResumeService(db)
    resume = await resume_service.create_resume(upload_file=file, user_id=current_user.id)
    return resume


@router.get(
    "/",
    response_model=ResumeListResponse,
    summary="List user's resumes",
    description="Get a paginated list of all resumes uploaded by the current user.",
)
def list_resumes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all resumes for the authenticated user with pagination.

    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 10, max: 100)

    **Returns:**
    - 200: List of resumes with pagination info
    - 401: Unauthorized (invalid/missing token)
    """
    resume_service = ResumeService(db)
    resumes, total = resume_service.get_user_resumes(
        user_id=current_user.id, page=page, page_size=page_size
    )

    return ResumeListResponse(resumes=resumes, total=total, page=page, page_size=page_size)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get a specific resume",
    description="Retrieve details of a specific resume by ID. User must own the resume.",
)
def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific resume by ID.

    **Security:**
    - Users can only access their own resumes
    - Attempting to access another user's resume returns 403

    **Returns:**
    - 200: Resume details with parsed data
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (resume belongs to another user)
    - 404: Resume not found
    """
    resume_service = ResumeService(db)
    resume = resume_service.get_resume_by_id(resume_id=resume_id, user_id=current_user.id)
    return resume


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume",
    description="Delete a resume and all associated data. This also deletes related analyses.",
)
def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a resume by ID.

    **What gets deleted:**
    - Resume file from R2 storage
    - Database record
    - All associated resume analyses (cascade delete)

    **Security:**
    - Users can only delete their own resumes
    - Attempting to delete another user's resume returns 403

    **Returns:**
    - 204: Resume deleted successfully (no content)
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (resume belongs to another user)
    - 404: Resume not found
    - 500: Server error during deletion
    """
    resume_service = ResumeService(db)
    resume_service.delete_resume(resume_id=resume_id, user_id=current_user.id)
    return None


@router.get(
    "/{resume_id}/download",
    summary="Generate download URL",
    description="Generate a presigned URL for downloading the resume file from R2 storage.",
)
def get_download_url(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a presigned download URL for a resume.

    **How it works:**
    - Generates a temporary presigned URL for secure file access
    - URL expires after 1 hour
    - Only works for resumes stored in R2 (not local storage)

    **Security:**
    - Users can only generate URLs for their own resumes
    - URL is time-limited for security

    **Returns:**
    - 200: Download URL with expiration time
    - 400: Resume not stored in R2 (local storage)
    - 401: Unauthorized (invalid/missing token)
    - 403: Forbidden (resume belongs to another user)
    - 404: Resume not found
    - 500: Server error generating URL
    """
    resume_service = ResumeService(db)
    download_info = resume_service.generate_download_url(
        resume_id=resume_id, user_id=current_user.id
    )
    return download_info
