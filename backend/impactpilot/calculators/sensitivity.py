"""One-at-a-time sensitivity / tornado data from low–base–high ranges."""

from __future__ import annotations

from dataclasses import dataclass

from impactpilot.domain.models import RangeValue
from impactpilot.domain.ranges import midpoint


@dataclass
class TornadoBar:
    name: str
    low_impact: float
    base_impact: float
    high_impact: float
    swing: float


def evaluate_linear(coefficients: dict[str, float], values: dict[str, float]) -> float:
    """Simple linear model: sum(coeff_i * value_i)."""
    return sum(coefficients.get(k, 0.0) * values.get(k, 0.0) for k in set(coefficients) | set(values))


def tornado_from_ranges(
    ranges: dict[str, RangeValue],
    coefficients: dict[str, float],
) -> list[TornadoBar]:
    """
    For each input, vary it to low/high while others stay at base; record impact.
    """
    base_values = {k: r.base for k, r in ranges.items()}
    base_impact = evaluate_linear(coefficients, base_values)
    bars: list[TornadoBar] = []
    for name, rv in ranges.items():
        low_vals = dict(base_values)
        high_vals = dict(base_values)
        low_vals[name] = rv.low
        high_vals[name] = rv.high
        low_i = evaluate_linear(coefficients, low_vals)
        high_i = evaluate_linear(coefficients, high_vals)
        bars.append(
            TornadoBar(
                name=name,
                low_impact=low_i,
                base_impact=base_impact,
                high_impact=high_i,
                swing=abs(high_i - low_i),
            )
        )
    bars.sort(key=lambda b: b.swing, reverse=True)
    return bars


def scenario_table(
    ranges: dict[str, RangeValue],
    coefficients: dict[str, float],
) -> dict[str, float]:
    """low / base / high scenarios using all lows, all bases, all highs."""
    return {
        "low": evaluate_linear(coefficients, {k: r.low for k, r in ranges.items()}),
        "base": evaluate_linear(coefficients, {k: r.base for k, r in ranges.items()}),
        "high": evaluate_linear(coefficients, {k: r.high for k, r in ranges.items()}),
        "midpoint_sum": evaluate_linear(
            coefficients, {k: midpoint(r) for k, r in ranges.items()}
        ),
    }
