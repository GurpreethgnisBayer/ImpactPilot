"""Markdown one-pager export."""

from __future__ import annotations

from impactpilot.domain.models import InitiativeRecord
from impactpilot.export.brief_content import build_brief_content


def build_markdown(record: InitiativeRecord) -> str:
    c = build_brief_content(record)
    lines: list[str] = [f"# Impact Brief: {c.title}", ""]
    if c.status == "draft":
        lines += [f"> **{c.draft_note}** ({c.unconfirmed_count} unconfirmed value(s).)", ""]
    lines += [f"> {c.disclaimer}", ""]

    if c.description:
        lines += ["## Idea", "", c.description, ""]

    lines += ["## Impact statement", "", c.statement or "_(not generated yet)_", ""]
    if c.score_rationale:
        lines += [f"_{c.score_rationale}_", ""]

    lines += ["## At a glance", ""] + [f"- **{k}:** {v}" for k, v in c.facts] + [""]

    if c.effects:
        lines += ["## Expected effects", ""]
        if c.exploratory_note:
            lines += [f"_{c.exploratory_note}_", ""]
        lines += ["| Dimension | Direction | Range | Confidence | Status | Sources |", "|---|---|---|---|---|---|"]
        for e in c.effects:
            state = "confirmed" if e.confirmed else "**unconfirmed**"
            lines.append(
                f"| {e.dimension} | {e.direction} | {e.range_text} | {e.confidence} | {state} | {e.citations or '—'} |"
            )
        lines.append("")

    if c.summary:
        lines += ["## Evidence summary", "", c.summary, ""]
    if c.findings:
        lines += ["## Key findings", ""] + [f"- {f}" for f in c.findings] + [""]
    if c.money:
        lines += ["## Monetization (EUR)", ""] + [f"- {m}" for m in c.money] + [""]
    if c.tco:
        lines += ["## Cost (TCO)", "", f"- {c.tco}", ""]
    if c.kpis:
        lines += ["## How we will measure it", ""] + [f"- **{n}**: {d}" for n, d in c.kpis] + [""]
    if c.risks:
        lines += ["## Risks and caveats", ""] + [f"- {r}" for r in c.risks] + [""]
    if c.open_questions:
        lines += ["## Open questions", ""] + [f"- {q}" for q in c.open_questions] + [""]

    roles = record.initiative.roles
    lines += [
        "## Roles and sign-off",
        "",
        f"- Project lead: {roles.project_lead_name or '—'}",
        f"- Business owner: {roles.business_owner_name or '—'} ({roles.business_owner_signoff_status.value})",
        f"- Product owner: {roles.product_owner_name or '—'}",
        f"- Reviewer: {roles.reviewer_name or '—'}",
        "",
    ]
    if c.references:
        lines += ["## References", ""] + [f"{i}. {r}" for i, r in enumerate(c.references, 1)] + [""]
    return "\n".join(lines)
