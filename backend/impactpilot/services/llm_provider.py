"""LLM provider implementations (OpenAI-compatible, Azure OpenAI)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import quote, urlencode

import requests


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from prompt."""


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible endpoint provider."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, timeout: int = 120) -> str:
        """POST {base_url}/v1/chat/completions; return choices[0].message.content."""
        # Base URLs such as https://<resource>.openai.azure.com/openai/v1 already end in /v1.
        if self.base_url.endswith("/v1"):
            url = f"{self.base_url}/chat/completions"
        else:
            url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", ""))


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI (resource endpoint + deployment name)."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment.strip()
        self.api_version = (api_version or "2024-08-01-preview").strip()

    def generate(self, prompt: str, timeout: int = 120) -> str:
        """
        POST {endpoint}/openai/deployments/{deployment}/chat/completions?api-version=...
        Uses api-key header (Azure REST). Returns choices[0].message.content.
        """
        dep = quote(self.deployment, safe="")
        qs = urlencode({"api-version": self.api_version})
        url = (
            f"{self.endpoint}/openai/deployments/{dep}/chat/completions?{qs}"
        )
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", ""))


def build_provider(settings: dict) -> LLMProvider:
    """Build provider instance from settings dict."""
    provider = settings.get("provider", "")
    if provider == "openai_compatible":
        return OpenAICompatibleProvider(
            base_url=settings.get("openai_base_url", ""),
            api_key=settings.get("openai_api_key", ""),
            model=settings.get("openai_model", ""),
        )
    elif provider == "azure_openai":
        return AzureOpenAIProvider(
            endpoint=settings.get("azure_openai_endpoint", ""),
            api_key=settings.get("azure_openai_api_key", ""),
            deployment=settings.get("azure_openai_deployment", ""),
            api_version=settings.get("azure_openai_api_version", "2024-08-01-preview"),
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
