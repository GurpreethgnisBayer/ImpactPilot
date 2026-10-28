"""OpenAlex works search (journal articles, preprints, reports)."""

from __future__ import annotations

import os
import time
from typing import Any

import requests

OPENALEX_URL = "https://api.openalex.org/works"
_SELECT = "id,display_name,publication_year,doi,type,abstract_inverted_index,primary_location,cited_by_count"


def _abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(word for _, word in positions)


def _get_with_retry(params: dict[str, Any], timeout: int, attempts: int = 3) -> requests.Response:
    for attempt in range(attempts):
        r = requests.get(OPENALEX_URL, params=params, timeout=timeout)
        if r.status_code != 429 or attempt == attempts - 1:
            r.raise_for_status()
            return r
        retry_after = r.headers.get("Retry-After")
        time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else 1.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def search_openalex(
    query: str,
    *,
    max_results: int = 15,
    from_year: int = 2015,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    params: dict[str, Any] = {
        "search": q,
        "per-page": max(1, min(max_results, 50)),
        "filter": f"has_abstract:true,from_publication_date:{from_year}-01-01",
        "select": _SELECT,
    }
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    if os.environ.get("OPENALEX_MAILTO"):
        params["mailto"] = os.environ["OPENALEX_MAILTO"]
    r = _get_with_retry(params, timeout)
    out: list[dict[str, Any]] = []
    for w in r.json().get("results") or []:
        work_id = str(w.get("id") or "").rsplit("/", 1)[-1]
        if not work_id:
            continue
        loc = w.get("primary_location") or {}
        source = loc.get("source") or {}
        doi = w.get("doi") or ""
        out.append(
            {
                "openalex_id": work_id,
                "title": w.get("display_name") or "",
                "abstract": _abstract_from_inverted_index(w.get("abstract_inverted_index")),
                "year": w.get("publication_year"),
                "venue": source.get("display_name") or "",
                "type": w.get("type") or "",
                "doi": doi,
                "url": doi or loc.get("landing_page_url") or f"https://openalex.org/{work_id}",
                "cited_by_count": w.get("cited_by_count") or 0,
            }
        )
    return out
