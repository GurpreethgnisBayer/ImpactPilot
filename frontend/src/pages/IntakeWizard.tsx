import {
  Button,
  Dropdown,
  Field,
  Input,
  Option,
  Spinner,
  Text,
  Textarea,
} from '@fluentui/react-components';
import { ArrowLeft24Regular, ArrowRight24Regular } from '@fluentui/react-icons';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '../components/ToastProvider';
import { PageHeader } from '../components/ui/PageHeader';
import { useConfig } from '../hooks/useConfig';
import { useCreateInitiative, useUpdateInitiative } from '../hooks/useInitiatives';
import api from '../lib/api';
import { apiErrorMessage } from '../lib/apiError';
import type { BaselineMetric, EvidenceItem, InitiativeRecord, SignoffStatus } from '../types/initiative';
import { emptyInitiativeRecord, eurosPermitted } from '../types/initiative';

const STEPS = [
  { id: 'basics', label: 'Basics' },
  { id: 'scope', label: 'Scope' },
  { id: 'baseline', label: 'Baseline' },
  { id: 'change', label: 'Change / lever' },
  { id: 'maturity', label: 'Maturity' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'estimates', label: 'Estimates' },
  { id: 'cost', label: 'Cost' },
  { id: 'monetization', label: 'Monetization' },
  { id: 'measurement', label: 'Measurement' },
  { id: 'review', label: 'Review' },
] as const;

