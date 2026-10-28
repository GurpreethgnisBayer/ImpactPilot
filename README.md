# ImpactPilot v2

Guided **impact-hypothesis and impact-tracking** tool for R&D / DAC initiatives.  
Standalone FastAPI + React (Fluent UI) app aligned with the DACcelerate look and feel.

## Features

- Intake wizard (initiative, scope, baseline, maturity, evidence, estimates, TCO, monetization, measurement plan)
- Maturity gating (Exploratory / Emerging local / Mature) — Exploratory never shows €
- Ranges everywhere (low / base / high) with source badges and confirmation
- Impact statement + quality checker; 5-dimension scorecard; categorical impact score 0–4
- PubMed evidence search; optional LLM inference (approved endpoints only); full LLM-off path
- Local SQLite persistence with versions and field-level audit
- Tracking (predicted vs realized), portfolio view, exports (JSON, Markdown, CSV, PDF, PPTX)

## Quick start (dev)

```bash
# Backend
cd backend
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic pydantic-settings pyyaml \
  requests python-dotenv python-multipart markdown python-pptx pytest httpx
export PYTHONPATH=.
export IMPACTPILOT_CONFIG_DIR=../config
uvicorn impactpilot.main:app --reload --port 5001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

- API: http://localhost:5001/docs  
- UI: http://localhost:5173 (proxies `/api` → `:5001`)

Copy `.env.example` to `.env` and fill LLM keys only if you use inference.

## Docker

```bash
docker compose up --build
```

- UI: http://localhost:3000  
- API: http://localhost:5001

## Tests

```bash
cd backend && PYTHONPATH=. IMPACTPILOT_CONFIG_DIR=../config pytest -q
cd frontend && npm test
```

## Configuration

All org values live under `config/*.yaml` (value chain, dimensions, focus areas, reference values, cost categories, scoring, LLM allowlist). The UI surfaces reference-value source and date.

## Docs

- Requirements: `ImpactPilot_v2_Requirements_for_Coding_Agent.md`
- DACcelerate reuse log: `docs/DAC_REUSE.md`
- JSON schema: `GET /api/schema` and `docs/schema/initiative.v1.json`

## Security note

Rotate any API keys that were previously shared in chat or temporary setup scripts. Never commit `.env`.
