"""Test PubMed term building functionality."""

from impactpilot.services.pubmed_eutils import build_term


def test_build_term_base_query_only():
    """Test building term with only base query."""
    term = build_term("cancer therapy")
    assert "cancer therapy" in term


def test_build_term_with_journal():
    """Test that journal filter is appended correctly."""
    term = build_term("cancer", journal="Nature")
    assert "cancer" in term
    assert '"Nature"[Journal]' in term
    assert "AND" in term


def test_build_term_with_author():
    """Test that author filter is appended correctly."""
    term = build_term("diabetes", author="Smith J")
    assert "diabetes" in term
    assert '"Smith J"[Author]' in term
    assert "AND" in term


def test_build_term_with_language():
    """Test that language filter is appended correctly."""
    term = build_term("covid", language="eng")
    assert "covid" in term
    assert "eng[Language]" in term
    assert "AND" in term


def test_build_term_with_abstract_required():
    """Test that hasabstract filter is appended."""
    term = build_term("immunology", has_abstract=True)
    assert "immunology" in term
    assert "hasabstract" in term
    assert "AND" in term


def test_build_term_with_publication_types():
    """Test that publication type filters are appended."""
    term = build_term("treatment", publication_types=["Clinical Trial", "Review"])
    assert "treatment" in term
    assert '"Clinical Trial"[Publication Type]' in term
    assert '"Review"[Publication Type]' in term
    assert term.count("AND") >= 2


def test_build_term_field_restriction_title():
    """Test field restriction to title only."""
    term = build_term("alzheimer", field_restriction="title")
    assert "[Title]" in term
    assert "alzheimer" in term


def test_build_term_field_restriction_title_abstract():
    """Test field restriction to title/abstract."""
    term = build_term("parkinson", field_restriction="title_abstract")
    assert "[Title/Abstract]" in term
    assert "parkinson" in term


def test_build_term_field_restriction_all():
    """Test field restriction set to all (default)."""
    term = build_term("neuroscience", field_restriction="all")
    assert "neuroscience" in term
    # Should not have field restrictions
    assert "[Title]" not in term
    assert "[Title/Abstract]" not in term


def test_build_term_multiple_filters():
    """Test combining multiple filters."""
    term = build_term(
        "machine learning",
        journal="Science",
        author="Doe J",
        language="eng",
        has_abstract=True,
        publication_types=["Review"],
        field_restriction="title_abstract"
    )
    
    assert "machine learning" in term
    assert "[Title/Abstract]" in term
    assert '"Science"[Journal]' in term
    assert '"Doe J"[Author]' in term
    assert "eng[Language]" in term
    assert "hasabstract" in term
    assert '"Review"[Publication Type]' in term
    # Should have multiple AND operators
    assert term.count("AND") >= 5


def test_build_term_empty_base_query():
    """Test handling of empty base query with filters."""
    term = build_term("", journal="Nature")
    assert '"Nature"[Journal]' in term


def test_build_term_no_filters():
    """Test with no filters applied."""
    term = build_term("genomics")
    assert term == "(genomics)"
