"""Test constants and enumerations match required values."""

from impactpilot.constants import IDEA_TYPE_OPTIONS, RD_STAGE_OPTIONS


def test_idea_type_options_exact():
    """Test IDEA_TYPE_OPTIONS has exact values in exact order."""
    expected = [
        "Software/Digital Tool",
        "Assay/Analytical Method",
        "Therapeutic/Drug",
        "Diagnostic",
        "Medical Device",
        "Platform Technology",
        "Process Optimization",
        "Other",
    ]
    assert IDEA_TYPE_OPTIONS == expected


def test_rd_stage_options_exact():
    """Test RD_STAGE_OPTIONS has exact values in exact order."""
    expected = [
        "Discovery/Research",
        "Proof of Concept",
        "Preclinical",
        "Phase 1 Clinical",
        "Phase 2 Clinical",
        "Phase 3 Clinical",
        "Regulatory/Commercialization",
    ]
    assert RD_STAGE_OPTIONS == expected


def test_idea_type_options_length():
    """Test IDEA_TYPE_OPTIONS has correct length."""
    assert len(IDEA_TYPE_OPTIONS) == 8


def test_rd_stage_options_length():
    """Test RD_STAGE_OPTIONS has correct length."""
    assert len(RD_STAGE_OPTIONS) == 7


def test_no_duplicates_in_idea_types():
    """Test that IDEA_TYPE_OPTIONS has no duplicates."""
    assert len(IDEA_TYPE_OPTIONS) == len(set(IDEA_TYPE_OPTIONS))


def test_no_duplicates_in_rd_stages():
    """Test that RD_STAGE_OPTIONS has no duplicates."""
    assert len(RD_STAGE_OPTIONS) == len(set(RD_STAGE_OPTIONS))
