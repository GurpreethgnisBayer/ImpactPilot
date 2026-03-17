"""Tests to verify report never fabricates data when evidence is missing."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.report import build_brief_markdown


def test_report_shows_not_found_when_assumptions_missing():
    """Test that report shows '[Not found in selected evidence]' when assumptions are None."""
    idea = {
        "title": "Test Idea",
        "description": "Testing no fabrication",
        "idea_type": "Test",
        "rd_stage": "Concept"
    }
    
    selected_articles = [
        {
            "pmid": "12345",
            "title": "Test Article",
            "authors": "Smith J",
            "year": "2024",
            "journal": "Test Journal",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345/"
        }
    ]
    
    # All assumptions are None (no evidence)
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            },
            "cost_avoided_per_year": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            }
        },
        "tco": {
            "implementation_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            },
            "annual_operating_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No numeric evidence found in selected abstracts."
            }
        }
    }
    
    tco_out = {
        "horizon_cost": None,
        "annual_run_cost": None,
        "breakdown": {},
        "explanation": "Insufficient evidence-derived inputs for TCO. Validate or provide inputs."
    }
    
    prod_out = {
        "horizon_productivity_value": None,
        "annual_productivity_value": None,
        "breakdown": {},
        "throughput_delta_per_year": None,
        "success_prob_delta": None,
        "explanation": "Insufficient evidence-derived inputs for productivity. Validate or provide inputs."
    }
    
    report = build_brief_markdown(
        idea=idea,
        selected_articles=selected_articles,
        extracted_numeric_evidence=[],
        assumptions=assumptions,
        tco_out=tco_out,
        prod_out=prod_out,
        horizon_years=3
    )
    
    # Check that report contains "[Not found in selected evidence]" markers
    assert "[Not found in selected evidence]" in report, "Report must indicate when evidence is not found"
    
    # Count occurrences - should have at least 4 (one for each assumption field)
    not_found_count = report.count("[Not found in selected evidence]")
    assert not_found_count >= 4, f"Expected at least 4 '[Not found]' markers, found {not_found_count}"


def test_report_does_not_contain_placeholder_numbers():
    """Test that report does not contain placeholder numbers like 123 or TBD when data is missing."""
    idea = {"title": "Test", "description": "Test", "idea_type": "", "rd_stage": ""}
    selected_articles = [{"pmid": "12345", "title": "Test", "authors": "Test", 
                         "year": "2024", "journal": "Test", "url": "https://test.com"}]
    
    # No evidence
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            },
            "cost_avoided_per_year": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        },
        "tco": {
            "implementation_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            },
            "annual_operating_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        }
    }
    
    tco_out = {
        "horizon_cost": None,
        "annual_run_cost": None,
        "breakdown": {},
        "explanation": "Insufficient evidence-derived inputs for TCO. Validate or provide inputs."
    }
    
    prod_out = {
        "horizon_productivity_value": None,
        "annual_productivity_value": None,
        "breakdown": {},
        "throughput_delta_per_year": None,
        "success_prob_delta": None,
        "explanation": "Insufficient evidence-derived inputs for productivity. Validate or provide inputs."
    }
    
    report = build_brief_markdown(idea, selected_articles, [], assumptions, tco_out, prod_out, 3)
    
    # Check that explanatory messages are present
    assert "Insufficient evidence-derived inputs for TCO" in report
    assert "Insufficient evidence-derived inputs for productivity" in report
    
    # Check that report does NOT contain placeholder values
    # (We allow legitimate PMIDs like 12345, but not context-free "123" or "TBD")
    lines = report.split('\n')
    for line in lines:
        # Skip PMID references
        if 'PMID' in line or 'pmid' in line:
            continue
        # Skip horizon years references
        if 'horizon =' in line:
            continue
        # Check for standalone placeholder patterns
        assert 'TBD' not in line, "Report must not contain 'TBD' placeholder"
        assert '$123' not in line, "Report must not contain placeholder dollar amounts"


def test_report_not_computable_messages():
    """Test that 'Not computable' messages appear when TCO/productivity cannot be computed."""
    idea = {"title": "Test", "description": "Test", "idea_type": "", "rd_stage": ""}
    selected_articles = [{"pmid": "12345", "title": "Test", "authors": "Test", 
                         "year": "2024", "journal": "Test", "url": "https://test.com"}]
    
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            },
            "cost_avoided_per_year": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        },
        "tco": {
            "implementation_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            },
            "annual_operating_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        }
    }
    
    tco_out = {
        "horizon_cost": None,
        "annual_run_cost": None,
        "breakdown": {},
        "explanation": "Insufficient evidence-derived inputs for TCO. Validate or provide inputs."
    }
    
    prod_out = {
        "horizon_productivity_value": None,
        "annual_productivity_value": None,
        "breakdown": {},
        "throughput_delta_per_year": None,
        "success_prob_delta": None,
        "explanation": "Insufficient evidence-derived inputs for productivity. Validate or provide inputs."
    }
    
    report = build_brief_markdown(idea, selected_articles, [], assumptions, tco_out, prod_out, 3)
    
    # Verify "not computable" or "insufficient" language in TCO section
    tco_section_start = report.find("## Computed TCO")
    tco_section_end = report.find("## Computed R&D pipeline", tco_section_start)
    tco_section = report[tco_section_start:tco_section_end]
    
    assert "Insufficient" in tco_section or "not computable" in tco_section.lower(), \
        "TCO section must state when not computable"
    
    # Verify "not computable" or "insufficient" language in productivity section
    prod_section_start = report.find("## Computed R&D pipeline")
    prod_section_end = report.find("## Evidence mapping", prod_section_start)
    prod_section = report[prod_section_start:prod_section_end]
    
    assert "Insufficient" in prod_section or "not computable" in prod_section.lower(), \
        "Productivity section must state when not computable"


def test_report_with_evidence_shows_provenance():
    """Test that when evidence exists, report shows proper provenance."""
    idea = {"title": "Test", "description": "Test", "idea_type": "", "rd_stage": ""}
    selected_articles = [
        {"pmid": "11111", "title": "Test Article", "authors": "Smith J", 
         "year": "2024", "journal": "Test Journal", "url": "https://pubmed.ncbi.nlm.nih.gov/11111/"}
    ]
    
    # With evidence
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": 15.5,
                "evidence_pmids": ["11111"],
                "evidence_raw": ["3 hours"],
                "explanation": "Estimated from time reduction of 3 hours mentioned in abstract."
            },
            "cost_avoided_per_year": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        },
        "tco": {
            "implementation_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            },
            "annual_operating_cost": {
                "value": None,
                "evidence_pmids": [],
                "evidence_raw": [],
                "explanation": "No evidence"
            }
        }
    }
    
    tco_out = {"horizon_cost": None, "annual_run_cost": None, "breakdown": {}, "explanation": "Insufficient"}
    prod_out = {
        "horizon_productivity_value": 18600,
        "annual_productivity_value": 6200,
        "breakdown": {"annual_hours_saved": 186, "annual_time_value": 6200, "cost_avoided_per_year": 0},
        "throughput_delta_per_year": None,
        "success_prob_delta": None,
        "explanation": ""
    }
    
    report = build_brief_markdown(idea, selected_articles, [], assumptions, tco_out, prod_out, 3)
    
    # Check that evidence-backed value is marked as such
    assert "[Evidence-derived]" in report, "Evidence-backed values must be marked"
    
    # Check that PMID provenance is shown
    assert "Source: PMID" in report, "Must show PMID source for evidence"
    assert "11111" in report, "Must include the actual PMID"
    assert "3 hours" in report, "Must show raw evidence snippet"
    
    # Check that computed value is shown (not "not computable")
    assert "$18,600" in report or "18600" in report, "Should show computed productivity value"
    assert "$6,200" in report or "6200" in report, "Should show annual productivity value"
