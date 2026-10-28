"""ISRCTN registry search (UK-led and international trials). The public API returns XML."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import requests

ISRCTN_URL = "https://www.isrctn.com/api/query/format/default"
_NS = {"i": "http://www.67bricks.com/isrctn"}
_MAX = 8


def _clip(text: str, limit: int = 1200) -> str:
    return " ".join((text or "").split())[:limit]


def _find(el: ET.Element, path: str) -> str:
    node = el.find(path, _NS)
    return (node.text or "").strip() if node is not None and node.text else ""


def search_isrctn(query: str, *, max_results: int = _MAX, timeout: int = 30) -> list[dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    limit = max(1, min(max_results, _MAX))
    r = requests.get(ISRCTN_URL, params={"q": q, "limit": limit}, timeout=timeout)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out: list[dict[str, Any]] = []
    for full in root.findall("i:fullTrial", _NS):
        trial = full.find("i:trial", _NS)
        if trial is None:
            continue
        number = _find(trial, "i:isrctn")
        desc = trial.find("i:trialDescription", _NS)
        if not number or desc is None:
            continue
        title = _find(desc, "i:title") or _find(desc, "i:scientificTitle")
        summary = _find(desc, "i:plainEnglishSummary") or _find(desc, "i:studyHypothesis")
        if not title or not summary:
            continue
        start = _find(trial, "i:participants/i:recruitmentStart")
        sponsor = _find(full, "i:sponsor/i:organisation")
        out.append(
            {
                "source_id": f"ISRCTN:{number}",
                "database": "isrctn",
                "doi": _find(trial, "i:externalRefs/i:doi"),
                "title": title,
                "abstract": _clip(summary),
                "year": start[:4],
                "venue": sponsor or "ISRCTN registry",
                "type": "trial",
                "url": f"https://www.isrctn.com/ISRCTN{number}",
            }
        )
    return out
