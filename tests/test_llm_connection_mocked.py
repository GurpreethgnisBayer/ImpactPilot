"""Test LLM connection functions with mocked requests."""

from unittest.mock import Mock, patch
from impactpilot.services.llm_health import check_llm_connection


def test_ollama_connection_success():
    """Test successful Ollama connection."""
    settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3.1:8b",
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "llama3.1:8b"}]}
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        ok, message = check_llm_connection(settings)
        
        assert ok is True
        assert "Connected" in message or "✓" in message
        mock_get.assert_called_once()
        assert "/api/tags" in mock_get.call_args[0][0]


def test_ollama_connection_timeout():
    """Test Ollama connection timeout."""
    settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3.1:8b",
    }
    
    with patch("requests.get", side_effect=Exception("Timeout")) as mock_get:
        ok, message = check_llm_connection(settings)
        
        assert ok is False
        assert len(message) > 0


def test_ollama_connection_missing_host():
    """Test Ollama connection with missing host."""
    settings = {
        "provider": "ollama",
        "ollama_host": "",
        "ollama_model": "llama3.1:8b",
    }
    
    ok, message = check_llm_connection(settings)
    
    assert ok is False
    assert "host" in message.lower() or "configured" in message.lower()


def test_openai_connection_success():
    """Test successful OpenAI connection."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com",
        "openai_api_key": "sk-test",
        "openai_model": "gpt-4",
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "gpt-4"}]}
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        ok, message = check_llm_connection(settings)
        
        assert ok is True
        assert "Connected" in message or "✓" in message
        mock_get.assert_called_once()
        
        # Verify Authorization header was set
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert "Bearer sk-test" in call_kwargs["headers"]["Authorization"]


def test_openai_connection_auth_failure():
    """Test OpenAI connection with authentication failure."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com",
        "openai_api_key": "invalid-key",
        "openai_model": "gpt-4",
    }
    
    mock_response = Mock()
    mock_response.status_code = 401
    
    with patch("requests.get", return_value=mock_response):
        ok, message = check_llm_connection(settings)
        
        assert ok is False
        assert "auth" in message.lower() or "key" in message.lower()


def test_openai_connection_missing_key():
    """Test OpenAI connection with missing API key."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com",
        "openai_api_key": "",
        "openai_model": "gpt-4",
    }
    
    ok, message = check_llm_connection(settings)
    
    assert ok is False
    assert "key" in message.lower() or "configured" in message.lower()


def test_unknown_provider():
    """Test connection with unknown provider."""
    settings = {
        "provider": "unknown",
    }
    
    ok, message = check_llm_connection(settings)
    
    assert ok is False
    assert "unknown" in message.lower() or "provider" in message.lower()
