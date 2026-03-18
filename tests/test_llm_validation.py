"""Test LLM settings validation."""

from impactpilot.services.llm_health import validate_llm_settings


def test_validate_ollama_missing_host():
    """Test that missing Ollama host produces error."""
    settings = {
        "provider": "ollama",
        "ollama_host": "",
        "ollama_model": "llama3.1:8b",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("host" in err.lower() for err in errors)


def test_validate_ollama_missing_model():
    """Test that missing Ollama model produces error."""
    settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("model" in err.lower() for err in errors)


def test_validate_ollama_complete():
    """Test that complete Ollama settings pass validation."""
    settings = {
        "provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "llama3.1:8b",
    }
    errors = validate_llm_settings(settings)
    assert errors == []


def test_validate_openai_missing_base_url():
    """Test that missing OpenAI base URL produces error."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "",
        "openai_api_key": "sk-test",
        "openai_model": "gpt-4",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("base url" in err.lower() or "url" in err.lower() for err in errors)


def test_validate_openai_missing_api_key():
    """Test that missing OpenAI API key produces error."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com",
        "openai_api_key": "",
        "openai_model": "gpt-4",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("api key" in err.lower() or "key" in err.lower() for err in errors)


def test_validate_openai_missing_model():
    """Test that missing OpenAI model produces error."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com",
        "openai_api_key": "sk-test",
        "openai_model": "",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("model" in err.lower() for err in errors)


def test_validate_openai_complete():
    """Test that complete OpenAI settings pass validation."""
    settings = {
        "provider": "openai_compatible",
        "openai_base_url": "https://api.openai.com",
        "openai_api_key": "sk-test123",
        "openai_model": "gpt-4",
    }
    errors = validate_llm_settings(settings)
    assert errors == []


def test_validate_missing_provider():
    """Test that missing provider produces error."""
    settings = {
        "provider": "",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("provider" in err.lower() for err in errors)


def test_validate_unknown_provider():
    """Test that unknown provider produces error."""
    settings = {
        "provider": "unknown_provider",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) > 0
    assert any("unknown" in err.lower() for err in errors)


def test_validate_multiple_errors():
    """Test that multiple missing fields produce multiple errors."""
    settings = {
        "provider": "ollama",
        "ollama_host": "",
        "ollama_model": "",
    }
    errors = validate_llm_settings(settings)
    assert len(errors) >= 2
