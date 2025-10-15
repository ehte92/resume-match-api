"""
Storage service for uploading files to Cloudflare R2 (S3-compatible).
Handles file uploads, downloads, deletion, and presigned URL generation.
"""

import logging
from typing import Optional
from urllib.parse import urljoin

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for managing file storage in Cloudflare R2 (S3-compatible storage).

    Uses boto3 S3 client configured for Cloudflare R2 endpoints.
    """

    def __init__(self):
        """Initialize the storage service with R2 credentials from settings."""
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        """
        Get or create boto3 S3 client configured for Cloudflare R2.

        Returns:
            boto3 S3 client instance

        Raises:
            ValueError: If R2 credentials are not configured
        """
        if self._client is not None:
            return self._client

        if not self.settings.R2_ACCOUNT_ID:
            raise ValueError("R2_ACCOUNT_ID is not configured")

        if not self.settings.R2_ACCESS_KEY_ID or not self.settings.R2_SECRET_ACCESS_KEY:
            raise ValueError(
                "R2 credentials (ACCESS_KEY_ID and SECRET_ACCESS_KEY) are not configured"
            )

        # Construct R2 endpoint URL
        endpoint_url = f"https://{self.settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

        # Create boto3 S3 client with R2 configuration
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=self.settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name=self.settings.R2_REGION,
        )

        logger.info(f"Initialized R2 client for bucket: {self.settings.R2_BUCKET_NAME}")
        return self._client

    def upload_file(
        self, file_path: str, object_key: str, content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to R2 storage.

        Args:
            file_path: Local path to the file to upload
            object_key: S3 object key (path in bucket, e.g., 'resumes/user123/file.pdf')
            content_type: MIME type of the file (e.g., 'application/pdf')

        Returns:
            Public URL of the uploaded file

        Raises:
            ClientError: If upload fails
            FileNotFoundError: If local file doesn't exist
        """
        try:
            client = self._get_client()

            # Prepare upload arguments
            upload_args = {"ContentType": content_type} if content_type else {}

            # Upload file to R2
            with open(file_path, "rb") as file_data:
                client.put_object(
                    Bucket=self.settings.R2_BUCKET_NAME,
                    Key=object_key,
                    Body=file_data,
                    **upload_args,
                )

            logger.info(f"Uploaded file to R2: {object_key}")

            # Return public URL
            return self._get_public_url(object_key)

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {e}")
            raise

    def download_file(self, object_key: str, local_path: str) -> None:
        """
        Download a file from R2 storage.

        Args:
            object_key: S3 object key in the bucket
            local_path: Local path where file should be saved

        Raises:
            ClientError: If download fails
        """
        try:
            client = self._get_client()

            client.download_file(
                Bucket=self.settings.R2_BUCKET_NAME, Key=object_key, Filename=local_path
            )

            logger.info(f"Downloaded file from R2: {object_key} -> {local_path}")

        except ClientError as e:
            logger.error(f"Failed to download file from R2: {e}")
            raise

    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from R2 storage.

        Args:
            object_key: S3 object key to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            ClientError: If deletion fails
        """
        try:
            client = self._get_client()

            client.delete_object(Bucket=self.settings.R2_BUCKET_NAME, Key=object_key)

            logger.info(f"Deleted file from R2: {object_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete file from R2: {e}")
            raise

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to a file.

        Args:
            object_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL for downloading the file

        Raises:
            ClientError: If URL generation fails
        """
        try:
            client = self._get_client()

            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.settings.R2_BUCKET_NAME, "Key": object_key},
                ExpiresIn=expiration,
            )

            logger.info(f"Generated presigned URL for: {object_key} (expires in {expiration}s)")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in R2 storage.

        Args:
            object_key: S3 object key to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            client = self._get_client()

            client.head_object(Bucket=self.settings.R2_BUCKET_NAME, Key=object_key)

            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking file existence: {e}")
            raise

    def _get_public_url(self, object_key: str) -> str:
        """
        Get the public URL for an object.

        Args:
            object_key: S3 object key

        Returns:
            Public URL (custom domain if configured, otherwise R2 public URL)
        """
        # If custom public URL is configured, use it
        if self.settings.R2_PUBLIC_URL:
            return urljoin(self.settings.R2_PUBLIC_URL, object_key)

        # Otherwise, construct R2 public URL
        # Note: R2 buckets need to have public access enabled for this to work
        return f"https://{self.settings.R2_BUCKET_NAME}.{self.settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{object_key}"  # noqa: E501


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    Get singleton instance of StorageService.

    Returns:
        StorageService instance
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
