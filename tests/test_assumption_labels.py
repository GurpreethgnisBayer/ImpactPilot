"""Test assumption label validation."""

import pytest
from impactpilot.assumptions import normalize_and_validate


def test_evidence_supported_requires_quotes():
    """Test that evidence_supported must have quotes."""
    inference = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "evidence_supported",
                "evidence_pmids": ["12345"],
                "evidence_quotes": [],  # Missing quotes!
                "explanation": "Based on evidence"
            },
            "cost_avoided_per_year": {
                "range_min": 1000,
                "range_max": 5000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 30,
                "range_max": 60,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        }
    }
    
    selected_pmids = {"12345"}
    
    with pytest.raises(ValueError) as exc_info:
        normalize_and_validate(inference, selected_pmids)
    
    assert "requires at least one quote" in str(exc_info.value)


def test_evidence_supported_requires_pmids():
    """Test that evidence_supported must have PMIDs."""
    inference = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "evidence_supported",
                "evidence_pmids": [],  # Missing PMIDs!
                "evidence_quotes": ["This is a quote"],
                "explanation": "Based on evidence"
            },
            "cost_avoided_per_year": {
                "range_min": 1000,
                "range_max": 5000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 30,
                "range_max": 60,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        }
    }
    
    selected_pmids = {"12345"}
    
    with pytest.raises(ValueError) as exc_info:
        normalize_and_validate(inference, selected_pmids)
    
    assert "requires at least one PMID" in str(exc_info.value)


def test_heuristic_ballpark_requires_empty_pmids():
    """Test that heuristic_ballpark must have empty PMIDs."""
    inference = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": ["12345"],  # Should be empty!
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "cost_avoided_per_year": {
                "range_min": 1000,
                "range_max": 5000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 30,
                "range_max": 60,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        }
    }
    
    selected_pmids = {"12345"}
    
    with pytest.raises(ValueError) as exc_info:
        normalize_and_validate(inference, selected_pmids)
    
    assert "must have empty evidence_pmids" in str(exc_info.value)


def test_heuristic_ballpark_requires_empty_quotes():
    """Test that heuristic_ballpark must have empty quotes."""
    inference = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": ["Some quote"],  # Should be empty!
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "cost_avoided_per_year": {
                "range_min": 1000,
                "range_max": 5000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 30,
                "range_max": 60,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        }
    }
    
    selected_pmids = {"12345"}
    
    with pytest.raises(ValueError) as exc_info:
        normalize_and_validate(inference, selected_pmids)
    
    assert "must have empty evidence_quotes" in str(exc_info.value)


def test_heuristic_ballpark_requires_correct_explanation_prefix():
    """Test that heuristic_ballpark explanation must start with required prefix."""
    inference = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "Wrong prefix here"  # Wrong prefix!
            },
            "cost_avoided_per_year": {
                "range_min": 1000,
                "range_max": 5000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 30,
                "range_max": 60,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        }
    }
    
    selected_pmids = {"12345"}
    
    with pytest.raises(ValueError) as exc_info:
        normalize_and_validate(inference, selected_pmids)
    
    assert "must start with" in str(exc_info.value)
    assert "No supporting evidence found" in str(exc_info.value)


def test_valid_inference_passes():
    """Test that a valid inference passes validation."""
    inference = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "evidence_supported",
                "evidence_pmids": ["12345"],
                "evidence_quotes": ["This tool saved significant time"],
                "explanation": "Based on empirical data"
            },
            "cost_avoided_per_year": {
                "range_min": 1000,
                "range_max": 5000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 30,
                "range_max": 60,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        }
    }
    
    selected_pmids = {"12345"}
    
    # Should not raise
    result = normalize_and_validate(inference, selected_pmids)
    assert result == inference
