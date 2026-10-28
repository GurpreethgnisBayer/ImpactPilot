"""Maturity-tier gating: which outputs may be shown / exported."""

from __future__ import annotations

from typing import Any

from impactpilot.domain.models import InitiativeRecord, MaturityTier


# Output keys controlled by maturity
OUTPUT_DIRECTION = "direction"
OUTPUT_QUALITATIVE = "qualitative_rationale"
OUTPUT_LOCAL_RANGES = "local_ranges"
OUTPUT_EUR_INDICATIVE = "eur_indicative"
OUTPUT_EUR_CONFIRMED = "eur_confirmed"
OUTPUT_SENSITIVITY = "sensitivity"


_ALLOWED: dict[MaturityTier, set[str]] = {
    MaturityTier.exploratory: {OUTPUT_DIRECTION, OUTPUT_QUALITATIVE},
    MaturityTier.emerging_local: {
        OUTPUT_DIRECTION,
        OUTPUT_QUALITATIVE,
        OUTPUT_LOCAL_RANGES,
        OUTPUT_EUR_INDICATIVE,
    },
    MaturityTier.mature: {
        OUTPUT_DIRECTION,
        OUTPUT_QUALITATIVE,
        OUTPUT_LOCAL_RANGES,
        OUTPUT_EUR_INDICATIVE,
        OUTPUT_EUR_CONFIRMED,
        OUTPUT_SENSITIVITY,
    },
}


def allowed_outputs(tier: MaturityTier | str) -> set[str]:
    if isinstance(tier, str):
        tier = MaturityTier(tier)
    return set(_ALLOWED[tier])


def allows(tier: MaturityTier | str, output: str) -> bool:
    return output in allowed_outputs(tier)


def assert_allows(tier: MaturityTier | str, output: str) -> None:
    if not allows(tier, output):
        raise PermissionError(
            f"Output '{output}' is not allowed for maturity tier '{tier}'"
        )


def filter_record_for_export(record: InitiativeRecord) -> dict[str, Any]:
    """
    Return a dict representation of the record with gated fields stripped.
    Exploratory: strip all € monetization and sensitivity.
    Emerging: keep monetization but force label=indicative.
    Mature: keep everything.
    """
    data = record.model_dump(mode="json")
    tier = record.maturity.tier
    allowed = allowed_outputs(tier)

    if OUTPUT_EUR_INDICATIVE not in allowed and OUTPUT_EUR_CONFIRMED not in allowed:
        data["monetization"] = []
    elif OUTPUT_EUR_CONFIRMED not in allowed:
        for m in data.get("monetization", []):
            m["label"] = "indicative"

    if OUTPUT_SENSITIVITY not in allowed:
        data.pop("sensitivity", None)

    if OUTPUT_LOCAL_RANGES not in allowed:
        # Keep direction/mechanism; blank numeric estimates for exploratory
        for est in data.get("estimates", []):
            est["estimate"] = None

    data["_gating"] = {
        "tier": tier.value if hasattr(tier, "value") else tier,
        "allowed_outputs": sorted(allowed),
    }
    return data


def euros_permitted(tier: MaturityTier | str) -> bool:
    return allows(tier, OUTPUT_EUR_INDICATIVE) or allows(tier, OUTPUT_EUR_CONFIRMED)
