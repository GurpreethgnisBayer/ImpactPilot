"""LLM provider abstraction for Ollama and OpenAI-compatible endpoints."""

import requests
from typing import Optional
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from prompt."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, host: str, model: str, temperature: float = 0.7, max_tokens: int = 1000):
        self.host = host.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Ollama API.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Generated text response
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            return f"Error generating response: {e}"


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible API provider."""
    
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float = 0.7):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using OpenAI-compatible API.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error generating response: {e}"


def get_provider(settings: dict) -> Optional[LLMProvider]:
    """
    Get LLM provider instance from settings.
    
    Args:
        settings: LLM settings dictionary
        
    Returns:
        LLMProvider instance or None
    """
    provider_type = settings.get("provider", "ollama")
    
    if provider_type == "ollama":
        return OllamaProvider(
            host=settings.get("ollama_host", "http://localhost:11434"),
            model=settings.get("ollama_model", "llama2"),
            temperature=settings.get("temperature", 0.7),
            max_tokens=settings.get("max_tokens", 1000)
        )
    elif provider_type == "openai_compatible":
        api_key = settings.get("openai_api_key", "")
        if not api_key:
            return None
        return OpenAICompatibleProvider(
            base_url=settings.get("openai_base_url", ""),
            api_key=api_key,
            model=settings.get("openai_model", "gpt-3.5-turbo"),
            temperature=settings.get("temperature", 0.7)
        )
    
    return None
