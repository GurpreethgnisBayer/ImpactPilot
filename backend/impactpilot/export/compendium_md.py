"""Markdown export of the LLM-generated impact compendium (draft, not a signed-off brief)."""

from __future__ import annotations

from typing import Any

from impactpilot.domain.disclaimer import DISCLAIMER_TEXT
from impactpilot.domain.gating import OUTPUT_LOCAL_RANGES, allows
from impactpilot.domain.models import InitiativeRecord
from impactpilot.domain.ranges import round_sig


def _fmt(v: float | None) -> str:
    if v is None:
        return "?"
    r = round_sig(v, 2)
    return f"{r:g}"


def build_compendium_markdown(record: InitiativeRecord) -> str:
    c: dict[str, Any] = record.compendium or {}
    sources = c.get("sources") or []
    ref_num = {s["source_id"]: i + 1 for i, s in enumerate(sources)}

    def cite(ids: list[str]) -> str:
        nums = [f"[{ref_num[i]}]" for i in ids if i in ref_num]
        return " " + "".join(nums) if nums else ""

    title = record.initiative.title or "Untitled initiative"
    tier = record.maturity.tier
    lines: list[str] = [f"# Impact Compendium: {title}", ""]
    lines += [
        "> **Draft — LLM-suggested, requires SME validation.** Values below are derived from "
        "published literature and have not been confirmed for this initiative.",
        f"> {DISCLAIMER_TEXT}",
        "",
        f"_Generated {c.get('generated_at', '')} · LLM synthesis: {'yes' if c.get('llm_used') else 'no'} · "
        f"{len(sources)} sources_",
        "",
        "## Idea",
        "",
        record.initiative.description or "",
        "",
    ]

    if c.get("executive_summary"):
        lines += ["## Executive summary", "", c["executive_summary"], ""]

    ctx = []
    if c.get("value_chain_phase"):
        ctx.append(f"- **Value-chain phase:** {c['value_chain_phase']}")
    if c.get("process_step"):
        ctx.append(f"- **Process step:** {c['process_step']}")
    if c.get("mechanism"):
        ctx.append(f"- **Mechanism:** {c['mechanism']}")
    if ctx:
        lines += ["## Where the impact lands", "", *ctx, ""]

    if c.get("key_findings"):
        lines += ["## Key findings from the literature", ""]
        for f in c["key_findings"]:
            lines.append(f"- {f['finding']}{cite(f.get('citations') or [])}")
        lines.append("")

    dims = c.get("dimensions") or []
    if dims:
        lines += ["## Literature-reported effects by productivity dimension", ""]
        if not allows(tier, OUTPUT_LOCAL_RANGES):
            lines += [
                "_Maturity is exploratory: these ranges describe published results for similar "
                "approaches and must not be quoted as estimates for this initiative._",
                "",
            ]
        lines += [
            "| Dimension | Direction | Low | Base | High | Unit | Confidence | Sources |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for d in dims:
            citations = d.get("citations") or []
            if not citations:
                sources_cell = "_none — unsupported_"
            elif not d.get("grounded"):
                sources_cell = f"{cite(citations).strip()} _(interpolated)_"
            else:
                sources_cell = cite(citations).strip()
            lines.append(
                f"| {d['dimension_id']} | {d['direction']} | {_fmt(d.get('low'))} | {_fmt(d.get('base'))} | "
                f"{_fmt(d.get('high'))} | {d.get('unit','')} | {d.get('confidence','')} | "
                f"{sources_cell} |"
            )
        lines.append("")
        for d in dims:
            if d.get("rationale") or d.get("quotes"):
                lines.append(f"**{d['dimension_id']}** — {d.get('rationale','')}")
                for q in d.get("quotes") or []:
                    lines.append(f"> “{q}”")
                lines.append("")

    lines += [
        "## Suggested maturity",
        "",
        f"**{c.get('suggested_maturity', 'exploratory')}** — {c.get('maturity_rationale', '')}",
        "",
    ]

    if record.impact_statement:
        lines += ["## Draft impact statement", "", record.impact_statement, ""]

    if c.get("suggested_kpis"):
        lines += ["## Suggested KPIs", ""]
        for k in c["suggested_kpis"]:
            lines.append(f"- **{k.get('name')}** ({k.get('cadence', 'quarterly')}): {k.get('definition', '')}")
        lines.append("")

    for key, heading in (("risks_and_caveats", "Risks and caveats"), ("open_questions", "Open questions for SMEs")):
        if c.get(key):
            lines += [f"## {heading}", ""] + [f"- {x}" for x in c[key]] + [""]

    if c.get("warnings"):
        lines += ["## Generation warnings", ""] + [f"- {w}" for w in c["warnings"]] + [""]

    lines += ["## References", ""]
    for s in sources:
        meta = ", ".join(str(x) for x in (s.get("venue"), s.get("year"), s.get("type")) if x)
        rank = f" User relevance: {s['relevance']}." if s.get("relevance") in ("high", "medium", "low") else ""
        lines.append(
            f"{ref_num[s['source_id']]}. {s.get('title', '')} ({meta}). {s['source_id']}.{rank} {s.get('url', '')}"
        )
    q = c.get("queries") or {}
    lines += ["", f"_Search queries — PubMed: `{q.get('pubmed', '')}` · OpenAlex: `{q.get('keyword', '')}`_", ""]
    return "\n".join(lines)
