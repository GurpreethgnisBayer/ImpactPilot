"""Tests for PubMed term building functionality."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.services.pubmed_eutils import build_term


def test_build_term_basic():
    """Test basic term building with just a query."""
    term = build_term("cancer research", has_abstract=False)
    
    assert "cancer research" in term
    assert term == "cancer research"


def test_build_term_with_journal():
    """Test term building with journal qualifier."""
    term = build_term("diabetes", journal="Nature")
    
    assert "diabetes" in term
    assert '"Nature"[Journal]' in term
    assert " AND " in term


def test_build_term_with_author():
    """Test term building with author qualifier."""
    term = build_term("protein folding", author="Smith J")
    
    assert "protein folding" in term
    assert '"Smith J"[Author]' in term
    assert " AND " in term


def test_build_term_with_language():
    """Test term building with language qualifier."""
    term = build_term("covid vaccine", language="eng")
    
    assert "covid vaccine" in term
    assert "eng[Language]" in term
    assert " AND " in term


def test_build_term_with_abstract_requirement():
    """Test term building with abstract requirement."""
    term = build_term("clinical trial", has_abstract=True)
    
    assert "clinical trial" in term
    assert "hasabstract" in term
    assert " AND " in term


def test_build_term_without_abstract_requirement():
    """Test term building without abstract requirement."""
    term = build_term("review", has_abstract=False)
    
    assert "review" in term
    assert "hasabstract" not in term


def test_build_term_with_publication_types():
    """Test term building with publication type filters."""
    term = build_term(
        "treatment",
        publication_types=["Clinical Trial", "Randomized Controlled Trial"]
    )
    
    assert "treatment" in term
    assert '"Clinical Trial"[Publication Type]' in term
    assert '"Randomized Controlled Trial"[Publication Type]' in term
    assert " AND " in term


def test_build_term_with_field_restriction():
    """Test term building with field restriction."""
    term = build_term("gene therapy", field_restriction="tiab")
    
    assert "(gene therapy[tiab])" in term


def test_build_term_multiple_qualifiers():
    """Test term building with multiple qualifiers."""
    term = build_term(
        base_query="alzheimer disease",
        journal="Journal of Neuroscience",
        author="Doe J",
        language="eng",
        has_abstract=True,
        publication_types=["Review"],
        field_restriction="tiab"
    )
    
    # Should contain all qualifiers joined by AND
    assert "(alzheimer disease[tiab])" in term
    assert '"Journal of Neuroscience"[Journal]' in term
    assert '"Doe J"[Author]' in term
    assert "eng[Language]" in term
    assert "hasabstract" in term
    assert '"Review"[Publication Type]' in term
    
    # Should have proper AND separators
    assert term.count(" AND ") >= 5


def test_build_term_empty_optional_params():
    """Test that empty optional parameters are ignored."""
    term = build_term(
        base_query="stem cells",
        journal="",
        author="",
        language="",
        has_abstract=False,
        publication_types=[],
        field_restriction=""
    )
    
    assert term == "stem cells"
    assert " AND " not in term


def test_build_term_only_qualifiers_no_base():
    """Test term building with qualifiers but no base query."""
    term = build_term(
        base_query="",
        journal="Science",
        has_abstract=True
    )
    
    # Should still build a valid term with just the qualifiers
    assert '"Science"[Journal]' in term
    assert "hasabstract" in term


def test_build_term_special_characters_in_journal():
    """Test term building with special characters in journal name."""
    term = build_term("cancer", journal="PLOS ONE")
    
    assert '"PLOS ONE"[Journal]' in term


def test_build_term_field_restriction_title_only():
    """Test term building with title-only field restriction."""
    term = build_term("machine learning", field_restriction="title")
    
    assert "(machine learning[title])" in term
