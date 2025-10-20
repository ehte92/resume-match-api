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
            tags=request.tags if request.tags else [],
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
        db: Session,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tags: Optional[list[str]] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[CoverLetter], int]:
        """
        List user's cover letters with pagination, search, and filters.

        Args:
            db: Database session
            user_id: Current user's ID
            page: Page number (1-indexed)
            page_size: Items per page (max 100)
            search: Search text in job_title, company_name, and cover_letter_text
            tags: List of tags to filter by (any tag match)
            tone: Filter by tone
            length: Filter by length
            sort_by: Field to sort by (created_at, word_count, job_title, company_name)
            sort_order: Sort order (asc, desc)

        Returns:
            Tuple of (list of CoverLetter objects, total count)
        """
        # Limit page_size to prevent abuse
        page_size = min(page_size, 100)

        # Start with base query
        query = db.query(CoverLetter).filter(CoverLetter.user_id == user_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (CoverLetter.job_title.ilike(search_pattern))
                | (CoverLetter.company_name.ilike(search_pattern))
                | (CoverLetter.cover_letter_text.ilike(search_pattern))
            )

        # Apply tag filter (any tag match)
        if tags and len(tags) > 0:
            # Using JSONB contains operator to check if any tag is in the tags array
            from sqlalchemy import func, cast
            from sqlalchemy.dialects.postgresql import ARRAY, TEXT

            # Convert Python list to PostgreSQL array for the overlap operator
            query = query.filter(func.jsonb_typeof(CoverLetter.tags) == "array").filter(
                cast(CoverLetter.tags, ARRAY(TEXT)).overlap(tags)
            )

        # Apply tone filter
        if tone:
            query = query.filter(CoverLetter.tone == tone)

        # Apply length filter
        if length:
            query = query.filter(CoverLetter.length == length)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(CoverLetter, sort_by, CoverLetter.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        cover_letters = query.offset((page - 1) * page_size).limit(page_size).all()

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

    @staticmethod
    async def refine_cover_letter(
        db: Session, cover_letter_id: UUID, user_id: UUID, refinement_instruction: str
    ) -> dict:
        """
        Refine an existing cover letter using AI based on user instructions.

        Args:
            db: Database session
            cover_letter_id: Cover letter ID to refine
            user_id: Current user's ID (for ownership check)
            refinement_instruction: User's instructions for refinement

        Returns:
            Dictionary with:
                - original_cover_letter: Original CoverLetter object
                - refined_cover_letter_text: Refined text
                - refinement_instruction: The instruction used
                - tokens_used: Tokens used for refinement
                - processing_time_ms: Time taken
                - word_count: Word count of refined version

        Raises:
            HTTPException 404: If cover letter not found
            HTTPException 503: If AI service unavailable
            HTTPException 500: If refinement fails
        """
        start_time = time.time()

        # 1. Get original cover letter and verify ownership
        cover_letter = CoverLetterService.get_cover_letter(db, cover_letter_id, user_id)

        if not cover_letter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cover letter not found"
            )

        # 2. Refine using AI
        try:
            generator = CoverLetterGenerator()
            context = {
                "job_title": cover_letter.job_title,
                "company_name": cover_letter.company_name,
            }

            ai_result = await generator.refine_cover_letter(
                original_text=cover_letter.cover_letter_text,
                refinement_instruction=refinement_instruction,
                context=context,
            )
        except ValueError as e:
            # AI not configured or disabled
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service unavailable: {str(e)}",
            )
        except Exception as e:
            logger.error(f"AI refinement failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cover letter refinement failed. Please try again.",
            )

        # 3. Calculate metrics
        processing_time_ms = int((time.time() - start_time) * 1000)
        word_count = len(ai_result["refined_text"].split())

        logger.info(
            f"Refined cover letter {cover_letter_id} to {word_count} words "
            f"in {processing_time_ms}ms using {ai_result['tokens_used']} tokens"
        )

        # 4. Return refinement result (do NOT save to database automatically)
        # User will decide whether to accept or reject the refinement
        return {
            "original_cover_letter": cover_letter,
            "refined_cover_letter_text": ai_result["refined_text"],
            "refinement_instruction": refinement_instruction,
            "tokens_used": ai_result["tokens_used"],
            "processing_time_ms": processing_time_ms,
            "word_count": word_count,
        }
