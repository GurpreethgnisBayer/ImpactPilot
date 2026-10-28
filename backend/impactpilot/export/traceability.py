"""Ensure every number in exports traces to confirmed input, evidence, or config."""

from __future__ import annotations

from impactpilot.domain.models import InitiativeRecord, ValueSource


def check_traceability(record: InitiativeRecord) -> list[str]:
    issues: list[str] = []
    for i, est in enumerate(record.estimates):
        if not est.estimate:
            continue
        src = est.estimate.source
        if src == ValueSource.llm_suggested and not est.estimate.confirmed:
            issues.append(f"estimates[{i}].estimate is llm_suggested and unconfirmed")
        if src == ValueSource.evidence and not est.estimate.evidence_ids and not est.linked_evidence_ids:
            issues.append(f"estimates[{i}].estimate claims evidence source without evidence ids")
    for i, m in enumerate(record.monetization):
        if m.amount_eur.source not in (ValueSource.config, ValueSource.user, ValueSource.evidence):
            if m.amount_eur.source == ValueSource.llm_suggested and not m.amount_eur.confirmed:
                issues.append(f"monetization[{i}] unconfirmed llm value")
        if not m.inputs_trace:
            issues.append(f"monetization[{i}] missing inputs_trace")
    for i, line in enumerate(record.tco.lines):
        if line.amount.source == ValueSource.llm_suggested and not line.amount.confirmed:
            issues.append(f"tco.lines[{i}] unconfirmed llm value")
    return issues
