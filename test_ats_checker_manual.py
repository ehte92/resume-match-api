#!/usr/bin/env python3
"""
Manual integration test for ATSChecker with ResumeParser.

This script tests the complete integration between ResumeParser and ATSChecker.
"""

import json
from pathlib import Path

from app.services.ats_checker import ATSChecker
from app.services.resume_parser import ResumeParser


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    """Run manual integration tests for ATSChecker."""
    print_section("ATSChecker Integration Test with ResumeParser")

    # Initialize services
    print("Initializing services...")
    parser = ResumeParser()
    checker = ATSChecker()
    print("✅ Services initialized successfully\n")

    # Path to test fixture
    test_pdf = Path("tests/fixtures/sample_resume.pdf")

    if not test_pdf.exists():
        print(f"❌ Test file not found: {test_pdf}")
        print("Please ensure tests/fixtures/sample_resume.pdf exists.")
        return

    # Test 1: Parse a real resume
    print_section("TEST 1: Parse Sample Resume")
    print(f"Parsing: {test_pdf}\n")

    try:
        parsed_resume = parser.parse(str(test_pdf), "pdf")
        print("✅ Resume parsed successfully")
        print(f"   Raw text length: {len(parsed_resume.get('raw_text', ''))} characters")
        print(f"   Sections found: {list(parsed_resume.get('sections', {}).keys())}")
    except Exception as e:
        print(f"❌ Failed to parse resume: {e}")
        return

    # Test 2: Check ATS compatibility
    print_section("TEST 2: ATS Compatibility Check")

    result = checker.check_ats_compatibility(parsed_resume)

    print(f"ATS Score: {result['ats_score']}/100")
    print(f"Status: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
    print(f"Issues Found: {result['issue_count']}\n")

    # Display issues by severity
    if result["issues"]:
        print("Issues Breakdown:")

        high_issues = [i for i in result["issues"] if i["severity"] == "high"]
        medium_issues = [i for i in result["issues"] if i["severity"] == "medium"]
        low_issues = [i for i in result["issues"] if i["severity"] == "low"]

        if high_issues:
            print(f"\n  HIGH Severity ({len(high_issues)}):")
            for issue in high_issues:
                print(f"    • {issue['message']}")

        if medium_issues:
            print(f"\n  MEDIUM Severity ({len(medium_issues)}):")
            for issue in medium_issues:
                print(f"    • {issue['message']}")

        if low_issues:
            print(f"\n  LOW Severity ({len(low_issues)}):")
            for issue in low_issues:
                print(f"    • {issue['message']}")
    else:
        print("✅ No ATS issues found - Resume is well-formatted!\n")

    # Display recommendations
    print_section("Recommendations")
    if result["recommendations"]:
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"{i}. {rec}")
    else:
        print("✅ No recommendations needed!")

    # Test 3: Complete result JSON
    print_section("TEST 3: Complete Result JSON")
    print(json.dumps(result, indent=2))

    # Summary
    print_section("SUMMARY")
    print("✅ ATSChecker successfully integrated with ResumeParser")
    print("✅ Complete workflow tested end-to-end")
    print("\nTest Results:")
    print("  • Resume parsed: ✅")
    print(f"  • ATS score calculated: ✅ ({result['ats_score']}/100)")
    print(f"  • Issues identified: ✅ ({result['issue_count']} issues)")
    print(f"  • Recommendations generated: ✅ ({len(result['recommendations'])} recommendations)")
    print("\n✨ Phase 13: ATS Checker Service - Integration Complete!")


if __name__ == "__main__":
    main()
