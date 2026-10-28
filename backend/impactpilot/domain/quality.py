"""Impact statement quality checker."""

from __future__ import annotations

import re
from typing import Any

from impactpilot.config_loader import get_config
from impactpilot.domain.models import InitiativeRecord
from impactpilot.domain.statement import _NUMBER_RE


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p for p in parts if p]


def check_statement(statement: str, record: InitiativeRecord) -> list[dict[str, Any]]:
    """
    Return structured warnings. Rules:
    1. Vague language
    2. Technology-first phrasing
    3. Missing baseline
    4. Single-point numbers (no range)
    5. Competitiveness claims
    6. Length > 3 sentences
    """
    warnings: list[dict[str, Any]] = []
    cfg = get_config().scoring
    vague = [p.lower() for p in (cfg.get("quality_vague_phrases") or [])]
    comp = [p.lower() for p in (cfg.get("quality_competitiveness_terms") or [])]
    lower = (statement or "").lower()

    for phrase in vague:
        if phrase and phrase in lower:
            warnings.append(
                {
                    "code": "vague_language",
                    "message": f"Vague phrase detected: '{phrase}'",
                    "detail": phrase,
                }
            )

    tech_starters = (
        "this ai ",
        "this algorithm",
        "this model",
        "this tool",
        "our platform",
        "the software",
        "using machine learning",
        "using ml",
        "using deep learning",
    )
    stripped = lower.lstrip()
    if any(stripped.startswith(t) for t in tech_starters):
        warnings.append(
            {
                "code": "technology_first",
                "message": "Statement opens with technology rather than business impact",
            }
        )

    known_baselines = [b for b in record.baselines if not b.unknown and b.value]
    if not known_baselines and "versus a baseline" not in lower and "baseline" not in lower:
        # Flag when estimates claim relative change without baseline
        if any(e.estimate for e in record.estimates):
            warnings.append(
                {
                    "code": "missing_baseline",
                    "message": "No baseline recorded; relative claims may be unsupported",
                }
            )

    # Single-point numbers: a number not part of a low–high range pattern
    for m in _NUMBER_RE.finditer(statement or ""):
        token = m.group(0)
        if "–" in token or "-" in token or "—" in token:
            continue
        # Skip tiny integers that are sentence counts / tier labels
        bare = re.sub(r"[€$%,]", "", token)
        try:
            if float(bare.replace(",", ".")) in (1.0, 2.0, 3.0, 4.0):
                continue
        except ValueError:
            pass
        # If the same number appears as a lone point (heuristic): flag once
        warnings.append(
            {
                "code": "single_point_number",
                "message": f"Single-point number '{token}' — prefer a low–high range",
                "detail": token,
            }
        )
        break  # one sample is enough

    for term in comp:
        if term and term in lower:
            warnings.append(
                {
                    "code": "competitiveness_claim",
                    "message": f"Competitiveness language detected: '{term}'",
                    "detail": term,
                }
            )

    sents = _sentences(statement)
    if len(sents) > 3:
        warnings.append(
            {
                "code": "too_long",
                "message": f"Statement has {len(sents)} sentences; target is 2–3",
                "detail": str(len(sents)),
            }
        )

    return warnings
