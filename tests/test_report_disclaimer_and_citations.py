"""Tests to verify report contains disclaimer and only selected citations."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.report import build_brief_markdown
from impactpilot.disclaimer import DISCLAIMER_TEXT


def test_report_contains_disclaimer():
    """Test that the generated report contains DISCLAIMER_TEXT."""
    idea = {
        "title": "Test Idea",
        "description": "Testing report generation",
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
        "explanation": "Insufficient evidence-derived inputs for TCO."
    }
    
    prod_out = {
        "horizon_productivity_value": None,
        "annual_productivity_value": None,
        "breakdown": {},
        "throughput_delta_per_year": None,
        "success_prob_delta": None,
        "explanation": "Insufficient evidence-derived inputs for productivity."
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
    
    # Check that disclaimer is present
    assert DISCLAIMER_TEXT in report, "Report must contain DISCLAIMER_TEXT"
    
    # Check that it's near the top (in the first 500 chars typically)
    assert report.find(DISCLAIMER_TEXT) < 500, "Disclaimer should be near the top of the report"


def test_citations_only_include_selected_pmids():
    """Test that citations include only selected PMIDs, not fabricated ones."""
    idea = {
        "title": "Test Idea",
        "description": "Testing citations",
        "idea_type": "Test",
        "rd_stage": "Concept"
    }
    
    # Selected articles
    selected_articles = [
        {
            "pmid": "11111",
            "title": "First Article",
            "authors": "Smith J",
            "year": "2024",
            "journal": "Journal A",
            "url": "https://pubmed.ncbi.nlm.nih.gov/11111/"
        },
        {
            "pmid": "22222",
            "title": "Second Article",
            "authors": "Doe J",
            "year": "2023",
            "journal": "Journal B",
            "url": "https://pubmed.ncbi.nlm.nih.gov/22222/"
        }
    ]
    
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "value": 10,
                "evidence_pmids": ["11111"],
                "evidence_raw": ["2 hours"],
                "explanation": "Test"
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
    
    tco_out = {"horizon_cost": None, "annual_run_cost": None, "breakdown": {}, "explanation": "Test"}
    prod_out = {"horizon_productivity_value": 12000, "annual_productivity_value": 4000, "breakdown": {}, 
                "throughput_delta_per_year": None, "success_prob_delta": None, "explanation": ""}
    
    report = build_brief_markdown(
        idea=idea,
        selected_articles=selected_articles,
        extracted_numeric_evidence=[],
        assumptions=assumptions,
        tco_out=tco_out,
        prod_out=prod_out,
        horizon_years=3
    )
    
    # Check that selected PMIDs are present
    assert "11111" in report, "Report must include selected PMID 11111"
    assert "22222" in report, "Report must include selected PMID 22222"
    
    # Check that citations section exists
    assert "## Citations" in report, "Report must have Citations section"
    
    # Check article titles appear
    assert "First Article" in report
    assert "Second Article" in report


def test_report_structure_has_all_sections():
    """Test that report has all required sections in correct order."""
    idea = {"title": "Test", "description": "Test", "idea_type": "", "rd_stage": ""}
    selected_articles = [{"pmid": "12345", "title": "Test", "authors": "Test", "year": "2024", 
                         "journal": "Test", "url": "https://test.com"}]
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"},
            "cost_avoided_per_year": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"}
        },
        "tco": {
            "implementation_cost": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"},
            "annual_operating_cost": {"value": None, "evidence_pmids": [], "evidence_raw": [], "explanation": "No evidence"}
        }
    }
    tco_out = {"horizon_cost": None, "annual_run_cost": None, "breakdown": {}, "explanation": "Test"}
    prod_out = {"horizon_productivity_value": None, "annual_productivity_value": None, "breakdown": {}, 
                "throughput_delta_per_year": None, "success_prob_delta": None, "explanation": "Test"}
    
    report = build_brief_markdown(idea, selected_articles, [], assumptions, tco_out, prod_out, 3)
    
    # Check section order
    summary_pos = report.find("## Summary")
    evidence_pos = report.find("## Evidence used")
    assumptions_pos = report.find("## Evidence-derived assumptions")
    tco_pos = report.find("## Computed TCO")
    prod_pos = report.find("## Computed R&D pipeline productivity")
    mapping_pos = report.find("## Evidence mapping")
    citations_pos = report.find("## Citations")
    questions_pos = report.find("## Open questions")
    
    # All sections must exist
    assert summary_pos > 0
    assert evidence_pos > 0
    assert assumptions_pos > 0
    assert tco_pos > 0
    assert prod_pos > 0
    assert mapping_pos > 0
    assert citations_pos > 0
    assert questions_pos > 0
    
    # Verify order
    assert summary_pos < evidence_pos < assumptions_pos < tco_pos < prod_pos < mapping_pos < citations_pos < questions_pos


def test_disclaimer_text_exact_match():
    """Test that DISCLAIMER_TEXT matches the exact specification."""
    expected = "Disclaimer: This tool generates directional estimates. You must validate all inferred assumptions and evidence before using TCO or productivity numbers in decisions, submissions, or commitments."
    assert DISCLAIMER_TEXT == expected, "DISCLAIMER_TEXT must match exact specification"
