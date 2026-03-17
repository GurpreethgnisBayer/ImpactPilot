"""Tests for query suggestion module."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.query_suggest import suggest_pubmed_query


def test_query_suggest_basic():
    """Test basic query suggestion from title and description."""
    title = "Machine Learning for Drug Discovery"
    description = "Applying neural networks to predict drug efficacy"
    
    query = suggest_pubmed_query(title, description)
    
    # Query should not be empty
    assert query
    assert len(query) > 0
    
    # Should contain key terms
    assert "machine" in query.lower() or "learning" in query.lower()
    assert "drug" in query.lower()


def test_query_suggest_stopword_filtering():
    """Test that stopwords are filtered out."""
    title = "The Impact of the New Method"
    description = "This is a study on the effect of a novel approach"
    
    query = suggest_pubmed_query(title, description)
    
    # Common stopwords should be filtered
    tokens = query.lower().split()
    assert "the" not in tokens
    assert "is" not in tokens
    assert "a" not in tokens
    
    # Content words should remain
    assert "impact" in query.lower() or "method" in query.lower()


def test_query_suggest_max_tokens():
    """Test that query is limited to first 10 unique tokens."""
    title = "One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve"
    description = "Additional words that should not appear"
    
    query = suggest_pubmed_query(title, description)
    tokens = query.split()
    
    # Should have at most 10 tokens
    assert len(tokens) <= 10


def test_query_suggest_unique_tokens():
    """Test that duplicate tokens are removed."""
    title = "cancer cancer cancer"
    description = "breast cancer breast cancer research"
    
    query = suggest_pubmed_query(title, description)
    tokens = query.split()
    
    # Should not have duplicate tokens
    assert len(tokens) == len(set(tokens))
    assert "cancer" in query.lower()
    assert "breast" in query.lower()
    assert "research" in query.lower()


def test_query_suggest_empty_input():
    """Test fallback behavior with empty input."""
    query = suggest_pubmed_query("", "")
    
    # Should never return empty
    assert query
    assert len(query) > 0


def test_query_suggest_title_only_fallback():
    """Test that title is used as fallback when no tokens found."""
    title = "Research Study"
    description = ""
    
    query = suggest_pubmed_query(title, description)
    
    # Should contain title words
    assert "research" in query.lower() or "study" in query.lower()


def test_query_suggest_hyphenated_words():
    """Test that hyphenated words are preserved."""
    title = "Machine-Learning and Deep-Learning Methods"
    description = "Testing hyphenated terms"
    
    query = suggest_pubmed_query(title, description)
    
    # Hyphenated words should be kept
    assert "machine-learning" in query.lower() or "deep-learning" in query.lower()


def test_query_suggest_sample_rd_idea():
    """Test with a realistic R&D idea."""
    title = "Automated Quality Control Using Computer Vision"
    description = "Develop a system that uses computer vision and machine learning to detect defects in manufacturing processes, reducing manual inspection time by 50%"
    
    query = suggest_pubmed_query(title, description)
    
    # Should not be empty
    assert query
    assert len(query) > 0
    
    # Should contain relevant technical terms
    tokens = query.lower().split()
    assert any(term in tokens for term in ["automated", "quality", "control", "computer", "vision"])
