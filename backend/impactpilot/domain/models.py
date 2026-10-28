"""Core domain models for ImpactPilot v2."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


SCHEMA_VERSION = "1.0.0"


class ValueSource(str, Enum):
    evidence = "evidence"
    user = "user"
    llm_suggested = "llm_suggested"
    default = "default"
    config = "config"


class Direction(str, Enum):
    up = "up"
    down = "down"
    flat = "flat"


class MaturityTier(str, Enum):
    exploratory = "exploratory"
    emerging_local = "emerging_local"
    mature = "mature"


class SignoffStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"


class EvidenceKind(str, Enum):
    pubmed = "pubmed"
    literature = "literature"
    internal_proof_point = "internal_proof_point"
    benchmark = "benchmark"
    expert_input = "expert_input"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Cadence(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    semiannual = "semiannual"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class RangeValue(BaseModel):
    low: float
    base: float
    high: float
    unit: str = ""
    source: ValueSource = ValueSource.user
    confirmed: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    rationale: str = ""

    @model_validator(mode="after")
    def _check_order(self) -> RangeValue:
        if not (self.low <= self.base <= self.high):
            raise ValueError(
                f"Range must satisfy low <= base <= high "
                f"(got {self.low}, {self.base}, {self.high})"
            )
        if self.source == ValueSource.llm_suggested and self.confirmed is False:
            pass
        return self


class Roles(BaseModel):
    project_lead_name: str = ""
    business_owner_name: str = ""
    product_owner_name: str = ""
    reviewer_name: str = ""
    business_owner_signoff_status: SignoffStatus = SignoffStatus.pending


class Scope(BaseModel):
    phase_id: str = ""
    process_step: str = ""
    process_step_free_text: str = ""


class BaselineMetric(BaseModel):
    id: str = Field(default_factory=_new_id)
    metric: str
    value: RangeValue | None = None
    unit: str = ""
    source: str = ""
    as_of: date | None = None
    unknown: bool = False


class DimensionEstimate(BaseModel):
    dimension_id: str
    direction: Direction = Direction.flat
    estimate: RangeValue | None = None
    confidence: Confidence = Confidence.low
    mechanism: str = ""
    linked_evidence_ids: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=_new_id)
    kind: EvidenceKind
    title: str = ""
    source_or_link: str = ""
    summary: str = ""
    pmid: str | None = None
    supports_assumption_ids: list[str] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)


class CostLine(BaseModel):
    category_id: str
    amount: RangeValue
    notes: str = ""


class MonetizationResult(BaseModel):
    dimension_id: str
    formula: str
    inputs_trace: list[str] = Field(default_factory=list)
    amount_eur: RangeValue
    label: Literal["indicative", "confirmed"] = "indicative"


class KpiPlan(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str
    definition: str = ""
    baseline: RangeValue | None = None
    target: RangeValue | None = None
    data_source: str = ""
    owner: str = ""
    cadence: Cadence = Cadence.quarterly


class RealizationRecord(BaseModel):
    id: str = Field(default_factory=_new_id)
    kpi_id: str
    period: str  # e.g. 2026-Q1
    actual: RangeValue | None = None
    notes: str = ""
    recorded_by: str = ""
    recorded_at: datetime = Field(default_factory=_utcnow)


class SuccessStory(BaseModel):
    situation: str = ""
    action: str = ""
    result: str = ""


class ScorecardEntry(BaseModel):
    dimension_id: str
    direction: Direction
    range: RangeValue | None = None
    unit: str = ""
    confidence: Confidence = Confidence.low
    evidence_count: int = 0


class ImpactScore(BaseModel):
    score: int = Field(ge=0, le=4)
    label: str = ""
    rationale: str = ""
    override: bool = False
    override_reason: str = ""


class DoubleCountingFlag(BaseModel):
    flagged: bool = False
    note: str = ""


class Initiative(BaseModel):
    title: str = ""
    description: str = ""
    focus_area_code: str = "UN"
    big_bet_type: str = ""
    big_bet_link: str = ""
    lifecycle_stage: str = "idea"
    roles: Roles = Field(default_factory=Roles)


class ChangeLever(BaseModel):
    what_changes: str = ""
    lever_type: str = ""  # faster | leaner | better_decisions
    affected_dimension_ids: list[str] = Field(default_factory=list)


class MaturityAssessment(BaseModel):
    tier: MaturityTier = MaturityTier.exploratory
    questionnaire_answers: dict[str, str] = Field(default_factory=dict)
    rationale: str = ""


class TcoSummary(BaseModel):
    horizon_years: int = 3
    lines: list[CostLine] = Field(default_factory=list)
    total: RangeValue | None = None
    trace: list[str] = Field(default_factory=list)


class InitiativeRecord(BaseModel):
    schema_version: str = SCHEMA_VERSION
    id: str = Field(default_factory=_new_id)
    status: str = "draft"  # draft | in_review | finalized
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    created_by: str = "local-user"
    updated_by: str = "local-user"

    initiative: Initiative = Field(default_factory=Initiative)
    scope: Scope = Field(default_factory=Scope)
    baselines: list[BaselineMetric] = Field(default_factory=list)
    change: ChangeLever = Field(default_factory=ChangeLever)
    maturity: MaturityAssessment = Field(default_factory=MaturityAssessment)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    estimates: list[DimensionEstimate] = Field(default_factory=list)
    tco: TcoSummary = Field(default_factory=TcoSummary)
    monetization: list[MonetizationResult] = Field(default_factory=list)
    measurement_plan: list[KpiPlan] = Field(default_factory=list)
    realizations: list[RealizationRecord] = Field(default_factory=list)
    success_story: SuccessStory = Field(default_factory=SuccessStory)

    compendium: dict[str, Any] | None = None
    impact_statement: str = ""
    quality_warnings: list[dict[str, Any]] = Field(default_factory=list)
    scorecard: list[ScorecardEntry] = Field(default_factory=list)
    impact_score: ImpactScore | None = None
    double_counting: DoubleCountingFlag = Field(default_factory=DoubleCountingFlag)

    @field_validator("schema_version")
    @classmethod
    def _schema(cls, v: str) -> str:
        if not v:
            return SCHEMA_VERSION
        return v


class InitiativeSummary(BaseModel):
    id: str
    title: str
    focus_area_code: str
    phase_id: str
    maturity_tier: MaturityTier
    impact_score: int | None
    status: str
    signoff: SignoffStatus
    updated_at: datetime
    dimensions: list[str] = Field(default_factory=list)
