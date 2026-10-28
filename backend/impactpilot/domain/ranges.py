"""Range validation and sensible rounding (avoid false precision)."""

from __future__ import annotations

import math
from typing import Any

from impactpilot.domain.models import RangeValue, ValueSource


def validate_range(low: float, base: float, high: float) -> None:
    if not (low <= base <= high):
        raise ValueError(f"Invalid range: low={low}, base={base}, high={high}")


def round_sig(value: float, sig: int = 2) -> float:
    """Round to `sig` significant figures."""
    if value == 0 or not math.isfinite(value):
        return 0.0
    order = math.floor(math.log10(abs(value)))
    factor = 10 ** (sig - 1 - order)
    return round(value * factor) / factor


def round_range(rv: RangeValue, sig: int = 2) -> RangeValue:
    return rv.model_copy(
        update={
            "low": round_sig(rv.low, sig),
            "base": round_sig(rv.base, sig),
            "high": round_sig(rv.high, sig),
        }
    )


def format_range(rv: RangeValue, sig: int = 2) -> str:
    r = round_range(rv, sig)
    unit = f" {r.unit}" if r.unit else ""
    if r.low == r.high:
        return f"{r.base}{unit}"
    return f"{r.low}–{r.high}{unit}"


def midpoint(rv: RangeValue) -> float:
    return (rv.low + rv.high) / 2.0


def scale_range(rv: RangeValue, factor: float) -> RangeValue:
    return rv.model_copy(
        update={
            "low": rv.low * factor,
            "base": rv.base * factor,
            "high": rv.high * factor,
        }
    )


def add_ranges(*ranges: RangeValue, unit: str = "", source: ValueSource = ValueSource.user) -> RangeValue:
    if not ranges:
        return RangeValue(low=0, base=0, high=0, unit=unit, source=source)
    return RangeValue(
        low=sum(r.low for r in ranges),
        base=sum(r.base for r in ranges),
        high=sum(r.high for r in ranges),
        unit=unit or ranges[0].unit,
        source=source,
        confirmed=all(r.confirmed for r in ranges),
        rationale="sum of ranges",
    )


def unconfirmed_llm_values(obj: Any, path: str = "") -> list[str]:
    """Walk a pydantic model / dict / list and collect paths of unconfirmed LLM values."""
    found: list[str] = []
    if isinstance(obj, RangeValue):
        if obj.source == ValueSource.llm_suggested and not obj.confirmed:
            found.append(path or "range")
        return found
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(unconfirmed_llm_values(item, f"{path}[{i}]"))
        return found
    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
        for k, v in data.items():
            child = getattr(obj, k, v)
            found.extend(unconfirmed_llm_values(child, f"{path}.{k}" if path else k))
        return found
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.extend(unconfirmed_llm_values(v, f"{path}.{k}" if path else str(k)))
    return found
