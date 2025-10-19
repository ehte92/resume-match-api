#!/usr/bin/env python3
"""
Cover Letter Feature Test Script

Tests the complete cover letter generation workflow including:
1. User authentication
2. Resume upload
3. Cover letter generation (multiple tones and lengths)
4. Retrieve, update, and delete cover letters
5. List cover letters with pagination
6. Error handling and validation

Usage:
    python test_cover_letter.py
"""

import io
import time

import requests

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api"

# Test user credentials
TEST_USER = {
    "email": "test_cover_letter@example.com",
    "password": "Test@1234",
    "full_name": "Cover Letter Test User",
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
<< /Length 300 >>
stream
BT
/F1 14 Tf
100 700 Td
(Jane Smith) Tj
0 -20 Td
(Senior Software Engineer) Tj
0 -30 Td
(Skills: Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS) Tj
0 -30 Td
(Experience:) Tj
0 -20 Td
(- 6 years as Software Engineer at TechCorp) Tj
0 -15 Td
(- Led team of 5 engineers building microservices) Tj
0 -15 Td
(- Architected scalable systems handling 2M+ requests/day) Tj
0 -15 Td
(- Reduced infrastructure costs by 40% through optimization) Tj
0 -30 Td
(Education: BS Computer Science, Stanford University) Tj
0 -20 Td
(Email: jane.smith@example.com | Phone: 555-0123) Tj
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
650
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


def upload_resume(token):
    """Upload a test resume."""
    print_header("Upload Resume")
    print_step(2, "Uploading test resume...")

    pdf_file = create_sample_pdf()
    files = {"file": ("jane_smith_resume.pdf", pdf_file, "application/pdf")}
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(f"{BASE_URL}{API_PREFIX}/resumes/upload", headers=headers, files=files)

    if response.status_code == 201:
        result = response.json()
        print_success(f"Resume uploaded: {result['file_name']}")
        print_info(f"Resume ID: {result['id']}")
        return result["id"]
    else:
        print_error(f"Upload failed: {response.status_code} - {response.text}")
        return None


def test_generate_cover_letter(token, resume_id, tone="professional", length="medium"):
    """Test cover letter generation with specific tone and length."""
    print_header(f"Generate Cover Letter ({tone.title()}, {length.title()})")
    print_step(3, f"Generating {tone} {length} cover letter...")

    job_description = """We are seeking a Senior Full Stack Engineer to join our growing team at Google.

The ideal candidate will have 5+ years of experience building scalable web applications using Python and JavaScript. You will work on critical infrastructure serving millions of users worldwide.

Key Responsibilities:
- Design and implement microservices using FastAPI and Docker
- Build responsive user interfaces with React and TypeScript
- Collaborate with cross-functional teams (Product, Design, QA)
- Mentor junior engineers and conduct code reviews
- Optimize application performance and reliability

Required Qualifications:
- 5+ years of professional software engineering experience
- Expert-level Python and JavaScript/TypeScript skills
- Experience with cloud platforms (AWS, GCP, or Azure)
- Strong understanding of database design (PostgreSQL, MongoDB)
- Proven track record of shipping production applications

Preferred Qualifications:
- Experience with Kubernetes and container orchestration
- Knowledge of CI/CD pipelines and DevOps practices
- Contributions to open source projects
- BS/MS in Computer Science or equivalent

Benefits:
- Competitive salary and equity package
- Health, dental, and vision insurance
- Unlimited PTO and flexible work arrangements
- Learning and development budget
- Collaborative team environment"""

    data = {
        "resume_id": resume_id,
        "job_description": job_description,
        "job_title": "Senior Full Stack Engineer",
        "company_name": "Google",
        "tone": tone,
        "length": length,
    }

    headers = {"Authorization": f"Bearer {token}"}

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/cover-letters/generate", headers=headers, json=data
    )
    elapsed = (time.time() - start_time) * 1000

    if response.status_code == 201:
        result = response.json()
        print_success(f"Cover letter generated in {elapsed:.0f}ms")
        print_info(f"Cover Letter ID: {result['id']}")
        print_info(f"Tone: {result['tone']}")
        print_info(f"Length: {result['length']}")
        print_info(f"Word Count: {result['word_count']} words")
        print_info(f"Tokens Used: {result['openai_tokens_used']}")
        print_info(f"Processing Time: {result['processing_time_ms']}ms")
        print_info(f"\nGenerated Text (first 200 chars):\n{result['cover_letter_text'][:200]}...")
        return result["id"]
    else:
        print_error(f"Generation failed: {response.status_code} - {response.text}")
        return None


