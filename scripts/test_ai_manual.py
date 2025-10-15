#!/usr/bin/env python3
"""
Manual test script for AI integration.

Tests the complete flow:
1. Register/login test user
2. Create resume with sample data
3. Run analysis with AI suggestions
4. Display results in readable format

Usage:
    python scripts/test_ai_manual.py
"""

import io
import sys
from pathlib import Path

import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.sample_data import JOB_SENIOR_PYTHON, SAMPLE_RESUME_TEXT

console = Console()

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
TEST_USER_EMAIL = "ai_test_user@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "AI Test User"


def print_header(text: str):
    """Print a styled header."""
    console.print(f"\n[bold cyan]{text}[/bold cyan]")
    console.print("=" * 60)


def print_success(text: str):
    """Print success message."""
    console.print(f"[green]✓[/green] {text}")


def print_error(text: str):
    """Print error message."""
    console.print(f"[red]✗[/red] {text}")


def print_info(text: str):
    """Print info message."""
    console.print(f"[blue]ℹ[/blue] {text}")


def register_or_login() -> str:
    """Register new user or login existing user. Returns access token."""
    print_header("Step 1: Authentication")

    # Try to register
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": TEST_USER_NAME,
            },
            timeout=10,
        )
        if response.status_code == 201:
            print_success("User registered successfully")
            # Registration only returns user data, not tokens - need to login
        elif response.status_code == 400:
            print_info("User already exists")
        else:
            print_info(f"Registration returned status {response.status_code}")
    except Exception as e:
        print_info(f"Registration error: {e}")

    # Login to get tokens (works for both new and existing users)
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=10,
        )
        response.raise_for_status()
        print_success("Logged in successfully")
        data = response.json()
        return data["access_token"]
    except Exception as e:
        print_error(f"Login failed: {e}")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            print_error(f"Response: {e.response.text}")
        raise


def create_resume_file() -> io.BytesIO:
    """Create a PDF file for resume upload."""
    # Create a PDF in memory
    pdf_buffer = io.BytesIO()

    # Create PDF using ReportLab
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # Split resume text into lines and add to PDF
    y_position = height - 50  # Start from top with margin
    line_height = 14

    for line in SAMPLE_RESUME_TEXT.split("\n"):
        if y_position < 50:  # Bottom margin reached, start new page
            c.showPage()
            y_position = height - 50

        c.drawString(50, y_position, line[:90])  # Limit line length
        y_position -= line_height

    c.save()

    # Reset buffer position to beginning
    pdf_buffer.seek(0)
    return pdf_buffer


def create_analysis(access_token: str) -> dict:
    """Create analysis with AI suggestions."""
    print_header("Step 2: Creating Analysis")

    headers = {"Authorization": f"Bearer {access_token}"}

    # Create a text file from resume
    resume_file = create_resume_file()

    files = {
        "file": ("resume.pdf", resume_file, "application/pdf"),
    }

    data = {
        "job_description": JOB_SENIOR_PYTHON,
        "job_title": "Senior Python Developer",
        "company_name": "Tech Corp",
    }

    try:
        print_info("Uploading resume and job description...")
        print_info("Calling OpenRouter AI with reasoning model (this may take 60-90 seconds)...")

        response = requests.post(
            f"{API_BASE_URL}/api/analyses/create",
            headers=headers,
            files=files,
            data=data,
            timeout=120,  # AI calls with reasoning models can take 60-90 seconds
        )

        response.raise_for_status()
        print_success("Analysis created successfully!")

        return response.json()

    except requests.exceptions.Timeout:
        print_error("Request timed out - AI call took too long")
        raise
    except requests.exceptions.RequestException as e:
        print_error(f"Analysis creation failed: {e}")
        if hasattr(e.response, "text"):
            print_error(f"Response: {e.response.text}")
        raise


