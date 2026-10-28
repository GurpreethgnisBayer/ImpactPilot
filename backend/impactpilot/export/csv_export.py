"""CSV export of portfolio summaries."""

from __future__ import annotations

import csv
import io

from impactpilot.domain.models import InitiativeSummary


def portfolio_csv(rows: list[InitiativeSummary]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "title",
            "focus_area_code",
            "phase_id",
            "maturity_tier",
            "impact_score",
            "status",
            "signoff",
            "dimensions",
            "updated_at",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.title,
                r.focus_area_code,
                r.phase_id,
                r.maturity_tier.value,
                r.impact_score if r.impact_score is not None else "",
                r.status,
                r.signoff.value,
                "|".join(r.dimensions),
                r.updated_at.isoformat(),
            ]
        )
    return buf.getvalue()
