"""Tests for numeric evidence extraction from abstracts."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.evidence_numbers import extract_numeric_evidence, extract_all_numeric_evidence


def test_extract_percentage():
    """Test extraction of percentage values."""
    article = {
        "pmid": "12345",
        "abstract": "The treatment showed a 25% improvement in outcomes over baseline."
    }
    
    evidence = extract_numeric_evidence(article)
    
    assert len(evidence) > 0
    percentage_evidence = [e for e in evidence if e["type"] == "percentage"]
    assert len(percentage_evidence) >= 1
    assert percentage_evidence[0]["value"] == 25.0
    assert percentage_evidence[0]["unit"] == "%"
    assert percentage_evidence[0]["pmid"] == "12345"


def test_extract_time_hours():
    """Test extraction of time durations in hours."""
    article = {
        "pmid": "67890",
        "abstract": "The procedure took 2 hours to complete and showed significant time savings."
    }
    
    evidence = extract_numeric_evidence(article)
    
    time_evidence = [e for e in evidence if e["type"] == "time"]
    assert len(time_evidence) >= 1
    
    hours_evidence = [e for e in time_evidence if e["unit"] == "hours"]
    assert len(hours_evidence) >= 1
    assert hours_evidence[0]["value"] == 2.0
    assert hours_evidence[0]["pmid"] == "67890"


def test_extract_multiple_numeric_types():
    """Test extraction of multiple numeric types from same abstract."""
    article = {
        "pmid": "11111",
        "abstract": "In a study of 30 patients over 6 weeks, we observed a 40% reduction in symptoms and processing time decreased by 3 hours."
    }
    
    evidence = extract_numeric_evidence(article)
    
    # Should find percentage, time, and count
    assert len(evidence) >= 3
    
    types_found = {e["type"] for e in evidence}
    assert "percentage" in types_found
    assert "time" in types_found
    assert "count" in types_found


def test_extract_no_abstract():
    """Test handling of missing abstract."""
    article = {
        "pmid": "99999",
        "abstract": "No abstract available"
    }
    
    evidence = extract_numeric_evidence(article)
    
    assert len(evidence) == 0


def test_extract_empty_abstract():
    """Test handling of empty abstract."""
    article = {
        "pmid": "88888",
        "abstract": ""
    }
    
    evidence = extract_numeric_evidence(article)
    
    assert len(evidence) == 0


def test_context_window_extraction():
    """Test that context window is extracted around numeric values."""
    article = {
        "pmid": "22222",
        "abstract": "Previous research found baseline levels. Our study demonstrated a 50% improvement in productivity metrics. This was significant."
    }
    
    evidence = extract_numeric_evidence(article)
    
    percentage_evidence = [e for e in evidence if e["type"] == "percentage"]
    assert len(percentage_evidence) >= 1
    
    # Context should include surrounding text
    context = percentage_evidence[0]["context"]
    assert "50%" in context or "50 " in context
    assert len(context) > 0


def test_extract_all_numeric_evidence_multiple_articles():
    """Test extraction across multiple articles."""
    articles = [
        {
            "pmid": "11111",
            "abstract": "Study found 30% improvement."
        },
        {
            "pmid": "22222",
            "abstract": "Treatment took 4 hours."
        }
    ]
    
    all_evidence = extract_all_numeric_evidence(articles)
    
    assert len(all_evidence) >= 2
    pmids = {e["pmid"] for e in all_evidence}
    assert "11111" in pmids
    assert "22222" in pmids


def test_extract_time_various_units():
    """Test extraction of time with various units."""
    article = {
        "pmid": "33333",
        "abstract": "Treatment duration was 10 minutes, with follow-up at 3 days, 2 weeks, and 6 months."
    }
    
    evidence = extract_numeric_evidence(article)
    
    time_evidence = [e for e in evidence if e["type"] == "time"]
    assert len(time_evidence) >= 4
    
    units_found = {e["unit"] for e in time_evidence}
    assert "minutes" in units_found
    assert "days" in units_found
    assert "weeks" in units_found
    assert "months" in units_found


def test_raw_text_captured():
    """Test that raw text snippet is captured."""
    article = {
        "pmid": "44444",
        "abstract": "The efficiency increased by 25% compared to baseline."
    }
    
    evidence = extract_numeric_evidence(article)
    
    assert len(evidence) > 0
    assert evidence[0]["raw"] in ["25%", "25 %"]
    assert evidence[0]["raw"] is not None


def test_decimal_percentages():
    """Test extraction of decimal percentages."""
    article = {
        "pmid": "55555",
        "abstract": "Success rate improved by 12.5% in the treatment group."
    }
    
    evidence = extract_numeric_evidence(article)
    
    percentage_evidence = [e for e in evidence if e["type"] == "percentage"]
    assert len(percentage_evidence) >= 1
    assert percentage_evidence[0]["value"] == 12.5
