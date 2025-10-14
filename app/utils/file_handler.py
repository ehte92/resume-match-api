"""
File handler utilities for resume upload and validation.
Handles temporary file storage, validation, and cleanup.
Supports both local storage and Cloudflare R2 (S3-compatible) storage.
"""

import os
import uuid
from typing import Dict, Optional

from fastapi import UploadFile

from app.config import get_settings

# Constants
TEMP_DIR = "/tmp/resume_uploads"
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


def validate_file_type(content_type: str) -> bool:
    """
    Validate that file type is PDF or DOCX.

    Args:
        content_type: MIME type of the file

    Returns:
        True if file type is allowed, False otherwise
    """
    return content_type in ALLOWED_TYPES


def validate_file_size(size: int) -> bool:
    """
    Validate that file size is under the maximum limit.

    Args:
        size: File size in bytes

    Returns:
        True if file size is within limit, False otherwise
    """
    return size <= MAX_SIZE_BYTES


async def save_temp_file(upload_file: UploadFile) -> str:
    """
    Save uploaded file to temporary directory.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        Path to saved temporary file

    Raises:
        OSError: If file cannot be saved
    """
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Generate unique filename
    ext = ".pdf" if "pdf" in upload_file.content_type else ".docx"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(TEMP_DIR, filename)

    # Save file
    try:
        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise OSError(f"Failed to save file: {str(e)}")


def delete_temp_file(file_path: str) -> None:
    """
    Delete temporary file.

    Args:
        file_path: Path to temporary file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        # Silently ignore errors - file may already be deleted
        pass


def get_file_extension(content_type: str) -> Optional[str]:
    """
    Get file extension from content type.

    Args:
        content_type: MIME type of the file

    Returns:
        File extension (.pdf or .docx) or None if invalid
    """
    if content_type == "application/pdf":
        return ".pdf"
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    return None


async def save_file_with_storage(
    upload_file: UploadFile, user_id: str, use_r2: bool = None
) -> Dict[str, str]:
    """
    Save uploaded file to local temp storage and optionally upload to R2.

    Args:
        upload_file: FastAPI UploadFile object
        user_id: User ID for organizing files in R2
        use_r2: Whether to upload to R2 (None = use config setting)

    Returns:
        Dictionary with:
            - local_path: Path to temporary local file
            - storage_url: R2 URL (if uploaded to R2)
            - storage_key: R2 object key (if uploaded to R2)
            - storage_backend: 'local' or 'r2'

    Raises:
        OSError: If file cannot be saved
        ValueError: If R2 upload fails
    """
    # Save to local temp first
    local_path = await save_temp_file(upload_file)

    result = {
        "local_path": local_path,
        "storage_url": None,
        "storage_key": None,
        "storage_backend": "local",
    }

    # Check if we should upload to R2
    settings = get_settings()
    should_use_r2 = use_r2 if use_r2 is not None else settings.STORAGE_BACKEND == "r2"

    if should_use_r2:
        try:
            from app.services.storage_service import get_storage_service

            storage = get_storage_service()

            # Generate object key: resumes/{user_id}/{filename}
            filename = os.path.basename(local_path)
            object_key = f"resumes/{user_id}/{filename}"

            # Upload to R2
            storage_url = storage.upload_file(
                file_path=local_path, object_key=object_key, content_type=upload_file.content_type
            )

            result.update(
                {
                    "storage_url": storage_url,
                    "storage_key": object_key,
                    "storage_backend": "r2",
                }
            )

        except Exception as e:
            # If R2 upload fails, clean up local file and re-raise
            delete_temp_file(local_path)
            raise ValueError(f"Failed to upload to R2: {str(e)}")

    return result


def delete_from_storage(storage_backend: str, storage_key: Optional[str] = None) -> None:
    """
    Delete file from storage (R2 or local).

    Args:
        storage_backend: 'local' or 'r2'
        storage_key: R2 object key (required if backend is 'r2')

    Raises:
        ValueError: If R2 deletion fails
    """
    if storage_backend == "r2" and storage_key:
        try:
            from app.services.storage_service import get_storage_service

            storage = get_storage_service()
            storage.delete_file(storage_key)

        except Exception as e:
            raise ValueError(f"Failed to delete from R2: {str(e)}")