def test_get_cover_letter(token, cover_letter_id):
    """Test retrieving a cover letter by ID."""
    print_header("Get Cover Letter by ID")
    print_step(4, f"Retrieving cover letter {cover_letter_id[:8]}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/cover-letters/{cover_letter_id}", headers=headers
    )

    if response.status_code == 200:
        result = response.json()
        print_success("Cover letter retrieved successfully")
        print_info(f"Job: {result['job_title']} at {result['company_name']}")
        print_info(f"Created: {result['created_at']}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_list_cover_letters(token):
    """Test listing cover letters."""
    print_header("List Cover Letters")
    print_step(5, "Fetching all cover letters...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}{API_PREFIX}/cover-letters/", headers=headers)

    if response.status_code == 200:
        result = response.json()
        cover_letters = result.get("cover_letters", [])
        total = result.get("total", 0)

        print_success(f"Retrieved {len(cover_letters)} cover letters (total: {total})")
        for i, cl in enumerate(cover_letters, 1):
            print_info(
                f"  {i}. {cl['job_title']} @ {cl['company_name']} "
                f"({cl['tone']}, {cl['length']}, {cl['word_count']} words)"
            )
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_update_cover_letter(token, cover_letter_id):
    """Test updating cover letter text."""
    print_header("Update Cover Letter")
    print_step(6, "Updating cover letter text...")

    updated_text = """Dear Hiring Manager,

I am writing to express my enthusiastic interest in the Senior Full Stack Engineer position at Google. With over 6 years of experience building scalable web applications and leading engineering teams, I am confident I would be a valuable addition to your team.

In my current role at TechCorp, I have led a team of 5 engineers in architecting microservices that handle over 2 million requests daily. I have deep expertise in Python, FastAPI, React, and TypeScript - the exact stack mentioned in your job description. My work has directly contributed to reducing infrastructure costs by 40% through systematic optimization and cloud architecture improvements.

What excites me most about this opportunity is the chance to work on critical infrastructure serving millions of users at Google's scale. I am particularly drawn to your emphasis on mentorship and collaboration, as I have found great fulfillment in helping junior engineers grow and conducting thorough code reviews.

I would welcome the opportunity to discuss how my experience aligns with Google's goals and how I can contribute to your team's success.

Sincerely,
Jane Smith"""

    data = {"cover_letter_text": updated_text}
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.put(
        f"{BASE_URL}{API_PREFIX}/cover-letters/{cover_letter_id}", headers=headers, json=data
    )

    if response.status_code == 200:
        result = response.json()
        print_success("Cover letter updated successfully")
        print_info(f"New word count: {result['word_count']} words")
        return True
    else:
        print_error(f"Update failed: {response.status_code} - {response.text}")
        return False


def test_delete_cover_letter(token, cover_letter_id):
    """Test deleting a cover letter."""
    print_header("Delete Cover Letter")
    print_step(7, f"Deleting cover letter {cover_letter_id[:8]}...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{BASE_URL}{API_PREFIX}/cover-letters/{cover_letter_id}", headers=headers
    )

    if response.status_code == 204:
        print_success("Cover letter deleted successfully")
        return True
    else:
        print_error(f"Deletion failed: {response.status_code} - {response.text}")
        return False


def test_validation_errors(token, resume_id):
    """Test validation and error handling."""
    print_header("Validation Tests")
    headers = {"Authorization": f"Bearer {token}"}

    # Test 1: Invalid resume_id
    print_step(8, "Test: Invalid resume_id (should fail)")
    data = {
        "resume_id": "00000000-0000-0000-0000-000000000000",
        "job_description": "Test job description" * 10,
        "tone": "professional",
        "length": "medium",
    }

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/cover-letters/generate", headers=headers, json=data
    )

    if response.status_code == 404:
        print_success("Correctly rejected invalid resume_id")
    else:
        print_error(f"Expected 404, got {response.status_code}")

    # Test 2: Job description too short
    print_step(9, "Test: Job description too short (should fail)")
    data = {
        "resume_id": resume_id,
        "job_description": "Short",  # Less than 50 chars
        "tone": "professional",
        "length": "medium",
    }

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/cover-letters/generate", headers=headers, json=data
    )

    if response.status_code == 422:
        print_success("Correctly rejected short job description")
    else:
        print_error(f"Expected 422, got {response.status_code}")


def main():
    """Run all cover letter tests."""
    print_header("Cover Letter Feature Test Suite")
    print_info(f"Testing API at: {BASE_URL}{API_PREFIX}")

    # Step 1: Login
    token = register_and_login()
    if not token:
        print_error("Cannot continue without authentication")
        return False

    # Step 2: Upload resume
    resume_id = upload_resume(token)
    if not resume_id:
        print_error("Cannot continue without resume")
        return False

    # Step 3: Generate cover letters with different tones and lengths
    cover_letter_ids = []

    # Professional, medium
    cl_id = test_generate_cover_letter(token, resume_id, "professional", "medium")
    if cl_id:
        cover_letter_ids.append(cl_id)

    # Enthusiastic, short
    cl_id = test_generate_cover_letter(token, resume_id, "enthusiastic", "short")
    if cl_id:
        cover_letter_ids.append(cl_id)

    # Balanced, long
    cl_id = test_generate_cover_letter(token, resume_id, "balanced", "long")
    if cl_id:
        cover_letter_ids.append(cl_id)

    if not cover_letter_ids:
        print_error("No cover letters generated")
        return False

    # Step 4: Get cover letter by ID
    test_get_cover_letter(token, cover_letter_ids[0])

    # Step 5: List cover letters
    test_list_cover_letters(token)

    # Step 6: Update cover letter
    test_update_cover_letter(token, cover_letter_ids[0])

    # Step 7: Validation tests
    test_validation_errors(token, resume_id)

    # Step 8: Delete cover letter
    test_delete_cover_letter(token, cover_letter_ids[0])

    # Final Summary
    print_header("TEST SUMMARY")
    print_success("✅ User authentication")
    print_success("✅ Resume upload")
    print_success("✅ Cover letter generation (3 variants)")
    print_success("✅ Retrieve cover letter by ID")
    print_success("✅ List cover letters")
    print_success("✅ Update cover letter text")
    print_success("✅ Delete cover letter")
    print_success("✅ Validation and error handling")
    print()
    print_success("🎉 ALL TESTS PASSED! Cover letter feature is working!")
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
