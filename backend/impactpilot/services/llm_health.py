"""LLM provider configuration validation and connection testing."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

_NON_CHAT = ("embedding", "embed", "whisper", "tts", "dall-e", "transcribe", "realtime", "audio")


def _chat_deployment(name: str, model: str) -> bool:
    blob = f"{name} {model}".lower()
    return not any(token in blob for token in _NON_CHAT)


def _fetch_azure_chat_deployments(
    base_url: str, api_key: str, *, timeout: int
) -> tuple[bool, str, list[dict[str, Any]]]:
    """Deployments that accept chat calls. The /models catalog lists models that are not deployed."""
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    url = f"{origin}/openai/deployments?api-version=2023-03-15-preview"
    r = requests.get(url, headers={"api-key": api_key}, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    raw = payload.get("data") or payload.get("value") or []
    rows: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("id") or item.get("name") or "")
        model = str(item.get("model") or item.get("modelName") or "")
        if name and _chat_deployment(name, model):
            rows.append({"id": name, "model": model})
    return (True, f"Found {len(rows)} deployment(s)", rows)


def fetch_openai_compatible_models(
    base_url: str,
    api_key: str,
    *,
    timeout: int = 15,
) -> tuple[bool, str, list[dict[str, Any]]]:
    """
    List models a caller can actually select.
    Azure hosts return chat deployments. Other hosts return GET {base_url}/models.
    Each row is {"id": str, "model": str}.
    """
    url_base = base_url.strip().rstrip("/")
    key = api_key.strip()
    if not url_base or not key:
        return (False, "Base URL and API key are required", [])

    if "openai.azure.com" in urlparse(url_base).netloc:
        try:
            return _fetch_azure_chat_deployments(url_base, key, timeout=timeout)
        except requests.RequestException:
            pass

    url = f"{url_base}/models"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        raw = data.get("data", [])
        if not isinstance(raw, list):
            return (False, "Unexpected models response shape", [])

        out: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if model_id and _chat_deployment(str(model_id), str(model_id)):
                out.append({"id": str(model_id), "model": str(model_id)})

        return (True, f"Found {len(out)} model(s)", out)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else "unknown"
        return (False, f"HTTP {status}: {exc}", [])
    except requests.RequestException as exc:
        return (False, f"Request failed: {exc}", [])
    except Exception as exc:  # noqa: BLE001
        return (False, str(exc), [])


def fetch_azure_openai_deployments(
    endpoint: str,
    api_key: str,
    *,
    timeout: int = 15,
) -> tuple[bool, str, list[dict[str, Any]]]:
    """
    List Azure OpenAI deployments for a resource (GET .../openai/deployments).
    Returns (ok, message, rows) where each row is {"name": str, "model": str}.
    """
    ep = endpoint.strip().rstrip("/")
    key = api_key.strip()
    if not ep or not key:
        return (False, "Endpoint and API key are required", [])

    # Try multiple API versions in case one fails
    api_versions = ["2024-06-01", "2023-05-15", "2024-08-01-preview"]
    last_error = None

    for api_version in api_versions:
        url = f"{ep}/openai/deployments?api-version={api_version}"
        headers = {"api-key": key}
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            raw = data.get("data") or data.get("value") or []
            if not isinstance(raw, list):
                last_error = f"Unexpected response shape (tried api-version={api_version})"
                continue

            out: list[dict[str, Any]] = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                props = item.get("properties") or {}
                if not name:
                    name = props.get("deploymentName") or props.get("name")
                if not name:
                    continue

                model_display = ""
                m = props.get("model")
                if isinstance(m, str):
                    model_display = m
                elif isinstance(m, dict):
                    model_display = str(m.get("name") or m.get("id") or "")

                out.append({"name": str(name), "model": model_display})

            return (True, f"Found {len(out)} deployment(s)", out)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response else "unknown"
            last_error = f"HTTP {status}: {exc}"
            # Don't retry on auth errors
            if status in (401, 403):
                break
        except requests.RequestException as exc:
            last_error = f"Request failed: {exc}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)

    return (False, f"Failed to list deployments: {last_error}", [])


def validate_llm_settings(settings: dict) -> list[str]:
    """
    Return list of validation error messages (empty if valid).
    provider==openai_compatible requires openai_base_url, openai_api_key, openai_model.
    provider==azure_openai requires azure_openai_endpoint, azure_openai_api_key, azure_openai_deployment.
    """
    errors: list[str] = []
    provider = settings.get("provider", "")

    if provider == "openai_compatible":
        if not settings.get("openai_base_url", "").strip():
            errors.append("OpenAI-compatible: Base URL is required")
        if not settings.get("openai_api_key", "").strip():
            errors.append("OpenAI-compatible: API key is required")
        if not settings.get("openai_model", "").strip():
            errors.append("OpenAI-compatible: Model is required")
    elif provider == "azure_openai":
        if not settings.get("azure_openai_endpoint", "").strip():
            errors.append("Azure OpenAI: Endpoint URL is required")
        if not settings.get("azure_openai_api_key", "").strip():
            errors.append("Azure OpenAI: API key is required")
        if not settings.get("azure_openai_deployment", "").strip():
            errors.append("Azure OpenAI: Deployment name is required")
    else:
        errors.append(f"Unknown provider: {provider}")

    return errors


def check_llm_connection(
    settings: dict,
) -> tuple[bool, str, list[dict[str, Any]] | None]:
    """
    Check connection to the configured LLM provider.
    openai_compatible: GET {openai_base_url}/v1/models with Authorization Bearer
    azure_openai: GET {endpoint}/openai/deployments?api-version=2024-06-01 with api-key header
    Returns (ok, message, azure_deployments_or_none). For Azure, third item is the parsed
    deployment list (possibly empty); for other providers it is None.
    """
    provider = settings.get("provider", "")

    if provider == "openai_compatible":
        base_url = settings.get("openai_base_url", "").strip()
        api_key = settings.get("openai_api_key", "").strip()
        if not base_url:
            return (False, "OpenAI base URL not configured", None)
        if not api_key:
            return (False, "OpenAI API key not configured", None)
        base = base_url.rstrip("/")
        url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            models = data.get("data", [])
            return (
                True,
                f"Connected to OpenAI-compatible ({len(models)} models)",
                None,
            )
        except requests.RequestException as exc:
            return (False, f"OpenAI connection failed: {exc}", None)
        except Exception as exc:  # noqa: BLE001
            return (False, f"OpenAI error: {exc}", None)

    elif provider == "azure_openai":
        endpoint = settings.get("azure_openai_endpoint", "").strip()
        api_key = settings.get("azure_openai_api_key", "").strip()
        if not endpoint:
            return (False, "Azure OpenAI endpoint not configured", None)
        if not api_key:
            return (False, "Azure OpenAI API key not configured", None)
        ok, msg, items = fetch_azure_openai_deployments(
            endpoint, api_key, timeout=5
        )
        if not ok:
            return (False, msg, items)
        n = len(items)
        return (
            True,
            f"Connected to Azure OpenAI ({n} deployments visible)",
            items,
        )

    return (False, f"Unknown provider: {provider}", None)
