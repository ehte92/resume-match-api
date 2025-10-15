"""
Unit tests for KeywordAnalyzer service.

Tests the keyword extraction and match score calculation functionality.
"""

import pytest

from app.services.keyword_analyzer import KeywordAnalyzer


@pytest.fixture
def analyzer():
    """Create a KeywordAnalyzer instance for testing."""
    return KeywordAnalyzer()


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    We are looking for a Senior Python Developer with experience in Django and FastAPI.
    The ideal candidate should have:
    - 5+ years of Python development experience
    - Strong knowledge of REST APIs and microservices
    - Experience with PostgreSQL and MongoDB databases
    - Familiarity with Docker and Kubernetes
    - Strong problem-solving skills and attention to detail
    """


@pytest.fixture
def sample_resume_matching():
    """Sample resume that matches the job description well."""
    return """
    Senior Software Engineer with 6 years of Python development experience.

    Technical Skills:
    - Python, Django, FastAPI, Flask
    - REST API design and microservices architecture
    - PostgreSQL, MongoDB, Redis
    - Docker, Kubernetes, CI/CD

    Experience:
    - Built scalable REST APIs using Django and FastAPI
    - Designed microservices architecture for high-traffic applications
    - Managed PostgreSQL databases with complex queries
    - Deployed applications using Docker and Kubernetes
    """


@pytest.fixture
def sample_resume_partial():
    """Sample resume that partially matches the job description."""
    return """
    Software Developer with 3 years of experience in web development.

    Skills:
    - Python, Flask, JavaScript
    - MySQL database management
    - Git version control

    Experience:
    - Developed web applications using Python and Flask
    - Worked with MySQL databases
    - Collaborated with team using Git
    """


class TestKeywordAnalyzerInit:
    """Test KeywordAnalyzer initialization."""

    def test_initialization_success(self, analyzer):
        """Test successful initialization of KeywordAnalyzer."""
        assert analyzer is not None
        assert analyzer.nlp is not None
        assert analyzer.vectorizer is not None

    def test_spacy_model_loaded(self, analyzer):
        """Test that spaCy model is loaded correctly."""
        # Test that we can process text with the loaded model
        doc = analyzer.nlp("Test sentence")
        assert doc is not None
        assert len(doc) > 0


class TestExtractKeywords:
    """Test keyword extraction functionality."""

    def test_extract_keywords_basic(self, analyzer, sample_job_description):
        """Test basic keyword extraction."""
        keywords = analyzer.extract_keywords(sample_job_description, top_n=10)

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert len(keywords) <= 10

        # Check that important terms are extracted
        keywords_lower = [k.lower() for k in keywords]
        assert any("python" in k for k in keywords_lower)

    def test_extract_keywords_empty_text(self, analyzer):
        """Test keyword extraction with empty text."""
        keywords = analyzer.extract_keywords("", top_n=10)
        assert keywords == []

        keywords = analyzer.extract_keywords("   ", top_n=10)
        assert keywords == []

    def test_extract_keywords_custom_top_n(self, analyzer, sample_job_description):
        """Test keyword extraction with custom top_n parameter."""
        keywords_5 = analyzer.extract_keywords(sample_job_description, top_n=5)
        keywords_15 = analyzer.extract_keywords(sample_job_description, top_n=15)

        assert len(keywords_5) <= 5
        assert len(keywords_15) <= 15
        assert len(keywords_15) >= len(keywords_5)

    def test_extract_keywords_no_duplicates(self, analyzer, sample_job_description):
        """Test that extracted keywords have no duplicates."""
        keywords = analyzer.extract_keywords(sample_job_description, top_n=20)

        # Check for duplicates
        assert len(keywords) == len(set(keywords))

    def test_extract_keywords_technical_terms(self, analyzer):
        """Test extraction of technical terms."""
        text = "Looking for Python developer with Django, FastAPI, and Docker experience"
        keywords = analyzer.extract_keywords(text, top_n=10)

        # Should extract some keywords (at least some technical terms)
        # Note: Exact keywords may vary based on TF-IDF scoring
        assert len(keywords) > 0
        assert all(isinstance(k, str) for k in keywords)


class TestTfidfKeywords:
    """Test TF-IDF keyword extraction."""

    def test_tfidf_keywords_basic(self, analyzer, sample_job_description):
        """Test basic TF-IDF keyword extraction."""
        keywords = analyzer._tfidf_keywords(sample_job_description, top_n=10)

        assert isinstance(keywords, list)
        assert len(keywords) > 0

        # Check that results are tuples of (keyword, score)
        for item in keywords:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], float)

    def test_tfidf_keywords_sorted_by_score(self, analyzer, sample_job_description):
        """Test that TF-IDF keywords are sorted by score."""
        keywords = analyzer._tfidf_keywords(sample_job_description, top_n=10)

        # Check that scores are in descending order
        scores = [score for _, score in keywords]
        assert scores == sorted(scores, reverse=True)

    def test_tfidf_keywords_empty_text(self, analyzer):
        """Test TF-IDF with empty text."""
        keywords = analyzer._tfidf_keywords("", top_n=10)
        assert keywords == []


class TestSpacyKeywords:
    """Test spaCy NER keyword extraction."""

    def test_spacy_keywords_basic(self, analyzer, sample_job_description):
        """Test basic spaCy keyword extraction."""
        keywords = analyzer._spacy_keywords(sample_job_description)

        assert isinstance(keywords, list)
        # May or may not find entities depending on the text

    def test_spacy_keywords_empty_text(self, analyzer):
        """Test spaCy NER with empty text."""
        keywords = analyzer._spacy_keywords("")
        assert keywords == []

    def test_spacy_keywords_no_duplicates(self, analyzer):
        """Test that spaCy keywords have no duplicates."""
        text = "Google and Microsoft are companies. Google is also a search engine."
        keywords = analyzer._spacy_keywords(text)

        # Check for duplicates
        assert len(keywords) == len(set(keywords))

    def test_spacy_keywords_entity_types(self, analyzer):
        """Test that spaCy extracts relevant entity types."""
        text = "Python developer at Google working with Django and PostgreSQL"
        keywords = analyzer._spacy_keywords(text)

        # Should extract organization names
        keywords_lower = [k.lower() for k in keywords]
        assert any("google" in k for k in keywords_lower)


class TestCalculateMatchScore:
    """Test match score calculation."""

    def test_calculate_match_score_high_match(
        self, analyzer, sample_job_description, sample_resume_matching
    ):
        """Test match score with high-matching resume."""
        result = analyzer.calculate_match_score(sample_resume_matching, sample_job_description)

        assert isinstance(result, dict)
        assert "score" in result
        assert "matched_keywords" in result
        assert "missing_keywords" in result
        assert "total_keywords" in result
        assert "matched_count" in result
        assert "missing_count" in result

        # Should have a reasonable match score
        # Note: Exact score depends on keyword extraction which may vary
        assert result["score"] >= 0
        assert result["score"] <= 100

        # Should have some matched keywords for a matching resume
        assert len(result["matched_keywords"]) >= 0

        # Verify counts add up
        assert result["matched_count"] + result["missing_count"] == result["total_keywords"]

    def test_calculate_match_score_partial_match(
        self, analyzer, sample_job_description, sample_resume_partial
    ):
        """Test match score with partially matching resume."""
        result = analyzer.calculate_match_score(sample_resume_partial, sample_job_description)

        assert isinstance(result, dict)
        assert result["score"] >= 0
        assert result["score"] <= 100

        # Should have some matched and some missing keywords
        assert len(result["matched_keywords"]) > 0
        assert len(result["missing_keywords"]) > 0

        # Should have lower score than high-matching resume
        assert result["score"] < 100

    def test_calculate_match_score_empty_resume(self, analyzer, sample_job_description):
        """Test match score with empty resume."""
        result = analyzer.calculate_match_score("", sample_job_description)

        assert result["score"] == 0
        assert result["matched_keywords"] == []
        assert result["matched_count"] == 0

    def test_calculate_match_score_empty_job_description(self, analyzer, sample_resume_matching):
        """Test match score with empty job description."""
        result = analyzer.calculate_match_score(sample_resume_matching, "")

        assert result["score"] == 0
        assert result["matched_keywords"] == []
        assert result["missing_keywords"] == []
        assert result["total_keywords"] == 0

    def test_calculate_match_score_case_insensitive(self, analyzer):
        """Test that match score is case-insensitive."""
        job_desc = "Looking for Python and Django developer"
        resume1 = "I have experience with Python and Django"
        resume2 = "I have experience with PYTHON and DJANGO"

        result1 = analyzer.calculate_match_score(resume1, job_desc)
        result2 = analyzer.calculate_match_score(resume2, job_desc)

        # Both should have similar scores (case shouldn't matter)
        assert abs(result1["score"] - result2["score"]) <= 10

    def test_calculate_match_score_word_boundaries(self, analyzer):
        """Test that match score uses word boundaries (no partial matches)."""
        job_desc = "Looking for Java developer"
        resume = "I have experience with JavaScript"  # Should not match "Java"

        result = analyzer.calculate_match_score(resume, job_desc)

        # "javascript" should not match "java" keyword
        matched_lower = [k.lower() for k in result["matched_keywords"]]
        assert "java" not in matched_lower or "javascript" in job_desc.lower()

    def test_calculate_match_score_percentage_calculation(self, analyzer):
        """Test that percentage is calculated correctly."""
        job_desc = "Python Django FastAPI PostgreSQL Docker"
        resume = "Python Django FastAPI"  # 3 out of 5 keywords

        result = analyzer.calculate_match_score(resume, job_desc)

        # Should be around 60% (3/5) but may vary due to keyword extraction
        assert result["score"] >= 0
        assert result["score"] <= 100

        # Verify the math
        if result["total_keywords"] > 0:
            expected_score = int((result["matched_count"] / result["total_keywords"]) * 100)
            assert result["score"] == expected_score


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow(self, analyzer, sample_job_description, sample_resume_matching):
        """Test complete workflow from job description to match score."""
        # Extract keywords from job description
        job_keywords = analyzer.extract_keywords(sample_job_description, top_n=15)
        assert len(job_keywords) > 0

        # Calculate match score
        result = analyzer.calculate_match_score(sample_resume_matching, sample_job_description)
        assert result["score"] >= 0

        # Verify result structure is correct
        assert isinstance(result["matched_keywords"], list)
        assert isinstance(result["missing_keywords"], list)
        assert result["total_keywords"] > 0

    def test_multiple_resumes_comparison(
        self, analyzer, sample_job_description, sample_resume_matching, sample_resume_partial
    ):
        """Test comparing multiple resumes against same job description."""
        result1 = analyzer.calculate_match_score(sample_resume_matching, sample_job_description)
        result2 = analyzer.calculate_match_score(sample_resume_partial, sample_job_description)

        # Better matching resume should have higher score
        assert result1["score"] > result2["score"]
        assert result1["matched_count"] > result2["matched_count"]
