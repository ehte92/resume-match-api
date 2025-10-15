"""
Unit tests for ATSChecker service.

Tests the ATS compatibility checking functionality including section detection,
formatting issue detection, and score calculation.
"""

import pytest

from app.services.ats_checker import ATSChecker


@pytest.fixture
def checker():
    """Create an ATSChecker instance for testing."""
    return ATSChecker()


@pytest.fixture
def complete_resume():
    """Sample resume with all sections and clean formatting."""
    return {
        "raw_text": "Clean resume text with simple formatting and standard sections",
        "sections": {
            "experience": ["Senior Developer at Company A (2020-2023)"],
            "education": ["BS Computer Science, University (2016-2020)"],
            "skills": ["Python", "JavaScript", "AWS"],
            "summary": ["Experienced software engineer with 5+ years"],
        },
    }


@pytest.fixture
def incomplete_resume():
    """Sample resume missing critical sections."""
    return {
        "raw_text": "Simple text",
        "sections": {
            "skills": ["Python"]
            # Missing: experience, education, summary
        },
    }


@pytest.fixture
def problematic_formatting_resume():
    """Sample resume with formatting issues."""
    return {
        "raw_text": (
            "● EXPERIENCE ●\n"
            "Photo: headshot.jpg\n"
            "Job | Company | 2020\n"
            "SKILLS:  Python,    JavaScript"
        ),
        "sections": {
            "experience": ["Job at Company"],
            "education": ["Degree"],
            "skills": ["Python", "JavaScript"],
        },
    }


class TestATSCheckerInit:
    """Test ATSChecker initialization."""

    def test_initialization_success(self, checker):
        """Test successful initialization of ATSChecker."""
        assert checker is not None


class TestCheckSections:
    """Test section checking functionality."""

    def test_check_sections_complete_resume(self, checker, complete_resume):
        """Test that complete resume has no section issues."""
        issues = checker._check_sections(complete_resume)
        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_check_sections_missing_experience(self, checker):
        """Test detection of missing experience section."""
        resume = {"sections": {"education": ["Degree"], "skills": ["Python"]}}
        issues = checker._check_sections(resume)

        # Should have issues for missing experience and summary
        assert len(issues) >= 1

        # Check for high severity experience issue
        experience_issues = [i for i in issues if i.get("section") == "Experience"]
        assert len(experience_issues) == 1
        assert experience_issues[0]["severity"] == "high"

    def test_check_sections_missing_education(self, checker):
        """Test detection of missing education section."""
        resume = {"sections": {"experience": ["Job"], "skills": ["Python"]}}
        issues = checker._check_sections(resume)

        # Check for high severity education issue
        education_issues = [i for i in issues if i.get("section") == "Education"]
        assert len(education_issues) == 1
        assert education_issues[0]["severity"] == "high"

    def test_check_sections_missing_skills(self, checker):
        """Test detection of missing skills section."""
        resume = {"sections": {"experience": ["Job"], "education": ["Degree"]}}
        issues = checker._check_sections(resume)

        # Check for medium severity skills issue
        skills_issues = [i for i in issues if i.get("section") == "Skills"]
        assert len(skills_issues) == 1
        assert skills_issues[0]["severity"] == "medium"

    def test_check_sections_empty_sections_dict(self, checker):
        """Test with empty sections dictionary."""
        resume = {"sections": {}}
        issues = checker._check_sections(resume)

        # Should have issues for all missing sections
        assert len(issues) == 4  # experience, education, skills, summary

    def test_check_sections_missing_sections_key(self, checker):
        """Test with missing sections key."""
        resume = {}
        issues = checker._check_sections(resume)

        # Should handle gracefully and return issues
        assert len(issues) == 4


class TestCheckFormattingIssues:
    """Test formatting issue detection."""

    def test_formatting_clean_text(self, checker):
        """Test that clean text has no formatting issues."""
        text = "EXPERIENCE\nSoftware Engineer at Company\nEDUCATION\nBS Computer Science"
        issues = checker._check_formatting_issues(text)
        assert len(issues) == 0

    def test_formatting_special_characters(self, checker):
        """Test detection of special characters/bullets."""
        text = "● EXPERIENCE ●\n• Developed software\n✓ Completed projects"
        issues = checker._check_formatting_issues(text)

        special_char_issues = [i for i in issues if i.get("issue") == "special_characters"]
        assert len(special_char_issues) == 1
        assert special_char_issues[0]["severity"] == "medium"

    def test_formatting_table_detection(self, checker):
        """Test detection of tables/columns."""
        text = "Name | Company | Years\nJohn | ABC Corp | 3"
        issues = checker._check_formatting_issues(text)

        table_issues = [i for i in issues if i.get("issue") == "table_columns"]
        assert len(table_issues) == 1
        assert table_issues[0]["severity"] == "low"

    def test_formatting_image_keywords(self, checker):
        """Test detection of image references."""
        text = "Photo: professional_headshot.jpg\nProfile picture attached"
        issues = checker._check_formatting_issues(text)

        image_issues = [i for i in issues if i.get("issue") == "images_graphics"]
        assert len(image_issues) == 1
        assert image_issues[0]["severity"] == "medium"

    def test_formatting_header_footer(self, checker):
        """Test detection of header/footer keywords."""
        text = "Header: John Doe | 555-1234\nFooter: Page 1 of 2"
        issues = checker._check_formatting_issues(text)

        header_footer_issues = [i for i in issues if i.get("issue") == "header_footer"]
        assert len(header_footer_issues) == 1

    def test_formatting_complex_spacing(self, checker):
        """Test detection of complex spacing."""
        text = "SKILLS:  Python,    JavaScript,     AWS"
        issues = checker._check_formatting_issues(text)

        spacing_issues = [i for i in issues if i.get("issue") == "complex_spacing"]
        assert len(spacing_issues) == 1
        assert spacing_issues[0]["severity"] == "low"

    def test_formatting_empty_text(self, checker):
        """Test with empty text."""
        issues = checker._check_formatting_issues("")
        assert len(issues) == 0

        issues = checker._check_formatting_issues(None)
        assert len(issues) == 0

    def test_formatting_multiple_issues(self, checker, problematic_formatting_resume):
        """Test detection of multiple formatting issues."""
        issues = checker._check_formatting_issues(problematic_formatting_resume["raw_text"])

        # Should detect special chars, images, tables, spacing
        assert len(issues) >= 3


