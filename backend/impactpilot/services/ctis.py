"""EU Clinical Trials Information System (CTIS) public search. Best-effort.

The endpoint backs the public CTIS website and is not a documented API. If its response shape
changes, this source switches itself off until the server restarts instead of failing every brief.
"""

from __future__ import annotations

from typing import Any

import requests

CTIS_URL = "https://euclinicaltrials.eu/ctis-public-api/search"
_MAX = 8

_disabled_reason = ""


def _clip(text: str, limit: int = 1200) -> str:
    return " ".join((text or "").split())[:limit]


def _year(ddmmyyyy: str) -> str:
    parts = (ddmmyyyy or "").split("/")
    return parts[-1] if len(parts) == 3 and parts[-1].isdigit() else ""


def reset() -> None:
    global _disabled_reason
    _disabled_reason = ""


def search_ctis(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    global _disabled_reason
    if _disabled_reason:
        raise RuntimeError(f"EU CTIS disabled: {_disabled_reason}")
    q = (query or "").strip()
    if not q:
        return []
    body = {
        "pagination": {"page": 1, "size": max(1, min(max_results, _MAX))},
        "sort": {"property": "decisionDate", "direction": "DESC"},
        "searchCriteria": {"containAll": q},
    }
    r = requests.post(CTIS_URL, json=body, timeout=timeout)
    r.raise_for_status()
    payload = r.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        _disabled_reason = "unexpected response format (the public CTIS search may have changed)"
        raise RuntimeError(f"EU CTIS disabled: {_disabled_reason}")
    out: list[dict[str, Any]] = []
    for trial in payload["data"]:
        number = str(trial.get("ctNumber") or "").strip()
        title = (trial.get("ctTitle") or trial.get("shortTitle") or "").strip()
        if not number or not title:
            continue
        abstract = f"{trial.get('trialPhase') or 'Clinical'} trial"
        if trial.get("conditions"):
            abstract += f" in {trial['conditions']}"
        abstract += "."
        if trial.get("product"):
            abstract += f" Product: {trial['product']}."
        if trial.get("primaryEndPoint"):
            abstract += f" Primary endpoint: {trial['primaryEndPoint']}"
        if str(trial.get("resultsFirstReceived") or "").lower() == "yes":
            abstract += " Results have been posted in CTIS."
        out.append(
            {
                "source_id": f"EUCT:{number}",
                "database": "ctis",
                "title": title,
                "abstract": _clip(abstract),
                "year": _year(str(trial.get("startDateEU") or "")),
                "venue": str(trial.get("sponsor") or "EU CTIS"),
                "type": "trial",
                "url": f"https://euclinicaltrials.eu/search-for-clinical-trials/?lang=en&EUCT={number}",
            }
        )
    return out
