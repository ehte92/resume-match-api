"""
AI-powered cover letter generator using OpenRouter + Instructor.

Generates personalized cover letters based on resume and job description
with guaranteed structured output format.
"""

import logging
from typing import Dict, Optional

import instructor
from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas.ai_suggestions import CoverLetterStructure

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    """Generate cover letters using AI with structured output."""

    def __init__(self):
        """Initialize with OpenRouter client."""
        self.settings = get_settings()

        if not self.settings.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not configured - cover letter generation disabled")
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

        # Patch with Instructor for structured outputs
        self.client = instructor.from_openai(openai_client)
        logger.info("Cover letter generator initialized")

    def _get_word_target(self, length: str) -> int:
        """Get target word count based on length parameter."""
        return {"short": 250, "medium": 350, "long": 500}.get(length, 350)

    def _get_tone_instructions(self, tone: str) -> str:
        """Get tone-specific writing instructions."""
        tone_map = {
            "professional": "formal and polished. Focus on qualifications and achievements. Use traditional business language.",
            "enthusiastic": "energetic and passionate. Show genuine excitement about the opportunity. Use dynamic, engaging language.",
            "balanced": "professional yet personable. Balance credentials with personality. Show warmth while maintaining professionalism.",
        }
        return tone_map.get(tone, tone_map["professional"])

    def _build_prompts(
        self,
        resume_text: str,
        job_description: str,
        job_title: Optional[str],
        company_name: Optional[str],
        tone: str,
        length: str,
    ) -> tuple[str, str]:
        """Build system and user prompts for AI generation."""
        word_target = self._get_word_target(length)
        tone_instructions = self._get_tone_instructions(tone)

        system_prompt = f"""You are an expert cover letter writer specializing in compelling, ATS-friendly cover letters that get interviews.

Write a {tone} cover letter targeting approximately {word_target} words.
The tone should be {tone_instructions}

Structure Requirements:
1. Opening paragraph - Hook with enthusiasm and direct relevance to the role
2. Body paragraphs (1-4 depending on length) - Map resume experience to job requirements with specific, quantifiable examples
3. Closing paragraph - Strong call to action expressing interest in next steps
4. Signature line - Professional closing with candidate's name from resume

Key Principles:
- Use specific examples and achievements from the resume
- Match important keywords from job description naturally (don't just list them)
- Quantify accomplishments where possible (percentages, numbers, scale)
- Show genuine interest and knowledge about the company/role
- Be concise, impactful, and avoid generic phrases
- Maintain appropriate formality for the tone
- End with clear call to action"""

        # Truncate resume to fit in context (~2000 chars = ~500 tokens)
        resume_snippet = resume_text[:2000]
        if len(resume_text) > 2000:
            resume_snippet += "\n[... resume truncated for length ...]"

        user_prompt = f"""<resume>
{resume_snippet}
</resume>

<job_description>
{job_description}
</job_description>

<job_details>
Job Title: {job_title or 'Not specified'}
Company: {company_name or 'Not specified'}
</job_details>

Generate a compelling cover letter that positions the candidate as an ideal fit for this role. Use the resume to provide specific examples that match the job requirements."""

        return system_prompt, user_prompt

    async def generate_cover_letter(
        self,
        resume_text: str,
        job_description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        tone: str = "professional",
        length: str = "medium",
    ) -> Dict:
        """
        Generate cover letter with AI.

        Args:
            resume_text: Parsed resume text
            job_description: Full job description
            job_title: Job title (optional)
            company_name: Company name (optional)
            tone: Writing tone (professional, enthusiastic, balanced)
            length: Target length (short, medium, long)

        Returns:
            Dictionary with:
                - cover_letter_text: Full generated cover letter
                - tokens_used: Token count for cost tracking

        Raises:
            ValueError: If AI client not initialized
            Exception: If generation fails
        """
        if not self.client:
            raise ValueError("AI client not initialized - check OPENROUTER_API_KEY")

        if not self.settings.ENABLE_AI_SUGGESTIONS:
            raise ValueError("AI suggestions disabled in configuration")

        try:
            system_prompt, user_prompt = self._build_prompts(
                resume_text, job_description, job_title, company_name, tone, length
            )

            logger.info(
                f"Generating {tone} {length} cover letter for {job_title or 'position'} "
                f"at {company_name or 'company'}"
            )

            # Call AI with structured output via Instructor
            response = await self.client.chat.completions.create(
                model=self.settings.OPENROUTER_MODEL,
                response_model=CoverLetterStructure,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # Slightly higher for creative writing
                max_tokens=1500,  # Enough for long cover letters
            )

            # Assemble structured response into full text
            full_text = f"{response.opening_paragraph}\n\n"
            full_text += "\n\n".join(response.body_paragraphs)
            full_text += f"\n\n{response.closing_paragraph}\n\n{response.signature_line}"

            # Extract token usage from raw response
            tokens_used = 0
            if hasattr(response, "_raw_response"):
                usage = getattr(response._raw_response, "usage", None)
                if usage:
                    tokens_used = getattr(usage, "total_tokens", 0)

            word_count = len(full_text.split())
            logger.info(
                f"Generated {word_count} word cover letter using {tokens_used} tokens "
                f"(target: {self._get_word_target(length)} words)"
            )

            return {"cover_letter_text": full_text, "tokens_used": tokens_used}

        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}", exc_info=True)
            raise

    async def refine_cover_letter(
        self, original_text: str, refinement_instruction: str, context: Optional[Dict] = None
    ) -> Dict:
        """
        Refine an existing cover letter based on specific instructions.

        Args:
            original_text: The original cover letter text to refine
            refinement_instruction: User instructions for refinement
            context: Optional dict with job_title, company_name for better context

        Returns:
            Dictionary with:
                - refined_text: The improved cover letter
                - tokens_used: Token count for cost tracking

        Raises:
            ValueError: If AI client not initialized
            Exception: If refinement fails
        """
        if not self.client:
            raise ValueError("AI client not initialized - check OPENROUTER_API_KEY")

        if not self.settings.ENABLE_AI_SUGGESTIONS:
            raise ValueError("AI suggestions disabled in configuration")

        try:
            # Build context information
            context_info = ""
            if context:
                job_title = context.get("job_title")
                company_name = context.get("company_name")
                if job_title or company_name:
                    context_info = (
                        f"\n\nContext: This is a cover letter for {job_title or 'a position'}"
                    )
                    if company_name:
                        context_info += f" at {company_name}"

            system_prompt = f"""You are an expert cover letter editor specializing in refining and improving cover letters.

Your task is to refine the provided cover letter based on the user's specific instructions while:
1. Maintaining the core message and key achievements
2. Preserving the overall structure (opening, body, closing, signature)
3. Keeping the professional tone appropriate for job applications
4. Ensuring all improvements are natural and authentic
5. Maintaining or improving ATS-friendliness

Apply the refinement instruction precisely but thoughtfully. If asked to shorten, be concise without losing impact. If asked to emphasize something, highlight it effectively without being repetitive.{context_info}"""

            user_prompt = f"""<original_cover_letter>
{original_text}
</original_cover_letter>

<refinement_instruction>
{refinement_instruction}
</refinement_instruction>

Please refine the cover letter according to the instruction above. Return the complete refined version."""

            logger.info(
                f"Refining cover letter with instruction: {refinement_instruction[:100]}..."
            )

            # Call AI with structured output
            response = await self.client.chat.completions.create(
                model=self.settings.OPENROUTER_MODEL,
                response_model=CoverLetterStructure,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            # Assemble structured response into full text
            refined_text = f"{response.opening_paragraph}\n\n"
            refined_text += "\n\n".join(response.body_paragraphs)
            refined_text += f"\n\n{response.closing_paragraph}\n\n{response.signature_line}"

            # Extract token usage
            tokens_used = 0
            if hasattr(response, "_raw_response"):
                usage = getattr(response._raw_response, "usage", None)
                if usage:
                    tokens_used = getattr(usage, "total_tokens", 0)

            word_count = len(refined_text.split())
            logger.info(f"Refined cover letter: {word_count} words using {tokens_used} tokens")

            return {"refined_text": refined_text, "tokens_used": tokens_used}

        except Exception as e:
            logger.error(f"Cover letter refinement failed: {e}", exc_info=True)
            raise
