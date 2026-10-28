"""Extract numeric evidence from PubMed abstracts."""

from __future__ import annotations

import re
from typing import Any


def extract_numeric_evidence(article: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract numeric mentions from article['abstract'].
    Returns list of dicts: {pmid, raw, type, value, unit, context}.
    """
    pmid = article.get("pmid", "")
    abstract = article.get("abstract", "")
    if not abstract:
        return []

    results: list[dict[str, Any]] = []
    # Pattern: number (optional decimal) + optional unit/percent
    # Capture context: up to 50 chars before and after
    pattern = r"(\d+(?:\.\d+)?)\s*(%|hours?|days?|weeks?|months?|years?|patients?|subjects?|participants?|samples?|mg|kg|ml|µg|nm|μm|mm|cm|m|g|L|min|sec|s)?"
    for match in re.finditer(pattern, abstract, re.IGNORECASE):
        start = max(0, match.start() - 50)
        end = min(len(abstract), match.end() + 50)
        context = abstract[start:end].strip()
        raw = match.group(0)
        value_str = match.group(1)
        unit = match.group(2) or ""
        try:
            value = float(value_str)
        except ValueError:
            continue

        # Classify type
        num_type = "count"
        if unit.strip().lower() in ("%", "percent"):
            num_type = "percent"
        elif unit.strip().lower() in (
            "hour",
            "hours",
            "day",
            "days",
            "week",
            "weeks",
            "month",
            "months",
            "year",
            "years",
            "min",
            "sec",
            "s",
        ):
            num_type = "time"

        results.append(
            {
                "pmid": pmid,
                "raw": raw,
                "type": num_type,
                "value": value,
                "unit": unit.strip(),
                "context": context,
            }
        )

    return results
