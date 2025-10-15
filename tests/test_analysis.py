"""
Integration tests for Analysis endpoints.

Tests the complete analysis workflow including resume upload,
keyword matching, ATS checking, and analysis CRUD operations.
"""

import io
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.utils.security import create_access_token, hash_password


@pytest.fixture
def test_user(db_session):
    """Create a test user for authentication."""
    user = User(
        id=uuid4(),
        email="testanalysis@example.com",
        password_hash=hash_password("Test@1234"),
        full_name="Analysis Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers with JWT token."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_pdf_file():
    """Create a mock PDF file for upload."""
    content = b"%PDF-1.4 Mock PDF content for testing"
    return ("sample_resume.pdf", io.BytesIO(content), "application/pdf")


@pytest.fixture
def mock_resume_parser():
    """Mock ResumeParser to avoid file parsing in tests."""
    with patch("app.routers.analysis.ResumeParser") as mock:
        parser_instance = MagicMock()
        parser_instance.parse.return_value = {
            "raw_text": "John Doe\nSoftware Engineer\nPython, FastAPI, Docker\nExperience: 5 years",
            "email": "john@example.com",
            "phone": "+1-555-0123",
            "sections": {
                "experience": ["Software Engineer at Tech Corp (2019-2024)"],
                "education": ["BS Computer Science, University (2015-2019)"],
                "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            },
        }
        mock.return_value = parser_instance
        yield mock


@pytest.fixture
def mock_keyword_analyzer():
    """Mock KeywordAnalyzer to return predictable results."""
    with patch("app.routers.analysis.KeywordAnalyzer") as mock:
        analyzer_instance = MagicMock()
        analyzer_instance.calculate_match_score.return_value = {
            "score": 75.0,
            "matched_keywords": ["python", "fastapi", "docker"],
            "missing_keywords": ["kubernetes", "aws"],
        }
        mock.return_value = analyzer_instance
        yield mock


@pytest.fixture
def mock_ats_checker():
    """Mock ATSChecker to return predictable results."""
    with patch("app.routers.analysis.ATSChecker") as mock:
        checker_instance = MagicMock()
        checker_instance.check_ats_compatibility.return_value = {
            "ats_score": 85,
            "issues": [
                {
                    "type": "missing_section",
                    "severity": "low",
                    "section": "Summary",
                    "message": "Missing 'Summary' section",
                    "recommendation": "Add professional summary",
                }
            ],
            "issue_count": 1,
            "recommendations": ["Add professional summary"],
            "passed": True,
        }
        mock.return_value = checker_instance
        yield mock


class TestCreateAnalysis:
    """Test POST /api/analyses/create endpoint."""

    def test_create_analysis_success(
        self,
        client,
        db_session,
        auth_headers,
        test_user,
        sample_pdf_file,
        mock_resume_parser,
        mock_keyword_analyzer,
        mock_ats_checker,
    ):
        """Test successful analysis creation."""
        filename, file_content, content_type = sample_pdf_file

        response = client.post(
            "/api/analyses/create",
            headers=auth_headers,
            data={
                "job_description": "We need a Python developer with FastAPI and Docker experience.",
                "job_title": "Senior Python Developer",
                "company_name": "Tech Corp",
            },
            files={"file": (filename, file_content, content_type)},
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "match_score" in data
        assert "ats_score" in data
        assert "semantic_similarity" in data
        assert "matching_keywords" in data
        assert "missing_keywords" in data
        assert "ats_issues" in data
        assert "processing_time_ms" in data

        # Verify calculated scores
        # match_score = (75 * 0.6) + (85 * 0.4) = 45 + 34 = 79
        assert data["match_score"] == 79.0
        assert data["ats_score"] == 85
        assert data["semantic_similarity"] == 75.0

        # Verify keywords
        assert "python" in data["matching_keywords"]
        assert "kubernetes" in data["missing_keywords"]

        # Verify database records created
        analysis = db_session.query(ResumeAnalysis).filter_by(id=data["id"]).first()
        assert analysis is not None
        assert analysis.user_id == test_user.id
        assert analysis.job_title == "Senior Python Developer"
        assert analysis.company_name == "Tech Corp"

    def test_create_analysis_invalid_file_type(self, client, auth_headers, test_user):
        """Test analysis creation with invalid file type."""
        # Create a text file instead of PDF/DOCX
        file_content = io.BytesIO(b"Plain text content")

        response = client.post(
            "/api/analyses/create",
            headers=auth_headers,
            data={
                "job_description": "Python developer needed",
            },
            files={"file": ("resume.txt", file_content, "text/plain")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_create_analysis_missing_job_description(self, client, auth_headers, sample_pdf_file):
        """Test analysis creation without job description."""
        filename, file_content, content_type = sample_pdf_file

        response = client.post(
            "/api/analyses/create",
            headers=auth_headers,
            files={"file": (filename, file_content, content_type)},
            # Missing job_description in data
        )

        assert response.status_code == 422  # Validation error

    def test_create_analysis_unauthorized(self, client, sample_pdf_file, mock_resume_parser):
        """Test analysis creation without authentication."""
        filename, file_content, content_type = sample_pdf_file

        response = client.post(
            "/api/analyses/create",
            data={"job_description": "Python developer needed"},
            files={"file": (filename, file_content, content_type)},
        )

        assert response.status_code == 403  # Forbidden


class TestListAnalyses:
    """Test GET /api/analyses/ endpoint."""

    def test_list_analyses_success(self, client, db_session, auth_headers, test_user):
        """Test successful retrieval of analysis list."""
        # Create test analyses
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            file_name="test_resume.pdf",
            file_path="/tmp/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            parsed_text="Resume text",
            parsed_data={},
            storage_backend="local",
        )
        db_session.add(resume)
        db_session.commit()

        for i in range(3):
            analysis = ResumeAnalysis(
                id=uuid4(),
                user_id=test_user.id,
                resume_id=resume.id,
                job_description=f"Job description {i}",
                job_title=f"Job Title {i}",
                match_score=70.0 + i,
                ats_score=80,
                semantic_similarity=75.0,
                matching_keywords=["python"],
                missing_keywords=["aws"],
                ats_issues=[],
                processing_time_ms=1000,
            )
            db_session.add(analysis)
        db_session.commit()

        response = client.get("/api/analyses/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "analyses" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        assert len(data["analyses"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_analyses_pagination(self, client, db_session, auth_headers, test_user):
        """Test pagination in analysis list."""
        # Create a resume first
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            file_name="test_resume.pdf",
            file_path="/tmp/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            parsed_text="Resume text",
            parsed_data={},
            storage_backend="local",
        )
        db_session.add(resume)
        db_session.commit()

        # Create 15 analyses
        for i in range(15):
            analysis = ResumeAnalysis(
                id=uuid4(),
                user_id=test_user.id,
                resume_id=resume.id,
                job_description=f"Job {i}",
                match_score=70.0,
                ats_score=80,
                semantic_similarity=75.0,
                matching_keywords=["python"],
                missing_keywords=[],
                ats_issues=[],
                processing_time_ms=1000,
            )
            db_session.add(analysis)
        db_session.commit()

        # Test page 1
        response = client.get("/api/analyses/?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["analyses"]) == 10
        assert data["total"] == 15

        # Test page 2
        response = client.get("/api/analyses/?page=2&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["analyses"]) == 5
        assert data["total"] == 15

    def test_list_analyses_empty(self, client, auth_headers):
        """Test listing when no analyses exist."""
        response = client.get("/api/analyses/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["analyses"]) == 0
        assert data["total"] == 0

    def test_list_analyses_unauthorized(self, client):
        """Test listing without authentication."""
        response = client.get("/api/analyses/")
        assert response.status_code == 403


class TestGetAnalysis:
    """Test GET /api/analyses/{id} endpoint."""

    def test_get_analysis_success(self, client, db_session, auth_headers, test_user):
        """Test successful retrieval of specific analysis."""
        # Create resume and analysis
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            file_name="test_resume.pdf",
            file_path="/tmp/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            parsed_text="Resume text",
            parsed_data={},
            storage_backend="local",
        )
        db_session.add(resume)
        db_session.commit()

        analysis = ResumeAnalysis(
            id=uuid4(),
            user_id=test_user.id,
            resume_id=resume.id,
            job_description="Python developer needed",
            job_title="Senior Developer",
            match_score=75.5,
            ats_score=85,
            semantic_similarity=70.0,
            matching_keywords=["python", "fastapi"],
            missing_keywords=["aws"],
            ats_issues=[],
            processing_time_ms=1234,
        )
        db_session.add(analysis)
        db_session.commit()

        response = client.get(f"/api/analyses/{analysis.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(analysis.id)
        assert data["job_title"] == "Senior Developer"
        assert data["match_score"] == 75.5

    def test_get_analysis_not_found(self, client, auth_headers):
        """Test getting non-existent analysis."""
        fake_id = uuid4()
        response = client.get(f"/api/analyses/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_analysis_forbidden(self, client, db_session, auth_headers, test_user):
        """Test getting another user's analysis."""
        # Create another user
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            password_hash=hash_password("Test@1234"),
            full_name="Other User",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        # Create resume and analysis for other user
        resume = Resume(
            id=uuid4(),
            user_id=other_user.id,
            file_name="other_resume.pdf",
            file_path="/tmp/other.pdf",
            file_type="application/pdf",
            file_size=1024,
            parsed_text="Resume text",
            parsed_data={},
            storage_backend="local",
        )
        db_session.add(resume)
        db_session.commit()

        analysis = ResumeAnalysis(
            id=uuid4(),
            user_id=other_user.id,
            resume_id=resume.id,
            job_description="Job description",
            match_score=70.0,
            ats_score=80,
            semantic_similarity=75.0,
            matching_keywords=[],
            missing_keywords=[],
            ats_issues=[],
            processing_time_ms=1000,
        )
        db_session.add(analysis)
        db_session.commit()

        # Try to access as test_user
        response = client.get(f"/api/analyses/{analysis.id}", headers=auth_headers)
        assert response.status_code == 403


class TestDeleteAnalysis:
    """Test DELETE /api/analyses/{id} endpoint."""

    def test_delete_analysis_success(self, client, db_session, auth_headers, test_user):
        """Test successful deletion of analysis."""
        # Create resume and analysis
        resume = Resume(
            id=uuid4(),
            user_id=test_user.id,
            file_name="test_resume.pdf",
            file_path="/tmp/test.pdf",
            file_type="application/pdf",
            file_size=1024,
            parsed_text="Resume text",
            parsed_data={},
            storage_backend="local",
        )
        db_session.add(resume)
        db_session.commit()

        analysis = ResumeAnalysis(
            id=uuid4(),
            user_id=test_user.id,
            resume_id=resume.id,
            job_description="Job description",
            match_score=70.0,
            ats_score=80,
            semantic_similarity=75.0,
            matching_keywords=[],
            missing_keywords=[],
            ats_issues=[],
            processing_time_ms=1000,
        )
        db_session.add(analysis)
        db_session.commit()

        analysis_id = analysis.id

        response = client.delete(f"/api/analyses/{analysis_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deletion
        deleted = db_session.query(ResumeAnalysis).filter_by(id=analysis_id).first()
        assert deleted is None

    def test_delete_analysis_not_found(self, client, auth_headers):
        """Test deleting non-existent analysis."""
        fake_id = uuid4()
        response = client.delete(f"/api/analyses/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_analysis_forbidden(self, client, db_session, auth_headers, test_user):
        """Test deleting another user's analysis."""
        # Create another user
        other_user = User(
            id=uuid4(),
            email="other2@example.com",
            password_hash=hash_password("Test@1234"),
            full_name="Other User 2",
            is_active=True,
        )
        db_session.add(other_user)
        db_session.commit()

        # Create resume and analysis for other user
        resume = Resume(
            id=uuid4(),
            user_id=other_user.id,
            file_name="other_resume.pdf",
            file_path="/tmp/other.pdf",
            file_type="application/pdf",
            file_size=1024,
            parsed_text="Resume text",
            parsed_data={},
            storage_backend="local",
        )
        db_session.add(resume)
        db_session.commit()

        analysis = ResumeAnalysis(
            id=uuid4(),
            user_id=other_user.id,
            resume_id=resume.id,
            job_description="Job description",
            match_score=70.0,
            ats_score=80,
            semantic_similarity=75.0,
            matching_keywords=[],
            missing_keywords=[],
            ats_issues=[],
            processing_time_ms=1000,
        )
        db_session.add(analysis)
        db_session.commit()

        # Try to delete as test_user
        response = client.delete(f"/api/analyses/{analysis.id}", headers=auth_headers)
        assert response.status_code == 403

        # Verify not deleted
        still_exists = db_session.query(ResumeAnalysis).filter_by(id=analysis.id).first()
        assert still_exists is not None
