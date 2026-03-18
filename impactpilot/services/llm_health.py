"""LLM health check and validation utilities."""

import requests
from typing import Tuple


def validate_llm_settings(settings: dict) -> list[str]:
    """
    Validate LLM settings based on provider type.
    
    Args:
        settings: Dictionary containing LLM configuration
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    provider = settings.get("provider", "")
    
    if not provider:
        errors.append("Provider not specified")
        return errors
    
    if provider == "ollama":
        if not settings.get("ollama_host"):
            errors.append("Ollama host is required")
        if not settings.get("ollama_model"):
            errors.append("Ollama model is required")
    
    elif provider == "openai_compatible":
        if not settings.get("openai_base_url"):
            errors.append("OpenAI base URL is required")
        if not settings.get("openai_api_key"):
            errors.append("OpenAI API key is required")
        if not settings.get("openai_model"):
            errors.append("OpenAI model is required")
    
    elif provider == "azure":
        if not settings.get("azure_endpoint"):
            errors.append("Azure endpoint is required")
        if not settings.get("azure_api_key"):
            errors.append("Azure API key is required")
        if not settings.get("azure_deployment"):
            errors.append("Azure deployment name is required")
    
    else:
        errors.append(f"Unknown provider: {provider}")
    
    return errors


def check_llm_connection(settings: dict) -> Tuple[bool, str]:
    """
    Test connection to LLM provider.
    
    Args:
        settings: Dictionary containing LLM configuration
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    provider = settings.get("provider", "")
    
    if provider == "ollama":
        return _test_ollama_connection(settings)
    elif provider == "openai_compatible":
        return _test_openai_connection(settings)
    elif provider == "azure":
        return _test_azure_connection(settings)
    else:
        return False, f"Unknown provider: {provider}"


def _test_ollama_connection(settings: dict) -> Tuple[bool, str]:
    """Test connection to Ollama server."""
    ollama_host = settings.get("ollama_host", "")
    
    if not ollama_host:
        return False, "Ollama host not configured"
    
    try:
        # Remove trailing slash and add /api/tags endpoint
        url = f"{ollama_host.rstrip('/')}/api/tags"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            model_count = len(models)
            return True, f"✓ Connected to Ollama ({model_count} models available)"
        else:
            return False, f"Ollama server returned status {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, "Connection timeout - is Ollama running?"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {ollama_host}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def _test_openai_connection(settings: dict) -> Tuple[bool, str]:
    """Test connection to OpenAI-compatible endpoint."""
    base_url = settings.get("openai_base_url", "")
    api_key = settings.get("openai_api_key", "")
    
    if not base_url:
        return False, "OpenAI base URL not configured"
    if not api_key:
        return False, "OpenAI API key not configured"
    
    try:
        # Remove trailing slash and add /v1/models endpoint
        url = f"{base_url.rstrip('/')}/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            model_count = len(models)
            return True, f"✓ Connected to OpenAI-compatible endpoint ({model_count} models available)"
        elif response.status_code == 401:
            return False, "Authentication failed - check API key"
        else:
            return False, f"Server returned status {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {base_url}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def _test_azure_connection(settings: dict) -> Tuple[bool, str]:
    """Test connection to Azure OpenAI endpoint."""
    endpoint = settings.get("azure_endpoint", "")
    api_key = settings.get("azure_api_key", "")
    deployment = settings.get("azure_deployment", "")
    api_version = settings.get("azure_api_version", "2024-02-15-preview")
    
    if not endpoint:
        return False, "Azure endpoint not configured"
    if not api_key:
        return False, "Azure API key not configured"
    if not deployment:
        return False, "Azure deployment not configured"
    
    try:
        # Test with a simple completion request
        url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }
        # Simple test payload
        payload = {
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5,
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, f"✓ Connected to Azure OpenAI (deployment: {deployment})"
        elif response.status_code == 401:
            return False, "Authentication failed - check API key"
        elif response.status_code == 404:
            return False, f"Deployment '{deployment}' not found"
        else:
            return False, f"Server returned status {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {endpoint}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
