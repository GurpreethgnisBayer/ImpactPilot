"""LLM settings, model listing, connection test, and inference."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from impactpilot.api.deps import acting_as, get_db, get_repo
from impactpilot.persistence.repository import InitiativeRepository
from impactpilot.services.infer import run_dimension_inference
from impactpilot.services.llm_allowlist import assert_host_allowed, host_allowed
from impactpilot.services.llm_health import (
    check_llm_connection,
    fetch_azure_openai_deployments,
    fetch_openai_compatible_models,
    validate_llm_settings,
)

router = APIRouter(prefix="/api/llm", tags=["llm"])


_BLANK = ("", "***")


def _settings_from_env() -> dict[str, Any]:
    return {
        "provider": os.environ.get("IMPACTPILOT_LLM_PROVIDER", ""),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", ""),
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "openai_model": os.environ.get("OPENAI_MODEL", ""),
        "azure_openai_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        "azure_openai_api_key": os.environ.get("AZURE_OPENAI_API_KEY", ""),
        "azure_openai_deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
        "azure_openai_api_version": os.environ.get(
            "AZURE_OPENAI_API_VERSION", "2024-08-01-preview"
        ),
    }


def _platform_env() -> dict[str, Any]:
    """Server LLM config, only when a provider and its secret were actually set."""
    provider = os.environ.get("IMPACTPILOT_LLM_PROVIDER", "").strip()
    if provider == "openai_compatible" and os.environ.get("OPENAI_API_KEY", "").strip():
        return _settings_from_env()
    if provider == "azure_openai" and os.environ.get("AZURE_OPENAI_API_KEY", "").strip():
        return _settings_from_env()
    return {}


SUPPORTED_PROVIDERS = ("openai_compatible", "azure_openai")


def resolve_llm_settings(requested: dict[str, Any] | None) -> dict[str, Any] | None:
    """Platform .env, with non-blank request fields overlaid. None when nothing is configured.

    Overrides naming an unsupported provider (e.g. a stale local-model choice) are ignored.
    """
    env = _platform_env()
    requested = requested or {}
    if requested.get("provider") and requested.get("provider") not in SUPPORTED_PROVIDERS:
        requested = {}
    req: dict[str, Any] = {}
    for key, value in requested.items():
        if key.startswith("ollama_"):
            continue
        if value is None:
            continue
        if isinstance(value, str) and value.strip() in _BLANK:
            continue
        req[key] = value
    if not env and not req:
        return None
    return {**env, **req}


def _public_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Fields safe to show in the browser. The API key never leaves the server."""
    return {
        "provider": settings.get("provider") or "",
        "openai_base_url": settings.get("openai_base_url") or "",
        "openai_model": settings.get("openai_model") or "",
        "azure_openai_endpoint": settings.get("azure_openai_endpoint") or "",
        "azure_openai_deployment": settings.get("azure_openai_deployment") or "",
        "azure_openai_api_version": settings.get("azure_openai_api_version") or "",
        "has_api_key": bool(settings.get("openai_api_key") or settings.get("azure_openai_api_key")),
    }


def _guard_host(settings: dict[str, Any]) -> None:
    provider = settings.get("provider")
    host = {
        "openai_compatible": settings.get("openai_base_url"),
        "azure_openai": settings.get("azure_openai_endpoint"),
    }.get(str(provider))
    if host:
        assert_host_allowed(str(host))


@router.get("/settings")
def get_settings() -> dict[str, Any]:
    return _public_settings(_platform_env())


@router.post("/validate")
def validate(settings: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_llm_settings(settings)
    return {"errors": validate_llm_settings(resolved or {})}


@router.post("/test")
def test_connection(settings: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_llm_settings(settings)
    if not resolved:
        raise HTTPException(400, "No LLM is configured")
    try:
        _guard_host(resolved)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    ok, msg, extra = check_llm_connection(resolved)
    return {"ok": ok, "message": msg, "azure_deployments": extra}


@router.post("/models")
def list_models(settings: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_llm_settings(settings)
    if not resolved:
        raise HTTPException(400, "No LLM is configured")
    provider = resolved.get("provider")
    try:
        _guard_host(resolved)
        if provider == "openai_compatible":
            ok, msg, rows = fetch_openai_compatible_models(
                resolved.get("openai_base_url", ""),
                resolved.get("openai_api_key", ""),
            )
            return {"ok": ok, "message": msg, "models": rows}
        if provider == "azure_openai":
            ok, msg, rows = fetch_azure_openai_deployments(
                resolved.get("azure_openai_endpoint", ""),
                resolved.get("azure_openai_api_key", ""),
            )
            return {"ok": ok, "message": msg, "deployments": rows}
        raise HTTPException(400, "Model listing only for openai_compatible or azure_openai")
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc


@router.get("/allowlist/check")
def check_url(url: str) -> dict[str, bool]:
    return {"allowed": host_allowed(url)}


@router.post("/infer/{initiative_id}")
def infer(
    initiative_id: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = get_repo(db)
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    settings = resolve_llm_settings(payload.get("llm_settings")) or {}
    articles = payload.get("articles") or []
    dims = payload.get("dimension_ids") or record.change.affected_dimension_ids
    if not dims:
        raise HTTPException(400, "No dimension_ids provided")
    try:
        estimates = run_dimension_inference(
            title=record.initiative.title,
            description=record.initiative.description,
            phase=record.scope.phase_id,
            step=record.scope.process_step,
            lever=record.change.lever_type,
            dimension_ids=dims,
            selected_articles=articles,
            llm_settings=settings,
        )
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, str(exc)) from exc

    # Merge: replace matching dims, keep others
    by_id = {e.dimension_id: e for e in record.estimates}
    for e in estimates:
        by_id[e.dimension_id] = e
    record.estimates = list(by_id.values())
    record = repo.save(record, actor=acting_as(), reason="llm_infer")
    return {
        "estimates": [e.model_dump(mode="json") for e in estimates],
        "record": record.model_dump(mode="json"),
    }
