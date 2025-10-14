"""
Test script to verify R2 connection and upload functionality.
This script tests actual R2 connectivity with your credentials.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.services.storage_service import get_storage_service


def test_r2_configuration():
    """Test that R2 configuration is properly loaded"""
    print("=" * 60)
    print("TESTING R2 CONFIGURATION")
    print("=" * 60)

    settings = get_settings()

    print(f"\n✓ Storage Backend: {settings.STORAGE_BACKEND}")
    print(f"✓ R2 Account ID: {settings.R2_ACCOUNT_ID[:8]}..." if settings.R2_ACCOUNT_ID else "✗ R2 Account ID: NOT SET")
    print(f"✓ R2 Access Key: {settings.R2_ACCESS_KEY_ID[:8]}..." if settings.R2_ACCESS_KEY_ID else "✗ R2 Access Key: NOT SET")
    print(f"✓ R2 Secret Key: {'*' * 20}" if settings.R2_SECRET_ACCESS_KEY else "✗ R2 Secret Key: NOT SET")
    print(f"✓ R2 Bucket Name: {settings.R2_BUCKET_NAME}")
    print(f"✓ R2 Region: {settings.R2_REGION}")

    # Check if all required settings are present
    if not settings.R2_ACCOUNT_ID:
        print("\n✗ ERROR: R2_ACCOUNT_ID is not configured")
        return False

    if not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY:
        print("\n✗ ERROR: R2 credentials are not configured")
        return False

    print("\n✓ All configuration values are set!")
    return True


def test_r2_client_initialization():
    """Test that R2 client can be initialized"""
    print("\n" + "=" * 60)
    print("TESTING R2 CLIENT INITIALIZATION")
    print("=" * 60)

    try:
        storage = get_storage_service()
        client = storage._get_client()

        print("\n✓ R2 client initialized successfully!")
        print(f"✓ Endpoint: https://{storage.settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com")
        return True

    except Exception as e:
        print(f"\n✗ ERROR: Failed to initialize R2 client")
        print(f"  Error: {str(e)}")
        return False


def test_r2_bucket_access():
    """Test that we can access the R2 bucket"""
    print("\n" + "=" * 60)
    print("TESTING R2 BUCKET ACCESS")
    print("=" * 60)

    try:
        storage = get_storage_service()
        client = storage._get_client()

        # Try to list objects (just the first one)
        print(f"\nAttempting to list objects in bucket: {storage.settings.R2_BUCKET_NAME}")

        response = client.list_objects_v2(
            Bucket=storage.settings.R2_BUCKET_NAME,
            MaxKeys=1
        )

        print(f"\n✓ Bucket is accessible!")
        print(f"✓ Bucket contains {response.get('KeyCount', 0)} objects (showing max 1)")

        if 'Contents' in response and len(response['Contents']) > 0:
            print(f"✓ Sample object: {response['Contents'][0]['Key']}")

        return True

    except Exception as e:
        print(f"\n✗ ERROR: Failed to access bucket")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error: {str(e)}")

        if "NoSuchBucket" in str(e):
            print(f"\n  Hint: Bucket '{storage.settings.R2_BUCKET_NAME}' does not exist.")
            print(f"        Create it in Cloudflare R2 dashboard.")
        elif "InvalidAccessKeyId" in str(e):
            print(f"\n  Hint: Access Key ID is invalid.")
            print(f"        Check R2_ACCESS_KEY_ID in .env")
        elif "SignatureDoesNotMatch" in str(e):
            print(f"\n  Hint: Secret Access Key is incorrect.")
            print(f"        Check R2_SECRET_ACCESS_KEY in .env")

        return False


def test_r2_upload():
    """Test uploading a file to R2"""
    print("\n" + "=" * 60)
    print("TESTING R2 FILE UPLOAD")
    print("=" * 60)

    try:
        storage = get_storage_service()

        # Create a test file
        test_file_path = "/tmp/test_r2_upload.txt"
        test_content = "This is a test file for R2 upload verification.\nTimestamp: " + str(os.time.time() if hasattr(os, 'time') else 'unknown')

        with open(test_file_path, "w") as f:
            f.write(test_content)

        print(f"\n✓ Created test file: {test_file_path}")

        # Upload to R2
        object_key = "test/test_upload_verification.txt"
        print(f"✓ Uploading to R2 with key: {object_key}")

        url = storage.upload_file(
            file_path=test_file_path,
            object_key=object_key,
            content_type="text/plain"
        )

        print(f"\n✓ Upload successful!")
        print(f"✓ File URL: {url}")

        # Verify the file exists
        exists = storage.file_exists(object_key)
        print(f"✓ File exists in R2: {exists}")

        # Generate presigned URL
        presigned_url = storage.generate_presigned_url(object_key, expiration=300)
        print(f"✓ Presigned URL (expires in 5 min):\n  {presigned_url}")

        # Clean up local test file
        os.remove(test_file_path)
        print(f"\n✓ Cleaned up local test file")

        print(f"\n✓✓✓ R2 UPLOAD TEST PASSED! ✓✓✓")
        print(f"\nNote: Test file '{object_key}' was uploaded to your bucket.")
        print(f"      You can delete it manually or leave it for reference.")

        return True

    except Exception as e:
        print(f"\n✗ ERROR: Failed to upload file")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error: {str(e)}")

        # Clean up on error
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

        return False


def main():
    """Run all R2 tests"""
    print("\n" + "=" * 60)
    print("R2 STORAGE CONNECTION TEST")
    print("=" * 60)
    print("\nThis script will test your R2 configuration and connectivity.")
    print("Make sure you have set R2 credentials in your .env file.\n")

    # Run tests in sequence
    tests = [
        ("Configuration", test_r2_configuration),
        ("Client Initialization", test_r2_client_initialization),
        ("Bucket Access", test_r2_bucket_access),
        ("File Upload", test_r2_upload),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))

            if not success:
                print(f"\n⚠️  Stopping tests - {test_name} failed")
                break

        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))
            break

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n🎉 All R2 tests passed! Your storage is ready to use.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
