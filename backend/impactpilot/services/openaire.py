"""OpenAIRE Graph search: research products from institutional repositories, including reports."""

from __future__ import annotations

import html
import re
from typing import Any

import requests

OPENAIRE_URL = "https://api.openaire.eu/graph/v1/researchProducts"
_MAX = 8


def _plain(text: str, limit: int = 1200) -> str:
    """Descriptions often carry JATS/HTML markup."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return " ".join(text.split())[:limit]


def search_openaire(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(max_results, _MAX))
    r = requests.get(OPENAIRE_URL, params={"search": q, "pageSize": limit}, timeout=timeout)
    r.raise_for_status()
    out: list[dict[str, Any]] = []
    for product in r.json().get("results") or []:
        product_id = str(product.get("id") or "").strip()
        title = (product.get("mainTitle") or "").strip()
        descriptions = product.get("descriptions") or []
        if isinstance(descriptions, str):
            descriptions = [descriptions]
        abstract = _plain(" ".join(str(d) for d in descriptions))
        if not product_id or not title or not abstract:
            continue
        pids = product.get("pids") or []
        doi = next((str(p.get("value")) for p in pids if isinstance(p, dict) and p.get("scheme") == "doi"), "")
        instances = [i for i in product.get("instances") or [] if isinstance(i, dict)]
        urls = [u for i in instances for u in (i.get("urls") or [])]
        kind = next((str(i.get("type")) for i in instances if i.get("type")), "") or str(product.get("type") or "")
        container = product.get("container") or {}
        out.append(
            {
                "source_id": f"OAIRE:{product_id}",
                "database": "openaire",
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "year": str(product.get("publicationDate") or "")[:4],
                "venue": str(container.get("name") or product.get("publisher") or "OpenAIRE"),
                "type": kind.lower() or "report",
                "url": urls[0] if urls else f"https://explore.openaire.eu/search/result?id={product_id}",
            }
        )
    return out
