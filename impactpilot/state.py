"""Session state management for Impact Estimate."""

import streamlit as st
import os


def init_state():
    """Initialize all session state keys with default values."""
    
    # Current step (0..3)
    if "step" not in st.session_state:
        st.session_state.step = 0
    
    # Step 1: Idea
    if "idea" not in st.session_state:
        st.session_state.idea = {
            "title": "",
            "description": "",
            "idea_type": "",
            "rd_stage": "",
        }
    
    # Step 2: Evidence query
    if "evidence_query" not in st.session_state:
        st.session_state.evidence_query = {
            "query": "",
            "date_preset": "5years",
            "max_results": 20,
            "sort": "relevance",
            "auto_update": True,
            # Advanced filters
            "journal": "",
            "author": "",
            "language": "",
            "has_abstract": False,
            "publication_types": [],
            "field_restriction": "all",
            "custom_mindate": "",
            "custom_maxdate": "",
        }
    
    # Step 2: Evidence results
    if "evidence_results" not in st.session_state:
        st.session_state.evidence_results = []
    
    # Step 2: Selected PMIDs
    if "evidence_selected_pmids" not in st.session_state:
        st.session_state.evidence_selected_pmids = set()
    
    # Step 3: Assumptions
    if "assumptions" not in st.session_state:
        st.session_state.assumptions = {}
    
    # Step 3: Extracted numeric evidence
    if "extracted_numeric_evidence" not in st.session_state:
        st.session_state.extracted_numeric_evidence = []
    
    # LLM settings (provider + parameters)
    # Prefill from environment variables if available
    if "llm_settings" not in st.session_state:
        st.session_state.llm_settings = {
            "provider": os.getenv("LLM_PROVIDER", "ollama"),
            "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "ollama_model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            "openai_base_url": os.getenv("OPENAI_BASE_URL", ""),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "openai_model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            "azure_api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            "azure_api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        }
    
    # Step 4: Brief markdown
    if "brief_markdown" not in st.session_state:
        st.session_state.brief_markdown = ""
