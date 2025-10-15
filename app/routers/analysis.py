"""
Analysis Router - Resume Analysis Endpoints.

Combines ResumeParser, KeywordAnalyzer, and ATSChecker to provide
complete resume analysis against job descriptions.
"""

import logging
import time
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse
from app.services.ats_checker import ATSChecker
from app.services.keyword_analyzer import KeywordAnalyzer
from app.services.resume_parser import ResumeParser
from app.utils.file_handler import (
    calculate_file_hash,
    delete_temp_file,
    save_temp_file,
    validate_file_type,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    file: Optional[UploadFile] = File(None),
    resume_id: Optional[UUID] = Form(None),
    job_description: str = Form(...),
    job_title: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new resume analysis (Hybrid Endpoint).

    Supports two workflows:
    1. Quick Analysis: Upload file + job description in one step
    2. Power User: Analyze existing resume_id from library against job description

    The endpoint accepts EITHER 'file' OR 'resume_id' (mutually exclusive).
    If a duplicate file is uploaded, it will be detected via SHA-256 hash and reused.

    Args:
        file: Resume file (PDF or DOCX, max 5MB) - provide EITHER file OR resume_id
        resume_id: UUID of existing resume from library - provide EITHER file OR resume_id
        job_description: Job description text (required)
        job_title: Optional job title
        company_name: Optional company name
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        AnalysisResponse with complete analysis results

    Raises:
        400: If both file and resume_id provided, or neither provided
        400: If file type is invalid
        404: If resume_id not found or doesn't belong to user
        500: If analysis processing fails
    """
    start_time = time.time()
    logger.info(f"Starting analysis for user {current_user.id}")

    # Treat empty-filename files as no file (for power user workflow with multipart/form-data)
    has_file = file is not None and file.filename
    has_resume_id = resume_id is not None

    # Step 1: Validate input - exactly one of file or resume_id must be provided
    if has_file == has_resume_id:
        logger.warning(
            "Invalid request: must provide either file or resume_id, not both or neither"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either 'file' or 'resume_id', not both or neither",
        )

    temp_path = None  # Track temp file for cleanup

    try:
        # Branch 1: Handle file upload (Quick Analysis or first-time upload)
        # Check if file has content (not just an empty placeholder for multipart form)
        if file and file.filename:
            logger.info("Processing new file upload...")

            # Validate file type
            if not validate_file_type(file.content_type):
                logger.warning(f"Invalid file type: {file.content_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Only PDF and DOCX files are supported.",
                )

            # Calculate file hash FIRST (before file is read by save_temp_file)
            file_hash = await calculate_file_hash(file)
            logger.info(f"Calculated file hash: {file_hash[:16]}...")

            # Save temp file SECOND
            temp_path = await save_temp_file(file)
            logger.info(f"Saved temp file: {temp_path}")

            # Check for existing resume with same hash (deduplication)
            existing_resume = (
                db.query(Resume)
                .filter(Resume.user_id == current_user.id, Resume.file_hash == file_hash)
                .first()
            )

            if existing_resume:
                # Reuse existing resume (duplicate detected)
                resume = existing_resume
                logger.info(
                    f"Duplicate file detected - reusing existing resume {resume.id} "
                    f"(original: {resume.file_name})"
                )
            else:
                # Parse and store new resume
                logger.info("Parsing new resume...")
                parser = ResumeParser()
                file_type_simple = "pdf" if "pdf" in file.content_type else "docx"
                parsed_resume = parser.parse(temp_path, file_type_simple)

                # Save resume to database
                logger.info("Saving new resume to database...")
                resume = Resume(
                    user_id=current_user.id,
                    file_name=file.filename,
                    file_path=temp_path,
                    file_type=file_type_simple,
                    file_size=file.size,
                    file_hash=file_hash,  # NEW: Store hash for deduplication
                    parsed_text=parsed_resume.get("raw_text", ""),
                    parsed_data=parsed_resume,
                    storage_backend="local",
                    storage_url=None,
                    storage_key=None,
                )
                db.add(resume)
                db.flush()  # Get resume.id without committing
                logger.info(f"New resume saved with ID: {resume.id}")

        # Branch 2: Handle resume_id (Power User workflow)
        else:
            logger.info(f"Using existing resume from library: {resume_id}")

            # Fetch existing resume from library
            resume = (
                db.query(Resume)
                .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
                .first()
            )

            if not resume:
                logger.warning(
                    f"Resume {resume_id} not found or access denied for user {current_user.id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Resume not found or access denied",
                )

            logger.info(
                f"Using existing resume {resume.id} (file: {resume.file_name}, "
                f"uploaded: {resume.created_at})"
            )

        # Step 2: Keyword analysis (using resume's parsed text)
        logger.info("Running keyword analysis...")
        analyzer = KeywordAnalyzer()
        keyword_result = analyzer.calculate_match_score(resume.parsed_text or "", job_description)
        logger.info(f"Keyword match score: {keyword_result['score']}")

        # Step 3: ATS compatibility check (using resume's parsed data)
        logger.info("Running ATS compatibility check...")
        checker = ATSChecker()
        ats_result = checker.check_ats_compatibility(resume.parsed_data or {})
        logger.info(f"ATS score: {ats_result['ats_score']}")

        # Step 4: Calculate overall match score (weighted average)
        # 60% keyword matching + 40% ATS compatibility
        match_score = (keyword_result["score"] * 0.6) + (ats_result["ats_score"] * 0.4)
        logger.info(f"Overall match score: {match_score}")

        # Step 5: Create analysis record
        processing_time = int((time.time() - start_time) * 1000)
        logger.info("Creating analysis record...")

        analysis = ResumeAnalysis(
            user_id=current_user.id,
            resume_id=resume.id,
            job_description=job_description,
            job_title=job_title,
            company_name=company_name,
            match_score=round(match_score, 2),
            ats_score=ats_result["ats_score"],
            semantic_similarity=keyword_result["score"],
            matching_keywords=keyword_result["matched_keywords"],
            missing_keywords=keyword_result["missing_keywords"],
            ats_issues=ats_result["issues"],
            ai_suggestions=None,  # Phase 14 - OpenAI integration
            rewritten_bullets=None,  # Phase 14 - OpenAI integration
            processing_time_ms=processing_time,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        logger.info(
            f"Analysis created successfully: ID={analysis.id}, "
            f"Score={analysis.match_score}, Time={processing_time}ms"
        )

        return analysis

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )

    finally:
        # Cleanup temp file (only if new file was uploaded)
        if temp_path:
            delete_temp_file(temp_path)
            logger.info("Temp file cleaned up")


@router.get("/", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List user's analysis history with pagination.

    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 10, max: 100)
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        AnalysisListResponse with paginated list of analyses
    """
    logger.info(f"Listing analyses for user {current_user.id}: page={page}, size={page_size}")

    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10

    # Calculate offset
    skip = (page - 1) * page_size

    # Query analyses for current user
    analyses = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == current_user.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Get total count
    total = db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == current_user.id).count()

    logger.info(f"Found {len(analyses)} analyses (total: {total})")

    return {"analyses": analyses, "total": total, "page": page, "page_size": page_size}


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific analysis by ID.

    Args:
        analysis_id: UUID of the analysis
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        AnalysisResponse with complete analysis details

    Raises:
        404: Analysis not found
        403: Not authorized to access this analysis
    """
    logger.info(f"Getting analysis {analysis_id} for user {current_user.id}")

    # Query analysis
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    # Verify ownership
    if analysis.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} tried to access analysis {analysis_id} "
            f"owned by {analysis.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this analysis",
        )

    logger.info(f"Analysis {analysis_id} retrieved successfully")
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an analysis.

    Args:
        analysis_id: UUID of the analysis to delete
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        404: Analysis not found
        403: Not authorized to delete this analysis
    """
    logger.info(f"Deleting analysis {analysis_id} for user {current_user.id}")

    # Query analysis
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()

    if not analysis:
        logger.warning(f"Analysis {analysis_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    # Verify ownership
    if analysis.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} tried to delete analysis {analysis_id} "
            f"owned by {analysis.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this analysis",
        )

    # Delete analysis
    db.delete(analysis)
    db.commit()

    logger.info(f"Analysis {analysis_id} deleted successfully")
    return None
