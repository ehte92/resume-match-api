# Cloudflare R2 Storage Setup Guide

This guide explains how to configure Cloudflare R2 (S3-compatible) storage for resume file uploads in the AI Resume Optimizer backend.

## Overview

The application supports two storage backends:
- **Local Storage**: Files stored temporarily in `/tmp/resume_uploads` (default)
- **Cloudflare R2**: Files stored permanently in Cloudflare R2 object storage

## Features

✅ S3-compatible API using boto3
✅ Automatic file upload to R2
✅ Presigned URLs for secure downloads
✅ File deletion from R2
✅ Configurable storage backend
✅ Free tier: 10GB storage + 10M read/write requests/month

## Setup Instructions

### 1. Create Cloudflare R2 Account

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **R2 Object Storage**
3. Click **Create bucket**
4. Name your bucket (e.g., `resume-uploads`)
5. Create the bucket

### 2. Generate R2 API Credentials

1. In R2 dashboard, go to **Manage R2 API Tokens**
2. Click **Create API Token**
3. Set permissions:
   - **Object Read & Write**
   - Scope: Apply to specific bucket or all buckets
4. Copy the credentials:
   - **Access Key ID**
   - **Secret Access Key**
   - **Account ID** (from R2 dashboard URL: `https://dash.cloudflare.com/<ACCOUNT_ID>/r2`)

### 3. Configure Environment Variables

Update your `.env` file:

```bash
# Storage Configuration
STORAGE_BACKEND=r2  # Change from 'local' to 'r2'

# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-account-id-here
R2_ACCESS_KEY_ID=your-access-key-id-here
R2_SECRET_ACCESS_KEY=your-secret-access-key-here
R2_BUCKET_NAME=resume-uploads
R2_REGION=auto
R2_PUBLIC_URL=  # Optional: https://your-custom-domain.com
```

### 4. Test the Configuration

```bash
# Run storage service tests
pytest tests/test_storage_service.py -v

# All 15 tests should pass
```

## Usage Examples

### Upload File to R2

```python
from app.utils.file_handler import save_file_with_storage

# Upload file with R2 enabled
result = await save_file_with_storage(
    upload_file=uploaded_file,
    user_id="user-uuid",
    use_r2=True
)

# Result contains:
# {
#     "local_path": "/tmp/resume_uploads/uuid.pdf",
#     "storage_url": "https://resume-uploads.account-id.r2.cloudflarestorage.com/resumes/user-uuid/uuid.pdf",
#     "storage_key": "resumes/user-uuid/uuid.pdf",
#     "storage_backend": "r2"
# }
```

### Generate Presigned URL

```python
from app.services.storage_service import get_storage_service

storage = get_storage_service()

# Generate URL that expires in 1 hour
presigned_url = storage.generate_presigned_url(
    object_key="resumes/user-uuid/resume.pdf",
    expiration=3600
)
```

### Delete File from R2

```python
from app.utils.file_handler import delete_from_storage

delete_from_storage(
    storage_backend="r2",
    storage_key="resumes/user-uuid/resume.pdf"
)
```

## Database Schema

The `resumes` table includes storage-related columns:

```sql
ALTER TABLE resumes ADD COLUMN storage_backend VARCHAR(20) DEFAULT 'local';
ALTER TABLE resumes ADD COLUMN storage_url TEXT;
ALTER TABLE resumes ADD COLUMN storage_key TEXT;
```

- `storage_backend`: 'local' or 'r2'
- `storage_url`: Public R2 URL for the file
- `storage_key`: R2 object key (used for deletion)

## Architecture

```
User Upload → FastAPI
    ↓
File Handler (validate)
    ↓
Save to /tmp (temporary)
    ↓
Storage Service → R2 Upload
    ↓
Database (save metadata)
    ↓
Delete local temp file
```

## Cost Considerations

### Cloudflare R2 Free Tier
- **Storage**: 10 GB/month
- **Class A Operations** (writes): 1 million/month
- **Class B Operations** (reads): 10 million/month

### Estimated Usage
- Average resume size: 500 KB
- Free tier supports: ~20,000 resumes
- 10M reads = millions of downloads

## Security Best Practices

1. **Never commit credentials**: Keep R2 credentials in `.env` only
2. **Use presigned URLs**: For temporary file access
3. **Set CORS policies**: Configure allowed origins in R2
4. **Implement access control**: Verify user ownership before generating URLs
5. **Enable versioning**: Optional R2 bucket versioning for backup

## Troubleshooting

### Error: "R2_ACCOUNT_ID is not configured"
- Ensure `R2_ACCOUNT_ID` is set in `.env`
- Restart the application after updating `.env`

### Error: "Failed to upload to R2"
- Verify API credentials are correct
- Check bucket name matches `R2_BUCKET_NAME`
- Ensure bucket has write permissions
- Check network connectivity

### Files not accessible publicly
- R2 buckets are private by default
- Use presigned URLs for downloads
- Or configure custom domain with public access

## Migration Strategy

### Development
1. Keep `STORAGE_BACKEND=local` for local testing
2. Test R2 integration in staging environment
3. Monitor for errors before production

### Production
1. Set `STORAGE_BACKEND=r2`
2. Existing local files remain accessible
3. New uploads go to R2
4. Optionally migrate old files with script

## Custom Domain Setup (Optional)

1. In Cloudflare R2, go to bucket settings
2. Add custom domain (e.g., `cdn.yourapp.com`)
3. Update `.env`:
   ```bash
   R2_PUBLIC_URL=https://cdn.yourapp.com
   ```
4. Files will be accessible via custom domain

## API Reference

### StorageService Methods

- `upload_file(file_path, object_key, content_type)` - Upload file to R2
- `download_file(object_key, local_path)` - Download from R2
- `delete_file(object_key)` - Delete from R2
- `generate_presigned_url(object_key, expiration)` - Generate signed URL
- `file_exists(object_key)` - Check if file exists

### File Handler Methods

- `save_file_with_storage(upload_file, user_id, use_r2)` - Save with storage
- `delete_from_storage(storage_backend, storage_key)` - Delete from storage

## Testing

Run all tests:

```bash
# Test storage service
pytest tests/test_storage_service.py -v

# Test file handler
pytest tests/test_file_handler.py -v

# Test with coverage
pytest --cov=app/services/storage_service --cov=app/utils/file_handler
```

## Support

For issues or questions:
- Check [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- Review [boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- Open issue in project repository

---

**Last Updated**: October 15, 2025
**Version**: 1.0.0
