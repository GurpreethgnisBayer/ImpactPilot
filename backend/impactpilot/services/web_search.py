"""Optional web search for white papers and reports, limited to an editable domain allowlist.

Provider: WEB_SEARCH_PROVIDER=tavily|brave with TAVILY_API_KEY or BRAVE_SEARCH_API_KEY. When the
provider is not set, whichever key is present is used (Tavily first).
"""

from __future__ import annotations

import hashlib
import html
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml

from impactpilot.config_loader import _default_config_dir

TAVILY_URL = "https://api.tavily.com/search"
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"
_MAX = 8
_SUFFIX = "white paper OR report"
_REPO_CONFIG = Path(__file__).resolve().parents[3] / "config"


def allowed_domains(path: Path | None = None) -> list[str]:
    p = path or (_default_config_dir() / "web_sources.yaml")
    if not p.exists():
        p = _REPO_CONFIG / "web_sources.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    groups = data.get("web_sources") or {}
    domains = [d for values in groups.values() for d in (values or [])]
    return [str(d).strip().lower() for d in dict.fromkeys(domains) if str(d).strip()]


def _allowed(url: str, domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in domains)


def _plain(text: str, limit: int = 1200) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text or "")).split())[:limit]


def _provider() -> tuple[str, str]:
    choice = os.environ.get("WEB_SEARCH_PROVIDER", "").strip().lower()
    keys = {
        "tavily": os.environ.get("TAVILY_API_KEY", "").strip(),
        "brave": os.environ.get("BRAVE_SEARCH_API_KEY", "").strip(),
    }
    if choice:
        if choice not in keys:
            raise RuntimeError(f"Unknown WEB_SEARCH_PROVIDER '{choice}'. Use tavily or brave.")
        if not keys[choice]:
            raise RuntimeError(f"WEB_SEARCH_PROVIDER={choice} but its API key is not set.")
        return choice, keys[choice]
    for name, key in keys.items():
        if key:
            return name, key
    raise RuntimeError("No web search key set (TAVILY_API_KEY or BRAVE_SEARCH_API_KEY).")


def _tavily(query: str, key: str, domains: list[str], limit: int, timeout: int) -> list[dict[str, str]]:
    r = requests.post(
        TAVILY_URL,
        json={"query": query, "max_results": limit, "include_domains": domains, "search_depth": "basic"},
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )
    r.raise_for_status()
    return [
        {
            "title": x.get("title") or "",
            "url": x.get("url") or "",
            "text": x.get("content") or "",
            "date": x.get("published_date") or "",
        }
        for x in r.json().get("results") or []
    ]


def _brave(query: str, key: str, limit: int, timeout: int) -> list[dict[str, str]]:
    # Brave has no domain filter parameter, so over-fetch and filter by the allowlist afterwards.
    r = requests.get(
        BRAVE_URL,
        params={"q": query, "count": 20},
        headers={"X-Subscription-Token": key, "Accept": "application/json"},
        timeout=timeout,
    )
    r.raise_for_status()
    return [
        {
            "title": x.get("title") or "",
            "url": x.get("url") or "",
            "text": " ".join([x.get("description") or "", *(x.get("extra_snippets") or [])]),
            "date": x.get("page_age") or x.get("age") or "",
        }
        for x in ((r.json().get("web") or {}).get("results") or [])
    ]


def search_web(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    provider, key = _provider()
    domains = allowed_domains()
    limit = max(1, min(max_results, _MAX))
    full_query = f"{q} {_SUFFIX}"
    if provider == "tavily":
        raw = _tavily(full_query, key, domains, limit, timeout)
    else:
        raw = _brave(full_query, key, limit, timeout)
    out: list[dict[str, Any]] = []
    for item in raw:
        url, title = item["url"].strip(), _plain(item["title"], 300)
        abstract = _plain(item["text"])
        if not url or not title or not abstract or not _allowed(url, domains):
            continue
        year = m.group(0) if (m := re.search(r"(19|20)\d{2}", item["date"] or "")) else ""
        out.append(
            {
                "source_id": f"WEB:{hashlib.sha1(url.encode()).hexdigest()[:12]}",
                "database": "web",
                "title": title,
                "abstract": abstract,
                "year": year,
                "venue": (urlparse(url).hostname or "").removeprefix("www."),
                "type": "report",
                "url": url,
            }
        )
        if len(out) >= limit:
            break
    return out
