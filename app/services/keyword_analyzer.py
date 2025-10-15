"""
Keyword Analyzer Service for Resume Optimization.

Uses TF-IDF (Term Frequency-Inverse Document Frequency) and spaCy Named Entity Recognition
to extract important keywords and calculate match scores between resumes and job descriptions.
"""

import logging
import re
from typing import Dict, List, Tuple

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class KeywordAnalyzer:
    """
    Analyzes text to extract keywords and calculate match scores.

    Combines TF-IDF statistical analysis with spaCy's Named Entity Recognition
    to identify the most important terms in job descriptions and resumes.
    """

    def __init__(self):
        """
        Initialize the KeywordAnalyzer with spaCy NLP model and TF-IDF vectorizer.

        Loads the en_core_web_sm language model for entity extraction.
        """
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            raise

        # Initialize TF-IDF vectorizer with optimized parameters
        self.vectorizer = TfidfVectorizer(
            max_features=100,  # Limit to top 100 terms
            stop_words="english",  # Remove common English stop words
            ngram_range=(1, 2),  # Include unigrams and bigrams
            min_df=1,  # Minimum document frequency
            lowercase=True,  # Convert to lowercase
        )

    def extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """
        Extract the most important keywords from text using combined approach.

        Uses both TF-IDF and spaCy NER to identify important terms.
        Combines results to capture both statistical importance and semantic meaning.

        Args:
            text: Input text to analyze
            top_n: Number of top keywords to return (default: 20)

        Returns:
            List of top N keywords sorted by importance

        Example:
            >>> analyzer = KeywordAnalyzer()
            >>> text = "Looking for Python developer with Django experience"
            >>> keywords = analyzer.extract_keywords(text, top_n=10)
            >>> print(keywords)
            ['python', 'django', 'developer', 'experience', ...]
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to extract_keywords")
            return []

        # Extract keywords using both methods
        tfidf_keywords = self._tfidf_keywords(text, top_n=top_n)
        spacy_keywords = self._spacy_keywords(text)

        # Combine and deduplicate
        combined = []
        seen = set()

        # Add TF-IDF keywords first (with scores)
        for keyword, score in tfidf_keywords:
            if keyword not in seen:
                combined.append(keyword)
                seen.add(keyword)

        # Add spaCy NER keywords
        for keyword in spacy_keywords:
            if keyword not in seen:
                combined.append(keyword)
                seen.add(keyword)

        # Return top N combined keywords
        return combined[:top_n]

    def calculate_match_score(self, resume_text: str, job_description: str) -> Dict[str, any]:
        """
        Calculate match score between resume and job description.

        Extracts keywords from job description and checks how many appear in resume.
        Returns detailed breakdown including percentage score, matched/missing keywords.

        Args:
            resume_text: Full text content of resume
            job_description: Full text content of job posting

        Returns:
            Dictionary with match score details:
            {
                "score": 75,  # Percentage match (0-100)
                "matched_keywords": ["python", "django", "api"],
                "missing_keywords": ["kubernetes", "docker"],
                "total_keywords": 10,
                "matched_count": 5,
                "missing_count": 5
            }

        Example:
            >>> analyzer = KeywordAnalyzer()
            >>> resume = "Python developer with Django and Flask experience"
            >>> job = "Need Python expert with Django and Docker skills"
            >>> result = analyzer.calculate_match_score(resume, job)
            >>> print(f"Match Score: {result['score']}%")
            Match Score: 67%
        """
        if not resume_text or not job_description:
            logger.warning("Empty text provided to calculate_match_score")
            return {
                "score": 0,
                "matched_keywords": [],
                "missing_keywords": [],
                "total_keywords": 0,
                "matched_count": 0,
                "missing_count": 0,
            }

        # Extract keywords from job description
        job_keywords = self.extract_keywords(job_description, top_n=20)

        if not job_keywords:
            logger.warning("No keywords extracted from job description")
            return {
                "score": 0,
                "matched_keywords": [],
                "missing_keywords": [],
                "total_keywords": 0,
                "matched_count": 0,
                "missing_count": 0,
            }

        # Normalize resume text for matching
        resume_lower = resume_text.lower()

        # Check which keywords are present in resume
        matched = []
        missing = []

        for keyword in job_keywords:
            # Use word boundary matching to avoid partial matches
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, resume_lower):
                matched.append(keyword)
            else:
                missing.append(keyword)

        # Calculate percentage score
        total_keywords = len(job_keywords)
        matched_count = len(matched)
        score = int((matched_count / total_keywords) * 100) if total_keywords > 0 else 0

        logger.info(f"Match score calculated: {score}% ({matched_count}/{total_keywords} keywords)")

        return {
            "score": score,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "total_keywords": total_keywords,
            "matched_count": matched_count,
            "missing_count": len(missing),
        }

    def _tfidf_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF (Term Frequency-Inverse Document Frequency).

        TF-IDF identifies words that are important in the document by balancing:
        - Term Frequency: How often the word appears
        - Inverse Document Frequency: How unique the word is

        Args:
            text: Input text to analyze
            top_n: Number of top keywords to return

        Returns:
            List of tuples (keyword, score) sorted by TF-IDF score descending

        Note:
            For single-document TF-IDF, we treat sentences as separate "documents"
            to calculate meaningful IDF scores.
        """
        try:
            # Split text into sentences to create a mini-corpus for IDF calculation
            sentences = [s.strip() for s in text.split(".") if s.strip()]

            if len(sentences) < 2:
                # If too few sentences, split by newlines or use full text
                sentences = [s.strip() for s in text.split("\n") if s.strip()]

            if not sentences:
                logger.warning("No sentences found for TF-IDF analysis")
                return []

            # Fit and transform the corpus
            tfidf_matrix = self.vectorizer.fit_transform(sentences)

            # Get feature names (terms)
            feature_names = self.vectorizer.get_feature_names_out()

            # Sum TF-IDF scores across all documents
            tfidf_scores = tfidf_matrix.sum(axis=0).A1

            # Create list of (term, score) tuples
            keyword_scores = list(zip(feature_names, tfidf_scores))

            # Sort by score descending
            keyword_scores.sort(key=lambda x: x[1], reverse=True)

            # Return top N
            return keyword_scores[:top_n]

        except Exception as e:
            logger.error(f"TF-IDF extraction failed: {e}")
            return []

    def _spacy_keywords(self, text: str) -> List[str]:
        """
        Extract keywords using spaCy Named Entity Recognition (NER).

        Identifies important entities like skills, technologies, organizations, etc.
        Focuses on technical terms and proper nouns that are typically important.

        Args:
            text: Input text to analyze

        Returns:
            List of extracted entity keywords

        Note:
            Filters entities to include only relevant types:
            - ORG: Organizations, companies
            - PRODUCT: Technologies, tools, products
            - GPE: Geo-political entities (locations)
            - PERSON: People (for references)
            - NORP: Nationalities, religious/political groups
        """
        try:
            doc = self.nlp(text)

            keywords = []
            relevant_entity_types = {"ORG", "PRODUCT", "GPE", "PERSON", "NORP"}

            for ent in doc.ents:
                if ent.label_ in relevant_entity_types:
                    # Normalize and clean entity text
                    keyword = ent.text.strip().lower()
                    if keyword and len(keyword) > 1:  # Filter out single chars
                        keywords.append(keyword)

            # Deduplicate while preserving order
            seen = set()
            unique_keywords = []
            for kw in keywords:
                if kw not in seen:
                    seen.add(kw)
                    unique_keywords.append(kw)

            logger.info(f"Extracted {len(unique_keywords)} entities via spaCy NER")
            return unique_keywords

        except Exception as e:
            logger.error(f"spaCy NER extraction failed: {e}")
            return []