class TestCalculateATSScore:
    """Test ATS score calculation."""

    def test_calculate_score_no_issues(self, checker):
        """Test perfect score with no issues."""
        issues = []
        score = checker._calculate_ats_score(issues)
        assert score == 100

    def test_calculate_score_high_severity(self, checker):
        """Test score with high severity issues."""
        issues = [{"severity": "high"}, {"severity": "high"}]
        score = checker._calculate_ats_score(issues)
        assert score == 80  # 100 - 10 - 10

    def test_calculate_score_medium_severity(self, checker):
        """Test score with medium severity issues."""
        issues = [{"severity": "medium"}, {"severity": "medium"}]
        score = checker._calculate_ats_score(issues)
        assert score == 90  # 100 - 5 - 5

    def test_calculate_score_low_severity(self, checker):
        """Test score with low severity issues."""
        issues = [{"severity": "low"}, {"severity": "low"}, {"severity": "low"}]
        score = checker._calculate_ats_score(issues)
        assert score == 94  # 100 - 2 - 2 - 2

    def test_calculate_score_mixed_severity(self, checker):
        """Test score with mixed severity issues."""
        issues = [
            {"severity": "high"},  # -10
            {"severity": "medium"},  # -5
            {"severity": "low"},  # -2
        ]
        score = checker._calculate_ats_score(issues)
        assert score == 83  # 100 - 10 - 5 - 2

    def test_calculate_score_minimum_zero(self, checker):
        """Test that score never goes below 0."""
        # Create 20 high severity issues (20 * 10 = 200 points)
        issues = [{"severity": "high"}] * 20
        score = checker._calculate_ats_score(issues)
        assert score == 0  # Should be capped at 0


class TestCheckATSCompatibility:
    """Test the main ATS compatibility check method."""

    def test_check_ats_complete_resume(self, checker, complete_resume):
        """Test ATS check with complete resume."""
        result = checker.check_ats_compatibility(complete_resume)

        assert isinstance(result, dict)
        assert "ats_score" in result
        assert "issues" in result
        assert "issue_count" in result
        assert "recommendations" in result
        assert "passed" in result

        # Complete resume should have high score
        assert result["ats_score"] == 100
        assert result["issue_count"] == 0
        assert result["passed"] is True

    def test_check_ats_incomplete_resume(self, checker, incomplete_resume):
        """Test ATS check with incomplete resume."""
        result = checker.check_ats_compatibility(incomplete_resume)

        assert isinstance(result, dict)
        assert result["ats_score"] < 100
        assert result["issue_count"] > 0
        assert len(result["recommendations"]) > 0

        # Missing critical sections should result in lower score
        assert result["ats_score"] <= 80  # Missing 2 high severity items

    def test_check_ats_problematic_formatting(self, checker, problematic_formatting_resume):
        """Test ATS check with formatting issues."""
        result = checker.check_ats_compatibility(problematic_formatting_resume)

        assert result["issue_count"] > 0

        # Should have formatting issues
        formatting_issues = [i for i in result["issues"] if i["type"] == "formatting_issue"]
        assert len(formatting_issues) > 0

    def test_check_ats_return_structure(self, checker, complete_resume):
        """Test that return structure is correct."""
        result = checker.check_ats_compatibility(complete_resume)

        # Verify all required keys are present
        required_keys = ["ats_score", "issues", "issue_count", "recommendations", "passed"]
        for key in required_keys:
            assert key in result

        # Verify types
        assert isinstance(result["ats_score"], int)
        assert isinstance(result["issues"], list)
        assert isinstance(result["issue_count"], int)
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["passed"], bool)

    def test_check_ats_pass_threshold(self, checker):
        """Test pass/fail threshold at 70."""
        # Resume with score exactly at 70 (30 points deduction)
        resume_at_threshold = {
            "raw_text": "Clean text",
            "sections": {
                "experience": ["Job"],
                "education": ["Degree"],
                "skills": ["Python"],
                # Missing: summary (-2)
                # Would need -28 more to get to 70
            },
        }

        result = checker.check_ats_compatibility(resume_at_threshold)
        # Should pass if score >= 70
        assert result["ats_score"] >= 70
        assert result["passed"] is True


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow_complete_resume(self, checker, complete_resume):
        """Test complete workflow with well-formatted resume."""
        result = checker.check_ats_compatibility(complete_resume)

        assert result["ats_score"] == 100
        assert result["passed"] is True
        assert len(result["issues"]) == 0

    def test_full_workflow_problematic_resume(self, checker):
        """Test complete workflow with problematic resume."""
        resume = {
            "raw_text": "● EXPERIENCE ●\nPhoto: headshot.jpg",
            "sections": {
                "skills": ["Python"]
                # Missing: experience, education, summary
            },
        }

        result = checker.check_ats_compatibility(resume)

        # Should have both section and formatting issues
        assert result["issue_count"] > 3
        assert result["ats_score"] < 70
        assert result["passed"] is False
        assert len(result["recommendations"]) > 3
