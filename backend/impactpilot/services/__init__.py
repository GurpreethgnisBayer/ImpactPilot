"""External service clients."""

from impactpilot.services.llm_health import (
    check_llm_connection,
    fetch_azure_openai_deployments,
    fetch_openai_compatible_models,
    validate_llm_settings,
)
from impactpilot.services.llm_provider import (
    AzureOpenAIProvider,
    LLMProvider,
    OpenAICompatibleProvider,
    build_provider,
)
from impactpilot.services.pubmed_eutils import (
    build_term,
    efetch,
    esearch,
    search_pubmed,
)

__all__ = [
    "build_term",
    "esearch",
    "efetch",
    "search_pubmed",
    "validate_llm_settings",
    "check_llm_connection",
    "fetch_azure_openai_deployments",
    "fetch_openai_compatible_models",
    "LLMProvider",
    "OpenAICompatibleProvider",
    "AzureOpenAIProvider",
    "build_provider",
]