def display_results(analysis: dict):
    """Display analysis results in a readable format."""
    print_header("Step 3: Analysis Results")

    # Overall scores
    scores_table = Table(title="📊 Scores", show_header=False)
    scores_table.add_column("Metric", style="cyan")
    scores_table.add_column("Value", style="bold green")

    scores_table.add_row("Overall Match Score", f"{analysis['match_score']}%")
    scores_table.add_row("ATS Compatibility Score", f"{analysis['ats_score']}%")
    scores_table.add_row("Semantic Similarity", f"{analysis['semantic_similarity']}%")

    console.print(scores_table)

    # Keywords
    print("\n[bold]🔑 Keyword Analysis[/bold]")
    matching = analysis.get("matching_keywords", [])
    missing = analysis.get("missing_keywords", [])

    console.print(f"  Matched ({len(matching)}): ", style="green", end="")
    console.print(", ".join(matching[:10]))

    console.print(f"  Missing ({len(missing)}): ", style="red", end="")
    console.print(", ".join(missing[:10]))

    # AI Suggestions
    ai_suggestions = analysis.get("ai_suggestions")
    if ai_suggestions and len(ai_suggestions) > 0:
        print("\n[bold green]🤖 AI-POWERED SUGGESTIONS[/bold green]")

        for i, suggestion in enumerate(ai_suggestions, 1):
            priority = suggestion.get("priority", "medium").upper()
            priority_color = {
                "HIGH": "red",
                "MEDIUM": "yellow",
                "LOW": "blue",
            }.get(priority, "white")

            console.print(
                f"\n[bold]{i}. [{priority_color}]{priority} PRIORITY[/{priority_color}][/bold]"
            )
            console.print(f"   Type: {suggestion.get('type', 'N/A')}")
            console.print(f"   Issue: {suggestion.get('issue', 'N/A')}")
            console.print(f"   [cyan]Suggestion:[/cyan] {suggestion.get('suggestion', 'N/A')}")
            console.print(f"   [green]Example:[/green] {suggestion.get('example', 'N/A')}")
            console.print(f"   [yellow]Impact:[/yellow] {suggestion.get('impact', 'N/A')}")
    else:
        print_error("\n⚠️  No AI suggestions generated (AI may be disabled or failed)")

    # Rewritten Bullets
    rewritten_bullets = analysis.get("rewritten_bullets")
    if rewritten_bullets and len(rewritten_bullets) > 0:
        print("\n[bold green]✨ REWRITTEN BULLET POINTS[/bold green]")

        for i, bullet in enumerate(rewritten_bullets, 1):
            console.print(f"\n[bold]{i}. Section: {bullet.get('section', 'N/A')}[/bold]")

            console.print("   [red]❌ Before:[/red]")
            console.print(f"      {bullet.get('original', 'N/A')}")

            console.print("   [green]✓ After:[/green]")
            console.print(f"      {bullet.get('improved', 'N/A')}")

            improvements = bullet.get("improvements", [])
            if improvements:
                console.print(f"   [cyan]Improvements:[/cyan] {', '.join(improvements)}")

            keywords = bullet.get("keywords_added", [])
            if keywords:
                console.print(f"   [yellow]Keywords Added:[/yellow] {', '.join(keywords)}")

            score_improvement = bullet.get("score_improvement", 0)
            console.print(
                f"   [bold green]Score Improvement:[/bold green] +{score_improvement} points"
            )
    else:
        print_error("\n⚠️  No bullet point rewrites generated")

    # Token usage and cost
    tokens_used = analysis.get("openai_tokens_used", 0)
    if tokens_used > 0:
        # GPT-5-mini estimated costs (adjust if needed)
        cost_per_1k_input = 0.00015  # $0.15 per 1M tokens
        cost_per_1k_output = 0.0006  # $0.60 per 1M tokens
        # Rough estimate: 70% input, 30% output
        estimated_cost = (tokens_used * 0.7 * cost_per_1k_input / 1000) + (
            tokens_used * 0.3 * cost_per_1k_output / 1000
        )

        print("\n[bold]💰 Cost Tracking[/bold]")
        console.print(f"  Tokens Used: {tokens_used:,}")
        console.print(f"  Estimated Cost: ${estimated_cost:.4f}")
    else:
        print_info("\n⚠️  No token usage tracked (AI may be disabled)")

    # Processing time
    processing_time = analysis.get("processing_time_ms", 0)
    console.print(
        f"\n[dim]⏱️  Processing Time: {processing_time}ms ({processing_time/1000:.2f}s)[/dim]"
    )


def main():
    """Run the complete test flow."""
    console.print(
        Panel.fit(
            "[bold cyan]AI Integration Test Script[/bold cyan]\n"
            "Testing OpenRouter + Instructor + GPT-5-mini\n\n"
            f"API: {API_BASE_URL}",
            border_style="cyan",
        )
    )

    try:
        # Step 1: Authenticate
        access_token = register_or_login()

        # Step 2: Create analysis
        analysis = create_analysis(access_token)

        # Step 3: Display results
        display_results(analysis)

        console.print("\n[bold green]✓ Test completed successfully![/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Test failed: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
