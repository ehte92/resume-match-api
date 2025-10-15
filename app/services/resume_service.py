"""
Resume service for handling resume CRUD operations.
Manages resume upload, parsing, storage, and retrieval with R2 integration.
"""

import logging
import os
from typing import Dict, List, Tuple
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.resume import Resume
from app.services.resume_parser import ResumeParser
from app.services.storage_service import get_storage_service
from app.utils import file_handler

logger = logging.getLogger(__name__)


class ResumeService:
    """Service for managing resume operations."""

    def __init__(self, db: Session):
        """
        Initialize resume service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.settings = get_settings()
        self.storage_service = get_storage_service()
        self.parser = ResumeParser()

    async def create_resume(self, upload_file: UploadFile, user_id: UUID) -> Resume:
        """
        Create a new resume with file upload, parsing, and storage.

        Workflow:
        1. Validate file type and size
        2. Save to temporary storage
        3. Upload to R2 storage
        4. Parse resume content
        5. Save to database with parsed data
        6. Clean up temporary file

        Args:
            upload_file: Uploaded file from FastAPI
            user_id: UUID of user uploading the resume

        Returns:
            Resume: Created resume model with all data

        Raises:
            HTTPException: 400 if validation fails, 500 if processing fails
        """
        temp_file_path = None

        try:
            # Step 1: Validate file type
            if not file_handler.validate_file_type(upload_file.content_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(  # noqa: E501
                        f"Invalid file type. Allowed types: {self.settings.ALLOWED_UPLOAD_TYPES}"
                    ),
                )

            # Step 2: Validate file size
            upload_file.file.seek(0, 2)  # Seek to end
            file_size = upload_file.file.tell()
            upload_file.file.seek(0)  # Reset to beginning

            if not file_handler.validate_file_size(file_size):
                max_size_mb = self.settings.MAX_UPLOAD_SIZE_MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size: {max_size_mb}MB",
                )

            # Step 3: Save to temporary storage
            logger.info(f"Saving temp file for user {user_id}: {upload_file.filename}")
            temp_file_path = await file_handler.save_temp_file(upload_file)

            # Step 4: Determine file type for parsing
            file_extension = file_handler.get_file_extension(upload_file.content_type)
            if not file_extension:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not determine file extension",
                )

            file_type = file_extension.replace(".", "")  # Remove dot

            # Step 5: Upload to R2 storage (if enabled)
            storage_result = await file_handler.save_file_with_storage(
                local_file_path=temp_file_path,
                user_id=str(user_id),
                content_type=upload_file.content_type,
                use_r2=None,
            )

            backend = storage_result["storage_backend"]
            location = storage_result.get("storage_url", temp_file_path)
            logger.info(f"File uploaded to {backend}: {location}")

            # Step 6: Parse resume
            logger.info(f"Parsing resume: {temp_file_path}")
            try:
                parsed_data = self.parser.parse(temp_file_path, file_type)
            except Exception as parse_error:
                logger.error(f"Resume parsing failed: {parse_error}")
                # Continue even if parsing fails - save raw file
                parsed_data = {
                    "raw_text": "",
                    "email": None,
                    "phone": None,
                    "linkedin": None,
                    "sections": {"experience": [], "education": [], "skills": []},
                }

            # Step 7: Create database record
            resume = Resume(
                user_id=user_id,
                file_name=upload_file.filename,
                file_path=storage_result["local_path"],
                file_type=file_type,
                file_size=file_size,
                parsed_text=parsed_data.get("raw_text"),
                parsed_data=parsed_data,
                storage_backend=storage_result["storage_backend"],
                storage_url=storage_result.get("storage_url"),
                storage_key=storage_result.get("storage_key"),
            )

            self.db.add(resume)
            self.db.commit()
            self.db.refresh(resume)

            # Add download URL to response
            self._add_download_url(resume)

            logger.info(f"Resume created successfully: {resume.id}")
            return resume

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            logger.error(f"Failed to create resume: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process resume: {str(e)}",
            )

        finally:
            # Step 8: Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    file_handler.delete_temp_file(temp_file_path)
                    logger.info(f"Cleaned up temp file: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file: {cleanup_error}")

    def _add_download_url(self, resume: Resume) -> None:
        """
        Add download_url attribute to resume object if stored in R2.

        This method modifies the resume object in-place by adding a
        download_url attribute with a presigned URL (or None for local storage).

        Args:
            resume: Resume object to add download URL to
        """
        if resume.storage_backend == "r2" and resume.storage_key:
            try:
                # Generate presigned URL (1 hour expiration)
                resume.download_url = self.storage_service.generate_presigned_url(
                    resume.storage_key, expiration=3600
                )
            except Exception as e:
                logger.error(f"Failed to generate download URL for resume {resume.id}: {e}")
                resume.download_url = None
        else:
            resume.download_url = None

    def get_resume_by_id(self, resume_id: UUID, user_id: UUID) -> Resume:
        """
        Get a specific resume by ID with ownership verification.

        Args:
            resume_id: UUID of the resume
            user_id: UUID of the requesting user

        Returns:
            Resume: The resume model with download_url attribute

        Raises:
            HTTPException: 404 if not found, 403 if not owner
        """
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with id {resume_id} not found",
            )

        # Verify ownership
        if resume.user_id != user_id:
            logger.warning(
                f"User {user_id} attempted to access resume {resume_id} owned by {resume.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resume",
            )

        # Add download URL
        self._add_download_url(resume)

        return resume

    def get_user_resumes(
        self, user_id: UUID, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Resume], int]:
        """
        Get paginated list of user's resumes.

        Args:
            user_id: UUID of the user
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of resumes with download_url attributes, total count)
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Query with pagination
        query = (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )

        # Get total count
        total = query.count()

        # Get paginated results
        resumes = query.offset(offset).limit(page_size).all()

        # Add download URLs to all resumes
        for resume in resumes:
            self._add_download_url(resume)

        logger.info(f"Retrieved {len(resumes)} resumes for user {user_id} (page {page})")
        return resumes, total

    def delete_resume(self, resume_id: UUID, user_id: UUID) -> bool:
        """
        Delete a resume with ownership verification and R2 cleanup.

        This will also cascade delete all related resume analyses.

        Args:
            resume_id: UUID of the resume to delete
            user_id: UUID of the requesting user

        Returns:
            bool: True if deletion successful

        Raises:
            HTTPException: 404 if not found, 403 if not owner, 500 if deletion fails
        """
        # Get resume with ownership check
        resume = self.get_resume_by_id(resume_id, user_id)

        try:
            # Delete from R2 if stored there
            if resume.storage_backend == "r2" and resume.storage_key:
                try:
                    logger.info(f"Deleting from R2: {resume.storage_key}")
                    self.storage_service.delete_file(resume.storage_key)
                    logger.info(f"Successfully deleted from R2: {resume.storage_key}")
                except Exception as r2_error:
                    logger.error(f"Failed to delete from R2: {r2_error}")
                    # Continue with database deletion even if R2 deletion fails
                    # We don't want orphaned database records

            # Delete local temp file if it exists
            if resume.file_path and os.path.exists(resume.file_path):
                try:
                    file_handler.delete_temp_file(resume.file_path)
                except Exception as local_error:
                    logger.warning(f"Failed to delete local file: {local_error}")

            # Delete from database (cascade will delete related analyses)
            self.db.delete(resume)
            self.db.commit()

            logger.info(f"Resume {resume_id} deleted successfully")
            return True

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete resume: {str(e)}",
            )

    def generate_download_url(self, resume_id: UUID, user_id: UUID) -> Dict[str, str]:
        """
        Generate a presigned download URL for a resume.

        Args:
            resume_id: UUID of the resume
            user_id: UUID of the requesting user

        Returns:
            Dict with 'url' and 'expires_in' keys

        Raises:
            HTTPException: 404 if not found, 403 if not owner, 400 if not in R2
        """
        # Get resume with ownership check
        resume = self.get_resume_by_id(resume_id, user_id)

        # Check if resume is stored in R2
        if resume.storage_backend != "r2" or not resume.storage_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume is not stored in cloud storage. Download not available.",
            )

        try:
            # Generate presigned URL (1 hour expiration)
            expiration_seconds = 3600
            presigned_url = self.storage_service.generate_presigned_url(
                resume.storage_key, expiration=expiration_seconds
            )

            logger.info(f"Generated download URL for resume {resume_id}")

            return {
                "url": presigned_url,
                "expires_in": expiration_seconds,
                "filename": resume.file_name,
            }

        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate download URL: {str(e)}",
            )
