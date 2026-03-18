"""LLM provider implementations for Ollama, OpenAI-compatible, and Azure OpenAI endpoints."""

import requests
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from prompt."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""
    
    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Ollama API.
        
        Args:
            prompt: The prompt to send to the model
        
        Returns:
            Generated text response
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
        
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {str(e)}")


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible LLM provider."""
    
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using OpenAI-compatible API.
        
        Args:
            prompt: The prompt to send to the model
        
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except requests.exceptions.Timeout:
            raise RuntimeError("OpenAI request timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response format: {str(e)}")


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider."""
    
    def __init__(self, endpoint: str, api_key: str, deployment_name: str, api_version: str = "2024-02-15-preview"):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.api_version = api_version
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Azure OpenAI API.
        
        Args:
            prompt: The prompt to send to the model
        
        Returns:
            Generated text response
        """
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": "user", "content": prompt}],
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except requests.exceptions.Timeout:
            raise RuntimeError("Azure OpenAI request timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Azure OpenAI request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected response format: {str(e)}")


def build_provider(settings: dict) -> LLMProvider:
    """
    Build an LLM provider instance from settings.
    
    Args:
        settings: Dictionary containing provider configuration
    
    Returns:
        Configured LLM provider instance
    
    Raises:
        ValueError: If provider type is unknown or configuration is invalid
    """
    provider = settings.get("provider")
    
    if provider == "ollama":
        host = settings.get("ollama_host")
        model = settings.get("ollama_model")
        
        if not host or not model:
            raise ValueError("Ollama host and model are required")
        
        return OllamaProvider(host=host, model=model)
    
    elif provider == "openai_compatible":
        base_url = settings.get("openai_base_url")
        api_key = settings.get("openai_api_key")
        model = settings.get("openai_model")
        
        if not base_url or not api_key or not model:
            raise ValueError("OpenAI base URL, API key, and model are required")
        
        return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, model=model)
    
    elif provider == "azure":
        endpoint = settings.get("azure_endpoint")
        api_key = settings.get("azure_api_key")
        deployment = settings.get("azure_deployment")
        api_version = settings.get("azure_api_version", "2024-02-15-preview")
        
        if not endpoint or not api_key or not deployment:
            raise ValueError("Azure endpoint, API key, and deployment are required")
        
        return AzureOpenAIProvider(
            endpoint=endpoint,
            api_key=api_key,
            deployment_name=deployment,
            api_version=api_version
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}")
