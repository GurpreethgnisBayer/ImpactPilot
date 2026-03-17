"""Session state management for ImpactPilot."""

import streamlit as st


def init_state():
    """Initialize all session state keys with default values."""
    
    # Current step (0..3)
    if "step" not in st.session_state:
        st.session_state.step = 0
    
    # Step 1: Idea input
    if "idea" not in st.session_state:
        st.session_state.idea = {
            "title": "",
            "description": "",
            "idea_type": "",
            "rd_stage": ""
        }
    
    # Step 2: Evidence query configuration
    if "evidence_query" not in st.session_state:
        st.session_state.evidence_query = {
            "query": "",
            "date_preset": "5years",
            "max_results": 20,
            "sort": "relevance",
            "advanced": {
                "publication_types": [],
                "journal": "",
                "author": "",
                "language": "",
                "has_abstract": True,
                "field_restriction": ""
            }
        }
    
    # Auto-update query from idea (default ON)
    if "auto_update_query" not in st.session_state:
        st.session_state.auto_update_query = True
    
    # Step 2: Evidence search results
    if "evidence_results" not in st.session_state:
        st.session_state.evidence_results = []
    
    # Step 2: User-selected PubMed IDs
    if "evidence_selected_pmids" not in st.session_state:
        st.session_state.evidence_selected_pmids = set()
    
    # Step 3: Extracted numeric evidence from selected abstracts
    if "extracted_numeric_evidence" not in st.session_state:
        st.session_state.extracted_numeric_evidence = []
    
    # Step 3: Assumptions (will be populated later)
    if "assumptions" not in st.session_state:
        st.session_state.assumptions = {}
    
    # LLM settings (sidebar configuration)
    if "llm_settings" not in st.session_state:
        st.session_state.llm_settings = {
            "provider": "ollama",  # "ollama" or "openai_compatible"
            "ollama_host": "http://localhost:11434",
            "ollama_model": "llama2",
            "temperature": 0.7,
            "max_tokens": 1000,
            "openai_base_url": "",
            "openai_api_key": "",
            "openai_model": "gpt-3.5-turbo"
        }
