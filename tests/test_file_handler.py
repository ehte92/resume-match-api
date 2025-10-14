"""
Unit tests for file handler utilities.
Tests file validation, saving, and deletion functionality.
"""

import os
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.utils import file_handler


def test_validate_file_type_pdf():
    """Test PDF file type validation"""
    assert file_handler.validate_file_type("application/pdf") is True


def test_validate_file_type_docx():
    """Test DOCX file type validation"""
    assert (
        file_handler.validate_file_type(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        is True
    )


def test_validate_file_type_invalid():
    """Test rejection of invalid file types"""
    assert file_handler.validate_file_type("text/plain") is False
    assert file_handler.validate_file_type("image/jpeg") is False
    assert file_handler.validate_file_type("application/json") is False


def test_validate_file_size_valid():
    """Test file size validation for valid sizes"""
    assert file_handler.validate_file_size(1024) is True  # 1KB
    assert file_handler.validate_file_size(1024 * 1024) is True  # 1MB
    assert file_handler.validate_file_size(5 * 1024 * 1024) is True  # 5MB (max)


def test_validate_file_size_too_large():
    """Test rejection of files that are too large"""
    assert file_handler.validate_file_size(10 * 1024 * 1024) is False  # 10MB
    assert file_handler.validate_file_size(100 * 1024 * 1024) is False  # 100MB


def test_validate_file_size_edge_case():
    """Test file size validation at boundary"""
    max_size = 5 * 1024 * 1024
    assert file_handler.validate_file_size(max_size) is True
    assert file_handler.validate_file_size(max_size + 1) is False


@pytest.mark.asyncio
async def test_save_temp_file_pdf():
    """Test saving a PDF file"""
    # Create mock uploaded file
    file_content = b"Test PDF content"
    headers = Headers({"content-type": "application/pdf"})
    upload_file = UploadFile(filename="test.pdf", file=BytesIO(file_content), headers=headers)

    # Save file
    file_path = await file_handler.save_temp_file(upload_file)

    try:
        # Verify file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".pdf")

        # Verify content
        with open(file_path, "rb") as f:
            assert f.read() == file_content
    finally:
        # Cleanup
        file_handler.delete_temp_file(file_path)


@pytest.mark.asyncio
async def test_save_temp_file_docx():
    """Test saving a DOCX file"""
    # Create mock uploaded file
    file_content = b"Test DOCX content"
    headers = Headers(
        {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    )
    upload_file = UploadFile(filename="test.docx", file=BytesIO(file_content), headers=headers)

    # Save file
    file_path = await file_handler.save_temp_file(upload_file)

    try:
        # Verify file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".docx")

        # Verify content
        with open(file_path, "rb") as f:
            assert f.read() == file_content
    finally:
        # Cleanup
        file_handler.delete_temp_file(file_path)


def test_delete_temp_file():
    """Test deleting a temporary file"""
    # Create a temporary file
    temp_path = os.path.join(file_handler.TEMP_DIR, "test_delete.txt")
    os.makedirs(file_handler.TEMP_DIR, exist_ok=True)

    with open(temp_path, "w") as f:
        f.write("test content")

    # Verify file exists
    assert os.path.exists(temp_path)

    # Delete file
    file_handler.delete_temp_file(temp_path)

    # Verify file is deleted
    assert not os.path.exists(temp_path)


def test_delete_temp_file_nonexistent():
    """Test deleting a file that doesn't exist (should not raise error)"""
    nonexistent_path = "/tmp/nonexistent_file_12345.txt"

    # Should not raise an exception
    file_handler.delete_temp_file(nonexistent_path)


def test_get_file_extension_pdf():
    """Test getting file extension for PDF"""
    assert file_handler.get_file_extension("application/pdf") == ".pdf"


def test_get_file_extension_docx():
    """Test getting file extension for DOCX"""
    assert (
        file_handler.get_file_extension(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        == ".docx"
    )


def test_get_file_extension_invalid():
    """Test getting file extension for invalid type"""
    assert file_handler.get_file_extension("text/plain") is None
    assert file_handler.get_file_extension("image/jpeg") is None
