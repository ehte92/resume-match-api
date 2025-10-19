"""
Service layer for cover letter generation and management.
Handles business logic for creating, retrieving, updating, and deleting cover letters.
"""

import logging
import time
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cover_letter import CoverLetter
from app.models.resume import Resume
from app.schemas.cover_letter import CoverLetterGenerateRequest, CoverLetterUpdateRequest
from app.services.cover_letter_generator import CoverLetterGenerator

logger = logging.getLogger(__name__)


class CoverLetterService:
    """Service for cover letter operations."""

    @staticmethod
    async def generate_cover_letter(
        db: Session, user_id: UUID, request: CoverLetterGenerateRequest
    ) -> CoverLetter:
        """
        Generate AI-powered cover letter for a job application.

        Args:
            db: Database session
            user_id: Current user's ID
            request: Cover letter generation request

        Returns:
            Created CoverLetter database object

        Raises:
            HTTPException 404: If resume not found or doesn't belong to user
            HTTPException 400: If resume has no parsed text
            HTTPException 500: If AI generation fails
        """
        start_time = time.time()

        # 1. Validate resume exists and belongs to user
        resume = (
            db.query(Resume)
            .filter(Resume.id == request.resume_id, Resume.user_id == user_id)
            .first()
        )

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or doesn't belong to user",
            )

        if not resume.parsed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume has no parsed text - upload may have failed. Please re-upload the resume.",
            )

        # 2. Generate cover letter using AI
        try:
            generator = CoverLetterGenerator()
            ai_result = await generator.generate_cover_letter(
                resume_text=resume.parsed_text,
                job_description=request.job_description,
                job_title=request.job_title,
                company_name=request.company_name,
                tone=request.tone,
                length=request.length,
            )
        except ValueError as e:
            # AI not configured or disabled
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service unavailable: {str(e)}",
            )
        except Exception as e:
            logger.error(f"AI generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cover letter generation failed. Please try again.",
            )

        # 3. Calculate metrics
        processing_time_ms = int((time.time() - start_time) * 1000)
        word_count = len(ai_result["cover_letter_text"].split())

        # 4. Create database record
        cover_letter = CoverLetter(
            user_id=user_id,
            resume_id=request.resume_id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_description=request.job_description,
            cover_letter_text=ai_result["cover_letter_text"],
            tone=request.tone,
            length=request.length,
            openai_tokens_used=ai_result["tokens_used"],
            processing_time_ms=processing_time_ms,
            word_count=word_count,
        )

        db.add(cover_letter)
        db.commit()
        db.refresh(cover_letter)

        logger.info(
            f"Generated {word_count} word cover letter {cover_letter.id} in {processing_time_ms}ms "
            f"using {ai_result['tokens_used']} tokens"
        )

        return cover_letter

    @staticmethod
    def get_cover_letter(
        db: Session, cover_letter_id: UUID, user_id: UUID
    ) -> Optional[CoverLetter]:
        """
        Get single cover letter by ID.

        Args:
            db: Database session
            cover_letter_id: Cover letter ID
            user_id: Current user's ID (for ownership check)

        Returns:
            CoverLetter object or None if not found
        """
        return (
            db.query(CoverLetter)
            .filter(CoverLetter.id == cover_letter_id, CoverLetter.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_cover_letters(
        db: Session, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[CoverLetter], int]:
        """
        List user's cover letters with pagination.

        Args:
            db: Database session
            user_id: Current user's ID
            page: Page number (1-indexed)
            page_size: Items per page (max 100)

        Returns:
            Tuple of (list of CoverLetter objects, total count)
        """
        # Limit page_size to prevent abuse
        page_size = min(page_size, 100)

        query = db.query(CoverLetter).filter(CoverLetter.user_id == user_id)
        total = query.count()

        cover_letters = (
            query.order_by(CoverLetter.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return cover_letters, total

    @staticmethod
    def update_cover_letter(
        db: Session,
        cover_letter_id: UUID,
        user_id: UUID,
        update_data: CoverLetterUpdateRequest,
    ) -> CoverLetter:
        """
        Update cover letter text (manual edits after generation).

        Args:
            db: Database session
            cover_letter_id: Cover letter ID
            user_id: Current user's ID (for ownership check)
            update_data: Updated cover letter text

        Returns:
            Updated CoverLetter object

        Raises:
            HTTPException 404: If cover letter not found
        """
        cover_letter = CoverLetterService.get_cover_letter(db, cover_letter_id, user_id)

        if not cover_letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cover letter not found"
            )

        # Update text and recalculate word count
        cover_letter.cover_letter_text = update_data.cover_letter_text
        cover_letter.word_count = len(update_data.cover_letter_text.split())

        db.commit()
        db.refresh(cover_letter)

        logger.info(
            f"Updated cover letter {cover_letter_id}, new word count: {cover_letter.word_count}"
        )

        return cover_letter

    @staticmethod
    def delete_cover_letter(db: Session, cover_letter_id: UUID, user_id: UUID) -> bool:
        """
        Delete cover letter permanently.

        Args:
            db: Database session
            cover_letter_id: Cover letter ID
            user_id: Current user's ID (for ownership check)

        Returns:
            True if deleted successfully

        Raises:
            HTTPException 404: If cover letter not found
        """
        cover_letter = CoverLetterService.get_cover_letter(db, cover_letter_id, user_id)

        if not cover_letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cover letter not found"
            )

        db.delete(cover_letter)
        db.commit()

        logger.info(f"Deleted cover letter {cover_letter_id}")

        return True
