"""Domain: ranges, gating, maturity, statement, quality, scoring."""

from __future__ import annotations

import pytest

from impactpilot.domain.gating import (
    OUTPUT_EUR_CONFIRMED,
    OUTPUT_EUR_INDICATIVE,
    OUTPUT_SENSITIVITY,
    allows,
    euros_permitted,
    filter_record_for_export,
)
from impactpilot.domain.maturity import classify_maturity
from impactpilot.domain.models import (
    DimensionEstimate,
    Direction,
    InitiativeRecord,
    MaturityTier,
    RangeValue,
    ValueSource,
)
from impactpilot.domain.quality import check_statement
from impactpilot.domain.ranges import format_range, round_sig, unconfirmed_llm_values, validate_range
from impactpilot.domain.scoring import apply_score_override, build_scorecard, suggest_impact_score
from impactpilot.domain.statement import build_impact_statement, guard_llm_polish


def test_range_order():
    validate_range(1, 2, 3)
    with pytest.raises(ValueError):
        RangeValue(low=3, base=2, high=1)


def test_round_sig():
    assert round_sig(0.3456, 2) == 0.35
    assert "0.3" in format_range(RangeValue(low=0.3, base=0.35, high=0.4, unit=""))


def test_gating_exploratory_no_eur():
    assert not euros_permitted(MaturityTier.exploratory)
    assert not allows(MaturityTier.exploratory, OUTPUT_EUR_INDICATIVE)
    assert not allows(MaturityTier.exploratory, OUTPUT_SENSITIVITY)
    assert allows(MaturityTier.mature, OUTPUT_EUR_CONFIRMED)


def test_filter_export_strips_eur_for_exploratory():
    rec = InitiativeRecord()
    rec.maturity.tier = MaturityTier.exploratory
    rec.monetization = []  # even if populated, filter clears
    from impactpilot.domain.models import MonetizationResult

    rec.monetization = [
        MonetizationResult(
            dimension_id="cycle_time",
            formula="x",
            amount_eur=RangeValue(low=1, base=2, high=3, unit="EUR"),
        )
    ]
    gated = filter_record_for_export(rec)
    assert gated["monetization"] == []


def test_maturity_classifier():
    a = classify_maturity(
        {"q_still_testing": "yes", "q_local_effect_known": "no", "q_benchmarks_available": "no"}
    )
    assert a.tier == MaturityTier.exploratory
    b = classify_maturity(
        {"q_still_testing": "no", "q_local_effect_known": "yes", "q_benchmarks_available": "yes"}
    )
    assert b.tier == MaturityTier.mature


def test_statement_and_quality():
    rec = InitiativeRecord()
    rec.scope.phase_id = "preclinical"
    rec.scope.process_step = "image analysis"
    rec.maturity.tier = MaturityTier.emerging_local
    rec.estimates = [
        DimensionEstimate(
            dimension_id="cycle_time",
            direction=Direction.down,
            estimate=RangeValue(
                low=5, base=7, high=10, unit="days", source=ValueSource.user, confirmed=True
            ),
            mechanism="automated image QC",
        )
    ]
    text = build_impact_statement(rec)
    assert "preclinical" in text.lower() or "Preclinical" in text
    assert "cycle" in text.lower() or "Cycle" in text
    polished = guard_llm_polish(text, text + " saving exactly 99.7 days", rec)
    assert "99.7" not in polished  # rejected
    warnings = check_statement(
        "This AI improves efficiency and delivers competitive advantage. Extra. More. Too many.",
        rec,
    )
    codes = {w["code"] for w in warnings}
    assert "vague_language" in codes
    assert "competitiveness_claim" in codes
    assert "too_long" in codes or "technology_first" in codes


def test_scoring_and_override():
    rec = InitiativeRecord()
    rec.maturity.tier = MaturityTier.mature
    rec.estimates = [
        DimensionEstimate(dimension_id="cycle_time", direction=Direction.down),
        DimensionEstimate(dimension_id="cost", direction=Direction.down),
        DimensionEstimate(dimension_id="volume", direction=Direction.up),
    ]
    from impactpilot.domain.models import Confidence

    for e in rec.estimates:
        e.confidence = Confidence.high
    suggested = suggest_impact_score(rec)
    assert 0 <= suggested.score <= 4
    card = build_scorecard(rec)
    assert len(card) == 3
    overridden = apply_score_override(suggested, 2, "Business owner judgment")
    assert overridden.override is True
    with pytest.raises(ValueError):
        apply_score_override(suggested, 2, "")


def test_unconfirmed_llm_blocks_paths():
    rec = InitiativeRecord()
    rec.estimates = [
        DimensionEstimate(
            dimension_id="cost",
            estimate=RangeValue(
                low=1,
                base=2,
                high=3,
                source=ValueSource.llm_suggested,
                confirmed=False,
            ),
        )
    ]
    paths = unconfirmed_llm_values(rec)
    assert any("estimate" in p for p in paths)
