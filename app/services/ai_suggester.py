"""
AI-powered resume suggestion service using OpenRouter + Instructor.

Uses Instructor library for guaranteed structured outputs with automatic
validation, retries, and type safety. Integrates with OpenRouter for access
to multiple AI models (GPT-4o-mini, Claude, Llama, etc.).

Key Features:
- Structured output via Instructor + Pydantic
- Automatic validation and retries
- Token-optimized context formatting
- Graceful error handling
- Cost tracking
"""

import logging
from typing import Dict, List

import instructor
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.ai_suggestions import AIAnalysisResult

logger = logging.getLogger(__name__)


class AISuggester:
    """Generate AI suggestions using OpenRouter with Instructor for structured outputs."""

    def __init__(self):
        """Initialize AI suggester with OpenRouter client + Instructor."""
        self.settings = get_settings()

        if not self.settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not configured - AI suggestions will be disabled")
            self.client = None
            return

        # Create OpenAI client configured for OpenRouter
        openai_client = AsyncOpenAI(
            base_url=self.settings.OPENROUTER_BASE_URL,
            api_key=self.settings.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": self.settings.OPENROUTER_SITE_URL,
                "X-Title": self.settings.OPENROUTER_APP_NAME,
            },
        )

        # Patch with Instructor for structured outputs - this is the magic!
        self.client = instructor.from_openai(openai_client)
        logger.info(f"AI suggester initialized with model: {self.settings.OPENROUTER_MODEL}")

    def _format_resume_context(self, resume_text: str, max_tokens: int = 1500) -> str:
        """
        Format resume text for optimal token usage.

        Uses structured format with clear XML delimiters to help LLM understand context.
        Truncates intelligently if resume is too long to fit in context window.

        Args:
            resume_text: Raw parsed resume text
            max_tokens: Maximum tokens for resume (rough estimate: 1 token ≈ 4 chars)

        Returns:
            Formatted resume context with XML tags
        """
        # Rough token estimation (1 token ≈ 4 characters)
        max_chars = max_tokens * 4

        if len(resume_text) > max_chars:
            # Truncate but keep structure
            resume_text = resume_text[:max_chars] + "\n[... truncated for length ...]"
            logger.info(f"Resume truncated to {max_chars} characters for token optimization")

        # Format with clear XML-style delimiters for LLM parsing
        formatted = f"""<resume>
{resume_text}
</resume>"""
        return formatted

    def _format_job_context(self, job_description: str, missing_keywords: List[str]) -> str:
        """
        Format job description with missing keywords highlighted.

        Args:
            job_description: Target job description
            missing_keywords: Keywords from job not in resume

        Returns:
            Formatted job context with XML tags
        """
        # Limit to top 15 keywords to avoid token bloat
        keywords_str = ", ".join(missing_keywords[:15])

        formatted = f"""<job_description>
{job_description}
</job_description>

<missing_keywords>
{keywords_str}
</missing_keywords>"""
        return formatted

    def _format_ats_issues(self, ats_issues: List[Dict]) -> str:
        """
        Format ATS issues for LLM context.

        Args:
            ats_issues: List of ATS compatibility issues

        Returns:
            Formatted ATS issues with XML tags
        """
        if not ats_issues:
            return "<ats_issues>None detected</ats_issues>"

        # Limit to top 5 issues
        issues_text = "\n".join(
            [
                f"- {issue.get('issue', 'Unknown issue')} "
                f"(Severity: {issue.get('severity', 'unknown')})"
                for issue in ats_issues[:5]
            ]
        )

        return f"""<ats_issues>
{issues_text}
</ats_issues>"""

    async def generate_suggestions(
        self,
        resume_text: str,
        job_description: str,
        missing_keywords: List[str],
        ats_issues: List[Dict],
    ) -> Dict:
        """
        Generate AI-powered suggestions using OpenRouter with structured output.

        Uses Instructor library to guarantee response matches Pydantic schema.
        Automatically validates and retries if response doesn't match schema.

        Args:
            resume_text: Parsed resume text
            job_description: Target job description
            missing_keywords: Keywords from job not in resume
            ats_issues: ATS compatibility issues found

        Returns:
            Dictionary with:
                - suggestions: List of improvement suggestions
                - rewritten_bullets: List of rewritten bullet points
                - overall_assessment: Brief assessment
                - estimated_score_gain: Estimated improvement
                - tokens_used: Token count for cost tracking
        """
        # Check if AI is enabled
        if not self.settings.ENABLE_AI_SUGGESTIONS:
            logger.info("AI suggestions disabled via config")
            return self._empty_response()

        # Check if client is initialized
        if not self.client:
            logger.warning("AI client not initialized - check OPENROUTER_API_KEY")
            return self._empty_response()

        try:
            # Format context for optimal token usage
            resume_context = self._format_resume_context(resume_text)
            job_context = self._format_job_context(job_description, missing_keywords)
            ats_summary = self._format_ats_issues(ats_issues)

            # System prompt - defines the AI's role and output format
            system_prompt = """You are an expert resume consultant and ATS optimization specialist.

Your goal: Help job seekers improve their resumes to pass ATS systems and impress recruiters.

Focus on:
1. Adding missing keywords naturally (don't just list them - show how to integrate)
2. Quantifying achievements with specific metrics and numbers
3. Using strong action verbs (e.g., "Architected" instead of "Made")
4. Improving ATS compatibility (standard headings, clean formatting)
5. Making bullet points more impactful and results-oriented

Provide specific, actionable suggestions with concrete examples.
Each suggestion should be immediately implementable."""

            # User prompt - provides the context
            user_prompt = f"""{resume_context}

{job_context}

{ats_summary}

Analyze this resume against the job description and provide:

1. **3-8 specific improvement suggestions** - Prioritize by impact (high impact first)
2. **2-5 rewritten bullet points** - Show before/after with clear improvements
3. **Overall assessment** - Brief summary of resume strength
4. **Estimated score improvement** - Total potential gain if all suggestions applied (0-30 points)

Focus on the most impactful changes first. Be specific and actionable."""

            logger.info(f"Calling OpenRouter API with model: {self.settings.OPENROUTER_MODEL}")

            # Call OpenRouter via Instructor - automatically handles JSON schema!
            # Instructor magic: response is guaranteed to match AIAnalysisResult schema
            response = await self.client.chat.completions.create(
                model=self.settings.OPENROUTER_MODEL,
                response_model=AIAnalysisResult,  # Instructor guarantees this structure!
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.settings.OPENROUTER_TEMPERATURE,
                max_tokens=self.settings.OPENROUTER_MAX_TOKENS,
            )

            # Response is already a validated Pydantic model!
            logger.info(
                f"AI analysis complete: {len(response.suggestions)} suggestions, "
                f"{len(response.rewritten_bullets)} rewrites, "
                f"estimated gain: +{response.estimated_score_gain} points"
            )

            # Extract token usage from raw response for cost tracking
            # Instructor wraps the response, need to access _raw_response
            tokens_used = 0
            if hasattr(response, "_raw_response"):
                usage = getattr(response._raw_response, "usage", None)
                if usage:
                    tokens_used = getattr(usage, "total_tokens", 0)
                    logger.info(f"Tokens used: {tokens_used}")

            return {
                "suggestions": [s.model_dump() for s in response.suggestions],
                "rewritten_bullets": [b.model_dump() for b in response.rewritten_bullets],
                "overall_assessment": response.overall_assessment,
                "estimated_score_gain": response.estimated_score_gain,
                "tokens_used": tokens_used,
            }

        except ValidationError as e:
            logger.error(f"AI response validation failed: {e}")
            # Instructor will automatically retry, but if all retries fail, return empty
            return self._empty_response()

        except Exception as e:
            logger.error(f"AI suggestion generation failed: {e}", exc_info=True)
            return self._empty_response()

    def _empty_response(self) -> Dict:
        """
        Return empty response structure for graceful degradation.

        Used when AI is disabled or fails - allows analysis to continue
        without AI suggestions.
        """
        return {
            "suggestions": [],
            "rewritten_bullets": [],
            "overall_assessment": "",
            "estimated_score_gain": 0,
            "tokens_used": 0,
        }
