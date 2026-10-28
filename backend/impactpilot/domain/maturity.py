"""Maturity tier classification from guided questionnaire answers."""

from __future__ import annotations

from impactpilot.config_loader import get_config
from impactpilot.domain.models import MaturityAssessment, MaturityTier


def classify_maturity(answers: dict[str, str]) -> MaturityAssessment:
    """
    Classify maturity from questionnaire answers.
    Keys expected (from scoring.yaml maturity_questionnaire):
      q_local_effect_known, q_benchmarks_available, q_still_testing
    """
    still = (answers.get("q_still_testing") or "").lower()
    local = (answers.get("q_local_effect_known") or "").lower()
    benches = (answers.get("q_benchmarks_available") or "").lower()

    if still == "yes" or (local in ("no", "unsure") and benches in ("no", "unsure")):
        tier = MaturityTier.exploratory
        rationale = "Still testing whether a gain exists, or no local effect / benchmarks known."
    elif benches == "yes" and local == "yes":
        tier = MaturityTier.mature
        rationale = "Local effect known and benchmarks/data available."
    else:
        tier = MaturityTier.emerging_local
        rationale = "Local effect known (or partially known); phase-level not fully quantified."

    return MaturityAssessment(
        tier=tier,
        questionnaire_answers=dict(answers),
        rationale=rationale,
    )


def questionnaire_from_config() -> list[dict]:
    cfg = get_config().scoring
    return list(cfg.get("maturity_questionnaire") or [])
