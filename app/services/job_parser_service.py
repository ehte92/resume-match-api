"""
AI-powered job description parser service.
Extracts structured information from job postings (text or URLs).
"""

import json
import logging

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas.job_parser import ParsedJobData

logger = logging.getLogger(__name__)
settings = get_settings()


class JobParserService:
    """Service for parsing job descriptions using AI."""

    def __init__(self):
        """Initialize with OpenRouter client."""
        self.settings = get_settings()

        if not self.settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not configured - job parser disabled")
            self.client = None
            return

        # Create OpenAI client configured for OpenRouter
        self.client = AsyncOpenAI(
            base_url=self.settings.OPENROUTER_BASE_URL,
            api_key=self.settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": self.settings.OPENROUTER_SITE_URL,
                "X-Title": self.settings.OPENROUTER_APP_NAME,
            },
        )
        logger.info("Job parser service initialized")

    async def parse_from_url(self, url: str) -> ParsedJobData:
        """
        Complete pipeline: URL -> HTML -> Text -> AI Parsing.

        Args:
            url: URL of the job posting to parse

        Returns:
            ParsedJobData with extracted information

        Raises:
            ValueError: If URL is invalid or content is too short
            httpx.HTTPError: If URL cannot be fetched
        """
        try:
            # Step 0: Normalize URL (e.g., LinkedIn collection URLs)
            normalized_url = self._normalize_url(url)

            # Step 1: Fetch webpage
            logger.info(f"Fetching job posting from URL: {normalized_url}")
            html = await self._fetch_webpage(normalized_url)

            # Step 2: Extract text from HTML
            logger.info("Extracting text from HTML")
            job_text = self._extract_text_from_html(html)

            if len(job_text) < 100:
                raise ValueError(
                    "Extracted text too short (< 100 chars) - may not be a valid job posting"
                )

            # Step 3: Parse with AI
            logger.info(f"Parsing {len(job_text)} characters of job text with AI")
            parsed_data = await self._parse_with_ai(job_text)

            # Store the original URL and raw text
            parsed_data.source_url = url  # Store original URL, not normalized
            parsed_data.raw_text = job_text[:5000]  # Limit stored text to 5000 chars

            logger.info(
                f"Successfully parsed job: {parsed_data.job_title} at {parsed_data.company_name}"
            )
            return parsed_data

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise ValueError(
                f"Could not fetch job posting from URL. This may happen with JavaScript-heavy sites. "
                f"Try using the direct job posting URL instead of a collection/search URL, "
                f"or paste the job description text directly. Error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error parsing job from URL: {e}")
            raise

    async def parse_from_text(self, job_text: str) -> ParsedJobData:
        """
        Direct text parsing (user pastes job description).

        Args:
            job_text: Job description text to parse

        Returns:
            ParsedJobData with extracted information

        Raises:
            ValueError: If text is too short
        """
        if len(job_text) < 100:
            raise ValueError(
                "Job description too short (minimum 100 characters required for accurate parsing)"
            )

        logger.info(f"Parsing {len(job_text)} characters of job text with AI")
        parsed_data = await self._parse_with_ai(job_text)
        parsed_data.raw_text = job_text[:5000]  # Limit stored text
        return parsed_data

    async def _fetch_webpage(self, url: str) -> str:
        """
        Fetch HTML content from URL with proper headers.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30.0,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _extract_text_from_html(self, html: str) -> str:
        """
        Extract clean text from HTML.

        Removes unwanted elements (scripts, styles, nav, etc.) and tries to
        find the main job description container for cleaner extraction.

        Args:
            html: Raw HTML string

        Returns:
            Clean text with normalized whitespace
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted elements
        for element in soup(
            ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]
        ):
            element.decompose()

        # Try to find main job description container
        # Common class names/patterns used by job sites
        job_selectors = [
            # LinkedIn, Indeed, etc.
            {
                "class_": lambda x: x
                and any(
                    term in x.lower()
                    for term in ["job-description", "description", "posting-description", "jd-info"]
                )
            },
            # Some sites use ID
            {
                "id": lambda x: x
                and any(term in x.lower() for term in ["description", "job-details"])
            },
        ]

        container = None
        for selector in job_selectors:
            container = soup.find("div", **selector) or soup.find("section", **selector)
            if container:
                logger.info(f"Found job description container using selector: {selector}")
                break

        # Fallback to article, main, or body
        if not container:
            container = soup.find("article") or soup.find("main") or soup.body
            logger.info("Using fallback container (article/main/body)")

        # Extract text
        text = container.get_text(separator="\n", strip=True) if container else ""

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n".join(lines)

        return clean_text

    def _normalize_url(self, url: str) -> str:
        """
        Normalize LinkedIn collection URLs to direct job view URLs.

        Converts URLs like:
        https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4309711459

        To:
        https://www.linkedin.com/jobs/view/4309711459

        Args:
            url: Original URL that may be a collection URL

        Returns:
            Normalized URL for direct job access
        """
        from urllib.parse import urlparse, parse_qs

        # Check if this is a LinkedIn collection URL
        if "linkedin.com/jobs/collections" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # Extract currentJobId parameter
            if "currentJobId" in query_params:
                job_id = query_params["currentJobId"][0]
                normalized_url = f"https://www.linkedin.com/jobs/view/{job_id}"
                logger.info(f"Normalized LinkedIn collection URL: {url} -> {normalized_url}")
                return normalized_url

        # Return original URL if not a collection URL
        return url

    async def _parse_with_ai(self, job_text: str) -> ParsedJobData:
        """
        Use OpenAI to extract structured data from job text.

        Args:
            job_text: Clean job description text

        Returns:
            ParsedJobData with extracted fields

        Raises:
            ValueError: If AI client not initialized
            Exception: If parsing fails
        """
        if not self.client:
            raise ValueError("AI client not initialized - check OPENROUTER_API_KEY")

        if not self.settings.ENABLE_AI_SUGGESTIONS:
            raise ValueError("AI suggestions disabled in configuration")

        try:
            system_prompt = """You are a precise job description parser. Extract structured information from job postings.
Return ONLY valid JSON matching the exact schema provided. Be thorough in extracting skills and requirements.
If a field is not found in the job posting, use null or an empty array as appropriate."""

            user_prompt = f"""Extract information from this job posting and return as JSON:

{{
  "job_title": "exact job title or null",
  "company_name": "company name or null",
  "location": "job location if mentioned or null",
  "key_skills": ["list", "of", "required", "technical", "skills"],
  "responsibilities": ["main", "job", "duties"],
  "qualifications": ["required", "qualifications"],
  "nice_to_have": ["preferred", "qualifications"],
  "tone": "professional" | "enthusiastic" | "balanced",
  "experience_level": "junior" | "mid" | "senior" | "lead" | null
}}

Guidelines:
- For key_skills, extract specific technologies, programming languages, tools, frameworks
- For tone, analyze the writing style: formal/traditional = professional, energetic/exciting = enthusiastic, mix = balanced
- For experience_level, infer from years of experience mentioned or seniority in title
- Be thorough but concise

Job Posting:
{job_text[:4000]}"""  # Limit to 4000 chars to stay within token limits

            logger.info("Calling OpenRouter AI for job parsing")
            response = await self.client.chat.completions.create(
                model="openai/gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,  # Low temperature for consistent extraction
                response_format={"type": "json_object"},  # Ensure JSON response
            )

            parsed_json = json.loads(response.choices[0].message.content)
            logger.info(f"Successfully parsed job data: {parsed_json.get('job_title', 'Unknown')}")

            # Create ParsedJobData with the JSON response
            # Set raw_text to empty for now, will be set by caller
            parsed_json["raw_text"] = ""
            return ParsedJobData(**parsed_json)

        except Exception as e:
            logger.error(f"Job parsing failed: {e}", exc_info=True)
            raise


# Global instance
_job_parser_service = None


def get_job_parser_service() -> JobParserService:
    """Get or create global JobParserService instance."""
    global _job_parser_service
    if _job_parser_service is None:
        _job_parser_service = JobParserService()
    return _job_parser_service
