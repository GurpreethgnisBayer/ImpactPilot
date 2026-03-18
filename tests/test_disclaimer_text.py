"""Test disclaimer text is present and correct."""

from impactpilot.disclaimer import DISCLAIMER_TEXT


def test_disclaimer_text_exists():
    """Test that DISCLAIMER_TEXT is defined and non-empty."""
    assert DISCLAIMER_TEXT is not None
    assert len(DISCLAIMER_TEXT) > 0
    assert isinstance(DISCLAIMER_TEXT, str)


def test_disclaimer_text_content():
    """Test that DISCLAIMER_TEXT contains expected key phrases."""
    assert "directional estimates" in DISCLAIMER_TEXT.lower()
    assert "validate" in DISCLAIMER_TEXT.lower()
    

def test_disclaimer_text_exact():
    """Test that DISCLAIMER_TEXT matches the exact required text."""
    expected = "Disclaimer: This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments."
    assert DISCLAIMER_TEXT == expected
