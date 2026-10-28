"""JSON export / schema helpers."""

from __future__ import annotations

from typing import Any

from impactpilot.domain.gating import filter_record_for_export
from impactpilot.domain.models import SCHEMA_VERSION, InitiativeRecord
from impactpilot.export.status import export_status
from impactpilot.export.traceability import check_traceability


def export_json(record: InitiativeRecord) -> dict[str, Any]:
    issues = check_traceability(record)
    status = export_status(record)
    data = filter_record_for_export(record)
    data["_export"] = {
        "schema_version": SCHEMA_VERSION,
        "export_status": status["status"],
        "unconfirmed_fields": status["unconfirmed"],
        "traceability_ok": len(issues) == 0,
        "traceability_issues": issues,
    }
    return data


def import_json(payload: dict[str, Any]) -> InitiativeRecord:
    # Strip export metadata if present
    clean = {k: v for k, v in payload.items() if not k.startswith("_")}
    return InitiativeRecord.model_validate(clean)


def json_schema_dict() -> dict[str, Any]:
    return InitiativeRecord.model_json_schema()
