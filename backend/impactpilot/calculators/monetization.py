"""Convert operational impact to € using reference values."""

from __future__ import annotations

from impactpilot.config_loader import get_config
from impactpilot.domain.gating import OUTPUT_EUR_CONFIRMED, allows
from impactpilot.domain.models import (
    DimensionEstimate,
    MaturityTier,
    MonetizationResult,
    RangeValue,
    ValueSource,
)
from impactpilot.domain.ranges import scale_range


def _ref(path: dict, *keys: str) -> dict:
    cur: object = path
    for k in keys:
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(k)  # type: ignore[union-attr]
    return cur if isinstance(cur, dict) else {}


def monetize_cycle_time(
    days_saved: RangeValue,
    phase_id: str,
    *,
    probability_factor: float | None = None,
    tier: MaturityTier = MaturityTier.emerging_local,
) -> MonetizationResult:
    refs = get_config().reference_values
    phase_ref = _ref(refs, "value_per_day_cycle_time_reduction", phase_id)
    if not phase_ref:
        raise ValueError(f"No reference value for phase '{phase_id}'")
    vpd = float(phase_ref["value"])
    pf = float(probability_factor if probability_factor is not None else refs.get("probability_factor_default", 1.0))
    formula = str((refs.get("formulas") or {}).get("cycle_time_to_eur") or "")
    amount = scale_range(days_saved, vpd * pf).model_copy(
        update={
            "unit": "EUR",
            "source": ValueSource.config,
            "rationale": f"days_saved × {vpd} EUR/day × pf={pf}",
            "confirmed": bool(phase_ref.get("confirmed")) and days_saved.confirmed,
        }
    )
    label = _label(tier, bool(phase_ref.get("confirmed")) and days_saved.confirmed)
    return MonetizationResult(
        dimension_id="cycle_time",
        formula=formula,
        inputs_trace=[
            f"days_saved={days_saved.low}–{days_saved.high}",
            f"value_per_day={vpd} (source={phase_ref.get('source')}, as_of={phase_ref.get('as_of')})",
            f"probability_factor={pf}",
        ],
        amount_eur=amount,
        label=label,
    )


def monetize_fte_hours(
    hours_saved: RangeValue,
    *,
    tier: MaturityTier = MaturityTier.emerging_local,
) -> MonetizationResult:
    refs = get_config().reference_values
    rate_ref = refs.get("loaded_fte_cost_per_hour") or {}
    rate = float(rate_ref.get("value", 75.0))
    formula = str((refs.get("formulas") or {}).get("fte_hours_to_eur") or "")
    amount = scale_range(hours_saved, rate).model_copy(
        update={
            "unit": "EUR",
            "source": ValueSource.config,
            "confirmed": bool(rate_ref.get("confirmed")) and hours_saved.confirmed,
        }
    )
    return MonetizationResult(
        dimension_id="cost",
        formula=formula,
        inputs_trace=[
            f"hours_saved={hours_saved.low}–{hours_saved.high}",
            f"loaded_fte_cost_per_hour={rate} (source={rate_ref.get('source')}, as_of={rate_ref.get('as_of')})",
        ],
        amount_eur=amount,
        label=_label(tier, bool(rate_ref.get("confirmed")) and hours_saved.confirmed),
    )


def monetize_estimates(
    estimates: list[DimensionEstimate],
    phase_id: str,
    tier: MaturityTier,
) -> list[MonetizationResult]:
    """Monetize cycle_time (days) and cost (hours) estimates when present."""
    if not allows(tier, "eur_indicative") and not allows(tier, "eur_confirmed"):
        return []
    out: list[MonetizationResult] = []
    for est in estimates:
        if not est.estimate:
            continue
        if est.dimension_id == "cycle_time":
            out.append(monetize_cycle_time(est.estimate, phase_id, tier=tier))
        elif est.dimension_id == "cost" and "hour" in (est.estimate.unit or "").lower():
            out.append(monetize_fte_hours(est.estimate, tier=tier))
    return out


def _label(tier: MaturityTier, confirmed: bool) -> str:
    if tier == MaturityTier.mature and confirmed and allows(tier, OUTPUT_EUR_CONFIRMED):
        return "confirmed"
    return "indicative"
