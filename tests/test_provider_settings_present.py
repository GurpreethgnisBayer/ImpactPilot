"""Test that provider settings are present in session state."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from impactpilot.state import init_state
from unittest.mock import MagicMock


class MockSessionState(dict):
    """Mock for Streamlit session_state that supports both dict and attribute access."""
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")


def test_provider_settings_keys_exist():
    """Test that llm_settings contains all required keys after init."""
    # Mock streamlit session_state
    mock_session_state = MockSessionState()
    
    # Mock streamlit module
    import streamlit as st
    original_session_state = st.session_state
    st.session_state = mock_session_state
    
    try:
        # Initialize state
        init_state()
        
        # Check that llm_settings exists
        assert "llm_settings" in mock_session_state
        
        settings = mock_session_state["llm_settings"]
        
        # Check required keys
        assert "provider" in settings
        assert "ollama_host" in settings
        assert "ollama_model" in settings
        assert "openai_base_url" in settings
        assert "openai_api_key" in settings
        assert "openai_model" in settings
    
    finally:
        # Restore original session_state
        st.session_state = original_session_state


def test_provider_default_values():
    """Test that llm_settings has sensible defaults."""
    # Mock streamlit session_state
    mock_session_state = MockSessionState()
    
    # Mock streamlit module
    import streamlit as st
    original_session_state = st.session_state
    st.session_state = mock_session_state
    
    try:
        # Initialize state
        init_state()
        
        settings = mock_session_state["llm_settings"]
        
        # Check defaults
        assert settings["provider"] in ["ollama", "openai_compatible"]
        assert isinstance(settings["ollama_host"], str)
        assert isinstance(settings["ollama_model"], str)
        assert isinstance(settings["openai_base_url"], str)
        assert isinstance(settings["openai_api_key"], str)
        assert isinstance(settings["openai_model"], str)
    
    finally:
        # Restore original session_state
        st.session_state = original_session_state


def test_provider_ollama_defaults():
    """Test that Ollama defaults are reasonable."""
    # Mock streamlit session_state
    mock_session_state = MockSessionState()
    
    # Mock streamlit module
    import streamlit as st
    original_session_state = st.session_state
    st.session_state = mock_session_state
    
    try:
        # Initialize state
        init_state()
        
        settings = mock_session_state["llm_settings"]
        
        # Check Ollama defaults
        assert settings["ollama_host"] != ""
        assert "localhost" in settings["ollama_host"] or "11434" in settings["ollama_host"]
        assert settings["ollama_model"] != ""
    
    finally:
        # Restore original session_state
        st.session_state = original_session_state
