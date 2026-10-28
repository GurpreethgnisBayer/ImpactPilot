# ImpactPilot v2 — Requirements & Framework (for coding agent)

> **Purpose of this document:** Give a coding agent enough context and a general framework to *plan and adapt* the existing Impact Pilot / Impact Brief application. It is intentionally not a line-by-line spec. Inspect the existing codebase first, reuse what works, and propose a plan before implementing.

---

## 1. Context — the problem we are solving

Teams across R&D (and the Data & Analytics Council, DAC) struggle to quantify the benefit of AI/analytics initiatives. Lessons learned from DAC discussions:

1. **One ROI number does not work for research.** Value in early R&D rarely reduces to a single ROI or %; business-defined outcomes refined iteratively work better.
2. **Directional is acceptable when quantitative is not credible.** State *which* productivity dimension moves and in *which direction*.
3. **Quantify locally, not globally.** Keep hard numbers at the process level (e.g., "image analysis 5 weeks → 1 week") rather than uncertain portfolio-level estimates.
4. **Ranges, not false precision.** "0.3–0.4", not "0.34".
5. **Focus Area leads cannot fill this alone.** Input must come from product owners and business owners together.
6. **Ownership of value realization is unclear.** Need standardized KPIs, baselines, and measurement approaches; business owners define success criteria and milestones.
7. **Move from activity tracking to impact tracking.** Capture delivered value (time saved, cost efficiencies, scientific outcomes, quality) on a recurring (e.g., quarterly) basis.
8. **Avoid double counting** across Focus Areas / Big Bets, and include AI tool/token costs in cost estimates.

## 2. Product goal

Turn ImpactPilot from a "number generator" into a **guided impact-hypothesis and impact-tracking tool** that:

- **Estimates** (at intake): produces a defensible, evidence-backed, uncertainty-aware impact statement and scorecard.
- **Tracks** (after delivery): compares realized vs. predicted impact over time.
- Is **standalone** for now (no live integrations), but exports structured data so it can later feed a portfolio tool (e.g., DACcelerate).
- Looks and behaves like part of the **DAC tool family** (see §8).

## 3. Core concepts (domain model)

| Concept | Description |
|---|---|
| **Initiative** | The project/idea being assessed. Has title, description, owner(s), Focus Area, linked Big Bet (optional), lifecycle stage. |
| **Value-chain scope** | Where in R&D it acts: phase (e.g., target ID, lead gen/opt, preclinical, clinical, regulatory, enabling platform) + specific process step. |
| **Productivity dimension** | One or more of: **Volume, Value (sales), PTS (probability of technical success), Cycle Time, Cost.** |
| **Impact lever type** | Faster / Leaner / Better decisions. |
| **Maturity tier** | **Mature** (data/benchmarks, realistic range) · **Emerging local** (local effect known, phase-level not quantified) · **Exploratory** (still testing whether a gain exists). |
| **Baseline** | Current state metric for the process step (value, unit, source, date). |
| **Estimate** | Per dimension: direction (↑/↓/↔), low/base/high, unit, confidence, rationale, linked evidence. |
| **Mechanism** | Short explanation of *how* the approach produces the change. |
| **Evidence** | Literature (PubMed etc.), internal proof points, benchmarks, expert input — each with source/link and which assumption it supports. |
| **Cost (TCO)** | Build, run, people (FTE), licences, cloud, **AI tool/token costs**, maintenance; over a configurable horizon. |
| **Monetization** | Optional conversion of operational impact to € via configurable reference values. |
| **Measurement plan** | KPI, definition, baseline, target, data source, owner, cadence. |
| **Realization record** | Periodic actuals vs. predicted, with notes. |
| **Roles / sign-off** | Project lead, business owner, product owner, reviewer; business-owner sign-off status. |

## 4. Key principles (design rules the agent must respect)

1. **Maturity gates precision.** Output detail depends on the tier:
   - Exploratory → direction + qualitative rationale only; no € values.
   - Emerging local → local process ranges; € optional and clearly labelled "indicative".
   - Mature → ranges per dimension + € conversion + sensitivity.
