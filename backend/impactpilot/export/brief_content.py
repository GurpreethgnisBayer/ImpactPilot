"""Structured one-pager content, rendered identically by the Markdown, PDF and PPTX exporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from impactpilot.config_loader import get_config
from impactpilot.domain.disclaimer import DISCLAIMER_TEXT
from impactpilot.domain.gating import OUTPUT_LOCAL_RANGES, allows, filter_record_for_export
from impactpilot.domain.models import InitiativeRecord
from impactpilot.domain.ranges import format_range, round_sig
from impactpilot.export.status import DRAFT_NOTE, export_status

_TIER_LABELS = {"exploratory": "Exploratory", "emerging_local": "Emerging (local)", "mature": "Mature"}
_DIRECTION = {"up": "Increase", "down": "Decrease", "flat": "No change"}


@dataclass
class EffectRow:
    dimension: str
    direction: str
    range_text: str
    confidence: str
    confirmed: bool
    citations: str = ""


@dataclass
class BriefContent:
    title: str
    status: str
    draft_note: str
    unconfirmed_count: int
    description: str
    statement: str
    score_line: str
    score_rationale: str
    facts: list[tuple[str, str]]
    effects: list[EffectRow]
    exploratory_note: str
    summary: str
    findings: list[str]
    kpis: list[tuple[str, str]]
    risks: list[str]
    open_questions: list[str]
    money: list[str]
    tco: str
    references: list[str]
    disclaimer: str = DISCLAIMER_TEXT
    extra: dict[str, Any] = field(default_factory=dict)


def _labels() -> tuple[dict[str, str], dict[str, str]]:
    cfg = get_config()
    dims = {d["id"]: d.get("label") or d["id"] for d in cfg.dimensions.get("dimensions") or []}
    phases = {p["id"]: p.get("label") or p["id"] for p in cfg.value_chain.get("phases") or []}
    return dims, phases


def _num(v: Any) -> str:
    if v is None:
        return "?"
    return f"{round_sig(float(v), 2):g}"


def build_brief_content(record: InitiativeRecord) -> BriefContent:
    dims, phases = _labels()
    status = export_status(record)
    comp: dict[str, Any] = record.compendium or {}
    sources = comp.get("sources") or []
    ref_num = {s["source_id"]: i + 1 for i, s in enumerate(sources)}

    def cite(ids: list[str] | None) -> str:
        return "".join(f"[{ref_num[i]}]" for i in (ids or []) if i in ref_num)

    comp_dims = {d.get("dimension_id"): d for d in comp.get("dimensions") or []}

    tier = record.maturity.tier
    local_ranges = allows(tier, OUTPUT_LOCAL_RANGES)

    def literature_range(cd: dict[str, Any]) -> str:
        if cd.get("low") is None:
            return "Withheld (exploratory)"
        return f"Literature: {_num(cd.get('low'))}–{_num(cd.get('high'))} {cd.get('unit', '')}".strip()

    effects: list[EffectRow] = []
    for est in record.estimates:
        rv = est.estimate
        cd = comp_dims.get(est.dimension_id) or {}
        if not rv:
            range_text = "Not estimated"
        elif local_ranges:
            range_text = format_range(rv)
        else:
            range_text = literature_range(cd)
        effects.append(
            EffectRow(
                dimension=dims.get(est.dimension_id, est.dimension_id),
                direction=_DIRECTION.get(est.direction.value, est.direction.value),
                range_text=range_text,
                confidence=est.confidence.value.capitalize(),
                confirmed=bool(rv and rv.confirmed),
                citations=cite(cd.get("citations")),
            )
        )
    if not effects:
        for d in comp_dims.values():
            effects.append(
                EffectRow(
                    dimension=dims.get(d.get("dimension_id"), str(d.get("dimension_id"))),
                    direction=_DIRECTION.get(str(d.get("direction")), str(d.get("direction"))),
                    range_text=literature_range(d),
                    confidence=str(d.get("confidence", "low")).capitalize(),
                    confirmed=False,
                    citations=cite(d.get("citations")),
                )
            )

    score = record.impact_score
    gated = filter_record_for_export(record)

    facts = [
        ("Maturity", _TIER_LABELS.get(tier.value, tier.value)),
        ("Value-chain phase", phases.get(record.scope.phase_id, record.scope.phase_id or "Not set")),
        ("Process step", record.scope.process_step or record.scope.process_step_free_text or "Not set"),
        ("Focus area", record.initiative.focus_area_code or "Unassigned"),
    ]
    if score:
        facts.insert(0, ("Impact score", f"{score.score} / 4 · {score.label}"))

    references = []
    for s in sources:
        meta = ", ".join(str(x) for x in (s.get("venue"), s.get("year")) if x)
        rank = f" · {s['relevance']} relevance" if s.get("relevance") else ""
        references.append(f"{s.get('title', '')}{f' ({meta})' if meta else ''} · {s['source_id']}{rank}")
    if not references:
        references = [ev.title or ev.source_or_link for ev in record.evidence if ev.title or ev.source_or_link]

    return BriefContent(
        title=record.initiative.title or "Untitled initiative",
        status=status["status"],
        draft_note=DRAFT_NOTE if status["status"] == "draft" else "",
        unconfirmed_count=status["unconfirmed_count"],
        description=record.initiative.description,
        statement=record.impact_statement or "",
        score_line=f"{score.score} / 4 · {score.label}" if score else "",
        score_rationale=score.rationale if score else "",
        facts=facts,
        effects=effects,
        exploratory_note=(
            "Maturity is exploratory: ranges describe published results for similar approaches, "
            "not validated estimates for this initiative."
            if effects and not local_ranges
            else ""
        ),
        summary=str(comp.get("executive_summary") or ""),
        findings=[f"{f.get('finding', '')} {cite(f.get('citations'))}".strip() for f in comp.get("key_findings") or []],
        kpis=[
            (k.name, f"{k.definition} ({k.cadence.value})".strip()) for k in record.measurement_plan
        ]
        or [(str(k.get("name")), str(k.get("definition", ""))) for k in comp.get("suggested_kpis") or []],
        risks=[str(x) for x in comp.get("risks_and_caveats") or []],
        open_questions=[str(x) for x in comp.get("open_questions") or []],
        money=[
            f"{dims.get(m.get('dimension_id'), m.get('dimension_id'))}: "
            f"{_num((m.get('amount_eur') or {}).get('low'))}–{_num((m.get('amount_eur') or {}).get('high'))} EUR "
            f"({m.get('label')})"
            for m in gated.get("monetization") or []
        ],
        tco=(
            f"{format_range(record.tco.total)} over {record.tco.horizon_years} years"
            if record.tco.total
            else ""
        ),
        references=references,
    )
