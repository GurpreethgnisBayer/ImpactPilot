"""Test that LLM provider.generate is actually called."""

import pytest
from unittest.mock import Mock, patch
from impactpilot.infer_engine import run_inference_pipeline


def test_provider_generate_is_called():
    """Test that provider.generate is called exactly once."""
    idea = {
        "title": "Test idea",
        "description": "Test description",
        "idea_type": "Software/Digital Tool",
        "rd_stage": "Proof of Concept"
    }
    
    selected_articles = [
        {
            "pmid": "12345",
            "title": "Test article",
            "abstract": "This is a test abstract with 25% improvement."
        }
    ]
    
    llm_settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3.1:8b"
    }
    
    # Mock response with valid JSON
    mock_response = """{
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
    }"""
    
    # Create a mock provider
    mock_provider = Mock()
    mock_provider.generate.return_value = mock_response
    
    # Patch build_provider to return our mock
    with patch("impactpilot.infer_engine.build_provider", return_value=mock_provider):
        result = run_inference_pipeline(idea, selected_articles, llm_settings)
        
        # Assert generate was called exactly once
        mock_provider.generate.assert_called_once()
        
        # Verify the result structure
        assert "inference" in result
        assert "numeric_evidence" in result


def test_invalid_settings_prevents_generate_call():
    """Test that invalid LLM settings prevent provider.generate from being called."""
    idea = {
        "title": "Test idea",
        "description": "Test description"
    }
    
    selected_articles = []
    
    # Invalid settings (missing host)
    llm_settings = {
        "provider": "ollama",
        "ollama_host": "",  # Invalid!
        "ollama_model": "llama3.1:8b"
    }
    
    # Create a mock provider
    mock_provider = Mock()
    
    # Patch build_provider
    with patch("impactpilot.infer_engine.build_provider", return_value=mock_provider):
        # Should raise ValueError before calling generate
        with pytest.raises(ValueError) as exc_info:
            run_inference_pipeline(idea, selected_articles, llm_settings)
        
        # Verify generate was NOT called
        mock_provider.generate.assert_not_called()
        
        # Verify error message mentions invalid settings
        assert "Invalid LLM settings" in str(exc_info.value)


def test_generate_called_with_prompt():
    """Test that provider.generate is called with a proper prompt."""
    idea = {
        "title": "AI Drug Discovery",
        "description": "Machine learning for drug screening",
        "idea_type": "Software/Digital Tool",
        "rd_stage": "Proof of Concept"
    }
    
    selected_articles = [
        {
            "pmid": "99999",
            "title": "Test",
            "abstract": "Test abstract"
        }
    ]
    
    llm_settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3.1:8b"
    }
    
    mock_response = """{
        "productivity": {
            "time_saved_hours_per_month": {
                "range_min": 5,
                "range_max": 15,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "cost_avoided_per_year": {
                "range_min": 500,
                "range_max": 2000,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "tco": {
            "build_person_days": {
                "range_min": 20,
                "range_max": 40,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            },
            "run_person_days_per_year": {
                "range_min": 5,
                "range_max": 15,
                "support_level": "heuristic_ballpark",
                "evidence_pmids": [],
                "evidence_quotes": [],
                "explanation": "No supporting evidence found in selected abstracts; directional estimate — user must verify."
            }
        },
        "overall_confidence": "medium",
        "assumptions": ["Test assumption"],
        "open_questions": ["Test question"]
    }"""
    
    mock_provider = Mock()
    mock_provider.generate.return_value = mock_response
    
    with patch("impactpilot.infer_engine.build_provider", return_value=mock_provider):
        result = run_inference_pipeline(idea, selected_articles, llm_settings)
        
        # Get the prompt that was passed
        call_args = mock_provider.generate.call_args
        prompt = call_args[0][0]
        
        # Verify prompt contains key elements
        assert "AI Drug Discovery" in prompt
        assert "Machine learning for drug screening" in prompt
        assert "PMID: 99999" in prompt
        assert "range_min" in prompt
        assert "range_max" in prompt
