"""Export status (draft vs final) and file naming shared by every export format."""

from __future__ import annotations

import re
from typing import Any

from impactpilot.domain.models import InitiativeRecord
from impactpilot.domain.ranges import unconfirmed_llm_values

DRAFT_NOTE = (
    "DRAFT: some values are LLM-suggested and not yet confirmed by the initiative team. "
    "Do not quote them as validated estimates."
)


def export_status(record: InitiativeRecord) -> dict[str, Any]:
    """`draft` while any LLM-suggested value is unconfirmed, else `final`."""
    pending = unconfirmed_llm_values(record)
    return {
        "status": "draft" if pending else "final",
        "unconfirmed": pending,
        "unconfirmed_count": len(pending),
    }


def export_filename(record: InitiativeRecord, ext: str, kind: str = "impact-brief") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (record.initiative.title or "untitled").lower()).strip("-")[:60]
    suffix = "-draft" if export_status(record)["status"] == "draft" else ""
    return f"{slug or 'untitled'}-{kind}{suffix}.{ext}"


def attachment_headers(filename: str) -> dict[str, str]:
    return {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
