"""TCO, monetization, sensitivity calculators."""

from __future__ import annotations

import pytest

from impactpilot.calculators.monetization import monetize_cycle_time, monetize_estimates
from impactpilot.calculators.sensitivity import scenario_table, tornado_from_ranges
from impactpilot.calculators.tco import compute_ai_token_cost, compute_tco
from impactpilot.domain.models import (
    CostLine,
    DimensionEstimate,
    Direction,
    MaturityTier,
    RangeValue,
    ValueSource,
)


def test_tco_scales_yearly():
    lines = [
        CostLine(
            category_id="build",
            amount=RangeValue(low=10, base=20, high=30, unit="EUR", source=ValueSource.user),
        ),
        CostLine(
            category_id="run",
            amount=RangeValue(low=5, base=5, high=5, unit="EUR/year", source=ValueSource.user),
        ),
    ]
    out = compute_tco(lines, horizon_years=3)
    assert out.total is not None
    assert out.total.base == 20 + 5 * 3


def test_ai_token_cost():
    cost = compute_ai_token_cost(
        RangeValue(low=1000, base=1000, high=1000),
        RangeValue(low=500, base=500, high=500),
        RangeValue(low=100, base=100, high=100),
        input_per_1k=1.0,
        output_per_1k=2.0,
        horizon_years=1,
    )
    # (1*1 + 0.5*2)*100 = 200
    assert cost.base == pytest.approx(200.0)


def test_monetize_blocked_for_exploratory():
    est = [
        DimensionEstimate(
            dimension_id="cycle_time",
            direction=Direction.down,
            estimate=RangeValue(low=1, base=2, high=3, unit="days", confirmed=True),
        )
    ]
    assert monetize_estimates(est, "preclinical", MaturityTier.exploratory) == []


def test_monetize_cycle_time_indicative():
    days = RangeValue(low=5, base=5, high=5, unit="days", confirmed=True)
    m = monetize_cycle_time(days, "preclinical", tier=MaturityTier.emerging_local)
    assert m.label == "indicative"
    assert m.amount_eur.base > 0
    assert m.inputs_trace


def test_sensitivity_tornado():
    ranges = {
        "a": RangeValue(low=1, base=2, high=3),
        "b": RangeValue(low=10, base=10, high=10),
    }
    coeffs = {"a": 2.0, "b": 1.0}
    bars = tornado_from_ranges(ranges, coeffs)
    assert bars[0].name == "a"
    sc = scenario_table(ranges, coeffs)
    assert sc["low"] < sc["high"]
