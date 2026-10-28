"""PubMed evidence search endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from impactpilot.services.pubmed_eutils import search_pubmed
from impactpilot.services.query_suggest import suggest_pubmed_query

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.post("/pubmed/suggest-query")
def suggest(payload: dict[str, str]) -> dict[str, str]:
    q = suggest_pubmed_query(payload.get("title", ""), payload.get("description", ""))
    return {"query": q}


@router.post("/pubmed/search")
def search(payload: dict[str, Any]) -> dict[str, Any]:
    query = (payload.get("query") or "").strip()
    if not query:
        raise HTTPException(400, "query is required")
    try:
        results = search_pubmed(
            base_query=query,
            journal=str(payload.get("journal") or ""),
            author=str(payload.get("author") or ""),
            language=str(payload.get("language") or ""),
            has_abstract=bool(payload.get("has_abstract") or False),
            publication_types=str(payload.get("publication_types") or ""),
            field_restriction=str(payload.get("field_restriction") or "all"),
            max_results=int(payload.get("max_results") or 25),
            sort=str(payload.get("sort") or "relevance"),
            date_preset=str(payload.get("date_preset") or "5y"),
            custom_mindate=str(payload.get("custom_mindate") or payload.get("mindate") or ""),
            custom_maxdate=str(payload.get("custom_maxdate") or payload.get("maxdate") or ""),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"PubMed search failed: {exc}") from exc
    return {"results": results, "count": len(results)}
