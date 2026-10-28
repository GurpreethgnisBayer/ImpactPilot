"""Impact statement generator with LLM-polish number guard."""

from __future__ import annotations

import re
from typing import Any

from impactpilot.config_loader import get_config
from impactpilot.domain.models import Direction, InitiativeRecord, MaturityTier
from impactpilot.domain.ranges import format_range


_NUMBER_RE = re.compile(
    r"(?<![A-Za-z/])"  # not mid-word or units like EUR/
    r"(?:€|\$)?"
    r"\d+(?:[.,]\d+)?"
    r"(?:\s*[-–—]\s*\d+(?:[.,]\d+)?)?"
    r"%?"
)


def _direction_word(d: Direction) -> str:
    return {"up": "increases", "down": "decreases", "flat": "holds"}.get(d.value, "changes")


def _phase_label(phase_id: str) -> str:
    phases = get_config().value_chain.get("phases") or []
    for p in phases:
        if p.get("id") == phase_id:
            return str(p.get("label") or phase_id)
    return phase_id or "the value chain"


def _dim_label(dim_id: str) -> str:
    dims = get_config().dimensions.get("dimensions") or []
    for d in dims:
        if d.get("id") == dim_id:
            return str(d.get("label") or dim_id)
    return dim_id


def _extract_numbers(text: str) -> set[str]:
    return {m.group(0).replace(" ", "") for m in _NUMBER_RE.finditer(text or "")}


def confirmed_numbers_from_record(record: InitiativeRecord) -> set[str]:
    """Collect numeric tokens that are allowed to appear in the statement."""
    allowed: set[str] = set()
    for est in record.estimates:
        if est.estimate and est.estimate.confirmed:
            allowed |= _extract_numbers(format_range(est.estimate))
            allowed |= _extract_numbers(str(est.estimate.low))
            allowed |= _extract_numbers(str(est.estimate.base))
            allowed |= _extract_numbers(str(est.estimate.high))
    for b in record.baselines:
        if b.value and not b.unknown:
            allowed |= _extract_numbers(format_range(b.value))
    for m in record.monetization:
        allowed |= _extract_numbers(format_range(m.amount_eur))
    return allowed


def build_impact_statement(record: InitiativeRecord) -> str:
    """
    Build a 2–3 sentence impact statement from structured fields.
    Does not invent numbers — only uses confirmed estimates.
    """
    phase = _phase_label(record.scope.phase_id)
    step = record.scope.process_step or record.scope.process_step_free_text or "the process step"
    tier = record.maturity.tier
    tier_label = {
        MaturityTier.exploratory: "exploratory",
        MaturityTier.emerging_local: "emerging (local effect known)",
        MaturityTier.mature: "mature",
    }.get(tier, tier.value)

    changing = [e for e in record.estimates if e.direction != Direction.flat]
    if not changing:
        s1 = (
            f"In {phase} ({step}), this initiative is still being assessed; "
            f"no confirmed directional productivity change is recorded yet."
        )
        s2 = f"Maturity is {tier_label}."
        return f"{s1} {s2}"

    bits: list[str] = []
    for e in changing:
        label = _dim_label(e.dimension_id)
        verb = _direction_word(e.direction)
        if e.estimate and e.estimate.confirmed and tier != MaturityTier.exploratory:
            bits.append(f"{label} {verb} by roughly {format_range(e.estimate)}")
        else:
            bits.append(f"{label} {verb}")

    change_clause = "; ".join(bits)
    baseline_note = ""
    known = [b for b in record.baselines if not b.unknown and b.value]
    if known:
        b0 = known[0]
        baseline_note = f" versus a baseline of {format_range(b0.value)}" if b0.value else ""

    s1 = (
        f"In {phase} ({step}), {change_clause}{baseline_note}."
    )
    mechanisms = [e.mechanism.strip() for e in changing if e.mechanism.strip()]
    mech = mechanisms[0].rstrip(".") if mechanisms else "the described approach"
    # LLM mechanisms often start with "By ...", which reads badly after "driven by".
    mech = re.sub(r"^by\s+", "", mech, flags=re.IGNORECASE)
    if mech and not mech[:2].isupper():
        mech = mech[0].lower() + mech[1:]
    s2 = f"The change is driven by {mech} (maturity: {tier_label})."

    dims = ", ".join(_dim_label(e.dimension_id) for e in changing)
    s3 = f"Affected productivity dimension(s): {dims}."
    return f"{s1} {s2} {s3}"


def guard_llm_polish(original: str, polished: str, record: InitiativeRecord) -> str:
    """
    Accept LLM polish only if it does not introduce numbers absent from
    confirmed inputs. On violation, return the original template text.
    """
    allowed = confirmed_numbers_from_record(record) | _extract_numbers(original)
    new_nums = _extract_numbers(polished)
    introduced = {n for n in new_nums if n not in allowed and not _is_trivial(n)}
    if introduced:
        return original
    return polished.strip() or original


def _is_trivial(token: str) -> bool:
    # Ignore lone sentence counts like "2" "3" that may appear in meta text
    try:
        v = float(token.replace("%", "").replace("€", "").replace("$", "").replace(",", "."))
        return v in (1.0, 2.0, 3.0)
    except ValueError:
        return False


def polish_with_optional_llm(
    record: InitiativeRecord,
    generate_fn: Any | None = None,
) -> str:
    """Build statement; optionally polish via generate_fn(prompt)->str."""
    base = build_impact_statement(record)
    if generate_fn is None:
        return base
    prompt = (
        "Rewrite the following impact statement in plain business language. "
        "Keep it to 2–3 sentences. Do NOT add, remove, or change any numbers.\n\n"
        f"{base}"
    )
    try:
        polished = generate_fn(prompt)
    except Exception:  # noqa: BLE001
        return base
    return guard_llm_polish(base, str(polished or ""), record)
