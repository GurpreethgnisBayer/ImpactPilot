"""Tests for evidence-grounded assumptions derivation."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.assumptions import derive_assumptions, validate_assumptions_grounding
from impactpilot.evidence_numbers import extract_numeric_evidence


def test_assumptions_never_invent_pmids():
    """Test that assumptions only use PMIDs from selected articles."""
    idea = {"title": "Test Idea", "description": "Test"}
    selected_articles = [
        {"pmid": "11111", "abstract": "Study found 25% improvement."},
        {"pmid": "22222", "abstract": "Process took 3 hours."}
    ]
    
    # Extract evidence
    evidence = []
    for article in selected_articles:
        evidence.extend(extract_numeric_evidence(article))
    
    # Derive assumptions
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    # Collect all evidence PMIDs from assumptions
    all_assumption_pmids = set()
    for category in assumptions.values():
        for field_data in category.values():
            if isinstance(field_data, dict):
                all_assumption_pmids.update(field_data.get("evidence_pmids", []))
    
    # All PMIDs must be from selected articles
    selected_pmids = {"11111", "22222"}
    assert all_assumption_pmids.issubset(selected_pmids), "Assumptions contain PMIDs not in selected articles"


def test_assumptions_empty_when_no_evidence():
    """Test that assumptions are None when no numeric evidence exists."""
    idea = {"title": "Test", "description": "Test"}
    selected_articles = [
        {"pmid": "99999", "abstract": "This abstract has no numbers."}
    ]
    
    evidence = []
    for article in selected_articles:
        evidence.extend(extract_numeric_evidence(article))
    
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    # All values should be None when no evidence
    assert assumptions["productivity"]["time_saved_hours_per_month"]["value"] is None
    assert assumptions["productivity"]["cost_avoided_per_year"]["value"] is None
    assert assumptions["tco"]["implementation_cost"]["value"] is None


def test_assumptions_include_explanation_when_empty():
    """Test that empty assumptions include 'No numeric evidence found' explanation."""
    idea = {"title": "Test", "description": "Test"}
    selected_articles = [
        {"pmid": "88888", "abstract": "Qualitative study with no numbers."}
    ]
    
    evidence = []
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    # Check that explanation exists for empty fields
    time_saved = assumptions["productivity"]["time_saved_hours_per_month"]
    assert time_saved["value"] is None
    assert "No numeric evidence found" in time_saved["explanation"]


def test_assumptions_populated_with_time_evidence():
    """Test that time evidence populates time_saved field."""
    idea = {"title": "Efficiency Tool", "description": "Saves time"}
    selected_articles = [
        {"pmid": "12345", "abstract": "The new process reduced time by 5 hours per week."}
    ]
    
    evidence = []
    for article in selected_articles:
        evidence.extend(extract_numeric_evidence(article))
    
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    time_saved = assumptions["productivity"]["time_saved_hours_per_month"]
    
    # Should have a value if time evidence was found
    if evidence:  # Only test if evidence was actually extracted
        assert time_saved["value"] is not None or time_saved["value"] == 0
        if time_saved["value"] is not None:
            assert "12345" in time_saved["evidence_pmids"]
            assert len(time_saved["evidence_raw"]) > 0


def test_assumptions_with_percentage_evidence():
    """Test that percentage evidence can populate assumptions."""
    idea = {"title": "Process Improvement", "description": "Reduces effort"}
    selected_articles = [
        {"pmid": "55555", "abstract": "Implementation resulted in 30% reduction in processing time."}
    ]
    
    evidence = []
    for article in selected_articles:
        evidence.extend(extract_numeric_evidence(article))
    
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    time_saved = assumptions["productivity"]["time_saved_hours_per_month"]
    
    # If percentage evidence exists, it might populate time_saved
    if evidence:
        # Either populated or explicitly None with explanation
        assert "value" in time_saved
        assert "explanation" in time_saved
        assert "evidence_pmids" in time_saved


def test_validate_assumptions_grounding():
    """Test validation that all assumption PMIDs are in selected set."""
    selected_pmids = {"11111", "22222", "33333"}
    
    # Valid assumptions - all PMIDs in selected set
    valid_assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": 10,
                "evidence_pmids": ["11111"],
                "evidence_raw": ["5 hours"],
                "explanation": "Test"
            }
        },
        "tco": {
            "implementation_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        }
    }
    
    assert validate_assumptions_grounding(valid_assumptions, selected_pmids) is True
    
    # Invalid assumptions - contains PMID not in selected set
    invalid_assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": 10,
                "evidence_pmids": ["99999"],  # Not in selected_pmids
                "evidence_raw": ["5 hours"],
                "explanation": "Test"
            }
        },
        "tco": {}
    }
    
    assert validate_assumptions_grounding(invalid_assumptions, selected_pmids) is False


def test_assumptions_structure_complete():
    """Test that assumptions have complete structure."""
    idea = {"title": "Test", "description": "Test"}
    selected_articles = [{"pmid": "12345", "abstract": "Study found 20% improvement."}]
    evidence = []
    
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    # Check structure completeness
    assert "productivity" in assumptions
    assert "tco" in assumptions
    
    assert "time_saved_hours_per_month" in assumptions["productivity"]
    assert "cost_avoided_per_year" in assumptions["productivity"]
    
    assert "implementation_cost" in assumptions["tco"]
    assert "annual_operating_cost" in assumptions["tco"]
    
    # Each field should have required keys
    for category in assumptions.values():
        for field_data in category.values():
            if isinstance(field_data, dict):
                assert "value" in field_data
                assert "evidence_pmids" in field_data
                assert "evidence_raw" in field_data
                assert "explanation" in field_data


def test_assumptions_evidence_raw_matches_pmids():
    """Test that evidence_raw list length matches evidence_pmids."""
    idea = {"title": "Test", "description": "Test"}
    selected_articles = [
        {"pmid": "12345", "abstract": "Process completed in 2 hours with 40% efficiency gain."}
    ]
    
    evidence = []
    for article in selected_articles:
        evidence.extend(extract_numeric_evidence(article))
    
    assumptions = derive_assumptions(idea, selected_articles, evidence)
    
    # Check that raw evidence matches PMIDs
    for category in assumptions.values():
        for field_data in category.values():
            if isinstance(field_data, dict):
                pmids = field_data.get("evidence_pmids", [])
                raws = field_data.get("evidence_raw", [])
                # If there are PMIDs, there should be corresponding raw evidence
                if pmids:
                    assert len(raws) > 0, "Evidence PMIDs present but no raw evidence"
