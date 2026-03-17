"""Test disclaimer text is present and correct."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.disclaimer import DISCLAIMER_TEXT


def test_disclaimer_exists():
    """Test that DISCLAIMER_TEXT is defined and non-empty."""
    assert DISCLAIMER_TEXT is not None
    assert len(DISCLAIMER_TEXT) > 0
    assert isinstance(DISCLAIMER_TEXT, str)


def test_disclaimer_content():
    """Test that DISCLAIMER_TEXT contains expected key phrases."""
    assert "Disclaimer" in DISCLAIMER_TEXT
    assert "directional estimates" in DISCLAIMER_TEXT
    assert "validate" in DISCLAIMER_TEXT
    assert "TCO" in DISCLAIMER_TEXT
    assert "productivity" in DISCLAIMER_TEXT


def test_disclaimer_exact_text():
    """Test the exact disclaimer text matches specification."""
    expected = "Disclaimer: This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments."
    assert DISCLAIMER_TEXT == expected
