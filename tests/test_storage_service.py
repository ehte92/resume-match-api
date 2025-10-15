"""
Unit tests for storage service (Cloudflare R2 integration).
Tests file upload, download, deletion, and presigned URL generation.
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services.storage_service import StorageService, get_storage_service


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    with patch("app.services.storage_service.get_settings") as mock_get_settings:
        mock_config = MagicMock()
        mock_config.R2_ACCOUNT_ID = "test-account-id"
        mock_config.R2_ACCESS_KEY_ID = "test-access-key"
        mock_config.R2_SECRET_ACCESS_KEY = "test-secret-key"
        mock_config.R2_BUCKET_NAME = "test-bucket"
        mock_config.R2_REGION = "auto"
        mock_config.R2_PUBLIC_URL = ""
        mock_get_settings.return_value = mock_config
        yield mock_config


@pytest.fixture
def storage_service(mock_settings):
    """Create StorageService instance with mocked settings"""
    return StorageService()


@pytest.fixture
def mock_s3_client():
    """Create mock boto3 S3 client"""
    with patch("boto3.client") as mock_client:
        yield mock_client.return_value


def test_get_storage_service_singleton():
    """Test that get_storage_service returns the same instance"""
    service1 = get_storage_service()
    service2 = get_storage_service()
    assert service1 is service2


def test_init_storage_service(mock_settings):
    """Test StorageService initialization"""
    service = StorageService()
    assert service.settings == mock_settings
    assert service._client is None


def test_get_client_creates_boto3_client(storage_service, mock_s3_client, mock_settings):
    """Test that _get_client creates boto3 S3 client with correct config"""
    with patch("boto3.client") as mock_boto3:
        mock_boto3.return_value = mock_s3_client

        client = storage_service._get_client()

        # Verify boto3.client was called with correct parameters
        mock_boto3.assert_called_once()
        call_kwargs = mock_boto3.call_args[1]

        assert (
            call_kwargs["endpoint_url"]
            == f"https://{mock_settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        )
        assert call_kwargs["aws_access_key_id"] == mock_settings.R2_ACCESS_KEY_ID
        assert call_kwargs["aws_secret_access_key"] == mock_settings.R2_SECRET_ACCESS_KEY
        assert call_kwargs["region_name"] == mock_settings.R2_REGION
        assert client == mock_s3_client


def test_get_client_raises_error_without_account_id(mock_settings):
    """Test that _get_client raises error if R2_ACCOUNT_ID is not configured"""
    mock_settings.R2_ACCOUNT_ID = ""
    service = StorageService()

    with pytest.raises(ValueError, match="R2_ACCOUNT_ID is not configured"):
        service._get_client()


def test_get_client_raises_error_without_credentials(mock_settings):
    """Test that _get_client raises error if credentials are not configured"""
    mock_settings.R2_ACCESS_KEY_ID = ""
    service = StorageService()

    with pytest.raises(ValueError, match="R2 credentials"):
        service._get_client()


def test_upload_file_success(storage_service, mock_s3_client, mock_settings, tmp_path):
    """Test successful file upload to R2"""
    # Create temporary test file
    test_file = tmp_path / "test_resume.pdf"
    test_file.write_text("Test resume content")

    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        # Upload file
        result_url = storage_service.upload_file(
            file_path=str(test_file),
            object_key="resumes/user123/test.pdf",
            content_type="application/pdf",
        )

        # Verify put_object was called
        mock_s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_client.put_object.call_args[1]

        assert call_kwargs["Bucket"] == mock_settings.R2_BUCKET_NAME
        assert call_kwargs["Key"] == "resumes/user123/test.pdf"
        assert call_kwargs["ContentType"] == "application/pdf"

        # Verify URL was returned
        assert "resumes/user123/test.pdf" in result_url


def test_upload_file_not_found(storage_service, mock_s3_client):
    """Test upload raises error for non-existent file"""
    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        with pytest.raises(FileNotFoundError):
            storage_service.upload_file(
                file_path="/nonexistent/file.pdf", object_key="resumes/test.pdf"
            )


def test_upload_file_client_error(storage_service, mock_s3_client, tmp_path):
    """Test upload handles boto3 ClientError"""
    test_file = tmp_path / "test_resume.pdf"
    test_file.write_text("Test content")

    mock_s3_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied"}}, "put_object"
    )

    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        with pytest.raises(ClientError):
            storage_service.upload_file(file_path=str(test_file), object_key="resumes/test.pdf")


def test_download_file_success(storage_service, mock_s3_client, mock_settings, tmp_path):
    """Test successful file download from R2"""
    download_path = tmp_path / "downloaded_resume.pdf"

    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        storage_service.download_file(
            object_key="resumes/user123/test.pdf", local_path=str(download_path)
        )

        # Verify download_file was called
        mock_s3_client.download_file.assert_called_once_with(
            Bucket=mock_settings.R2_BUCKET_NAME,
            Key="resumes/user123/test.pdf",
            Filename=str(download_path),
        )


def test_delete_file_success(storage_service, mock_s3_client, mock_settings):
    """Test successful file deletion from R2"""
    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        result = storage_service.delete_file(object_key="resumes/user123/test.pdf")

        # Verify delete_object was called
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket=mock_settings.R2_BUCKET_NAME, Key="resumes/user123/test.pdf"
        )

        assert result is True


def test_generate_presigned_url_success(storage_service, mock_s3_client, mock_settings):
    """Test presigned URL generation"""
    mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com/test.pdf"

    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        url = storage_service.generate_presigned_url(
            object_key="resumes/user123/test.pdf", expiration=3600
        )

        # Verify generate_presigned_url was called
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": mock_settings.R2_BUCKET_NAME, "Key": "resumes/user123/test.pdf"},
            ExpiresIn=3600,
        )

        assert url == "https://presigned-url.com/test.pdf"


def test_file_exists_true(storage_service, mock_s3_client, mock_settings):
    """Test file_exists returns True when file exists"""
    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        exists = storage_service.file_exists(object_key="resumes/user123/test.pdf")

        # Verify head_object was called
        mock_s3_client.head_object.assert_called_once_with(
            Bucket=mock_settings.R2_BUCKET_NAME, Key="resumes/user123/test.pdf"
        )

        assert exists is True


def test_file_exists_false(storage_service, mock_s3_client, mock_settings):
    """Test file_exists returns False when file doesn't exist"""
    mock_s3_client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "head_object")

    with patch.object(storage_service, "_get_client", return_value=mock_s3_client):
        exists = storage_service.file_exists(object_key="resumes/user123/nonexistent.pdf")

        assert exists is False


def test_get_public_url_with_custom_domain(storage_service, mock_settings):
    """Test public URL generation with custom domain"""
    mock_settings.R2_PUBLIC_URL = "https://cdn.example.com"

    url = storage_service._get_public_url("resumes/user123/test.pdf")

    assert url == "https://cdn.example.com/resumes/user123/test.pdf"


def test_get_public_url_without_custom_domain(storage_service, mock_settings):
    """Test public URL generation without custom domain"""
    mock_settings.R2_PUBLIC_URL = ""

    url = storage_service._get_public_url("resumes/user123/test.pdf")

    expected = f"https://{mock_settings.R2_BUCKET_NAME}.{mock_settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/resumes/user123/test.pdf"  # noqa: E501
    assert url == expected
