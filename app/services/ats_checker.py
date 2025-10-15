"""
ATS Checker Service for Resume Optimization.

Analyzes resumes for ATS (Applicant Tracking System) compatibility issues.
Checks for missing sections, formatting problems, and calculates an ATS score.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class ATSChecker:
    """
    Analyzes resumes for ATS compatibility.

    Checks for critical sections, formatting issues, and provides
    recommendations for improving ATS compatibility.
    """

    def __init__(self):
        """Initialize the ATSChecker."""
        logger.info("ATSChecker initialized")

    def check_ats_compatibility(self, parsed_resume: Dict) -> Dict:
        """
        Check ATS compatibility of a parsed resume.

        Args:
            parsed_resume: Dictionary containing parsed resume data with keys:
                - raw_text: Full text content of resume
                - sections: Dict with section names as keys

        Returns:
            Dictionary with ATS compatibility report:
            {
                "ats_score": int (0-100),
                "issues": List[Dict],
                "issue_count": int,
                "recommendations": List[str],
                "passed": bool
            }

        Example:
            >>> checker = ATSChecker()
            >>> parsed = {
            ...     "raw_text": "Clean resume text",
            ...     "sections": {
            ...         "experience": ["Job 1"],
            ...         "education": ["Degree 1"],
            ...         "skills": ["Python"]
            ...     }
            ... }
            >>> result = checker.check_ats_compatibility(parsed)
            >>> print(f"ATS Score: {result['ats_score']}/100")
        """
        logger.info("Starting ATS compatibility check")

        # Step 1: Check for missing sections
        section_issues = self._check_sections(parsed_resume)

        # Step 2: Check for formatting issues
        raw_text = parsed_resume.get("raw_text", "")
        formatting_issues = self._check_formatting_issues(raw_text)

        # Step 3: Combine all issues
        all_issues = section_issues + formatting_issues

        # Step 4: Calculate ATS score
        ats_score = self._calculate_ats_score(all_issues)

        # Step 5: Extract recommendations
        recommendations = [
            issue["recommendation"] for issue in all_issues if "recommendation" in issue
        ]

        # Step 6: Determine pass/fail (threshold: 70)
        passed = ats_score >= 70

        result = {
            "ats_score": ats_score,
            "issues": all_issues,
            "issue_count": len(all_issues),
            "recommendations": recommendations,
            "passed": passed,
        }

        logger.info(
            f"ATS check complete: Score={ats_score}/100, Issues={len(all_issues)}, Passed={passed}"
        )
        return result

    def _check_sections(self, parsed_resume: Dict) -> List[Dict]:
        """
        Check for presence of critical resume sections.

        Args:
            parsed_resume: Dictionary containing parsed resume data

        Returns:
            List of issue dictionaries for missing sections

        Example:
            >>> issues = checker._check_sections({"sections": {"skills": ["Python"]}})
            >>> # Returns issues for missing Experience and Education
        """
        issues = []

        # Get sections from parsed resume
        sections = parsed_resume.get("sections", {})

        # Define critical sections with severity levels
        critical_sections = {
            "experience": {
                "severity": "high",
                "message": "Missing 'Experience' section",
                "recommendation": (
                    "Add a detailed work experience section with job titles, "
                    "companies, dates, and key achievements"
                ),
            },
            "education": {
                "severity": "high",
                "message": "Missing 'Education' section",
                "recommendation": (
                    "Add an education section with degrees, institutions, " "and graduation dates"
                ),
            },
            "skills": {
                "severity": "medium",
                "message": "Missing 'Skills' section",
                "recommendation": "Add a skills section listing relevant technical and soft skills",
            },
            "summary": {
                "severity": "low",
                "message": "Missing 'Summary' or 'Objective' section",
                "recommendation": (
                    "Consider adding a professional summary or career objective "
                    "at the top of your resume"
                ),
            },
        }

        # Check for missing sections
        for section_name, section_info in critical_sections.items():
            # Check if section exists and has content
            section_content = sections.get(section_name, [])

            # Section is missing if it doesn't exist or is empty
            if not section_content or (
                isinstance(section_content, list) and len(section_content) == 0
            ):
                issues.append(
                    {
                        "type": "missing_section",
                        "severity": section_info["severity"],
                        "section": section_name.capitalize(),
                        "message": section_info["message"],
                        "recommendation": section_info["recommendation"],
                    }
                )

        logger.info(f"Section check found {len(issues)} issues")
        return issues

    def _check_formatting_issues(self, text: str) -> List[Dict]:
        """
        Check for ATS-unfriendly formatting patterns.

        Args:
            text: Raw resume text to analyze

        Returns:
            List of formatting issue dictionaries

        Example:
            >>> text = "● EXPERIENCE ●\\nPhoto: headshot.jpg"
            >>> issues = checker._check_formatting_issues(text)
            >>> # Returns issues for special chars and images
        """
        issues = []

        if not text:
            return issues

        # Normalize text to lowercase for keyword checking
        text_lower = text.lower()

        # Check 1: Special characters/bullets in text
        special_chars_pattern = r"[✓✔✗✘●•○◦▪▫◾◽⬛⬜]"
        if re.search(special_chars_pattern, text):
            issues.append(
                {
                    "type": "formatting_issue",
                    "severity": "medium",
                    "issue": "special_characters",
                    "message": "Special characters or bullets detected in resume",
                    "recommendation": (
                        "Use simple text for section headings "
                        "(e.g., 'EXPERIENCE' instead of '● Experience')"
                    ),
                }
            )

        # Check 2: Table/column indicators (pipe characters)
        table_pattern = r"\|\s*.*\s*\|"
        if re.search(table_pattern, text) or "table" in text_lower or "column" in text_lower:
            issues.append(
                {
                    "type": "formatting_issue",
                    "severity": "low",
                    "issue": "table_columns",
                    "message": "Resume may contain tables or columns",
                    "recommendation": (
                        "Avoid tables and multi-column layouts; use simple "
                        "single-column format for better ATS compatibility"
                    ),
                }
            )

        # Check 3: Image/graphics keywords
        image_keywords = [
            "image",
            "photo",
            "picture",
            "graphic",
            ".jpg",
            ".png",
            ".jpeg",
            ".gif",
        ]
        if any(keyword in text_lower for keyword in image_keywords):
            issues.append(
                {
                    "type": "formatting_issue",
                    "severity": "medium",
                    "issue": "images_graphics",
                    "message": "Resume may contain images or graphics",
                    "recommendation": (
                        "Remove images, photos, and graphics; "
                        "ATS systems cannot parse visual content"
                    ),
                }
            )

        # Check 4: Header/footer indicators
        header_footer_keywords = ["header", "footer"]
        if any(keyword in text_lower for keyword in header_footer_keywords):
            issues.append(
                {
                    "type": "formatting_issue",
                    "severity": "low",
                    "issue": "header_footer",
                    "message": "Resume may have headers or footers",
                    "recommendation": (
                        "Avoid putting important information in headers or footers; "
                        "ATS may not parse them correctly"
                    ),
                }
            )

        # Check 5: Complex spacing (3+ consecutive spaces)
        complex_spacing_pattern = r"\s{3,}"
        if re.search(complex_spacing_pattern, text):
            issues.append(
                {
                    "type": "formatting_issue",
                    "severity": "low",
                    "issue": "complex_spacing",
                    "message": "Resume may have complex spacing or formatting",
                    "recommendation": (
                        "Use consistent single spaces between words; "
                        "avoid excessive spacing for alignment"
                    ),
                }
            )

        logger.info(f"Formatting check found {len(issues)} issues")
        return issues

    def _calculate_ats_score(self, issues: List[Dict]) -> int:
        """
        Calculate ATS compatibility score based on issues found.

        Args:
            issues: List of issue dictionaries with "severity" key

        Returns:
            Integer score from 0-100

        Algorithm:
            - Start at 100
            - Deduct points: high (-10), medium (-5), low (-2)
            - Minimum score is 0

        Example:
            >>> issues = [{"severity": "high"}, {"severity": "medium"}]
            >>> score = checker._calculate_ats_score(issues)
            >>> print(score)  # 85 (100 - 10 - 5)
        """
        # Start with perfect score
        score = 100

        # Deduct points based on severity
        for issue in issues:
            severity = issue.get("severity", "low")

            if severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            elif severity == "low":
                score -= 2

        # Ensure score doesn't go below 0
        score = max(0, score)

        logger.info(f"Calculated ATS score: {score}/100 (based on {len(issues)} issues)")
        return score
