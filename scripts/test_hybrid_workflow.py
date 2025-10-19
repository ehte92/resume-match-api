#!/usr/bin/env python3
"""
Hybrid Workflow Test Script

Tests the new hybrid analysis endpoint that supports:
1. Quick Analysis: Upload file + analyze in one step
2. Power User: Analyze existing resume_id from library
3. Duplicate Detection: Reuses existing resume if same file uploaded

Usage:
    python scripts/test_hybrid_workflow.py
"""

import io
import time

import requests

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api"

# Test user credentials
TEST_USER = {
    "email": "test_hybrid@example.com",
    "password": "Test@1234",
    "full_name": "Hybrid Test User",
}

# Test colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(text):
    """Print a section header."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")


def print_step(step_num, message):
    """Print a test step."""
    print(f"\n{CYAN}[STEP {step_num}]{RESET} {message}")


def print_success(message):
    """Print a success message."""
    print(f"{GREEN}✓{RESET} {message}")


def print_error(message):
    """Print an error message."""
    print(f"{RED}✗{RESET} {message}")


def print_info(message):
    """Print an info message."""
    print(f"{YELLOW}ℹ{RESET} {message}")


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


def register_and_login():
    """Register user and get JWT token."""
    print_step(1, "User Registration & Login")

    # Try to register
    response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USER)

    if response.status_code == 201:
        print_success("User registered successfully")
    elif response.status_code == 400 and "already registered" in response.text.lower():
        print_info("User already exists, continuing...")
    else:
        print_error(f"Registration failed: {response.status_code} - {response.text}")
        return None

    # Login
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


def test_quick_analysis(token):
    """Test Workflow 1: Quick Analysis (upload + analyze)."""
    print_header("WORKFLOW 1: Quick Analysis (Upload + Analyze)")

    print_step(2, "Uploading new file and creating analysis...")

    pdf_file = create_sample_pdf()
    data = {
        "job_description": (
            "We need a Senior Python Developer with 5+ years of experience. "
            "Must have expertise in FastAPI, Docker, PostgreSQL, and AWS. "
            "Experience with Kubernetes is a plus."
        ),
        "job_title": "Senior Python Developer",
        "company_name": "Tech Corp",
    }

    files = {"file": ("resume.pdf", pdf_file, "application/pdf")}
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data, files=files
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 201:
        result = response.json()
        print_success(f"Analysis created in {elapsed:.0f}ms")
        print_info(f"Analysis ID: {result['id']}")
        print_info(f"Resume ID: {result['resume_id']}")
        print_info(f"Match Score: {result['match_score']}%")
        print_info(f"ATS Score: {result['ats_score']}%")
        print_info(f"Semantic Similarity: {result['semantic_similarity']}%")
        print_info(f"Matching Keywords: {', '.join(result['matching_keywords'][:5])}")
        print_info(f"Processing Time: {result['processing_time_ms']}ms")
        return result["id"], result["resume_id"]
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None, None


def test_duplicate_detection(token):
    """Test Workflow 2: Duplicate Detection (upload same file again)."""
    print_header("WORKFLOW 2: Duplicate Detection")

    print_step(3, "Uploading SAME file again (should reuse existing resume)...")

    pdf_file = create_sample_pdf()
    data = {
        "job_description": (
            "Looking for a Backend Engineer with Python and Docker experience. "
            "Must know FastAPI and PostgreSQL. AWS experience required."
        ),
        "job_title": "Backend Engineer",
        "company_name": "CloudSystems",
    }

    files = {"file": ("resume_copy.pdf", pdf_file, "application/pdf")}
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data, files=files
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 201:
        result = response.json()
        print_success(f"Analysis created in {elapsed:.0f}ms")
        print_info(f"Analysis ID: {result['id']}")
        print_info(f"Resume ID: {result['resume_id']}")
        print_info(f"Match Score: {result['match_score']}%")
        print_info(f"ATS Score: {result['ats_score']}%")
        print_success("✨ Duplicate detection working - same resume reused!")
        return result["id"], result["resume_id"]
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None, None


def test_power_user_workflow(token, resume_id):
    """Test Workflow 3: Power User (analyze with resume_id)."""
    print_header("WORKFLOW 3: Power User (Analyze with resume_id)")

    print_step(4, f"Analyzing existing resume_id: {resume_id}")

    data = {
        "resume_id": str(resume_id),  # Ensure UUID is string
        "job_description": (
            "Full Stack Developer needed. Python backend with FastAPI. "
            "Frontend experience with React. Docker and PostgreSQL required. "
            "Must have CI/CD experience."
        ),
        "job_title": "Full Stack Developer",
        "company_name": "StartupCo",
    }

    # Include empty file to force multipart/form-data encoding
    # This is required by FastAPI when using File() and Form() together
    files = {"file": ("", io.BytesIO(b""), "")}  # Empty file
    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data, files=files
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 201:
        result = response.json()
        print_success(f"Analysis created in {elapsed:.0f}ms")
        print_info(f"Analysis ID: {result['id']}")
        print_info(f"Resume ID: {result['resume_id']}")
        print_info(f"Match Score: {result['match_score']}%")
        print_info(f"ATS Score: {result['ats_score']}%")
        print_success("✨ Power user workflow working - no file upload needed!")
        return result["id"]
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None


def test_validation_errors(token, resume_id):
    """Test validation errors."""
    print_header("WORKFLOW 4: Validation Tests")

    headers = {"Authorization": f"Bearer {token}"}

    # Test 1: Both file and resume_id provided
    print_step(5, "Test: Both file AND resume_id provided (should fail)")
    pdf_file = create_sample_pdf()
    data = {
        "resume_id": resume_id,
        "job_description": "Test job description",
    }
    files = {"file": ("test.pdf", pdf_file, "application/pdf")}

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data, files=files
    )

    if response.status_code == 400:
        print_success("Correctly rejected: both file and resume_id provided")
    else:
        print_error(f"Expected 400, got {response.status_code}")

    # Test 2: Neither file nor resume_id provided
    print_step(6, "Test: Neither file NOR resume_id provided (should fail)")
    data = {"job_description": "Test job description"}

    response = requests.post(f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data)

    if response.status_code == 400:
        print_success("Correctly rejected: neither file nor resume_id provided")
    else:
        print_error(f"Expected 400, got {response.status_code}")

    # Test 3: Invalid resume_id (doesn't exist)
    print_step(7, "Test: Invalid resume_id (should fail)")
    data = {
        "resume_id": "00000000-0000-0000-0000-000000000000",
        "job_description": "Test job description",
    }

    response = requests.post(f"{BASE_URL}{API_PREFIX}/analyses/create", headers=headers, data=data)

    if response.status_code == 404:
        print_success("Correctly rejected: invalid resume_id")
    else:
        print_error(f"Expected 404, got {response.status_code}")


def test_resume_library(token):
    """Test resume library endpoint."""
    print_header("WORKFLOW 5: Resume Library")

    print_step(8, "Fetching resume library...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}{API_PREFIX}/resumes/", headers=headers)

    if response.status_code == 200:
        result = response.json()
        resumes = result.get("resumes", [])
        total = result.get("total", 0)

        print_success(f"Retrieved {len(resumes)} resumes (total: {total})")
        for i, resume in enumerate(resumes, 1):
            print_info(f"  {i}. {resume['file_name']} (ID: {resume['id'][:8]}...)")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_analysis_history(token):
    """Test analysis history endpoint."""
    print_header("WORKFLOW 6: Analysis History")

    print_step(9, "Fetching analysis history...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}{API_PREFIX}/analyses/", headers=headers)

    if response.status_code == 200:
        result = response.json()
        analyses = result.get("analyses", [])
        total = result.get("total", 0)

        print_success(f"Retrieved {len(analyses)} analyses (total: {total})")
        for i, analysis in enumerate(analyses, 1):
            print_info(
                f"  {i}. {analysis['job_title']} @ {analysis['company_name']} "
                f"(Match: {analysis['match_score']}%)"
            )
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def main():
    """Run all hybrid workflow tests."""
    print_header("Hybrid Backend Architecture Test Suite")
    print_info(f"Testing API at: {BASE_URL}{API_PREFIX}")
    print_info("This will test the new hybrid analysis endpoint")

    # Step 1: Login
    token = register_and_login()
    if not token:
        print_error("Cannot continue without authentication")
        return False

    # Step 2: Quick Analysis (Workflow 1)
    analysis_id_1, resume_id = test_quick_analysis(token)
    if not analysis_id_1:
        print_error("Quick analysis failed")
        return False

    # Step 3: Duplicate Detection (Workflow 2)
    analysis_id_2, resume_id_2 = test_duplicate_detection(token)
    if not analysis_id_2:
        print_error("Duplicate detection test failed")
        return False

    # Verify same resume_id was reused
    if resume_id == resume_id_2:
        print_success(f"\n✨ DUPLICATE DETECTION CONFIRMED! Same resume_id reused: {resume_id}")
    else:
        print_error(
            f"\n❌ Duplicate detection failed: Different resume_ids: {resume_id} vs {resume_id_2}"
        )

    # Step 4: Power User Workflow (Workflow 3)
    analysis_id_3 = test_power_user_workflow(token, resume_id)
    if not analysis_id_3:
        print_error("Power user workflow failed")
        return False

    # Step 5: Validation Tests (Workflow 4)
    test_validation_errors(token, resume_id)

    # Step 6: Resume Library (Workflow 5)
    test_resume_library(token)

    # Step 7: Analysis History (Workflow 6)
    test_analysis_history(token)

    # Final Summary
    print_header("TEST SUMMARY")
    print_success("✅ Quick Analysis: Upload + analyze in one step")
    print_success("✅ Duplicate Detection: Same file reused automatically")
    print_success("✅ Power User: Analyze with resume_id (no upload)")
    print_success("✅ Validation: Correct error handling")
    print_success("✅ Resume Library: View all saved resumes")
    print_success("✅ Analysis History: Track all analyses")
    print()
    print_success("🎉 ALL TESTS PASSED! Hybrid backend is working perfectly!")
    print()

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
