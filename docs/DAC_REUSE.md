# DACcelerate component / pattern reuse log

Reference checkout: `/Users/gnvuy/DAC TalentFlow` branch `staging`, release **v2.9.66**.

ImpactPilot stays standalone (no runtime dependency on DACcelerate). Components and patterns below were **adapted**, not copied wholesale.

| Area | Source in DACcelerate | ImpactPilot usage |
|------|----------------------|-------------------|
| Brand theme | `frontend/src/theme.ts` haze-blue `bayerBrand`, light/dark themes, `bayerColors`, `surfaces`, sidebar tokens | `frontend/src/theme.ts` |
| Global CSS | `frontend/src/index.css` (`.page-title`, `.card`, `.badge`, content bg) | `frontend/src/index.css` |
| App shell | `layouts/AppLayout.tsx`, `Sidebar.tsx`, `nav-entries.tsx` | Same layout pattern; roles stripped |
| Toasts / errors | `ToastProvider.tsx`, `ErrorCard.tsx`, `ErrorBoundary.tsx` | Ported under `components/` |
| API client | `lib/api.ts`, `lib/apiError.ts`, `lib/queryClient.ts` | Axios without JWT/impersonation |
| Wizard gating | `DemandIntakeForm.tsx` step validity | `IntakeWizard.tsx` |
| Inline help | `TitleWithHelp` | `TitleWithHelp.tsx` |
| Sticky save | `PriorityTab` save bar surfaces | Initiative detail sticky save |
| List → detail tabs | DemandList → DemandDetail | InitiativesList → InitiativeDetail |
| Scoring UX | Priority criteria + override reason | Impact score 0–4 with required override reason |
| Field naming | snake_case JSON | snake_case end-to-end |
| Focus areas | `FA1`–`FA4`, `BO`, `UN` | `config/focus_areas.yaml` |
| Big bet types | `constants/portfolio.py` `BET_TYPES` | `config/focus_areas.yaml` |
| Lifecycle | product `poc\|mvp\|portfolio\|sunset` | + `idea` in config |
| Frontend Docker | `frontend/Dockerfile` + nginx | `frontend/Dockerfile` + `nginx.conf` |
| Charts | Recharts dependency (unused in DAC) | Used for tornado / tracking charts |

## Deliberate non-reuse

- **Auth / Azure AD / impersonation** — out of scope for standalone mode.
- **`competitiveness` scoring field** — requirements forbid competitiveness claims in the impact statement.
- **Demand stages / kanban** — not part of impact-hypothesis workflow.

## Future merge notes

JSON export (`schema_version: 1.0.0`) uses `focus_area_code`, `lifecycle_stage`, and role name fields compatible with DACcelerate naming so a later portfolio integration can map without renaming.
