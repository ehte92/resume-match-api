"""
Pydantic schemas for AI-generated suggestions.

Used with Instructor library for guaranteed structured outputs from LLMs.
Ensures type-safe, validated responses from OpenRouter API.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    """Single improvement suggestion for the resume."""

    type: Literal["keyword", "metric", "formatting", "section", "action_verb", "impact"] = Field(
        description="Category of suggestion"
    )
    priority: Literal["high", "medium", "low"] = Field(
        description="Priority level based on impact on match score"
    )
    category: str = Field(
        description="Specific sub-category like 'missing_skill', 'quantification', etc."
    )
    issue: str = Field(description="Clear description of what's missing or wrong")
    suggestion: str = Field(description="Actionable recommendation to fix the issue")
    example: str = Field(description="Concrete example of how to implement the suggestion")
    impact: str = Field(description="Expected impact on ATS score or match percentage")


class RewrittenBullet(BaseModel):
    """Before/after bullet point with improvements explained."""

    section: Literal["experience", "education", "projects", "other"] = Field(
        description="Resume section where this bullet appears"
    )
    original: str = Field(description="Original bullet point text")
    improved: str = Field(description="Improved version with stronger language and metrics")
    improvements: List[str] = Field(description="List of specific improvements made")
    keywords_added: List[str] = Field(description="Keywords from job description added to bullet")
    score_improvement: int = Field(
        ge=0, le=20, description="Estimated improvement in match score (0-20 points)"
    )


class AIAnalysisResult(BaseModel):
    """
    Complete AI analysis result with suggestions and rewrites.

    This schema is used with Instructor to guarantee structured output
    from the LLM. Instructor automatically validates responses and retries
    if validation fails.
    """

    suggestions: List[Suggestion] = Field(
        min_length=3, max_length=8, description="3-8 prioritized suggestions for improvement"
    )
    rewritten_bullets: List[RewrittenBullet] = Field(
        min_length=2, max_length=5, description="2-5 rewritten bullet points with improvements"
    )
    overall_assessment: str = Field(description="Brief overall assessment of resume quality")
    estimated_score_gain: int = Field(
        ge=0,
        le=30,
        description="Total estimated match score improvement if all suggestions applied",
    )
