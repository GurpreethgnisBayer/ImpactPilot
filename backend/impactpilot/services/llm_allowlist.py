"""Refuse LLM requests to hosts not in llm_endpoints.yaml allowlist."""

from __future__ import annotations

import fnmatch
from urllib.parse import urlparse

from impactpilot.config_loader import get_config


def host_allowed(url: str) -> bool:
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()
    if not host:
        return False
    cfg = get_config().llm_endpoints
    for entry in cfg.get("approved_endpoints") or []:
        pattern = str(entry.get("host") or "").lower()
        schemes = [s.lower() for s in (entry.get("schemes") or ["https"])]
        if scheme and scheme not in schemes:
            continue
        if fnmatch.fnmatch(host, pattern):
            return True
    return False


def assert_host_allowed(url: str) -> None:
    if not host_allowed(url):
        raise PermissionError(
            f"LLM endpoint host is not on the approved allowlist: {urlparse(url).hostname}"
        )
