"""Europe PMC search (guidelines, preprints, reports, and MEDLINE)."""

from __future__ import annotations

from typing import Any

import requests

EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_MAX = 8


def _clip(text: str, limit: int = 1200) -> str:
    text = " ".join((text or "").split())
    return text[:limit]


def search_europepmc(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(max_results, _MAX))
    r = requests.get(
        EUROPEPMC_URL,
        # `lite` omits abstractText, and hits without an abstract are dropped.
        params={"query": q, "format": "json", "pageSize": limit, "resultType": "core"},
        timeout=timeout,
    )
    r.raise_for_status()
    hits = (r.json().get("resultList") or {}).get("result") or []
    out: list[dict[str, Any]] = []
    for hit in hits:
        title = (hit.get("title") or "").strip()
        abstract = _clip(hit.get("abstractText") or "")
        if not title or not abstract:
            continue
        pmid = str(hit.get("pmid") or "").strip()
        pmcid = str(hit.get("pmcid") or "").strip()
        doi = str(hit.get("doi") or "").strip()
        pub_type = hit.get("pubType") or hit.get("source") or "report"
        if isinstance(pub_type, list):
            pub_type = pub_type[0] if pub_type else "report"
        if pmcid:
            source_id = f"PMC:{pmcid}"
        elif pmid:
            source_id = f"PMID:{pmid}"
        else:
            source_id = f"EPMC:{hit.get('id') or doi or title[:40]}"
        if pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        elif pmcid:
            url = f"https://europepmc.org/article/PMC/{pmcid.removeprefix('PMC')}"
        elif doi:
            url = f"https://doi.org/{doi}"
        else:
            url = "https://europepmc.org/"
        out.append(
            {
                "source_id": source_id,
                "database": "europepmc",
                "pmid": pmid,
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "year": hit.get("pubYear") or "",
                "venue": hit.get("journalTitle") or hit.get("source") or "Europe PMC",
                "type": str(pub_type),
                "url": url,
            }
        )
    return out
