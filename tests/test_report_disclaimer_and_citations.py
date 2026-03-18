"""Test that report includes disclaimer and only selected PMIDs."""

from impactpilot.report import build_brief_markdown
from impactpilot.disclaimer import DISCLAIMER_TEXT


def test_report_includes_disclaimer():
    """Test that the brief includes the required disclaimer text."""
    idea = {
        "title": "Test Idea",
        "description": "Test description",
        "idea_type": "Software/Digital Tool",
        "rd_stage": "Proof of Concept"
    }
    
    selected_articles = [
        {
            "pmid": "12345",
            "title": "Test Article",
            "abstract": "Test abstract",
            "journal": "Test Journal",
            "year": "2024",
            "authors": ["Smith J"],
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345/"
        }
    ]
    
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
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
        },
        "overall_confidence": "low",
        "assumptions": [],
        "open_questions": []
    }
    
    tco_out = {
        "build_person_days_midpoint": 45.0,
        "run_person_days_per_year_midpoint": 15.0,
        "build_cost_usd": 36000.0,
        "run_cost_per_year_usd": 12000.0,
        "total_run_cost_usd": 36000.0,
        "total_tco_usd": 72000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    prod_out = {
        "time_saved_hours_per_month_midpoint": 15.0,
        "cost_avoided_per_year_midpoint": 3000.0,
        "time_saved_hours_per_year": 180.0,
        "time_value_per_year_usd": 18000.0,
        "total_time_saved_hours": 540.0,
        "total_time_value_usd": 54000.0,
        "total_cost_avoided_usd": 9000.0,
        "total_productivity_gain_usd": 63000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    brief = build_brief_markdown(idea, selected_articles, assumptions, tco_out, prod_out, 3)
    
    # Check that disclaimer text is present
    assert DISCLAIMER_TEXT in brief
    
    # Check that it's in a blockquote (markdown > )
    assert f"> **Disclaimer:** {DISCLAIMER_TEXT}" in brief


def test_report_includes_only_selected_pmids():
    """Test that the report only includes citations for selected articles."""
    idea = {
        "title": "Test Idea",
        "description": "Test description",
        "idea_type": "Software/Digital Tool",
        "rd_stage": "Proof of Concept"
    }
    
    # Only these articles were selected
    selected_articles = [
        {
            "pmid": "11111",
            "title": "Selected Article 1",
            "abstract": "Abstract 1",
            "journal": "Journal A",
            "year": "2023",
            "authors": ["Author A"],
            "url": "https://pubmed.ncbi.nlm.nih.gov/11111/"
        },
        {
            "pmid": "22222",
            "title": "Selected Article 2",
            "abstract": "Abstract 2",
            "journal": "Journal B",
            "year": "2024",
            "authors": ["Author B"],
            "url": "https://pubmed.ncbi.nlm.nih.gov/22222/"
        }
    ]
    
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "evidence_supported",
                "evidence_pmids": ["11111"],
                "evidence_quotes": ["This tool saved time"],
                "explanation": "Based on article 11111"
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
        },
        "overall_confidence": "medium",
        "assumptions": [],
        "open_questions": []
    }
    
    tco_out = {
        "build_person_days_midpoint": 45.0,
        "run_person_days_per_year_midpoint": 15.0,
        "build_cost_usd": 36000.0,
        "run_cost_per_year_usd": 12000.0,
        "total_run_cost_usd": 36000.0,
        "total_tco_usd": 72000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    prod_out = {
        "time_saved_hours_per_month_midpoint": 15.0,
        "cost_avoided_per_year_midpoint": 3000.0,
        "time_saved_hours_per_year": 180.0,
        "time_value_per_year_usd": 18000.0,
        "total_time_saved_hours": 540.0,
        "total_time_value_usd": 54000.0,
        "total_cost_avoided_usd": 9000.0,
        "total_productivity_gain_usd": 63000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    brief = build_brief_markdown(idea, selected_articles, assumptions, tco_out, prod_out, 3)
    
    # Check that selected PMIDs are in the citations
    assert "11111" in brief
    assert "22222" in brief
    
    # Check that article titles are present
    assert "Selected Article 1" in brief
    assert "Selected Article 2" in brief
    
    # Check Citations section exists
    assert "## Citations" in brief
    
    # Check that the PMIDs appear in the Evidence Used section
    assert "PMID: 11111" in brief
    assert "PMID: 22222" in brief


def test_report_shows_ranges_not_just_midpoints():
    """Test that the report displays full ranges, not just midpoints."""
    idea = {
        "title": "Test Idea",
        "description": "Test description",
        "idea_type": "Software/Digital Tool",
        "rd_stage": "Proof of Concept"
    }
    
    selected_articles = []
    
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
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
        },
        "overall_confidence": "low",
        "assumptions": [],
        "open_questions": []
    }
    
    tco_out = {
        "build_person_days_midpoint": 45.0,
        "run_person_days_per_year_midpoint": 15.0,
        "build_cost_usd": 36000.0,
        "run_cost_per_year_usd": 12000.0,
        "total_run_cost_usd": 36000.0,
        "total_tco_usd": 72000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    prod_out = {
        "time_saved_hours_per_month_midpoint": 15.0,
        "cost_avoided_per_year_midpoint": 3000.0,
        "time_saved_hours_per_year": 180.0,
        "time_value_per_year_usd": 18000.0,
        "total_time_saved_hours": 540.0,
        "total_time_value_usd": 54000.0,
        "total_cost_avoided_usd": 9000.0,
        "total_productivity_gain_usd": 63000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    brief = build_brief_markdown(idea, selected_articles, assumptions, tco_out, prod_out, 3)
    
    # Check that ranges are displayed in the assumptions section
    assert "10–20 hours" in brief  # time saved range
    assert "1000–5000 USD" in brief  # cost avoided range
    assert "30–60 person-days" in brief  # build time range
    assert "10–20 person-days/year" in brief  # run time range


def test_report_includes_support_labels():
    """Test that support labels (evidence-supported vs heuristic) are shown."""
    idea = {
        "title": "Test Idea",
        "description": "Test description",
        "idea_type": "Software/Digital Tool",
        "rd_stage": "Proof of Concept"
    }
    
    selected_articles = [
        {
            "pmid": "99999",
            "title": "Test Article",
            "abstract": "Test",
            "journal": "Test Journal",
            "year": "2024",
            "authors": ["Test Author"],
            "url": "https://pubmed.ncbi.nlm.nih.gov/99999/"
        }
    ]
    
    assumptions = {
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 10,
                "range_max": 20,
                "support_level": "evidence_supported",
                "evidence_pmids": ["99999"],
                "evidence_quotes": ["This proves the point"],
                "explanation": "Strong evidence"
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
        },
        "overall_confidence": "medium",
        "assumptions": [],
        "open_questions": []
    }
    
    tco_out = {
        "build_person_days_midpoint": 45.0,
        "run_person_days_per_year_midpoint": 15.0,
        "build_cost_usd": 36000.0,
        "run_cost_per_year_usd": 12000.0,
        "total_run_cost_usd": 36000.0,
        "total_tco_usd": 72000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    prod_out = {
        "time_saved_hours_per_month_midpoint": 15.0,
        "cost_avoided_per_year_midpoint": 3000.0,
        "time_saved_hours_per_year": 180.0,
        "time_value_per_year_usd": 18000.0,
        "total_time_saved_hours": 540.0,
        "total_time_value_usd": 54000.0,
        "total_cost_avoided_usd": 9000.0,
        "total_productivity_gain_usd": 63000.0,
        "horizon_years": 3,
        "hourly_rate": 100.0
    }
    
    brief = build_brief_markdown(idea, selected_articles, assumptions, tco_out, prod_out, 3)
    
    # Check for support level labels
    assert "Evidence-supported" in brief
    assert "Heuristic/Ballpark" in brief
    
    # Check for evidence quotes
    assert "This proves the point" in brief
    
    # Check for PMID reference
    assert "99999" in brief
