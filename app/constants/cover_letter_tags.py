"""
Predefined tag categories for cover letter organization.
Provides structured categorization for cover letters.
"""

from typing import Dict, List

# Job role categories
JOB_CATEGORIES: List[str] = [
    "Software Engineering",
    "Data Science & Analytics",
    "Product Management",
    "Design & UX",
    "Marketing & Growth",
    "Sales & Business Development",
    "Customer Success",
    "Operations & Project Management",
    "Finance & Accounting",
    "Human Resources",
    "Legal & Compliance",
    "Healthcare & Medical",
    "Education & Teaching",
    "Engineering (Non-Software)",
    "Research & Development",
    "Consulting",
    "Other",
]

# Work arrangement types
WORK_TYPES: List[str] = [
    "Remote",
    "Hybrid",
    "On-site",
]

# Experience level categories
EXPERIENCE_LEVELS: List[str] = [
    "Internship",
    "Entry Level",
    "Mid-Level",
    "Senior",
    "Lead / Principal",
    "Director / VP",
    "Executive / C-Level",
]

# Industry sectors
INDUSTRIES: List[str] = [
    "Technology & Software",
    "Financial Services",
    "Healthcare & Biotechnology",
    "E-commerce & Retail",
    "Education & EdTech",
    "Media & Entertainment",
    "Consulting & Professional Services",
    "Manufacturing & Industrial",
    "Real Estate & Construction",
    "Energy & Utilities",
    "Telecommunications",
    "Transportation & Logistics",
    "Nonprofit & Government",
    "Hospitality & Tourism",
    "Agriculture & Food",
    "Other",
]

# Company size categories
COMPANY_SIZES: List[str] = [
    "Startup (1-50)",
    "Small (51-200)",
    "Medium (201-1000)",
    "Large (1001-5000)",
    "Enterprise (5000+)",
]

# Application status (for tracking)
APPLICATION_STATUS: List[str] = [
    "Draft",
    "Ready to Send",
    "Sent",
    "Follow-up Sent",
    "Interview Scheduled",
    "Offer Received",
    "Rejected",
    "Withdrawn",
]

# All available tag categories grouped by type
TAG_CATEGORIES: Dict[str, List[str]] = {
    "job_category": JOB_CATEGORIES,
    "work_type": WORK_TYPES,
    "experience_level": EXPERIENCE_LEVELS,
    "industry": INDUSTRIES,
    "company_size": COMPANY_SIZES,
    "status": APPLICATION_STATUS,
}

# Flattened list of all available tags
ALL_TAGS: List[str] = [tag for category_tags in TAG_CATEGORIES.values() for tag in category_tags]


def get_tag_category(tag: str) -> str | None:
    """
    Get the category name for a given tag.

    Args:
        tag: The tag to look up

    Returns:
        Category name or None if tag not found

    Example:
        >>> get_tag_category("Remote")
        'work_type'
        >>> get_tag_category("Software Engineering")
        'job_category'
    """
    for category, tags in TAG_CATEGORIES.items():
        if tag in tags:
            return category
    return None


def validate_tags(tags: List[str]) -> bool:
    """
    Validate that all provided tags are in the predefined list.

    Args:
        tags: List of tags to validate

    Returns:
        True if all tags are valid, False otherwise

    Example:
        >>> validate_tags(["Remote", "Software Engineering"])
        True
        >>> validate_tags(["Invalid Tag"])
        False
    """
    return all(tag in ALL_TAGS for tag in tags)
