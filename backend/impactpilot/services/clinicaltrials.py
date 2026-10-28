"""ClinicalTrials.gov API v2 study search."""

from __future__ import annotations

import re
from typing import Any

import requests

CTGOV_URL = "https://clinicaltrials.gov/api/v2/studies"
_MAX = 8


def _clip(text: str, limit: int = 1200) -> str:
    return " ".join((text or "").split())[:limit]


# Words that appear in nearly every registry record and make a poor fallback query.
_GENERIC = frozenset(
    {"clinical", "trial", "trials", "study", "studies", "patient", "patients", "phase", "based", "using"}
)


def _strongest_terms(query: str, n: int = 2) -> str:
    """The `n` longest distinctive words, kept in their original order."""
    words = [w for w in re.findall(r"[A-Za-z0-9\-]+", query) if len(w) > 2 and w.lower() not in _GENERIC]
    keep = set(sorted(words, key=len, reverse=True)[:n])
    return " ".join(w for w in words if w in keep)


def _fetch(params: dict[str, Any], limit: int, timeout: int) -> list[dict[str, Any]]:
    r = requests.get(CTGOV_URL, params={**params, "pageSize": limit, "format": "json"}, timeout=timeout)
    # The API answers 400 to queries it cannot parse (often very long ones); try the next fallback.
    if r.status_code == 400:
        return []
    r.raise_for_status()
    return r.json().get("studies") or []


def search_clinicaltrials(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    """Full-text search. When a long phrase matches nothing, retry its first six words, then the
    two strongest terms as an intervention, a condition, and plain text (registry text is terse)."""
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(max_results, _MAX))
    words = q.split()
    attempts: list[dict[str, str]] = [{"query.term": q}]
    if len(words) > 6:
        attempts.append({"query.term": " ".join(words[:6])})
    core = _strongest_terms(q)
    if core and core.lower() != q.lower():
        attempts += [{"query.intr": core}, {"query.cond": core}, {"query.term": core}]
    studies: list[dict[str, Any]] = []
    for params in attempts:
        studies = _fetch(params, limit, timeout)
        if studies:
            break
    out: list[dict[str, Any]] = []
    for study in studies:
        proto = study.get("protocolSection") or {}
        ident = proto.get("identificationModule") or {}
        nct = str(ident.get("nctId") or "").strip()
        if not nct:
            continue
        title = (ident.get("officialTitle") or ident.get("briefTitle") or nct).strip()
        summary = (proto.get("descriptionModule") or {}).get("briefSummary") or ""
        if study.get("hasResults"):
            summary = f"{summary} Results have been posted on ClinicalTrials.gov."
        abstract = _clip(summary)
        if not abstract:
            continue
        start = ((proto.get("statusModule") or {}).get("startDateStruct") or {}).get("date") or ""
        sponsor = ((proto.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}).get("name") or ""
        out.append(
            {
                "source_id": f"NCT:{nct}",
                "database": "clinicaltrials",
                "title": title,
                "abstract": abstract,
                "year": str(start)[:4],
                "venue": sponsor or "ClinicalTrials.gov",
                "type": "trial",
                "url": f"https://clinicaltrials.gov/study/{nct}",
            }
        )
    return out