export function IntakeWizard() {
  const [stepIndex, setStepIndex] = useState(0);
  const [record, setRecord] = useState<InitiativeRecord>(emptyInitiativeRecord());
  const [recordId, setRecordId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { data: config } = useConfig();
  const createMutation = useCreateInitiative();
  const updateMutation = useUpdateInitiative();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const step = STEPS[stepIndex];
  const showEuros = eurosPermitted(record.maturity?.tier);

  const visibleSteps = STEPS.filter((s) => s.id !== 'monetization' || showEuros);
  const current = visibleSteps.findIndex((s) => s.id === step.id);
  const effectiveIndex = current >= 0 ? current : stepIndex;

  const patch = (fn: (r: InitiativeRecord) => void) => {
    setRecord((prev) => {
      const next = structuredClone(prev);
      fn(next);
      return next;
    });
  };

  const ensurePersisted = async (): Promise<string> => {
    if (recordId) return recordId;
    const created = await createMutation.mutateAsync(record);
    setRecordId(created.id!);
    setRecord(created);
    return created.id!;
  };

  const canAdvance = (): boolean => {
    if (step.id === 'basics') {
      return Boolean(record.initiative.title?.trim());
    }
    return true;
  };

  const goNext = async () => {
    if (!canAdvance()) {
      showToast({ title: 'Title required', body: 'Enter a title before continuing.', intent: 'warning' });
      return;
    }
    setBusy(true);
    try {
      const id = await ensurePersisted();
      const saved = await updateMutation.mutateAsync({ id, record });
      setRecord(saved);
      const nextVisible = visibleSteps[effectiveIndex + 1];
      if (nextVisible) {
        const nextGlobal = STEPS.findIndex((s) => s.id === nextVisible.id);
        setStepIndex(nextGlobal);
      }
    } catch (e) {
      showToast({ title: 'Could not save step', body: apiErrorMessage(e), intent: 'error' });
    } finally {
      setBusy(false);
    }
  };

  const goBack = () => {
    const prevVisible = visibleSteps[effectiveIndex - 1];
    if (prevVisible) {
      setStepIndex(STEPS.findIndex((s) => s.id === prevVisible.id));
    }
  };

  const runReviewActions = async () => {
    const id = await ensurePersisted();
    setBusy(true);
    try {
      const [stmt, sc] = await Promise.all([
        api.post(`/initiatives/${id}/statement`),
        api.post(`/initiatives/${id}/scorecard`),
      ]);
      patch((r) => {
        r.impact_statement = stmt.data.impact_statement;
        r.quality_warnings = stmt.data.quality_warnings;
        r.scorecard = sc.data.scorecard;
        r.impact_score = sc.data.impact_score;
      });
      showToast({ title: 'Statement and scorecard ready', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Review generation failed', body: apiErrorMessage(e), intent: 'error' });
    } finally {
      setBusy(false);
    }
  };

  const focusAreas = config?.focus_areas ?? [];
  const phases = config?.value_chain?.phases ?? [];

  return (
    <div className="page">
      <Link to="/initiatives" className="back-link">
        ← All initiatives
      </Link>
      <PageHeader
        eyebrow="Advanced"
        title="Intake wizard"
        subtitle="The full structured intake, for teams that already have baseline data and local evidence."
      />

      <div className="surface" style={{ marginBottom: 16 }}>
        <Text weight="semibold" block style={{ marginBottom: 10 }}>
          Step {effectiveIndex + 1} of {visibleSteps.length}: {step.label}
        </Text>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {visibleSteps.map((s, i) => (
            <span
              key={s.id}
              className="pill"
              style={{
                background: i === effectiveIndex ? 'var(--gradient)' : i < effectiveIndex ? 'var(--success-soft)' : '#f1f5f9',
                color: i === effectiveIndex ? '#fff' : i < effectiveIndex ? 'var(--success)' : 'var(--text-3)',
              }}
            >
              {s.label}
            </span>
          ))}
        </div>
      </div>

      <div className="card">
        {step.id === 'basics' && (
          <>
            <Field label="Title" required>
              <Input
                value={record.initiative.title ?? ''}
                onChange={(_, d) => patch((r) => { r.initiative.title = d.value; })}
              />
            </Field>
            <Field label="Description">
              <Textarea
                value={record.initiative.description ?? ''}
                onChange={(_, d) => patch((r) => { r.initiative.description = d.value; })}
                rows={4}
              />
            </Field>
            <Field label="Focus area">
              <Dropdown
                selectedOptions={[record.initiative.focus_area_code ?? 'UN']}
                onOptionSelect={(_, d) => patch((r) => { r.initiative.focus_area_code = d.optionValue ?? 'UN'; })}
              >
                {focusAreas.map((fa) => (
                  <Option key={fa.code} value={fa.code}>
                    {fa.label || fa.code}
                  </Option>
                ))}
              </Dropdown>
            </Field>
          </>
        )}

        {step.id === 'scope' && (
          <>
            <Field label="Value chain phase">
              <Dropdown
                selectedOptions={record.scope?.phase_id ? [record.scope.phase_id] : []}
                onOptionSelect={(_, d) => patch((r) => {
                  r.scope = r.scope ?? {};
                  r.scope.phase_id = d.optionValue ?? '';
                })}
              >
                {phases.map((p) => (
                  <Option key={p.id} value={p.id}>
                    {p.label || p.id}
                  </Option>
                ))}
              </Dropdown>
            </Field>
            <Field label="Process step">
              <Input
                value={record.scope?.process_step ?? ''}
                onChange={(_, d) => patch((r) => {
                  r.scope = r.scope ?? {};
                  r.scope.process_step = d.value;
                })}
              />
            </Field>
          </>
        )}

        {step.id === 'baseline' && (
          <>
            <Field label="Primary baseline metric">
              <Input
                value={record.baselines?.[0]?.metric ?? ''}
                onChange={(_, d) =>
                  patch((r) => {
                    const list = r.baselines ?? [];
                    const first: BaselineMetric = list[0] ?? { metric: '' };
                    first.metric = d.value;
                    r.baselines = [first, ...list.slice(1)];
                  })
                }
              />
            </Field>
          </>
        )}

        {step.id === 'change' && (
          <>
            <Field label="What changes">
              <Textarea
                value={record.change?.what_changes ?? ''}
                onChange={(_, d) => patch((r) => {
                  r.change = r.change ?? {};
                  r.change.what_changes = d.value;
                })}
              />
            </Field>
            <Field label="Lever type">
              <Dropdown
                selectedOptions={record.change?.lever_type ? [record.change.lever_type] : []}
                onOptionSelect={(_, d) => patch((r) => {
                  r.change = r.change ?? {};
                  r.change.lever_type = d.optionValue ?? '';
                })}
              >
                <Option value="faster">Faster</Option>
                <Option value="leaner">Leaner</Option>
                <Option value="better_decisions">Better decisions</Option>
              </Dropdown>
            </Field>
          </>
        )}

        {step.id === 'maturity' && (
          <>
            <Field label="Maturity tier">
              <Dropdown
                selectedOptions={[record.maturity?.tier ?? 'exploratory']}
                onOptionSelect={(_, d) => patch((r) => {
                  r.maturity = r.maturity ?? {};
                  r.maturity.tier = d.optionValue as typeof r.maturity.tier;
                  if (!eurosPermitted(r.maturity.tier)) r.monetization = [];
                })}
              >
                <Option value="exploratory">Exploratory</Option>
                <Option value="emerging_local">Emerging (local)</Option>
                <Option value="mature">Mature</Option>
              </Dropdown>
            </Field>
            <Field label="Rationale">
              <Textarea
                value={record.maturity?.rationale ?? ''}
                onChange={(_, d) => patch((r) => {
                  r.maturity = r.maturity ?? {};
                  r.maturity.rationale = d.value;
                })}
              />
            </Field>
          </>
        )}

        {step.id === 'evidence' && (
          <>
            <Field label="Evidence title">
              <Input
                value={record.evidence?.[0]?.title ?? ''}
                onChange={(_, d) =>
                  patch((r) => {
                    const list = r.evidence ?? [];
                    const first: EvidenceItem = list[0] ?? { kind: 'expert_input' };
                    first.title = d.value;
                    r.evidence = [first, ...list.slice(1)];
                  })
                }
              />
            </Field>
            <Text size={200}>Add PubMed search from initiative detail after save.</Text>
          </>
        )}

        {step.id === 'estimates' && (
          <Text>Add dimension estimates after wizard via LLM inference or manual edit on initiative detail.</Text>
        )}

        {step.id === 'cost' && (
          <Text>TCO lines can be computed from the Estimate tab after intake.</Text>
        )}

        {step.id === 'monetization' && showEuros && (
          <Text>Run monetization from initiative detail once estimates exist.</Text>
        )}

        {step.id === 'measurement' && (
          <>
            <Field label="Primary KPI name">
              <Input
                value={record.measurement_plan?.[0]?.name ?? ''}
                onChange={(_, d) =>
                  patch((r) => {
                    const list = r.measurement_plan ?? [];
                    const first = list[0] ?? { name: '' };
                    first.name = d.value;
                    r.measurement_plan = [first, ...list.slice(1)];
                  })
                }
              />
            </Field>
          </>
        )}

        {step.id === 'review' && (
          <>
            <Button appearance="secondary" onClick={() => void runReviewActions()} disabled={busy}>
              Generate statement & scorecard
            </Button>
            {(record.quality_warnings ?? []).length > 0 ? (
              <ul>
                {record.quality_warnings!.map((w, i) => (
                  <li key={i}>{w.message ?? JSON.stringify(w)}</li>
                ))}
              </ul>
            ) : null}
            <Field label="Business owner sign-off" style={{ marginTop: 16 }}>
              <Dropdown
                selectedOptions={[record.initiative.roles?.business_owner_signoff_status ?? 'pending']}
                onOptionSelect={(_, d) =>
                  patch((r) => {
                    r.initiative.roles = r.initiative.roles ?? {};
                    r.initiative.roles.business_owner_signoff_status = d.optionValue as SignoffStatus;
                  })
                }
              >
                <Option value="pending">Pending</Option>
                <Option value="confirmed">Confirmed</Option>
                <Option value="rejected">Rejected</Option>
              </Dropdown>
            </Field>
            {recordId ? (
              <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                <Button appearance="secondary" as="a" href={`${api.defaults.baseURL}/initiatives/${recordId}/export.json`}>
                  Export JSON
                </Button>
                <Button appearance="secondary" as="a" href={`${api.defaults.baseURL}/initiatives/${recordId}/export.md`}>
                  Export MD
                </Button>
                <Button appearance="primary" onClick={() => navigate(`/initiatives/${recordId}`)}>
                  Open initiative
                </Button>
              </div>
            ) : null}
          </>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 16 }}>
        <Button appearance="subtle" icon={<ArrowLeft24Regular />} disabled={effectiveIndex === 0} onClick={goBack}>
          Back
        </Button>
        {step.id !== 'review' ? (
          <Button appearance="primary" icon={<ArrowRight24Regular />} iconPosition="after" disabled={busy || !canAdvance()} onClick={() => void goNext()}>
            {busy ? <Spinner size="tiny" /> : 'Next'}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
