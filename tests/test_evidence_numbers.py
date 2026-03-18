"""Test numeric evidence extraction."""

from impactpilot.evidence_numbers import extract_numeric_evidence


def test_extract_percentage():
    """Test extraction of percentage values."""
    article = {
        "pmid": "12345",
        "abstract": "The study showed a 25% improvement in outcomes."
    }
    
    results = extract_numeric_evidence(article)
    
    # Should find the 25%
    assert len(results) > 0
    percent_entries = [r for r in results if r["type"] == "percentage"]
    assert len(percent_entries) == 1
    assert percent_entries[0]["value"] == 25.0
    assert percent_entries[0]["unit"] == "%"
    assert percent_entries[0]["pmid"] == "12345"
    assert "25" in percent_entries[0]["context"]


def test_extract_time_duration():
    """Test extraction of time duration values."""
    article = {
        "pmid": "67890",
        "abstract": "The procedure took 2 hours to complete in most cases."
    }
    
    results = extract_numeric_evidence(article)
    
    # Should find the 2 hours
    assert len(results) > 0
    time_entries = [r for r in results if r["type"] == "time_duration"]
    assert len(time_entries) == 1
    assert time_entries[0]["value"] == 2.0
    assert "hour" in time_entries[0]["unit"].lower()
    assert time_entries[0]["pmid"] == "67890"


def test_extract_multiple_values():
    """Test extraction of multiple numeric values."""
    article = {
        "pmid": "11111",
        "abstract": "Study of 100 patients showed 25% improvement over 3 days."
    }
    
    results = extract_numeric_evidence(article)
    
    # Should find percentage, count, and time
    assert len(results) >= 2
    
    types_found = {r["type"] for r in results}
    assert "percentage" in types_found
    assert "time_duration" in types_found or "count" in types_found


def test_extract_empty_abstract():
    """Test handling of empty abstract."""
    article = {
        "pmid": "99999",
        "abstract": ""
    }
    
    results = extract_numeric_evidence(article)
    assert results == []


def test_extract_no_numbers():
    """Test handling of abstract without numbers."""
    article = {
        "pmid": "88888",
        "abstract": "This study examined various therapeutic approaches."
    }
    
    results = extract_numeric_evidence(article)
    assert results == []


def test_context_extraction():
    """Test that context is extracted around numbers."""
    article = {
        "pmid": "77777",
        "abstract": "The innovative method reduced processing time by 30% compared to baseline."
    }
    
    results = extract_numeric_evidence(article)
    
    percent_entries = [r for r in results if r["type"] == "percentage"]
    assert len(percent_entries) == 1
    
    context = percent_entries[0]["context"]
    assert "30" in context
    assert len(context) > 10  # Should have surrounding context


def test_decimal_values():
    """Test extraction of decimal values."""
    article = {
        "pmid": "55555",
        "abstract": "Efficiency improved by 12.5% after implementation."
    }
    
    results = extract_numeric_evidence(article)
    
    percent_entries = [r for r in results if r["type"] == "percentage"]
    assert len(percent_entries) == 1
    assert percent_entries[0]["value"] == 12.5
