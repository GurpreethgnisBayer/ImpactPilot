"""Semantic Scholar paper search. Uses SEMANTIC_SCHOLAR_API_KEY when the server has one."""

from __future__ import annotations

import os
from typing import Any

import requests

S2_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_MAX = 8
_FIELDS = "title,abstract,year,venue,externalIds,url,publicationTypes"


def search_semanticscholar(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(max_results, _MAX))
    headers: dict[str, str] = {}
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    if key:
        headers["x-api-key"] = key
    r = requests.get(
        S2_URL,
        params={"query": q, "limit": limit, "fields": _FIELDS},
        headers=headers,
        timeout=timeout,
    )
    if r.status_code == 429:
        raise RuntimeError(
            "Semantic Scholar rate limited (HTTP 429). Set SEMANTIC_SCHOLAR_API_KEY to raise the limit."
        )
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for paper in r.json().get("data") or []:
        paper_id = str(paper.get("paperId") or "").strip()
        title = (paper.get("title") or "").strip()
        abstract = " ".join((paper.get("abstract") or "").split())[:1200]
        if not paper_id or not title or not abstract:
            continue
        external = paper.get("externalIds") or {}
        pmid = str(external.get("PubMed") or "").strip()
        doi = str(external.get("DOI") or "").strip()
        types = paper.get("publicationTypes") or []
        out.append(
            {
                "source_id": f"S2:{paper_id}",
                "database": "semanticscholar",
                "pmid": pmid,
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "year": paper.get("year") or "",
                "venue": paper.get("venue") or "Semantic Scholar",
                "type": types[0] if types else "paper",
                "url": paper.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}",
            }
        )
    return out
