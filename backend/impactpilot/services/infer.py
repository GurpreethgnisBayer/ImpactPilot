"""Per-dimension LLM inference (proposals marked llm_suggested / unconfirmed)."""

from __future__ import annotations

import json
from typing import Any

from impactpilot.domain.models import (
    Confidence,
    DimensionEstimate,
    Direction,
    RangeValue,
    ValueSource,
)
from impactpilot.services.evidence_numbers import extract_numeric_evidence
from impactpilot.services.llm_allowlist import assert_host_allowed
from impactpilot.services.llm_health import validate_llm_settings
from impactpilot.services.llm_provider import build_provider


PROMPT = """You are an R&D impact analyst. Propose directional estimate ranges for the listed productivity dimensions.

Title: {title}
Description: {description}
Phase: {phase}
Process step: {step}
Lever: {lever}
Dimensions: {dimensions}

Evidence summary:
{evidence}

Numeric snippets:
{numeric}

Return ONLY JSON:
{{
  "estimates": [
    {{
      "dimension_id": "...",
      "direction": "up|down|flat",
      "low": number,
      "base": number,
      "high": number,
      "unit": "...",
      "confidence": "low|medium|high",
      "mechanism": "...",
      "rationale": "..."
    }}
  ]
}}
Rules: always provide low<=base<=high; do not invent PMIDs.
"""


def run_dimension_inference(
    *,
    title: str,
    description: str,
    phase: str,
    step: str,
    lever: str,
    dimension_ids: list[str],
    selected_articles: list[dict[str, Any]],
    llm_settings: dict[str, Any],
) -> list[DimensionEstimate]:
    errors = validate_llm_settings(llm_settings)
    if errors:
        raise ValueError("; ".join(errors))

    # Allowlist check based on provider host
    provider_id = llm_settings.get("provider")
    if provider_id == "openai_compatible":
        assert_host_allowed(llm_settings.get("openai_base_url") or "")
    elif provider_id == "azure_openai":
        assert_host_allowed(llm_settings.get("azure_openai_endpoint") or "")

    provider = build_provider(llm_settings)
    numeric: list[dict[str, Any]] = []
    for art in selected_articles:
        numeric.extend(extract_numeric_evidence(art))

    evidence_lines = []
    for art in selected_articles:
        evidence_lines.append(f"[{art.get('pmid','')}] {art.get('title','')}")
        if art.get("abstract"):
            evidence_lines.append(art["abstract"][:400])

    prompt = PROMPT.format(
        title=title,
        description=description,
        phase=phase,
        step=step,
        lever=lever,
        dimensions=", ".join(dimension_ids),
        evidence="\n".join(evidence_lines) or "(none)",
        numeric="\n".join(
            f"[{n.get('pmid')}] {n.get('raw')} — {n.get('context','')[:60]}" for n in numeric[:20]
        )
        or "(none)",
    )
    raw = provider.generate(prompt)
    parsed = json.loads(raw)
    out: list[DimensionEstimate] = []
    for item in parsed.get("estimates") or []:
        dim = item.get("dimension_id")
        if dim not in dimension_ids:
            continue
        rv = RangeValue(
            low=float(item["low"]),
            base=float(item["base"]),
            high=float(item["high"]),
            unit=str(item.get("unit") or ""),
            source=ValueSource.llm_suggested,
            confirmed=False,
            rationale=str(item.get("rationale") or ""),
        )
        out.append(
            DimensionEstimate(
                dimension_id=dim,
                direction=Direction(item.get("direction") or "flat"),
                estimate=rv,
                confidence=Confidence(item.get("confidence") or "low"),
                mechanism=str(item.get("mechanism") or ""),
            )
        )
    return out
