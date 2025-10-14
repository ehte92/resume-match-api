"""
Unit tests for database models.
Tests Resume and ResumeAnalysis models including relationships and JSONB fields.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models import Resume, ResumeAnalysis, User
from app.utils.security import hash_password


# Fixtures for model testing
@pytest.fixture
def test_user_model(db_session: Session) -> User:
    """Create a test user for model tests."""
    user = User(
        email=f"model_test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("testpassword123"),
        full_name="Model Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_resume_model(db_session: Session, test_user_model: User) -> Resume:
    """Create a test resume for model tests."""
    resume = Resume(
        user_id=test_user_model.id,
        file_name="model_test_resume.pdf",
        file_path="/uploads/test/resume.pdf",
        file_type="pdf",
        file_size=100000,
        parsed_text="Sample resume text",
        parsed_data={
            "contact": {"email": "test@example.com"},
            "sections": {"skills": ["Python", "JavaScript"]},
        },
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


class TestResumeModel:
    """Tests for the Resume model."""

    def test_create_resume(self, db_session: Session, test_user_model: User):
        """Test creating a resume with all fields."""
        resume = Resume(
            user_id=test_user_model.id,
            file_name="test_resume.pdf",
            file_path="/uploads/test/resume.pdf",
            file_type="pdf",
            file_size=100000,
            parsed_text="Sample resume text",
            parsed_data={
                "contact": {"email": "test@example.com", "phone": "+1-555-0123"},
                "sections": {"experience": ["Job 1"], "skills": ["Python"]},
            },
        )
        db_session.add(resume)
        db_session.commit()
        db_session.refresh(resume)

        assert resume.id is not None
        assert resume.user_id == test_user_model.id
        assert resume.file_name == "test_resume.pdf"
        assert resume.file_type == "pdf"
        assert resume.file_size == 100000
        assert resume.parsed_data["contact"]["email"] == "test@example.com"
        assert "Python" in resume.parsed_data["sections"]["skills"]

    def test_resume_user_relationship(self, db_session: Session, test_user_model: User):
        """Test relationship between Resume and User."""
        resume = Resume(
            user_id=test_user_model.id,
            file_name="test.pdf",
            file_path="/test.pdf",
            file_type="pdf",
            file_size=100,
        )
        db_session.add(resume)
        db_session.commit()
        db_session.refresh(test_user_model)

        assert len(test_user_model.resumes) == 1
        assert test_user_model.resumes[0].file_name == "test.pdf"
        assert resume.user.email == test_user_model.email

    def test_resume_nullable_fields(self, db_session: Session, test_user_model: User):
        """Test that parsed_text and parsed_data can be null."""
        resume = Resume(
            user_id=test_user_model.id,
            file_name="test.pdf",
            file_path="/test.pdf",
            file_type="pdf",
            file_size=100,
        )
        db_session.add(resume)
        db_session.commit()
        db_session.refresh(resume)

        assert resume.parsed_text is None
        assert resume.parsed_data is None

    def test_resume_cascade_delete_with_user(self, db_session: Session, test_user_model: User):
        """Test that deleting a user cascades to resumes."""
        resume = Resume(
            user_id=test_user_model.id,
            file_name="test.pdf",
            file_path="/test.pdf",
            file_type="pdf",
            file_size=100,
        )
        db_session.add(resume)
        db_session.commit()
        resume_id = resume.id

        db_session.delete(test_user_model)
        db_session.commit()

        # Check resume was deleted
        deleted_resume = db_session.query(Resume).filter(Resume.id == resume_id).first()
        assert deleted_resume is None


class TestResumeAnalysisModel:
    """Tests for the ResumeAnalysis model."""

    def test_create_analysis(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test creating an analysis with all fields."""
        analysis = ResumeAnalysis(
            user_id=test_user_model.id,
            resume_id=test_resume_model.id,
            job_description="Looking for Python developer",
            job_title="Python Developer",
            company_name="TechCorp",
            match_score=85.5,
            ats_score=92.0,
            semantic_similarity=78.3,
            matching_keywords=["Python", "FastAPI"],
            missing_keywords=["Docker"],
            ats_issues=[{"type": "warning", "message": "Test issue"}],
            ai_suggestions=[{"type": "keyword", "suggestion": "Add Docker"}],
            rewritten_bullets=[{"original": "A", "improved": "B"}],
            processing_time_ms=1500,
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)

        assert analysis.id is not None
        assert analysis.user_id == test_user_model.id
        assert analysis.resume_id == test_resume_model.id
        assert analysis.job_title == "Python Developer"
        assert analysis.match_score == 85.5
        assert "Python" in analysis.matching_keywords
        assert "Docker" in analysis.missing_keywords

    def test_analysis_relationships(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test relationships between Analysis, User, and Resume."""
        analysis = ResumeAnalysis(
            user_id=test_user_model.id,
            resume_id=test_resume_model.id,
            job_description="Test job",
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(test_user_model)
        db_session.refresh(test_resume_model)

        # User -> Analyses
        assert len(test_user_model.analyses) == 1
        assert test_user_model.analyses[0].job_description == "Test job"

        # Resume -> Analyses
        assert len(test_resume_model.analyses) == 1
        assert test_resume_model.analyses[0].job_description == "Test job"

        # Analysis -> User and Resume
        assert analysis.user.email == test_user_model.email
        assert analysis.resume.file_name == test_resume_model.file_name

    def test_analysis_optional_fields(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test that optional fields can be null."""
        analysis = ResumeAnalysis(
            user_id=test_user_model.id, resume_id=test_resume_model.id, job_description="Test"
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)

        assert analysis.job_title is None
        assert analysis.company_name is None
        assert analysis.match_score is None
        assert analysis.matching_keywords is None

    def test_analysis_jsonb_fields(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test JSONB field functionality."""
        analysis = ResumeAnalysis(
            user_id=test_user_model.id,
            resume_id=test_resume_model.id,
            job_description="Test",
            matching_keywords=["Python", "JavaScript", "React"],
            ats_issues=[
                {
                    "type": "missing_section",
                    "severity": "high",
                    "message": "No certifications",
                    "recommendation": "Add certifications",
                }
            ],
            ai_suggestions=[
                {
                    "type": "keyword",
                    "priority": "high",
                    "issue": "Missing Docker",
                    "suggestion": "Add Docker experience",
                    "example": "Deployed with Docker",
                }
            ],
        )
        db_session.add(analysis)
        db_session.commit()
        db_session.refresh(analysis)

        # Test list access
        assert len(analysis.matching_keywords) == 3
        assert "Python" in analysis.matching_keywords

        # Test dict access
        assert analysis.ats_issues[0]["type"] == "missing_section"
        assert analysis.ats_issues[0]["severity"] == "high"
        assert analysis.ai_suggestions[0]["priority"] == "high"

    def test_analysis_cascade_delete_with_resume(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test that deleting a resume cascades to analyses."""
        analysis = ResumeAnalysis(
            user_id=test_user_model.id, resume_id=test_resume_model.id, job_description="Test"
        )
        db_session.add(analysis)
        db_session.commit()
        analysis_id = analysis.id

        db_session.delete(test_resume_model)
        db_session.commit()

        # Check analysis was deleted
        deleted_analysis = (
            db_session.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
        )
        assert deleted_analysis is None

    def test_analysis_cascade_delete_with_user(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test that deleting a user cascades to analyses."""
        analysis = ResumeAnalysis(
            user_id=test_user_model.id, resume_id=test_resume_model.id, job_description="Test"
        )
        db_session.add(analysis)
        db_session.commit()
        analysis_id = analysis.id

        db_session.delete(test_user_model)
        db_session.commit()

        # Check analysis was deleted
        deleted_analysis = (
            db_session.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
        )
        assert deleted_analysis is None

    def test_multiple_analyses_per_resume(
        self, db_session: Session, test_user_model: User, test_resume_model: Resume
    ):
        """Test that a resume can have multiple analyses."""
        analysis1 = ResumeAnalysis(
            user_id=test_user_model.id,
            resume_id=test_resume_model.id,
            job_description="Job 1",
            job_title="Developer",
        )
        analysis2 = ResumeAnalysis(
            user_id=test_user_model.id,
            resume_id=test_resume_model.id,
            job_description="Job 2",
            job_title="Engineer",
        )
        db_session.add_all([analysis1, analysis2])
        db_session.commit()
        db_session.refresh(test_resume_model)

        assert len(test_resume_model.analyses) == 2
        job_titles = [a.job_title for a in test_resume_model.analyses]
        assert "Developer" in job_titles
        assert "Engineer" in job_titles
