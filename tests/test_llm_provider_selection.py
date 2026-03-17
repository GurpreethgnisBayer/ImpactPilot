"""Tests for LLM provider selection and configuration."""

import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from impactpilot.services.llm_provider import (
    OllamaProvider, OpenAICompatibleProvider, get_provider
)


def test_ollama_provider_initialization():
    """Test Ollama provider initializes with correct parameters."""
    provider = OllamaProvider(
        host="http://localhost:11434",
        model="llama2",
        temperature=0.7,
        max_tokens=1000
    )
    
    assert provider.host == "http://localhost:11434"
    assert provider.model == "llama2"
    assert provider.temperature == 0.7
    assert provider.max_tokens == 1000


def test_openai_compatible_provider_initialization():
    """Test OpenAI-compatible provider initializes with correct parameters."""
    provider = OpenAICompatibleProvider(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    assert provider.base_url == "https://api.openai.com/v1"
    assert provider.api_key == "test-key"
    assert provider.model == "gpt-3.5-turbo"
    assert provider.temperature == 0.7


def test_get_provider_ollama():
    """Test get_provider returns Ollama provider for ollama settings."""
    settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama2",
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    provider = get_provider(settings)
    
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama2"


def test_get_provider_openai_compatible():
    """Test get_provider returns OpenAI provider for openai_compatible settings."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com/v1",
        "openai_api_key": "test-key",
        "openai_model": "gpt-4",
        "temperature": 0.8
    }
    
    provider = get_provider(settings)
    
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "gpt-4"


def test_get_provider_missing_api_key():
    """Test get_provider returns None when API key is missing."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com/v1",
        "openai_api_key": "",
        "openai_model": "gpt-4"
    }
    
    provider = get_provider(settings)
    
    assert provider is None


@patch('requests.post')
def test_ollama_generate_no_network_call(mock_post):
    """Test Ollama generate method with mocked network call."""
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"response": "Generated text"}
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    provider = OllamaProvider(
        host="http://localhost:11434",
        model="llama2"
    )
    
    result = provider.generate("Test prompt")
    
    # Verify no real network call was made (mocked)
    assert mock_post.called
    assert result == "Generated text"
    
    # Verify correct API endpoint
    call_args = mock_post.call_args
    assert "localhost:11434/api/generate" in call_args[0][0]


@patch('requests.post')
def test_openai_compatible_generate_no_network_call(mock_post):
    """Test OpenAI-compatible generate method with mocked network call."""
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "AI response"}}]
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    provider = OpenAICompatibleProvider(
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    result = provider.generate("Test prompt")
    
    # Verify no real network call was made (mocked)
    assert mock_post.called
    assert result == "AI response"
    
    # Verify correct headers and endpoint
    call_args = mock_post.call_args
    assert "/v1/chat/completions" in call_args[0][0]
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"


def test_provider_selection_based_on_type():
    """Test that correct provider type is selected based on settings."""
    ollama_settings = {"provider": "ollama", "ollama_host": "http://localhost:11434", "ollama_model": "llama2"}
    openai_settings = {"provider": "openai_compatible", "openai_base_url": "https://api.openai.com/v1", 
                       "openai_api_key": "key", "openai_model": "gpt-4"}
    
    ollama_provider = get_provider(ollama_settings)
    openai_provider = get_provider(openai_settings)
    
    assert type(ollama_provider).__name__ == "OllamaProvider"
    assert type(openai_provider).__name__ == "OpenAICompatibleProvider"
