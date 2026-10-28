"""Initiative CRUD, statement, scorecard, tracking, export endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from impactpilot.api.deps import acting_as, get_db, get_repo
from impactpilot.calculators.monetization import monetize_estimates
from impactpilot.calculators.sensitivity import scenario_table, tornado_from_ranges
from impactpilot.calculators.tco import compute_ai_token_cost, compute_tco
from impactpilot.domain.gating import euros_permitted, filter_record_for_export
from impactpilot.domain.maturity import classify_maturity
from impactpilot.domain.models import (
    CostLine,
    ImpactScore,
    InitiativeRecord,
    RangeValue,
    RealizationRecord,
    SuccessStory,
)
from impactpilot.domain.quality import check_statement
from impactpilot.domain.scoring import apply_score_override, build_scorecard, suggest_impact_score
from impactpilot.domain.statement import build_impact_statement, polish_with_optional_llm
from impactpilot.export.csv_export import portfolio_csv
from impactpilot.export.json_export import export_json, import_json, json_schema_dict
from impactpilot.export.markdown_export import build_markdown
from impactpilot.export.pdf_export import build_pdf_bytes
from impactpilot.export.pptx_export import build_pptx_bytes
from impactpilot.export.status import attachment_headers, export_filename, export_status
from impactpilot.persistence.repository import InitiativeRepository

router = APIRouter(prefix="/api", tags=["initiatives"])


def _repo(db: Session = Depends(get_db)) -> InitiativeRepository:
    return get_repo(db)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/config")
def get_all_config() -> dict[str, Any]:
    from impactpilot.config_loader import get_config

    return get_config().model_dump()


@router.get("/schema")
def schema() -> dict[str, Any]:
    return json_schema_dict()


@router.get("/initiatives")
def list_initiatives(
    focus_area_code: str | None = None,
    phase_id: str | None = None,
    maturity_tier: str | None = None,
    dimension_id: str | None = None,
    repo: InitiativeRepository = Depends(_repo),
) -> list[dict[str, Any]]:
    rows = repo.list(
        focus_area_code=focus_area_code,
        phase_id=phase_id,
        maturity_tier=maturity_tier,
        dimension_id=dimension_id,
    )
    return [r.model_dump(mode="json") for r in rows]


@router.post("/initiatives", status_code=201)
def create_initiative(
    payload: dict[str, Any] | None = None,
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    data = payload or {}
    record = InitiativeRecord.model_validate(data) if data else InitiativeRecord()
    record = repo.create(record, actor=acting_as())
    return record.model_dump(mode="json")


@router.get("/initiatives/{initiative_id}")
def get_initiative(
    initiative_id: str, repo: InitiativeRepository = Depends(_repo)
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    return record.model_dump(mode="json")


@router.put("/initiatives/{initiative_id}")
def update_initiative(
    initiative_id: str,
    payload: dict[str, Any],
    reason: str = Query("update"),
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    existing = repo.get(initiative_id)
    if not existing:
        raise HTTPException(404, "Initiative not found")
    payload = dict(payload)
    payload["id"] = initiative_id
    record = InitiativeRecord.model_validate(payload)
    record = repo.save(record, actor=acting_as(), reason=reason)
    return record.model_dump(mode="json")


@router.delete("/initiatives/{initiative_id}")
def delete_initiative(
    initiative_id: str, repo: InitiativeRepository = Depends(_repo)
) -> dict[str, bool]:
    if not repo.delete(initiative_id):
        raise HTTPException(404, "Initiative not found")
    return {"ok": True}


@router.post("/initiatives/{initiative_id}/classify-maturity")
def classify(
    initiative_id: str,
    answers: dict[str, str],
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    record.maturity = classify_maturity(answers)
    # Strip € if downgraded to exploratory
    if not euros_permitted(record.maturity.tier):
        record.monetization = []
    record = repo.save(record, actor=acting_as(), reason="classify_maturity")
    return record.model_dump(mode="json")


@router.post("/initiatives/{initiative_id}/statement")
def generate_statement(
    initiative_id: str,
    polish: bool = False,
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    if polish:
        text = polish_with_optional_llm(record, generate_fn=None)
    else:
        text = build_impact_statement(record)
    record.impact_statement = text
    record.quality_warnings = check_statement(text, record)
    record = repo.save(record, actor=acting_as(), reason="generate_statement")
    return {
        "impact_statement": record.impact_statement,
        "quality_warnings": record.quality_warnings,
    }


@router.post("/initiatives/{initiative_id}/scorecard")
def generate_scorecard(
    initiative_id: str,
    override: dict[str, Any] | None = None,
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    record.scorecard = build_scorecard(record)
    suggested = suggest_impact_score(record)
    if override and "score" in override:
        record.impact_score = apply_score_override(
            suggested, int(override["score"]), str(override.get("reason") or "")
        )
    else:
        record.impact_score = suggested
    if override and "double_counting" in override:
        dc = override["double_counting"]
        record.double_counting.flagged = bool(dc.get("flagged"))
        record.double_counting.note = str(dc.get("note") or "")
    record = repo.save(record, actor=acting_as(), reason="scorecard")
    return {
        "scorecard": [s.model_dump(mode="json") for s in record.scorecard],
        "impact_score": record.impact_score.model_dump(mode="json") if record.impact_score else None,
        "double_counting": record.double_counting.model_dump(mode="json"),
    }


@router.post("/initiatives/{initiative_id}/tco")
def compute_tco_endpoint(
    initiative_id: str,
    payload: dict[str, Any],
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    lines = [CostLine.model_validate(x) for x in payload.get("lines") or []]
    # Optional AI token block
    ai = payload.get("ai_tokens")
    if ai:
        token_cost = compute_ai_token_cost(
            RangeValue.model_validate(ai["input_tokens_per_run"]),
            RangeValue.model_validate(ai["output_tokens_per_run"]),
            RangeValue.model_validate(ai["runs_per_year"]),
            horizon_years=int(payload.get("horizon_years") or 3),
        )
        lines.append(CostLine(category_id="ai_tokens", amount=token_cost))
    record.tco = compute_tco(lines, horizon_years=payload.get("horizon_years"))
    record = repo.save(record, actor=acting_as(), reason="tco")
    return record.tco.model_dump(mode="json")


@router.post("/initiatives/{initiative_id}/monetize")
def monetize_endpoint(
    initiative_id: str, repo: InitiativeRepository = Depends(_repo)
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    if not euros_permitted(record.maturity.tier):
        raise HTTPException(400, "€ monetization not permitted for this maturity tier")
    record.monetization = monetize_estimates(
        record.estimates, record.scope.phase_id, record.maturity.tier
    )
    record = repo.save(record, actor=acting_as(), reason="monetize")
    return {"monetization": [m.model_dump(mode="json") for m in record.monetization]}


@router.post("/initiatives/{initiative_id}/sensitivity")
def sensitivity_endpoint(
    initiative_id: str,
    payload: dict[str, Any],
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    if record.maturity.tier.value != "mature":
        raise HTTPException(400, "Sensitivity only available for mature initiatives")
    ranges = {k: RangeValue.model_validate(v) for k, v in (payload.get("ranges") or {}).items()}
    coeffs = {k: float(v) for k, v in (payload.get("coefficients") or {}).items()}
    bars = tornado_from_ranges(ranges, coeffs)
    return {
        "tornado": [b.__dict__ for b in bars],
        "scenarios": scenario_table(ranges, coeffs),
    }


@router.post("/initiatives/{initiative_id}/realizations")
def add_realization(
    initiative_id: str,
    payload: dict[str, Any],
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    rec = RealizationRecord.model_validate(payload)
    rec.recorded_by = acting_as()
    record.realizations.append(rec)
    record = repo.save(record, actor=acting_as(), reason="realization")
    return record.model_dump(mode="json")


@router.get("/initiatives/{initiative_id}/tracking")
def tracking_view(
    initiative_id: str, repo: InitiativeRepository = Depends(_repo)
) -> dict[str, Any]:
    """Predicted (KPI target) vs realized actuals with variance."""
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    kpis = {k.id: k for k in record.measurement_plan}
    rows: list[dict[str, Any]] = []
    for r in record.realizations:
        kpi = kpis.get(r.kpi_id)
        predicted = kpi.target.model_dump(mode="json") if kpi and kpi.target else None
        actual = r.actual.model_dump(mode="json") if r.actual else None
        variance = None
        if kpi and kpi.target and r.actual:
            variance = {
                "low": r.actual.low - kpi.target.low,
                "base": r.actual.base - kpi.target.base,
                "high": r.actual.high - kpi.target.high,
                "unit": r.actual.unit or kpi.target.unit,
            }
        rows.append(
            {
                "realization_id": r.id,
                "kpi_id": r.kpi_id,
                "kpi_name": kpi.name if kpi else "",
                "period": r.period,
                "predicted": predicted,
                "actual": actual,
                "variance": variance,
                "notes": r.notes,
            }
        )
    return {
        "rows": rows,
        "success_story": record.success_story.model_dump(mode="json"),
    }


@router.put("/initiatives/{initiative_id}/success-story")
def success_story(
    initiative_id: str,
    payload: dict[str, Any],
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    record.success_story = SuccessStory.model_validate(payload)
    record = repo.save(record, actor=acting_as(), reason="success_story")
    return record.success_story.model_dump(mode="json")


@router.post("/initiatives/{initiative_id}/rebaseline")
def rebaseline(
    initiative_id: str,
    payload: dict[str, Any],
    repo: InitiativeRepository = Depends(_repo),
) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    reason = str(payload.get("reason") or "rebaseline")
    if "baselines" in payload:
        from impactpilot.domain.models import BaselineMetric

        record.baselines = [BaselineMetric.model_validate(b) for b in payload["baselines"]]
    if "maturity_tier" in payload:
        from impactpilot.domain.models import MaturityTier

        record.maturity.tier = MaturityTier(payload["maturity_tier"])
        record.maturity.rationale = str(payload.get("maturity_rationale") or reason)
        if not euros_permitted(record.maturity.tier):
            record.monetization = []
    record = repo.save(record, actor=acting_as(), reason=reason)
    return record.model_dump(mode="json")


@router.get("/initiatives/{initiative_id}/versions")
def versions(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> list[dict]:
    if not repo.get(initiative_id):
        raise HTTPException(404, "Initiative not found")
    return repo.versions(initiative_id)


@router.get("/initiatives/{initiative_id}/versions/{version}")
def get_version(
    initiative_id: str, version: int, repo: InitiativeRepository = Depends(_repo)
) -> dict[str, Any]:
    record = repo.get_version(initiative_id, version)
    if not record:
        raise HTTPException(404, "Version not found")
    return record.model_dump(mode="json")


@router.get("/initiatives/{initiative_id}/audit")
def audit(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> list[dict]:
    if not repo.get(initiative_id):
        raise HTTPException(404, "Initiative not found")
    return repo.audit(initiative_id)


def _record_or_404(repo: InitiativeRepository, initiative_id: str) -> InitiativeRecord:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    return record


@router.get("/initiatives/{initiative_id}/export-status")
def export_status_endpoint(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> dict[str, Any]:
    return export_status(_record_or_404(repo, initiative_id))


@router.get("/initiatives/{initiative_id}/export.json")
def export_json_endpoint(
    initiative_id: str, repo: InitiativeRepository = Depends(_repo)
) -> JSONResponse:
    record = _record_or_404(repo, initiative_id)
    return JSONResponse(export_json(record), headers=attachment_headers(export_filename(record, "json")))


@router.get("/initiatives/{initiative_id}/export.md")
def export_md(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> PlainTextResponse:
    record = _record_or_404(repo, initiative_id)
    return PlainTextResponse(
        build_markdown(record),
        media_type="text/markdown",
        headers=attachment_headers(export_filename(record, "md")),
    )


@router.get("/initiatives/{initiative_id}/export.pdf")
def export_pdf(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> Response:
    record = _record_or_404(repo, initiative_id)
    try:
        pdf = build_pdf_bytes(record)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"PDF export failed: {exc}") from exc
    return Response(pdf, media_type="application/pdf", headers=attachment_headers(export_filename(record, "pdf")))


@router.get("/initiatives/{initiative_id}/export.pptx")
def export_pptx(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> Response:
    record = _record_or_404(repo, initiative_id)
    try:
        pptx = build_pptx_bytes(record)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"PowerPoint export failed: {exc}") from exc
    return Response(
        pptx,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=attachment_headers(export_filename(record, "pptx")),
    )


@router.post("/import")
def import_endpoint(
    payload: dict[str, Any], repo: InitiativeRepository = Depends(_repo)
) -> dict[str, Any]:
    record = import_json(payload)
    record = repo.import_record(record.model_dump(mode="json"), actor=acting_as())
    return record.model_dump(mode="json")


@router.get("/portfolio/export.csv")
def portfolio_export_csv(repo: InitiativeRepository = Depends(_repo)) -> PlainTextResponse:
    rows = repo.list()
    return PlainTextResponse(portfolio_csv(rows), media_type="text/csv")


@router.get("/portfolio/aggregations")
def portfolio_aggregations(repo: InitiativeRepository = Depends(_repo)) -> dict[str, Any]:
    rows = repo.list()
    by_tier: dict[str, int] = {}
    by_fa: dict[str, int] = {}
    by_score: dict[str, int] = {}
    for r in rows:
        by_tier[r.maturity_tier.value] = by_tier.get(r.maturity_tier.value, 0) + 1
        by_fa[r.focus_area_code] = by_fa.get(r.focus_area_code, 0) + 1
        key = str(r.impact_score) if r.impact_score is not None else "none"
        by_score[key] = by_score.get(key, 0) + 1
    return {
        "count": len(rows),
        "by_tier": by_tier,
        "by_focus_area": by_fa,
        "by_impact_score": by_score,
        "note": "Aggregations are counts only; incompatible units are never summed.",
    }


@router.get("/initiatives/{initiative_id}/gated")
def gated_view(initiative_id: str, repo: InitiativeRepository = Depends(_repo)) -> dict[str, Any]:
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    return filter_record_for_export(record)
