"""Quick brief -> literature search -> LLM impact compendium."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from impactpilot.api.deps import acting_as, get_db, get_repo
from impactpilot.api.llm import resolve_llm_settings
from impactpilot.domain.models import InitiativeRecord, ValueSource
from impactpilot.domain.quality import check_statement
from impactpilot.domain.scoring import build_scorecard, suggest_impact_score
from impactpilot.domain.statement import build_impact_statement
from impactpilot.export.compendium_md import build_compendium_markdown
from impactpilot.export.status import attachment_headers, export_filename
from impactpilot.services.compendium import (
    apply_compendium,
    generate_compendium,
    search_literature,
    synthesize_from_sources,
)
from impactpilot.services.llm_health import validate_llm_settings
from impactpilot.services.sources import registry

router = APIRouter(prefix="/api", tags=["compendium"])


class QuickBrief(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    focus_area_code: str = ""
    phase_id: str = ""
    # Registry keys to search; None means every default, available source.
    sources: list[str] | None = None
    # Older clients send per-source flags; they still toggle the matching key.
    include_pubmed: bool | None = None
    include_openalex: bool | None = None
    include_europepmc: bool | None = None
    include_clinicaltrials: bool | None = None
    include_openfda: bool | None = None
    include_semanticscholar: bool | None = None
    max_per_source: int = Field(default=12, ge=3, le=30)
    llm_settings: dict[str, Any] | None = None


class SearchLiteratureRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    phase_id: str = ""
    # Registry keys to search; None means every default, available source.
    sources: list[str] | None = None
    # Older clients send per-source flags; they still toggle the matching key.
    include_pubmed: bool | None = None
    include_openalex: bool | None = None
    include_europepmc: bool | None = None
    include_clinicaltrials: bool | None = None
    include_openfda: bool | None = None
    include_semanticscholar: bool | None = None
    max_per_source: int = Field(default=12, ge=3, le=30)
    llm_settings: dict[str, Any] | None = None


class SynthesizeRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=10)
    focus_area_code: str = ""
    phase_id: str = ""
    sources: list[dict[str, Any]] = Field(min_length=1)
    llm_settings: dict[str, Any] | None = None


class ConfirmEstimate(BaseModel):
    low: float | None = None
    base: float | None = None
    high: float | None = None
    unit: str | None = None


def _effective_settings(requested: dict[str, Any] | None) -> dict[str, Any] | None:
    """Platform .env, unless the request supplies its own valid, non-blank fields.

    A browser override that is present but incomplete (e.g. a stale partial value) is ignored
    rather than silently breaking the platform default.
    """
    resolved = resolve_llm_settings(requested)
    if resolved and validate_llm_settings(resolved):
        platform_only = resolve_llm_settings(None)
        if platform_only and not validate_llm_settings(platform_only):
            return platform_only
        return None
    return resolved


def _legacy_flags(req: BaseModel) -> dict[str, bool]:
    return {
        k: v for k, v in req.model_dump().items() if k.startswith("include_") and v is not None
    }


@router.get("/compendium/sources")
def list_sources() -> list[dict[str, Any]]:
    """Every searchable source, its group, and whether the server has the key it needs."""
    return [spec.public() for spec in registry.SOURCES.values()]


def _run(brief: QuickBrief) -> dict[str, Any]:
    return generate_compendium(
        title=brief.title,
        description=brief.description,
        phase_hint=brief.phase_id,
        llm_settings=_effective_settings(brief.llm_settings),
        sources=brief.sources,
        max_per_source=brief.max_per_source,
        **_legacy_flags(brief),
    )


@router.post("/compendium/search")
def search_candidate_sources(req: SearchLiteratureRequest) -> dict[str, Any]:
    """Step 1 of the guided flow: search the literature and flag candidates worth reviewing."""
    return search_literature(
        title=req.title,
        description=req.description,
        phase_hint=req.phase_id,
        llm_settings=_effective_settings(req.llm_settings),
        sources=req.sources,
        max_per_source=req.max_per_source,
        **_legacy_flags(req),
    )


@router.post("/compendium/synthesize")
def synthesize_compendium(req: SynthesizeRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Step 2 of the guided flow: synthesize from the sources the user kept, then save an initiative."""
    repo = get_repo(db)
    try:
        compendium = synthesize_from_sources(
            title=req.title,
            description=req.description,
            phase_hint=req.phase_id,
            sources=req.sources,
            llm_settings=_effective_settings(req.llm_settings),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    record = apply_compendium(
        InitiativeRecord(),
        compendium,
        title=req.title,
        description=req.description,
        focus_area_code=req.focus_area_code,
    )
    record = repo.create(record, actor=acting_as())
    return {"initiative_id": record.id, "compendium": record.compendium, "record": record.model_dump(mode="json")}


@router.post("/compendium")
def create_compendium(brief: QuickBrief, db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = get_repo(db)
    compendium = _run(brief)
    record = apply_compendium(
        InitiativeRecord(),
        compendium,
        title=brief.title,
        description=brief.description,
        focus_area_code=brief.focus_area_code,
    )
    record = repo.create(record, actor=acting_as())
    return {"initiative_id": record.id, "compendium": record.compendium, "record": record.model_dump(mode="json")}


_REGENERATE_FIELDS = {"sources", "max_per_source", "llm_settings"} | {
    k for k in QuickBrief.model_fields if k.startswith("include_")
}


@router.post("/initiatives/{initiative_id}/compendium")
def regenerate_compendium(
    initiative_id: str, payload: dict[str, Any], db: Session = Depends(get_db)
) -> dict[str, Any]:
    repo = get_repo(db)
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    brief = QuickBrief(
        title=record.initiative.title,
        description=record.initiative.description,
        focus_area_code=record.initiative.focus_area_code,
        phase_id=record.scope.phase_id,
        **{
            k: v
            for k, v in payload.items()
            if k
            in _REGENERATE_FIELDS
        },
    )
    compendium = _run(brief)
    record = apply_compendium(
        record, compendium, title=brief.title, description=brief.description,
        focus_area_code=brief.focus_area_code,
    )
    record = repo.save(record, actor=acting_as(), reason="compendium_regenerate")
    return {"initiative_id": record.id, "compendium": record.compendium, "record": record.model_dump(mode="json")}


@router.get("/initiatives/{initiative_id}/compendium.md", response_class=PlainTextResponse)
def compendium_markdown(initiative_id: str, db: Session = Depends(get_db)) -> PlainTextResponse:
    record = get_repo(db).get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    if not record.compendium:
        raise HTTPException(404, "No compendium generated for this initiative")
    return PlainTextResponse(
        build_compendium_markdown(record),
        media_type="text/markdown",
        headers=attachment_headers(export_filename(record, "md", kind="compendium")),
    )


def _refresh_derived(record: InitiativeRecord) -> None:
    record.impact_statement = build_impact_statement(record)
    record.quality_warnings = check_statement(record.impact_statement, record)
    record.scorecard = build_scorecard(record)
    record.impact_score = suggest_impact_score(record)


@router.post("/initiatives/{initiative_id}/estimates/{dimension_id}/confirm")
def confirm_estimate(
    initiative_id: str,
    dimension_id: str,
    body: ConfirmEstimate | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = get_repo(db)
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    est = next((e for e in record.estimates if e.dimension_id == dimension_id), None)
    if not est or not est.estimate:
        raise HTTPException(404, "No numeric estimate for this dimension")
    rv = est.estimate
    body = body or ConfirmEstimate()
    edited = any(v is not None for v in (body.low, body.base, body.high, body.unit))
    try:
        est.estimate = rv.model_copy(
            update={
                "low": body.low if body.low is not None else rv.low,
                "base": body.base if body.base is not None else rv.base,
                "high": body.high if body.high is not None else rv.high,
                "unit": body.unit if body.unit is not None else rv.unit,
                "confirmed": True,
                "source": ValueSource.user if edited else rv.source,
            }
        )
        type(rv).model_validate(est.estimate.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    _refresh_derived(record)
    record = repo.save(record, actor=acting_as(), reason=f"confirm_estimate:{dimension_id}")
    return record.model_dump(mode="json")


@router.post("/initiatives/{initiative_id}/estimates/confirm-all")
def confirm_all_estimates(initiative_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = get_repo(db)
    record = repo.get(initiative_id)
    if not record:
        raise HTTPException(404, "Initiative not found")
    for est in record.estimates:
        if est.estimate and not est.estimate.confirmed:
            est.estimate = est.estimate.model_copy(update={"confirmed": True})
    _refresh_derived(record)
    record = repo.save(record, actor=acting_as(), reason="confirm_all_estimates")
    return record.model_dump(mode="json")
