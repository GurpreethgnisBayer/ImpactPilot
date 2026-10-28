"""CORE (core.ac.uk) search: open-access reports, theses, and repository papers. Needs CORE_API_KEY."""

from __future__ import annotations

import os
from typing import Any

import requests

CORE_URL = "https://api.core.ac.uk/v3/search/works"
_MAX = 8


def _clip(text: str, limit: int = 1200) -> str:
    return " ".join((text or "").split())[:limit]


def search_core(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    q = (query or "").strip()
    key = os.environ.get("CORE_API_KEY", "").strip()
    if not q:
        return []
    if not key:
        raise RuntimeError("CORE_API_KEY is not set.")
    limit = max(1, min(max_results, _MAX))
    r = requests.get(
        CORE_URL,
        params={"q": q, "limit": limit},
        headers={"Authorization": f"Bearer {key}"},
        timeout=timeout,
    )
    if r.status_code == 429:
        raise RuntimeError("CORE rate limited (HTTP 429).")
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for work in r.json().get("results") or []:
        work_id = str(work.get("id") or "").strip()
        title = (work.get("title") or "").strip()
        # Many repository records (reports, theses) have no abstract; the start of the text stands in.
        abstract = _clip(work.get("abstract") or "") or _clip(work.get("fullText") or "")
        if not work_id or not title or not abstract:
            continue
        links = {link.get("type"): link.get("url") for link in work.get("links") or [] if isinstance(link, dict)}
        url = links.get("display") or work.get("downloadUrl") or f"https://core.ac.uk/works/{work_id}"
        out.append(
            {
                "source_id": f"CORE:{work_id}",
                "database": "core",
                "doi": str(work.get("doi") or "").strip(),
                "title": title,
                "abstract": abstract,
                "year": str(work.get("yearPublished") or ""),
                "venue": str(work.get("publisher") or "CORE repository"),
                "type": str(work.get("documentType") or "report"),
                "url": url,
            }
        )
    return out
