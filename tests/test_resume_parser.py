"""
Unit tests for resume parser service.
Tests PDF/DOCX extraction, contact info extraction, and section identification.
"""

import os

import pytest

from app.services.resume_parser import ResumeParser

# Path to test fixtures
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE_PDF = os.path.join(FIXTURES_DIR, "sample_resume.pdf")
SAMPLE_DOCX = os.path.join(FIXTURES_DIR, "sample_resume.docx")


@pytest.fixture
def parser():
    """Create ResumeParser instance for tests"""
    return ResumeParser()


def test_parse_pdf_file(parser):
    """Test parsing a PDF resume file"""
    result = parser.parse(SAMPLE_PDF, "pdf")

    # Verify structure
    assert "raw_text" in result
    assert "email" in result
    assert "phone" in result
    assert "linkedin" in result
    assert "sections" in result

    # Verify raw text contains key information
    assert "JOHN DOE" in result["raw_text"]
    assert "Software Engineer" in result["raw_text"]
    assert len(result["raw_text"]) > 100


def test_parse_docx_file(parser):
    """Test parsing a DOCX resume file"""
    result = parser.parse(SAMPLE_DOCX, "docx")

    # Verify structure
    assert "raw_text" in result
    assert "email" in result
    assert "phone" in result
    assert "linkedin" in result
    assert "sections" in result

    # Verify raw text contains key information
    assert "JOHN DOE" in result["raw_text"]
    assert "Software Engineer" in result["raw_text"]
    assert len(result["raw_text"]) > 100


def test_extract_contact_info_pdf(parser):
    """Test extracting contact information from PDF"""
    result = parser.parse(SAMPLE_PDF, "pdf")

    # Verify email extraction
    assert result["email"] == "john.doe@example.com"

    # Verify phone extraction
    assert result["phone"] is not None
    assert "555" in result["phone"]

    # Verify LinkedIn extraction
    assert result["linkedin"] is not None
    assert "linkedin.com/in/johndoe" in result["linkedin"]


def test_extract_contact_info_docx(parser):
    """Test extracting contact information from DOCX"""
    result = parser.parse(SAMPLE_DOCX, "docx")

    # Verify email extraction
    assert result["email"] == "john.doe@example.com"

    # Verify phone extraction
    assert result["phone"] is not None
    assert "555" in result["phone"]

    # Verify LinkedIn extraction
    assert result["linkedin"] is not None
    assert "linkedin.com/in/johndoe" in result["linkedin"]


def test_identify_sections_pdf(parser):
    """Test identifying resume sections from PDF"""
    result = parser.parse(SAMPLE_PDF, "pdf")
    sections = result["sections"]

    # Verify sections exist
    assert "experience" in sections
    assert "education" in sections
    assert "skills" in sections

    # Verify experience section content
    assert len(sections["experience"]) > 0
    experience_text = " ".join(sections["experience"]).lower()
    assert "tech corp" in experience_text or "software engineer" in experience_text

    # Verify education section content
    assert len(sections["education"]) > 0
    education_text = " ".join(sections["education"]).lower()
    assert "computer science" in education_text or "university" in education_text

    # Verify skills section content
    assert len(sections["skills"]) > 0
    skills_text = " ".join(sections["skills"]).lower()
    assert "python" in skills_text or "javascript" in skills_text


def test_identify_sections_docx(parser):
    """Test identifying resume sections from DOCX"""
    result = parser.parse(SAMPLE_DOCX, "docx")
    sections = result["sections"]

    # Verify sections exist
    assert "experience" in sections
    assert "education" in sections
    assert "skills" in sections

    # Verify experience section content
    assert len(sections["experience"]) > 0
    experience_text = " ".join(sections["experience"]).lower()
    assert "tech corp" in experience_text or "software engineer" in experience_text

    # Verify education section content
    assert len(sections["education"]) > 0
    education_text = " ".join(sections["education"]).lower()
    assert "computer science" in education_text or "university" in education_text

    # Verify skills section content
    assert len(sections["skills"]) > 0
    skills_text = " ".join(sections["skills"]).lower()
    assert "python" in skills_text or "javascript" in skills_text


def test_parse_invalid_file_type(parser):
    """Test parsing with unsupported file type"""
    with pytest.raises(ValueError, match="Unsupported file type"):
        parser.parse("/tmp/test.txt", "txt")


def test_parse_nonexistent_pdf(parser):
    """Test parsing non-existent PDF file"""
    with pytest.raises(ValueError, match="Error extracting PDF"):
        parser.parse("/tmp/nonexistent_file_12345.pdf", "pdf")


def test_parse_nonexistent_docx(parser):
    """Test parsing non-existent DOCX file"""
    with pytest.raises(ValueError, match="Error extracting DOCX"):
        parser.parse("/tmp/nonexistent_file_12345.docx", "docx")


def test_extract_contact_info_with_missing_data(parser):
    """Test contact extraction when some fields are missing"""
    # Test with text that has only email
    text = "Contact me at test@example.com for more info."
    contact = parser._extract_contact_info(text)

    assert contact.get("email") == "test@example.com"
    assert "phone" not in contact or contact.get("phone") is None
    assert "linkedin" not in contact or contact.get("linkedin") is None


def test_identify_sections_empty_text(parser):
    """Test section identification with empty text"""
    sections = parser._identify_sections("")

    assert sections["experience"] == []
    assert sections["education"] == []
    assert sections["skills"] == []


def test_identify_sections_no_headers(parser):
    """Test section identification when no section headers present"""
    text = "Just some random text without any section headers."
    sections = parser._identify_sections(text)

    # Should return empty sections
    assert sections["experience"] == []
    assert sections["education"] == []
    assert sections["skills"] == []
