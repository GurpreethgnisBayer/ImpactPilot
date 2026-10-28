"""Scorecard and categorical impact score (0–4)."""

from __future__ import annotations

from impactpilot.config_loader import get_config
from impactpilot.domain.models import (
    Confidence,
    Direction,
    ImpactScore,
    InitiativeRecord,
    MaturityTier,
    ScorecardEntry,
)


def build_scorecard(record: InitiativeRecord) -> list[ScorecardEntry]:
    evidence_by_id = {e.id: e for e in record.evidence}
    entries: list[ScorecardEntry] = []
    for est in record.estimates:
        linked = set(est.linked_evidence_ids)
        if est.estimate:
            linked |= set(est.estimate.evidence_ids)
        count = sum(1 for eid in linked if eid in evidence_by_id) or len(linked)
        entries.append(
            ScorecardEntry(
                dimension_id=est.dimension_id,
                direction=est.direction,
                range=est.estimate,
                unit=(est.estimate.unit if est.estimate else ""),
                confidence=est.confidence,
                evidence_count=count,
            )
        )
    return entries


def suggest_impact_score(record: InitiativeRecord) -> ImpactScore:
    labels = get_config().scoring.get("impact_score_labels") or {}
    changing = [e for e in record.estimates if e.direction != Direction.flat]
    tier = record.maturity.tier
    n_dims = len({e.dimension_id for e in changing})
    high_conf = any(e.confidence == Confidence.high for e in changing)

    if not changing:
        score = 0
        rationale = "No dimensions with a directional change."
    elif tier == MaturityTier.exploratory or (n_dims == 1 and tier != MaturityTier.mature):
        score = 1
        rationale = "Exploratory maturity or single local-only dimension."
    elif tier == MaturityTier.emerging_local and n_dims <= 2:
        score = 2
        rationale = "Emerging local effect across one or two dimensions."
    elif tier == MaturityTier.mature and (n_dims >= 2 or high_conf):
        score = 3 if n_dims < 3 or not high_conf else 4
        rationale = (
            "Mature multi-dimension / high-confidence effect."
            if score == 3
            else "Mature multi-dimension transformational effect with high confidence."
        )
    else:
        score = 2
        rationale = "Default moderate score based on available evidence."

    label = str(labels.get(str(score)) or labels.get(score) or _fallback_label(score))
    return ImpactScore(score=score, label=label, rationale=rationale)


def apply_score_override(
    suggested: ImpactScore,
    score: int,
    reason: str,
) -> ImpactScore:
    if not (0 <= score <= 4):
        raise ValueError("Impact score must be 0–4")
    if not (reason or "").strip():
        raise ValueError("Override requires a written reason")
    labels = get_config().scoring.get("impact_score_labels") or {}
    label = str(labels.get(str(score)) or labels.get(score) or _fallback_label(score))
    return ImpactScore(
        score=score,
        label=label,
        rationale=suggested.rationale,
        override=True,
        override_reason=reason.strip(),
    )


def _fallback_label(score: int) -> str:
    return {
        0: "Negligible",
        1: "Minor",
        2: "Moderate",
        3: "Major",
        4: "Transformational",
    }.get(score, "Unknown")
