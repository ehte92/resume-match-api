"""
Tests for resume API endpoints.

This module tests all resume-related endpoints including upload,
listing, retrieval, deletion, and download URL generation.
"""

import io

# import os  # noqa: F401
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.user import User


@pytest.fixture
def test_resume(db_session: Session, test_user: User):
    """
    Create a test resume in the database.

    This fixture creates a sample resume that can be used for
    testing retrieval, update, and delete operations.

    Args:
        db_session: The test database session fixture
        test_user: The test user fixture

    Returns:
        Resume: The created test resume object
    """
    resume = Resume(
        user_id=test_user.id,
        file_name="test_resume.pdf",
        file_type="pdf",
        file_size=1024,
        file_path="/test/path/test_resume.pdf",
        storage_backend="local",
        parsed_text="Test resume content",
        parsed_data={
            "name": "Test User",
            "email": "test@example.com",
            "sections": {
                "experience": ["Software Engineer at Test Corp"],
                "education": ["BS in Computer Science"],
            },
        },
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


@pytest.fixture
def another_user(db_session: Session):
    """
    Create another test user for ownership testing.

    This fixture is used to test that users cannot access
    resumes belonging to other users.

    Args:
        db_session: The test database session fixture

    Returns:
        User: The created user object
    """
    from app.utils.security import hash_password

    user = User(
        email="another@example.com",
        password_hash=hash_password("anotherpassword123"),
        full_name="Another User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def another_user_auth_headers(client: TestClient, another_user: User):
    """
    Get authentication headers for another user.

    Args:
        client: The test client fixture
        another_user: The another user fixture

    Returns:
        dict: Authorization headers with Bearer token
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "another@example.com", "password": "anotherpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_pdf_file():
    """
    Create a minimal valid PDF file in memory.

    Returns:
        BytesIO: A file-like object containing PDF data
    """
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Resume) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return io.BytesIO(pdf_content)


def create_test_docx_file():
    """
    Create a minimal valid DOCX file in memory.

    Returns:
        BytesIO: A file-like object containing DOCX data
    """
    # Create a minimal DOCX (ZIP with required structure)
    import zipfile

    docx_buffer = io.BytesIO()
    with zipfile.ZipFile(docx_buffer, "w", zipfile.ZIP_DEFLATED) as docx:
        # Add [Content_Types].xml
        docx.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'  # noqa: E501
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'  # noqa: E501
            "</Types>",
        )

        # Add _rels/.rels
        docx.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'  # noqa: E501
            "</Relationships>",
        )

        # Add word/document.xml
        docx.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            "<w:p><w:r><w:t>Test Resume Content</w:t></w:r></w:p>"
            "</w:body>"
            "</w:document>",
        )

    docx_buffer.seek(0)
    return docx_buffer


class TestResumeUpload:
    """Tests for resume upload endpoint."""

    def test_upload_pdf_success(self, client: TestClient, auth_headers: dict, monkeypatch):
        """
        Test successful PDF upload.

        Verifies that a valid PDF file can be uploaded and parsed.
        """
        # Mock the file handler to avoid actual R2 upload in tests
        # from unittest.mock import AsyncMock  # noqa: F401

        async def mock_save_file_with_storage(*args, **kwargs):
            return {
                "local_path": "/tmp/test_resume.pdf",
                "storage_url": "https://r2.example.com/test-key",
                "storage_key": "test-key",
                "storage_backend": "r2",
            }

        from app.utils import file_handler

        monkeypatch.setattr(file_handler, "save_file_with_storage", mock_save_file_with_storage)

        # Mock storage service to generate presigned URL
        from app.services.storage_service import StorageService

        def mock_generate_presigned_url(self, key, expiration=3600):
            return f"https://r2.example.com/presigned/{key}"

        monkeypatch.setattr(StorageService, "generate_presigned_url", mock_generate_presigned_url)

        # Create test PDF file
        pdf_file = create_test_pdf_file()

        response = client.post(
            "/api/resumes/upload",
            headers=auth_headers,
            files={"file": ("test_resume.pdf", pdf_file, "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response data
        assert "id" in data
        assert data["file_name"] == "test_resume.pdf"
        assert data["file_type"] == "pdf"
        assert data["file_size"] > 0
        assert "parsed_text" in data
        assert "created_at" in data

        # Verify download_url field is present for R2-stored files
        assert "download_url" in data
        assert data["download_url"] is not None
        assert "presigned" in data["download_url"]

    def test_upload_docx_success(self, client: TestClient, auth_headers: dict, monkeypatch):
        """
        Test successful DOCX upload.

        Verifies that a valid DOCX file can be uploaded and parsed.
        """

        async def mock_save_file_with_storage(*args, **kwargs):
            return {
                "local_path": "/tmp/test_resume.docx",
                "storage_url": "https://r2.example.com/test-key",
                "storage_key": "test-key",
                "storage_backend": "r2",
            }

        from app.utils import file_handler

        monkeypatch.setattr(file_handler, "save_file_with_storage", mock_save_file_with_storage)

        # Mock storage service to generate presigned URL
        from app.services.storage_service import StorageService

        def mock_generate_presigned_url(self, key, expiration=3600):
            return f"https://r2.example.com/presigned/{key}"

        monkeypatch.setattr(StorageService, "generate_presigned_url", mock_generate_presigned_url)

        # Create test DOCX file
        docx_file = create_test_docx_file()

        response = client.post(
            "/api/resumes/upload",
            headers=auth_headers,
            files={
                "file": (
                    "test_resume.docx",
                    docx_file,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify response data
        assert "id" in data
        assert data["file_name"] == "test_resume.docx"
        assert data["file_type"] == "docx"
        assert "parsed_text" in data

        # Verify download_url field is present for R2-stored files
        assert "download_url" in data
        assert data["download_url"] is not None

    def test_upload_invalid_file_type(self, client: TestClient, auth_headers: dict):
        """
        Test upload with invalid file type fails.

        Verifies that non-PDF/DOCX files are rejected.
        """
        # Create a fake text file
        txt_file = io.BytesIO(b"This is a text file, not a resume")

        response = client.post(
            "/api/resumes/upload",
            headers=auth_headers,
            files={"file": ("test.txt", txt_file, "text/plain")},
        )

        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    def test_upload_file_too_large(self, client: TestClient, auth_headers: dict):
        """
        Test upload with file exceeding size limit fails.

        Verifies that files larger than 5MB are rejected.
        """
        # Create a large fake PDF (6MB) with PDF header for content type validation
        pdf_header = b"%PDF-1.4\n"
        large_content = b"X" * (6 * 1024 * 1024 - len(pdf_header))
        large_file = io.BytesIO(pdf_header + large_content)

        response = client.post(
            "/api/resumes/upload",
            headers=auth_headers,
            files={"file": ("large_resume.pdf", large_file, "application/pdf")},
        )

        assert response.status_code == 400
        assert "file" in response.json()["detail"].lower() and (
            "size" in response.json()["detail"].lower()
            or "large" in response.json()["detail"].lower()
        )  # noqa: E501

    def test_upload_no_auth(self, client: TestClient):
        """
        Test upload without authentication fails.

        Verifies that the upload endpoint requires authentication.
        """
        pdf_file = create_test_pdf_file()

        response = client.post(
            "/api/resumes/upload",
            files={"file": ("test_resume.pdf", pdf_file, "application/pdf")},
        )

        assert response.status_code == 403

    def test_upload_invalid_token(self, client: TestClient):
        """
        Test upload with invalid token fails.

        Verifies that an invalid authentication token is rejected.
        """
        pdf_file = create_test_pdf_file()

        response = client.post(
            "/api/resumes/upload",
            headers={"Authorization": "Bearer invalid_token"},
            files={"file": ("test_resume.pdf", pdf_file, "application/pdf")},
        )

        assert response.status_code == 401


class TestResumeList:
    """Tests for resume list endpoint."""

    def test_list_resumes_success(
        self, client: TestClient, auth_headers: dict, test_resume: Resume
    ):
        """
        Test successful retrieval of user's resumes.

        Verifies that authenticated users can list their own resumes.
        """
        response = client.get("/api/resumes/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify pagination structure
        assert "resumes" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        # Verify resume data
        assert len(data["resumes"]) > 0
        assert data["resumes"][0]["id"] == str(test_resume.id)
        assert data["resumes"][0]["file_name"] == "test_resume.pdf"

        # Verify download_url field is present (should be None for local storage)
        assert "download_url" in data["resumes"][0]
        assert data["resumes"][0]["download_url"] is None  # Local storage

    def test_list_resumes_pagination(
        self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User
    ):
        """
        Test pagination in resume list.

        Verifies that pagination parameters work correctly.
        """
        # Create multiple test resumes
        for i in range(15):
            resume = Resume(
                user_id=test_user.id,
                file_name=f"resume_{i}.pdf",
                file_type="pdf",
                file_size=1024,
                file_path=f"/test/path/resume_{i}.pdf",
                storage_backend="local",
            )
            db_session.add(resume)
        db_session.commit()

        # Test first page
        response = client.get("/api/resumes/?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["resumes"]) == 10
        assert data["total"] == 15
        assert data["page"] == 1
        assert data["page_size"] == 10

        # Test second page
        response = client.get("/api/resumes/?page=2&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["resumes"]) == 5
        assert data["total"] == 15
        assert data["page"] == 2

    def test_list_resumes_empty(self, client: TestClient, auth_headers: dict):
        """
        Test listing resumes when user has none.

        Verifies that empty list is returned correctly.
        """
        response = client.get("/api/resumes/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["resumes"] == []
        assert data["total"] == 0

    def test_list_resumes_user_filtering(
        self,
        client: TestClient,
        auth_headers: dict,
        another_user_auth_headers: dict,
        test_resume: Resume,
        db_session: Session,
        another_user: User,
    ):
        """
        Test that users only see their own resumes.

        Verifies that resume list is properly filtered by user ownership.
        """
        # Create resume for another user
        other_resume = Resume(
            user_id=another_user.id,
            file_name="other_user_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/test/path/other_resume.pdf",
            storage_backend="local",
        )
        db_session.add(other_resume)
        db_session.commit()

        # Test first user sees only their resume
        response = client.get("/api/resumes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["resumes"][0]["id"] == str(test_resume.id)

        # Test another user sees only their resume
        response = client.get("/api/resumes/", headers=another_user_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["resumes"][0]["id"] == str(other_resume.id)

    def test_list_resumes_no_auth(self, client: TestClient):
        """
        Test listing resumes without authentication fails.

        Verifies that the list endpoint requires authentication.
        """
        response = client.get("/api/resumes/")

        assert response.status_code == 403

    def test_list_resumes_with_r2_storage(
        self,  # noqa: E501
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_user: User,
        monkeypatch,
    ):
        """
        Test that list resumes includes download_url for R2-stored files.

        Verifies that resumes stored in R2 have presigned download URLs.
        """
        # Create resume with R2 storage
        r2_resume = Resume(
            user_id=test_user.id,
            file_name="r2_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/tmp/test.pdf",
            storage_backend="r2",
            storage_key="resumes/test-user/test.pdf",
            storage_url="https://r2.example.com/test-key",
        )
        db_session.add(r2_resume)
        db_session.commit()
        db_session.refresh(r2_resume)

        # Mock storage service to generate presigned URL
        from app.services.storage_service import StorageService

        def mock_generate_presigned_url(self, key, expiration=3600):
            return f"https://r2.example.com/presigned/{key}"

        monkeypatch.setattr(StorageService, "generate_presigned_url", mock_generate_presigned_url)

        response = client.get("/api/resumes/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Find the R2 resume in the list
        r2_resume_data = next((r for r in data["resumes"] if r["id"] == str(r2_resume.id)), None)
        assert r2_resume_data is not None

        # Verify download_url is present and valid for R2-stored files
        assert "download_url" in r2_resume_data
        assert r2_resume_data["download_url"] is not None
        assert "presigned" in r2_resume_data["download_url"]
        assert r2_resume_data["storage_backend"] == "r2"


class TestGetSingleResume:
    """Tests for getting a specific resume."""

    def test_get_resume_success(self, client: TestClient, auth_headers: dict, test_resume: Resume):
        """
        Test successful retrieval of specific resume.

        Verifies that users can get details of their own resumes.
        """
        response = client.get(f"/api/resumes/{test_resume.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify resume data
        assert data["id"] == str(test_resume.id)
        assert data["file_name"] == "test_resume.pdf"
        assert data["file_type"] == "pdf"
        assert data["parsed_text"] == "Test resume content"
        assert "parsed_data" in data

        # Verify download_url field is present (should be None for local storage)
        assert "download_url" in data
        assert data["download_url"] is None  # Local storage

    def test_get_resume_not_found(self, client: TestClient, auth_headers: dict):
        """
        Test getting non-existent resume returns 404.

        Verifies that requesting a resume that doesn't exist
        returns a proper 404 error.
        """
        fake_id = uuid4()
        response = client.get(f"/api/resumes/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_resume_forbidden(
        self,
        client: TestClient,
        another_user_auth_headers: dict,
        test_resume: Resume,
    ):
        """
        Test accessing another user's resume returns 403.

        Verifies that users cannot access resumes belonging
        to other users (ownership verification).
        """
        response = client.get(f"/api/resumes/{test_resume.id}", headers=another_user_auth_headers)

        assert response.status_code == 403
        assert "permission denied" in response.json()["detail"].lower()

    def test_get_resume_no_auth(self, client: TestClient, test_resume: Resume):
        """
        Test getting resume without authentication fails.

        Verifies that the get endpoint requires authentication.
        """
        response = client.get(f"/api/resumes/{test_resume.id}")

        assert response.status_code == 403

    def test_get_resume_invalid_uuid(self, client: TestClient, auth_headers: dict):
        """
        Test getting resume with invalid UUID format.

        Verifies that invalid UUID format is rejected.
        """
        response = client.get("/api/resumes/not-a-valid-uuid", headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_get_resume_with_r2_storage(
        self,
        client: TestClient,  # noqa: E501
        auth_headers: dict,
        db_session: Session,
        test_user: User,
        monkeypatch,
    ):
        """
        Test getting a specific resume with R2 storage includes download_url.

        Verifies that resumes stored in R2 have presigned download URLs.
        """
        # Create resume with R2 storage
        r2_resume = Resume(
            user_id=test_user.id,
            file_name="r2_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/tmp/test.pdf",
            storage_backend="r2",
            storage_key="resumes/test-user/test.pdf",
            storage_url="https://r2.example.com/test-key",
            parsed_text="Test content",
        )
        db_session.add(r2_resume)
        db_session.commit()
        db_session.refresh(r2_resume)

        # Mock storage service to generate presigned URL
        from app.services.storage_service import StorageService

        def mock_generate_presigned_url(self, key, expiration=3600):
            return f"https://r2.example.com/presigned/{key}"

        monkeypatch.setattr(StorageService, "generate_presigned_url", mock_generate_presigned_url)

        response = client.get(f"/api/resumes/{r2_resume.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify download_url is present and valid for R2-stored files
        assert "download_url" in data
        assert data["download_url"] is not None
        assert "presigned" in data["download_url"]
        assert data["storage_backend"] == "r2"


class TestDeleteResume:
    """Tests for resume deletion endpoint."""

    def test_delete_resume_success(
        self, client: TestClient, auth_headers: dict, test_resume: Resume, db_session: Session
    ):
        """
        Test successful resume deletion.

        Verifies that users can delete their own resumes
        and that the resume is removed from the database.
        """
        resume_id = test_resume.id

        response = client.delete(f"/api/resumes/{resume_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify resume is deleted from database
        deleted_resume = db_session.query(Resume).filter(Resume.id == resume_id).first()
        assert deleted_resume is None

    def test_delete_resume_not_found(self, client: TestClient, auth_headers: dict):
        """
        Test deleting non-existent resume returns 404.

        Verifies that attempting to delete a resume that
        doesn't exist returns a proper 404 error.
        """
        fake_id = uuid4()
        response = client.delete(f"/api/resumes/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_resume_forbidden(
        self,
        client: TestClient,
        another_user_auth_headers: dict,
        test_resume: Resume,
    ):
        """
        Test deleting another user's resume returns 403.

        Verifies that users cannot delete resumes belonging
        to other users (ownership verification).
        """
        response = client.delete(
            f"/api/resumes/{test_resume.id}", headers=another_user_auth_headers
        )

        assert response.status_code == 403  # noqa: E501
        assert "permission denied" in response.json()["detail"].lower()

    def test_delete_resume_with_r2_storage(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_user: User,
        monkeypatch,
    ):
        """
        Test deletion of resume stored in R2.

        Verifies that R2 cleanup is triggered when deleting
        a resume stored in cloud storage.
        """
        from unittest.mock import MagicMock

        # Create resume with R2 storage
        r2_resume = Resume(
            user_id=test_user.id,
            file_name="r2_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/tmp/test.pdf",
            storage_backend="r2",
            storage_key="test-key",
            storage_url="https://r2.example.com/test-key",
        )
        db_session.add(r2_resume)
        db_session.commit()
        db_session.refresh(r2_resume)

        # Mock storage service at the class level
        mock_storage = MagicMock()
        mock_storage.delete_file = MagicMock()

        from app.services.storage_service import StorageService

        monkeypatch.setattr(StorageService, "delete_file", mock_storage.delete_file)

        response = client.delete(f"/api/resumes/{r2_resume.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify R2 delete was called
        mock_storage.delete_file.assert_called_once_with("test-key")

    def test_delete_resume_no_auth(self, client: TestClient, test_resume: Resume):
        """
        Test deleting resume without authentication fails.

        Verifies that the delete endpoint requires authentication.
        """
        response = client.delete(f"/api/resumes/{test_resume.id}")

        assert response.status_code == 403


class TestDownloadURL:
    """Tests for download URL generation endpoint."""

    def test_generate_download_url_success(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_user: User,
        monkeypatch,
    ):
        """
        Test successful generation of presigned download URL.

        Verifies that download URLs can be generated for
        resumes stored in R2.
        """
        from unittest.mock import MagicMock  # noqa: F401

        # Create resume with R2 storage
        r2_resume = Resume(
            user_id=test_user.id,
            file_name="r2_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/tmp/test.pdf",
            storage_backend="r2",
            storage_key="test-key",
            storage_url="https://r2.example.com/test-key",
        )
        db_session.add(r2_resume)
        db_session.commit()
        db_session.refresh(r2_resume)

        # Mock storage service at the class level
        from app.services.storage_service import StorageService

        def mock_generate_presigned_url(self, key, expiration=3600):
            return "https://r2.example.com/presigned-url"

        monkeypatch.setattr(StorageService, "generate_presigned_url", mock_generate_presigned_url)

        response = client.get(f"/api/resumes/{r2_resume.id}/download", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify download URL structure
        assert "url" in data
        assert "expires_in" in data
        assert "filename" in data
        assert data["url"] == "https://r2.example.com/presigned-url"
        assert data["expires_in"] == 3600
        assert data["filename"] == "r2_resume.pdf"

    def test_generate_download_url_local_storage(
        self, client: TestClient, auth_headers: dict, test_resume: Resume
    ):
        """
        Test download URL generation fails for local storage.

        Verifies that presigned URLs cannot be generated for
        resumes stored locally (not in R2).
        """
        response = client.get(f"/api/resumes/{test_resume.id}/download", headers=auth_headers)

        assert response.status_code == 400
        assert "not in cloud storage" in response.json()["detail"].lower()

    def test_generate_download_url_not_found(self, client: TestClient, auth_headers: dict):
        """
        Test download URL generation for non-existent resume.

        Verifies that requesting a download URL for a resume
        that doesn't exist returns a 404 error.
        """
        fake_id = uuid4()
        response = client.get(f"/api/resumes/{fake_id}/download", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_download_url_forbidden(
        self,
        client: TestClient,
        another_user_auth_headers: dict,
        db_session: Session,
        test_user: User,
    ):
        """
        Test download URL generation for another user's resume.

        Verifies that users cannot generate download URLs for
        resumes belonging to other users.
        """
        # Create R2 resume for test_user
        r2_resume = Resume(
            user_id=test_user.id,
            file_name="r2_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/tmp/test.pdf",
            storage_backend="r2",
            storage_key="test-key",
            storage_url="https://r2.example.com/test-key",
        )
        db_session.add(r2_resume)
        db_session.commit()
        db_session.refresh(r2_resume)

        response = client.get(
            f"/api/resumes/{r2_resume.id}/download", headers=another_user_auth_headers
        )

        assert response.status_code == 403
        assert "permission denied" in response.json()["detail"].lower()

    def test_generate_download_url_no_auth(
        self, client: TestClient, db_session: Session, test_user: User
    ):
        """
        Test download URL generation without authentication fails.

        Verifies that the download URL endpoint requires authentication.
        """
        # Create R2 resume
        r2_resume = Resume(
            user_id=test_user.id,
            file_name="r2_resume.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="/tmp/test.pdf",
            storage_backend="r2",
            storage_key="test-key",
            storage_url="https://r2.example.com/test-key",
        )
        db_session.add(r2_resume)
        db_session.commit()
        db_session.refresh(r2_resume)

        response = client.get(f"/api/resumes/{r2_resume.id}/download")

        assert response.status_code == 403
