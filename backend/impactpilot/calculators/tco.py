"""Range-based TCO calculator including AI token costs."""

from __future__ import annotations

from impactpilot.config_loader import get_config
from impactpilot.domain.models import CostLine, RangeValue, TcoSummary, ValueSource
from impactpilot.domain.ranges import add_ranges, scale_range


def compute_ai_token_cost(
    input_tokens_per_run: RangeValue,
    output_tokens_per_run: RangeValue,
    runs_per_year: RangeValue,
    *,
    input_per_1k: float | None = None,
    output_per_1k: float | None = None,
    horizon_years: int = 3,
) -> RangeValue:
    cfg = get_config().cost_categories.get("ai_token_pricing") or {}
    inp = input_per_1k if input_per_1k is not None else float(cfg.get("input_per_1k", 0.005))
    out = output_per_1k if output_per_1k is not None else float(cfg.get("output_per_1k", 0.015))

    def _year(side: str) -> float:
        it = getattr(input_tokens_per_run, side)
        ot = getattr(output_tokens_per_run, side)
        runs = getattr(runs_per_year, side)
        return ((it / 1000.0) * inp + (ot / 1000.0) * out) * runs

    annual = RangeValue(
        low=_year("low"),
        base=_year("base"),
        high=_year("high"),
        unit="EUR/year",
        source=ValueSource.user,
        rationale="AI tokens: (in/1k*price_in + out/1k*price_out) × runs/year",
    )
    return scale_range(annual, float(horizon_years)).model_copy(
        update={"unit": "EUR", "rationale": f"{annual.rationale} × {horizon_years}y"}
    )


def compute_tco(
    lines: list[CostLine],
    *,
    horizon_years: int | None = None,
) -> TcoSummary:
    cfg = get_config().cost_categories
    defaults = cfg.get("defaults") or {}
    years = horizon_years if horizon_years is not None else int(defaults.get("horizon_years", 3))
    trace: list[str] = [f"horizon_years={years}"]
    normalized: list[CostLine] = []

    for line in lines:
        amt = line.amount
        # Recurring categories are scaled by horizon when unit ends with /year
        if amt.unit.endswith("/year"):
            scaled = scale_range(amt, float(years)).model_copy(update={"unit": "EUR"})
            trace.append(f"{line.category_id}: scaled {format_hint(amt)} × {years}y")
            normalized.append(CostLine(category_id=line.category_id, amount=scaled, notes=line.notes))
        else:
            trace.append(f"{line.category_id}: {format_hint(amt)}")
            normalized.append(line)

    total = add_ranges(*(ln.amount for ln in normalized), unit="EUR", source=ValueSource.user)
    total = total.model_copy(update={"rationale": "sum of TCO lines", "confirmed": all(ln.amount.confirmed for ln in normalized)})
    return TcoSummary(horizon_years=years, lines=normalized, total=total, trace=trace)


def format_hint(rv: RangeValue) -> str:
    return f"{rv.low}–{rv.high} {rv.unit}".strip()
