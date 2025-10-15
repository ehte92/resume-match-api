#!/usr/bin/env python3
"""
Manual End-to-End Test Script for Analysis Endpoints.

Tests all 4 analysis endpoints with real HTTP requests to verify
they work correctly in a running server environment.

Usage:
    python scripts/test_analysis_manual.py
"""

import io
import time

import requests

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api"

# Test user credentials
TEST_USER = {
    "email": "test_analysis_manual@example.com",
    "password": "Test@1234",
    "full_name": "Manual Test User",
}

# Test colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_step(step_num, message):
    """Print a test step."""
    print(f"\n{BLUE}[STEP {step_num}]{RESET} {message}")


def print_success(message):
    """Print a success message."""
    print(f"{GREEN}✓{RESET} {message}")


def print_error(message):
    """Print an error message."""
    print(f"{RED}✗{RESET} {message}")


def print_info(message):
    """Print an info message."""
    print(f"{YELLOW}ℹ{RESET} {message}")


def register_user():
    """Register a test user. Returns True if successful or user already exists."""
    print_step(1, "Registering test user...")
    response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USER)

    if response.status_code == 201:
        print_success("User registered successfully")
        return True
    elif response.status_code == 400 and "already registered" in response.text.lower():
        print_info("User already exists, continuing...")
        return True
    else:
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return False


def login_user():
    """Login and get JWT token. Returns token or None."""
    print_step(2, "Logging in...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print_success(f"Login successful, token: {token[:20]}...")
        return token
    else:
        print_error(f"Login failed: {response.status_code} - {response.text}")
        return None


def create_sample_pdf():
    """Create a sample PDF file for testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
endobj
5 0 obj
<< /Length 100 >>
stream
BT
/F1 12 Tf
100 700 Td
(John Doe) Tj
0 -20 Td
(Software Engineer) Tj
0 -20 Td
(Skills: Python, FastAPI, Docker, PostgreSQL) Tj
0 -20 Td
(Experience: 5 years at Tech Corp) Tj
0 -20 Td
(Education: BS Computer Science, MIT) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
0000000299 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
450
%%EOF
"""
    return io.BytesIO(pdf_content)


def test_create_analysis(token):
    """Test POST /api/analyses/create endpoint."""
    print_step(3, "Testing POST /api/analyses/create...")

    # Prepare file
    pdf_file = create_sample_pdf()

    # Prepare data
    data = {
        "job_description": (
            "We are looking for a Senior Python Developer with 5+ years of experience. "
            "Must have expertise in FastAPI, Docker, PostgreSQL, and AWS. "
            "Experience with Kubernetes is a plus."
        ),
        "job_title": "Senior Python Developer",
        "company_name": "Tech Innovations Inc.",
    }

    # Prepare headers
    headers = {"Authorization": f"Bearer {token}"}

    # Send request
    files = {"file": ("test_resume.pdf", pdf_file, "application/pdf")}

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data, files=files
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 201:
        result = response.json()
        analysis_id = result.get("id")

        print_success(f"Analysis created successfully in {elapsed:.0f}ms")
        print_info(f"Analysis ID: {analysis_id}")
        print_info(f"Match Score: {result.get('match_score')}")
        print_info(f"ATS Score: {result.get('ats_score')}")
        print_info(f"Semantic Similarity: {result.get('semantic_similarity')}")
        print_info(f"Matching Keywords: {', '.join(result.get('matching_keywords', []))}")
        print_info(f"Missing Keywords: {', '.join(result.get('missing_keywords', []))}")
        print_info(f"ATS Issues: {len(result.get('ats_issues', []))}")

        return analysis_id
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None


def test_list_analyses(token):
    """Test GET /api/analyses/ endpoint."""
    print_step(4, "Testing GET /api/analyses/ (list)...")

    headers = {"Authorization": f"Bearer {token}"}

    # Test without pagination
    response = requests.get(f"{BASE_URL}{API_PREFIX}/analyses/", headers=headers)

    if response.status_code == 200:
        result = response.json()
        analyses = result.get("analyses", [])
        total = result.get("total", 0)

        print_success("List retrieved successfully")
        print_info(f"Total analyses: {total}")
        print_info(f"Analyses in page: {len(analyses)}")
        print_info(f"Page: {result.get('page')}, Page size: {result.get('page_size')}")

        # Test with pagination
        response2 = requests.get(
            f"{BASE_URL}{API_PREFIX}/analyses/?page=1&page_size=5", headers=headers
        )
        if response2.status_code == 200:
            result2 = response2.json()
            print_info(f"Pagination test: Got {len(result2.get('analyses', []))} analyses")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_get_analysis(token, analysis_id):
    """Test GET /api/analyses/{id} endpoint."""
    print_step(5, f"Testing GET /api/analyses/{analysis_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}{API_PREFIX}/analyses/{analysis_id}", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print_success("Analysis retrieved successfully")
        print_info(f"ID: {result.get('id')}")
        print_info(f"Job Title: {result.get('job_title')}")
        print_info(f"Company: {result.get('company_name')}")
        print_info(f"Match Score: {result.get('match_score')}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_delete_analysis(token, analysis_id):
    """Test DELETE /api/analyses/{id} endpoint."""
    print_step(6, f"Testing DELETE /api/analyses/{analysis_id}...")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(f"{BASE_URL}{API_PREFIX}/analyses/{analysis_id}", headers=headers)

    if response.status_code == 204:
        print_success("Analysis deleted successfully")

        # Verify deletion
        response2 = requests.get(
            f"{BASE_URL}{API_PREFIX}/analyses/{analysis_id}", headers=headers
        )
        if response2.status_code == 404:
            print_success("Verified: Analysis no longer exists")
            return True
        else:
            print_error("Verification failed: Analysis still exists")
            return False
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def main():
    """Run all manual tests."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Manual End-to-End Test for Analysis Endpoints{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Step 1: Register user
    if not register_user():
        print_error("Cannot continue without user registration")
        return False

    # Step 2: Login
    token = login_user()
    if not token:
        print_error("Cannot continue without authentication")
        return False

    # Step 3: Create analysis
    analysis_id = test_create_analysis(token)
    if not analysis_id:
        print_error("Cannot continue without analysis creation")
        return False

    # Step 4: List analyses
    if not test_list_analyses(token):
        print_error("List test failed")
        return False

    # Step 5: Get specific analysis
    if not test_get_analysis(token, analysis_id):
        print_error("Get test failed")
        return False

    # Step 6: Delete analysis
    if not test_delete_analysis(token, analysis_id):
        print_error("Delete test failed")
        return False

    # Summary
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}✓ All tests passed successfully!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback

        traceback.print_exc()
        exit(1)
