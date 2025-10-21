"""
Job description parser API endpoints.
Provides REST API for AI-powered job description parsing from text or URLs.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.job_parser import JobParseRequest, ParsedJobData
from app.services.job_parser_service import get_job_parser_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@router.post(
    "/parse",
    response_model=ParsedJobData,
    summary="Parse job description",
    description="Extract structured information from a job posting (text or URL) using AI",
)
@limiter.limit("10/minute")
async def parse_job_description(
    request: Request,
    parse_request: JobParseRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Parse job description and extract structured information.

    This endpoint uses AI to extract key information from job postings:
    - Job title and company name
    - Required skills and technologies
    - Responsibilities and qualifications
    - Inferred tone and experience level

    Supports two input modes:
    1. **URL**: Fetches and parses the job posting from the provided URL
    2. **Text**: Parses job description text directly

    Request body:
    - source_type: "url" or "text"
    - content: URL or job description text

    Returns:
    - Structured job data with all extracted fields

    Raises:
    - 400: If URL is invalid, unreachable, or content is too short
    - 503: If AI service is unavailable
    - 500: If parsing fails

    Rate limit: 10 requests per minute

    Examples:
    ```json
    // Parse from URL
    {
      "source_type": "url",
      "content": "https://www.linkedin.com/jobs/view/3845729183"
    }

    // Parse from text
    {
      "source_type": "text",
      "content": "Senior Software Engineer\\n\\nWe are seeking an experienced engineer..."
    }
    ```
    """
    try:
        parser_service = get_job_parser_service()

        if parse_request.source_type == "url":
            logger.info(f"Parsing job from URL: {parse_request.content[:100]}...")
            parsed_data = await parser_service.parse_from_url(parse_request.content)
        else:  # text
            logger.info(f"Parsing job from text ({len(parse_request.content)} chars)")
            parsed_data = await parser_service.parse_from_text(parse_request.content)

        logger.info(
            f"Successfully parsed job: {parsed_data.job_title} at {parsed_data.company_name}"
        )
        return parsed_data

    except ValueError as e:
        # Client errors (invalid URL, short text, etc.)
        logger.warning(f"Job parsing validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        # Server errors (AI service down, parsing failed, etc.)
        logger.error(f"Job parsing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse job description. Please try again or paste the text directly if you used a URL.",
        )
