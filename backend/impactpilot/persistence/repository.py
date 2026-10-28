"""Initiative persistence with versions and field-level audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from impactpilot.domain.models import InitiativeRecord, InitiativeSummary, MaturityTier, SignoffStatus
from impactpilot.persistence.models import AuditEventRow, InitiativeRow, InitiativeVersionRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _flatten(obj: Any, prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            flat.update(_flatten(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}[{i}]"
            flat.update(_flatten(v, key))
    else:
        flat[prefix] = json.dumps(obj, default=str) if not isinstance(obj, str) else obj
    return flat


def _diff(old: dict[str, Any], new: dict[str, Any]) -> list[tuple[str, str, str]]:
    old_f = _flatten(old)
    new_f = _flatten(new)
    keys = set(old_f) | set(new_f)
    changes: list[tuple[str, str, str]] = []
    for k in sorted(keys):
        o = old_f.get(k, "")
        n = new_f.get(k, "")
        if o != n:
            changes.append((k, o, n))
    return changes


def _to_summary(row: InitiativeRow) -> InitiativeSummary:
    doc = json.loads(row.document_json or "{}")
    dims = [e.get("dimension_id") for e in doc.get("estimates", []) if e.get("dimension_id")]
    return InitiativeSummary(
        id=row.id,
        title=row.title,
        focus_area_code=row.focus_area_code,
        phase_id=row.phase_id,
        maturity_tier=MaturityTier(row.maturity_tier),
        impact_score=row.impact_score,
        status=row.status,
        signoff=SignoffStatus(row.signoff),
        updated_at=row.updated_at,
        dimensions=dims,
    )


def _sync_columns(row: InitiativeRow, record: InitiativeRecord) -> None:
    row.title = record.initiative.title
    row.focus_area_code = record.initiative.focus_area_code
    row.phase_id = record.scope.phase_id
    row.maturity_tier = record.maturity.tier.value
    row.impact_score = record.impact_score.score if record.impact_score else None
    row.status = record.status
    row.signoff = record.initiative.roles.business_owner_signoff_status.value
    row.updated_at = record.updated_at
    row.updated_by = record.updated_by
    row.document_json = record.model_dump_json()


class InitiativeRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(
        self,
        *,
        focus_area_code: str | None = None,
        phase_id: str | None = None,
        maturity_tier: str | None = None,
        dimension_id: str | None = None,
    ) -> list[InitiativeSummary]:
        q = select(InitiativeRow)
        if focus_area_code:
            q = q.where(InitiativeRow.focus_area_code == focus_area_code)
        if phase_id:
            q = q.where(InitiativeRow.phase_id == phase_id)
        if maturity_tier:
            q = q.where(InitiativeRow.maturity_tier == maturity_tier)
        rows = list(self.session.scalars(q.order_by(InitiativeRow.updated_at.desc())))
        summaries = [_to_summary(r) for r in rows]
        if dimension_id:
            summaries = [s for s in summaries if dimension_id in s.dimensions]
        return summaries

    def get(self, initiative_id: str) -> InitiativeRecord | None:
        row = self.session.get(InitiativeRow, initiative_id)
        if not row:
            return None
        return InitiativeRecord.model_validate_json(row.document_json)

    def create(self, record: InitiativeRecord, actor: str = "local-user") -> InitiativeRecord:
        record.created_by = actor
        record.updated_by = actor
        record.created_at = _utcnow()
        record.updated_at = record.created_at
        row = InitiativeRow(id=record.id, created_by=actor, updated_by=actor)
        _sync_columns(row, record)
        self.session.add(row)
        self.session.add(
            InitiativeVersionRow(
                initiative_id=record.id,
                version=1,
                document_json=record.model_dump_json(),
                created_by=actor,
                reason="create",
            )
        )
        self.session.flush()
        return record

    def save(
        self,
        record: InitiativeRecord,
        actor: str = "local-user",
        reason: str = "update",
    ) -> InitiativeRecord:
        row = self.session.get(InitiativeRow, record.id)
        if not row:
            return self.create(record, actor=actor)

        old = json.loads(row.document_json or "{}")
        record.updated_by = actor
        record.updated_at = _utcnow()
        new = json.loads(record.model_dump_json())

        for path, ov, nv in _diff(old, new):
            self.session.add(
                AuditEventRow(
                    initiative_id=record.id,
                    actor=actor,
                    path=path,
                    old_value=ov,
                    new_value=nv,
                )
            )

        _sync_columns(row, record)
        next_ver = (
            self.session.scalar(
                select(InitiativeVersionRow.version)
                .where(InitiativeVersionRow.initiative_id == record.id)
                .order_by(InitiativeVersionRow.version.desc())
                .limit(1)
            )
            or 0
        ) + 1
        self.session.add(
            InitiativeVersionRow(
                initiative_id=record.id,
                version=next_ver,
                document_json=record.model_dump_json(),
                created_by=actor,
                reason=reason,
            )
        )
        self.session.flush()
        return record

    def delete(self, initiative_id: str) -> bool:
        row = self.session.get(InitiativeRow, initiative_id)
        if not row:
            return False
        self.session.delete(row)
        return True

    def versions(self, initiative_id: str) -> list[dict[str, Any]]:
        rows = self.session.scalars(
            select(InitiativeVersionRow)
            .where(InitiativeVersionRow.initiative_id == initiative_id)
            .order_by(InitiativeVersionRow.version.asc())
        )
        return [
            {
                "version": r.version,
                "created_at": r.created_at.isoformat(),
                "created_by": r.created_by,
                "reason": r.reason,
            }
            for r in rows
        ]

    def get_version(self, initiative_id: str, version: int) -> InitiativeRecord | None:
        row = self.session.scalar(
            select(InitiativeVersionRow).where(
                InitiativeVersionRow.initiative_id == initiative_id,
                InitiativeVersionRow.version == version,
            )
        )
        if not row:
            return None
        return InitiativeRecord.model_validate_json(row.document_json)

    def audit(self, initiative_id: str) -> list[dict[str, Any]]:
        rows = self.session.scalars(
            select(AuditEventRow)
            .where(AuditEventRow.initiative_id == initiative_id)
            .order_by(AuditEventRow.timestamp.asc())
        )
        return [
            {
                "actor": r.actor,
                "timestamp": r.timestamp.isoformat(),
                "path": r.path,
                "old_value": r.old_value,
                "new_value": r.new_value,
            }
            for r in rows
        ]

    def import_record(self, data: dict[str, Any], actor: str = "local-user") -> InitiativeRecord:
        record = InitiativeRecord.model_validate(data)
        existing = self.session.get(InitiativeRow, record.id)
        if existing:
            return self.save(record, actor=actor, reason="import")
        return self.create(record, actor=actor)