2. **Ranges everywhere.** Every quantitative output is low/base/high. Display with sensible rounding; never imply false precision.
3. **Deterministic calculations.** LLMs may *suggest* inputs and draft text; all numbers are computed by transparent, testable, deterministic code.
4. **Every assumption is traceable.** Each input shows its source: evidence, user-entered, LLM-suggested (unconfirmed), or default. LLM-suggested values must be confirmed by a human before final export.
5. **Business co-ownership.** Brief is not "final" without business-owner confirmation (simple status field in standalone mode).
6. **Plain language first.** Output leads with business impact, not technology. No competitiveness arguments in the impact statement.
7. **Lightweight.** Target completion of an intake in ~15–20 minutes. Progressive disclosure; advanced fields optional.
8. **Configurable, not hard-coded.** Value-chain phases, dimensions, reference values, cost categories, and scoring scale live in config files.
9. **Responsible use.** Approved LLM endpoints only; no sensitive data sent to unapproved services; outputs labelled as directional estimates requiring SME validation.
10. **Consistent DAC look & feel.** Follow DACcelerate / DAC Talentflow UI conventions (§8).

## 5. Functional modules

### Module A — Intake & Estimation (wizard)

Suggested flow (agent may adapt to existing UI):

1. **Initiative basics** — title, description, owners/roles, Focus Area, Big Bet link, stage.
2. **Scope** — value-chain phase + process step (guided pick-list + free text).
3. **Baseline** — current process metrics (time, FTE-hours, reruns, cost, volume). Allow "unknown" with a flag.
4. **Change & lever** — what changes, lever type (faster/leaner/better), affected productivity dimensions.
5. **Maturity tier** — guided questions to classify; tier drives downstream behaviour.
6. **Evidence** — existing literature search (keep) + add *internal proof point* and *benchmark/expert input* entries; link evidence to specific assumptions.
7. **Assumptions & estimates** — LLM proposes ranges from description + evidence; user reviews/edits/confirms each; show source badge per field.
8. **Cost (TCO)** — cost categories incl. AI tool/token usage; horizon configurable.
9. **Monetization (if tier allows)** — convert operational changes to € using reference values (see §6).
10. **Measurement plan** — KPIs, baseline, target, data source, owner, review cadence.
11. **Review & generate** — impact statement, scorecard, quality checks, export.

### Module B — Impact Statement generator

- Produces a **2–3 sentence** statement answering: *where* in the value chain, *what* improves and *by roughly how much* (vs. baseline), *which* productivity dimension(s), *maturity*, and *mechanism*.
- Built from structured fields (template + optional LLM polish); must not introduce numbers absent from confirmed inputs.
- Include a **quality checker** that flags: vague language ("improves efficiency"), technology-first phrasing, missing baseline, single-point numbers, competitiveness claims, length > 3 sentences.

### Module C — Scorecard & Prioritization support

- **5-dimension scorecard:** per dimension → direction, range, unit, confidence, evidence count.
- **Impact score** on a categorical 0–4 scale (Negligible → Transformational) with written rationale; numeric score optional/supporting.
- Simple **sensitivity view** (low/base/high scenarios; tornado or range chart).
- Flag potential **double counting** (same benefit claimed under another initiative/Big Bet — in standalone mode, a manual checkbox + note is sufficient).

### Module D — Impact Tracking (post-delivery)

- Per initiative, record **actuals** at a chosen cadence (e.g., quarterly) against the measurement plan.
- Show **predicted vs. realized** per KPI, variance, and notes.
- Allow **re-baselining** and **maturity upgrade** (e.g., Emerging → Mature) as evidence accumulates; keep version history.
- Capture a short **success story** field (situation, action, result) for communication use.

### Module E — Portfolio view (local)

- List/table of all initiatives stored locally with tier, dimensions, impact score, status, last update.
- Filters by Focus Area, phase, dimension, tier.
- Aggregations must avoid summing incompatible units; show counts and ranges, and € only where available.

### Module F — Export

- **Markdown / PDF / PPTX one-pager** (impact statement, scorecard, assumptions table with sources, evidence citations, cost, measurement plan, disclaimer).
- **JSON** export of the full structured record (stable schema, versioned) for future integration.
- **CSV** export of portfolio view.

## 6. Monetization approach (€ conversion)

