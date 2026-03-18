"""Test query suggestion functionality."""

from impactpilot.query_suggest import suggest_pubmed_query


def test_query_non_empty():
    """Test that query suggestion never returns empty string."""
    # Normal case
    result = suggest_pubmed_query("AI drug discovery", "Using machine learning")
    assert result != ""
    assert len(result) > 0
    
    # Empty inputs - fallback to "research"
    result = suggest_pubmed_query("", "")
    assert result != ""
    
    # Only stopwords - fallback
    result = suggest_pubmed_query("the and or", "a is it")
    assert result != ""


def test_query_contains_expected_tokens():
    """Test that query suggestion extracts expected tokens."""
    result = suggest_pubmed_query(
        "AI-powered drug screening platform",
        "Machine learning for pharmaceutical research"
    )
    
    # Should contain key terms (lowercase, no stopwords)
    tokens = result.split()
    
    # Check that we get reasonable tokens
    assert "ai" in tokens or "powered" in tokens
    assert "drug" in tokens or "screening" in tokens
    
    # Should not contain stopwords
    assert "the" not in tokens
    assert "for" not in tokens
    assert "a" not in tokens


def test_query_max_10_tokens():
    """Test that query suggestion returns at most 10 tokens."""
    long_text = "One two three four five six seven eight nine ten eleven twelve"
    result = suggest_pubmed_query(long_text, "")
    
    tokens = result.split()
    assert len(tokens) <= 10


def test_query_removes_stopwords():
    """Test that stopwords are removed."""
    result = suggest_pubmed_query("the cancer research and therapy", "")
    
    tokens = result.split()
    assert "the" not in tokens
    assert "and" not in tokens
    assert "cancer" in tokens
    assert "research" in tokens
    assert "therapy" in tokens


def test_query_unique_tokens():
    """Test that duplicate tokens are removed."""
    result = suggest_pubmed_query("cancer cancer cancer research", "cancer therapy")
    
    tokens = result.split()
    # Count occurrences of "cancer"
    cancer_count = tokens.count("cancer")
    assert cancer_count == 1  # Should appear only once


def test_query_fallback_to_title():
    """Test fallback to title when all stopwords."""
    result = suggest_pubmed_query("Research Study", "the and or")
    
    # Should contain something from title
    assert result != ""
    assert len(result) > 0


def test_query_preserves_order():
    """Test that token order is preserved from input."""
    result = suggest_pubmed_query("alpha beta gamma delta", "")
    
    tokens = result.split()
    # Check relative order is preserved
    if "alpha" in tokens and "beta" in tokens:
        assert tokens.index("alpha") < tokens.index("beta")
