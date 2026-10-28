"""Assumption validation and normalization."""

from __future__ import annotations

from typing import Any

REQUIRED_PREFIX = (
    "No supporting evidence found in selected abstracts; directional estimate — user must verify."
)


def normalize_and_validate(
    inference: dict[str, Any], selected_pmids: set[str]
) -> dict[str, Any]:
    """
    Validate inference structure and support_level constraints:
    - evidence_supported: evidence_pmids subset of selected_pmids, evidence_quotes non-empty
    - heuristic_ballpark: evidence_pmids==[], evidence_quotes==[], explanation starts with required prefix
    Returns validated inference dict (raises ValueError if invalid).
    """
    errors: list[str] = []

    # Check top-level keys
    if "productivity" not in inference:
        errors.append("Missing 'productivity' key")
    if "tco" not in inference:
        errors.append("Missing 'tco' key")

    if errors:
        raise ValueError("; ".join(errors))

    # Validate each field
    for category_name in ("productivity", "tco"):
        category = inference.get(category_name, {})
        for field_name, field_data in category.items():
            if not isinstance(field_data, dict):
                errors.append(f"{category_name}.{field_name} is not a dict")
                continue

            support = field_data.get("support_level", "")
            pmids = field_data.get("evidence_pmids", [])
            quotes = field_data.get("evidence_quotes", [])
            explanation = field_data.get("explanation", "")

            if support == "evidence_supported":
                if not pmids:
                    errors.append(
                        f"{category_name}.{field_name}: evidence_supported requires evidence_pmids"
                    )
                if not quotes:
                    errors.append(
                        f"{category_name}.{field_name}: evidence_supported requires evidence_quotes"
                    )
                # Check PMIDs are in selected set
                for pmid in pmids:
                    if pmid not in selected_pmids:
                        errors.append(
                            f"{category_name}.{field_name}: PMID {pmid} not in selected papers"
                        )

            elif support == "heuristic_ballpark":
                if pmids:
                    errors.append(
                        f"{category_name}.{field_name}: heuristic_ballpark must have evidence_pmids=[]"
                    )
                if quotes:
                    errors.append(
                        f"{category_name}.{field_name}: heuristic_ballpark must have evidence_quotes=[]"
                    )
                if not explanation.startswith(REQUIRED_PREFIX):
                    errors.append(
                        f"{category_name}.{field_name}: heuristic_ballpark explanation must start with required prefix"
                    )
            else:
                errors.append(
                    f"{category_name}.{field_name}: unknown support_level '{support}'"
                )

    if errors:
        raise ValueError("; ".join(errors))

    return inference