- Provide a **reference-values config file** (e.g., value per day of cycle-time reduction by phase, loaded FTE cost per hour, cost per experiment/rerun). Values are **placeholders until supplied by the business/finance**; the UI must show their source and date.
- Formulae are explicit and shown to the user (e.g., `€ = days saved × value per day (phase) × probability factor`).
- Always output € as a range, labelled "indicative" unless the tier is Mature and the reference values are confirmed.
- Never mix monetized and non-monetized values in a single total.

## 7. Non-functional requirements

- **Standalone:** runs locally or in a container; local persistence (e.g., SQLite or JSON files).
- **LLM-optional:** full workflow must work with LLM disabled (deterministic fallback / manual entry).
- **Configurable LLM provider** limited to approved endpoints.
- **Testability:** unit tests for all calculators, gating logic, and statement quality checks.
- **Auditability:** each record stores who changed what and when; versions retained.
- **Schema versioning** for the JSON export.
- **Accessibility & clarity:** plain-language labels, inline help and examples for each question.

## 8. Front-end & UI design — reuse DACcelerate / DAC Talentflow

The coding agent **has access to the DACcelerate and DAC Talentflow codebases**. Use them as the reference for front-end and UI design so ImpactPilot feels like part of the same DAC tool family.

**What to leverage**
- **Design system:** colour palette, typography, spacing, iconography, theming (incl. light/dark if present).
- **Component library:** layout shell, navigation, cards, tables, forms, steppers/wizards, filters, badges/status chips, modals, toasts, charts.
- **Interaction patterns:** form validation, inline help/tooltips, progressive disclosure, empty states, loading/error states, save/draft behaviour.
- **Information architecture:** how initiatives/portfolio items and people/roles are listed, filtered, and drilled into; reuse similar list → detail → edit flows for the Portfolio view (Module E) and initiative records.
- **Data conventions:** field names and enumerations (Focus Areas, value-chain phases, statuses, roles) — align with DACcelerate where they overlap so the JSON export can later map cleanly into DACcelerate.
- **Front-end stack & structure:** if the existing ImpactPilot stack differs (e.g., Streamlit), assess and recommend whether to (a) migrate to the DACcelerate/Talentflow stack or (b) replicate the design language in the current stack — and state the trade-offs in the plan.

**Guidance**
- Reuse or adapt components rather than copying wholesale; keep ImpactPilot **standalone** (no runtime dependency on, or data calls to, DACcelerate/Talentflow).
- Do not copy real data, credentials, environment configs, or secrets from those repositories.
- Document which components/patterns were reused and from where, to ease a future merge/integration.
- Where DACcelerate and Talentflow differ, prefer DACcelerate conventions (portfolio context) and note the decision.

## 9. Acceptance criteria (high level)

- A user can complete an intake and export a brief without the LLM.
- Exploratory-tier initiatives never display € values.
- Every number in the export traces back to a confirmed input, evidence item, or config value.
- The impact statement passes the quality checker or shows the specific warnings.
- Predicted vs. realized can be recorded and displayed for at least one KPI per initiative.
- JSON export round-trips (export → import) without data loss.
- UI is visually and interaction-wise consistent with DACcelerate / DAC Talentflow (shared components, patterns, and field conventions).

## 10. Out of scope (for now)

- Live integration with DACcelerate, Talentflow, or other enterprise systems.
- Automated pull of internal operational data (cycle-time systems etc.).
- Multi-user authentication and permissions beyond simple role fields.

## 11. Instructions to the coding agent

1. Review the existing ImpactPilot repository and summarize current architecture, features, and gaps vs. this document.
2. Review the DACcelerate and DAC Talentflow front ends and include a short **UI alignment proposal** (stack decision, reused components, field/enum mapping) — see §8.
3. Propose a **phased plan** (suggested: Phase 1 = data model + maturity gating + statement generator + scorecard + UI alignment; Phase 2 = baseline/measurement plan + monetization; Phase 3 = tracking + portfolio view + exports).
4. List open questions and assumptions before building.
5. Reuse existing components (evidence search, deterministic TCO/productivity calculators, export) where they fit.
6. Keep configuration externalized; do not hard-code organizational values.
