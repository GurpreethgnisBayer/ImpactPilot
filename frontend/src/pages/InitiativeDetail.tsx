import {
  Button,
  Dropdown,
  Field,
  Input,
  Option,
  Spinner,
  Tab,
  TabList,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
  Text,
  Textarea,
} from '@fluentui/react-components';
import { ArrowLeft16Regular, ArrowSync20Regular, BookOpen24Regular } from '@fluentui/react-icons';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ErrorCard } from '../components/ErrorCard';
import { ExportMenu, exportStatusKey } from '../components/ExportMenu';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { PrimaryButton } from '../components/ui/PrimaryButton';
import { SkeletonCards } from '../components/ui/Skeleton';
import { SensitivityTornado, type TornadoBar } from '../components/SensitivityTornado';
import { SourceBadge } from '../components/SourceBadge';
import { TrackingChart, type TrackingRow } from '../components/TrackingChart';
import { useToast } from '../components/ToastProvider';
import { useConfig } from '../hooks/useConfig';
import { useInitiative, useUpdateInitiative } from '../hooks/useInitiatives';
import { CompendiumView } from '../components/CompendiumView';
import api from '../lib/api';
import { apiErrorMessage } from '../lib/apiError';
import { savedLlmSettings } from '../lib/llmSettings';
import { queryClient } from '../lib/queryClient';
import type { InitiativeRecord, RangeValue, SignoffStatus } from '../types/initiative';
import { eurosPermitted } from '../types/initiative';

function EstimateRangeEditor({
  range,
  onConfirm,
}: {
  range: RangeValue;
  onConfirm: (values?: { low: number; base: number; high: number }) => void;
}) {
  const [vals, setVals] = useState({ low: String(range.low), base: String(range.base), high: String(range.high) });
  useEffect(() => {
    setVals({ low: String(range.low), base: String(range.base), high: String(range.high) });
  }, [range.low, range.base, range.high]);
  const edited =
    Number(vals.low) !== range.low || Number(vals.base) !== range.base || Number(vals.high) !== range.high;
  const numeric = [vals.low, vals.base, vals.high].every((v) => v.trim() !== '' && !Number.isNaN(Number(v)));

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap', marginTop: 8 }}>
      {(['low', 'base', 'high'] as const).map((k) => (
        <Field key={k} label={k} style={{ width: 90 }}>
          <Input size="small" value={vals[k]} onChange={(_, d) => setVals((v) => ({ ...v, [k]: d.value }))} />
        </Field>
      ))}
      <Text size={200} style={{ paddingBottom: 6 }}>
        {range.unit}
      </Text>
      <SourceBadge source={range.source} />
      {range.confirmed ? (
        <span className="pill pill-success" style={{ marginBottom: 6 }}>Confirmed</span>
      ) : (
        <span className="pill pill-warning" style={{ marginBottom: 6 }}>Unconfirmed</span>
      )}
      {(!range.confirmed || edited) && (
        <Button
          size="small"
          appearance="primary"
          disabled={!numeric}
          onClick={() =>
            onConfirm(edited ? { low: Number(vals.low), base: Number(vals.base), high: Number(vals.high) } : undefined)
          }
        >
          {edited ? 'Save & confirm' : 'Confirm'}
        </Button>
      )}
      {range.rationale && (
        <Text size={200} block style={{ width: '100%', color: 'var(--text-3)' }}>
          {range.rationale}
        </Text>
      )}
    </div>
  );
}

type TabId = 'compendium' | 'overview' | 'estimate' | 'evidence' | 'scorecard' | 'tracking' | 'history';

export function InitiativeDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error, refetch } = useInitiative(id);
  const updateMutation = useUpdateInitiative();
  const { showToast } = useToast();
  const { data: config } = useConfig();

  const [tab, setTab] = useState<TabId | null>(null);
  const [draft, setDraft] = useState<InitiativeRecord | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [audit, setAudit] = useState<unknown[]>([]);
  const [versions, setVersions] = useState<unknown[]>([]);
  const [tornado, setTornado] = useState<TornadoBar[]>([]);
  const [scenarios, setScenarios] = useState<{ low: number; base: number; high: number } | undefined>();
  const [trackingRows, setTrackingRows] = useState<TrackingRow[]>([]);

  useEffect(() => {
    if (data) {
      setDraft(structuredClone(data));
      setDirty(false);
      setTab((t) => t ?? (data.compendium ? 'compendium' : 'overview'));
    }
  }, [data]);

  const applyServerRecord = (record: InitiativeRecord) => {
    setDraft(structuredClone(record));
    setDirty(false);
    if (id) {
      queryClient.setQueryData(['initiative', id], record);
      void queryClient.invalidateQueries({ queryKey: exportStatusKey(id) });
    }
  };

  const confirmEstimate = async (dimensionId: string, values?: { low: number; base: number; high: number }) => {
    if (!id) return;
    if (dirty) {
      showToast({ title: 'Save your changes first', intent: 'warning' });
      return;
    }
    try {
      const { data: rec } = await api.post<InitiativeRecord>(
        `/initiatives/${id}/estimates/${dimensionId}/confirm`,
        values ?? {},
      );
      applyServerRecord(rec);
      showToast({ title: `${dimensionId} confirmed`, intent: 'success' });
    } catch (e) {
      showToast({ title: 'Confirm failed', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  const confirmAll = async () => {
    if (!id) return;
    try {
      const { data: rec } = await api.post<InitiativeRecord>(`/initiatives/${id}/estimates/confirm-all`);
      applyServerRecord(rec);
      showToast({ title: 'All estimates confirmed', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Confirm failed', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  const regenerate = async () => {
    if (!id) return;
    setRegenerating(true);
    try {
      const { data: res } = await api.post<{ record: InitiativeRecord }>(`/initiatives/${id}/compendium`, {
        llm_settings: savedLlmSettings(),
      });
      applyServerRecord(res.record);
      showToast({ title: 'Compendium regenerated', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Regenerate failed', body: apiErrorMessage(e), intent: 'error' });
    } finally {
      setRegenerating(false);
    }
  };

  useEffect(() => {
    if (tab === 'history' && id) {
      void api.get(`/initiatives/${id}/audit`).then((r) => setAudit(r.data));
      void api.get(`/initiatives/${id}/versions`).then((r) => setVersions(r.data));
    }
    if (tab === 'tracking' && id) {
      void api
        .get<{ rows: TrackingRow[] }>(`/initiatives/${id}/tracking`)
        .then((r) => setTrackingRows(r.data.rows ?? []))
        .catch(() => setTrackingRows([]));
    }
  }, [tab, id]);

  const onTabSelect = (_: unknown, d: { value: unknown }) => {
    setTab(d.value as TabId);
  };

  const patch = (fn: (r: InitiativeRecord) => void) => {
    setDraft((prev) => {
      if (!prev) return prev;
      const next = structuredClone(prev);
      fn(next);
      return next;
    });
    setDirty(true);
  };

  const save = async () => {
    if (!id || !draft) return;
    try {
      await updateMutation.mutateAsync({ id, record: draft });
      setDirty(false);
      void queryClient.invalidateQueries({ queryKey: exportStatusKey(id) });
      showToast({ title: 'Saved', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Save failed', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  const runStatement = async () => {
    if (!id) return;
    try {
      const { data: res } = await api.post<{ impact_statement: string; quality_warnings: unknown[] }>(
        `/initiatives/${id}/statement`,
      );
      patch((r) => {
        r.impact_statement = res.impact_statement;
        r.quality_warnings = res.quality_warnings as InitiativeRecord['quality_warnings'];
      });
      showToast({ title: 'Statement generated', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Statement failed', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  const runScorecard = async () => {
    if (!id) return;
    try {
      const { data: res } = await api.post<{
        scorecard: InitiativeRecord['scorecard'];
        impact_score: InitiativeRecord['impact_score'];
      }>(`/initiatives/${id}/scorecard`);
      patch((r) => {
        r.scorecard = res.scorecard;
        r.impact_score = res.impact_score;
      });
      showToast({ title: 'Scorecard updated', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Scorecard failed', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  const runMonetize = async () => {
    if (!id) return;
    try {
      const { data: res } = await api.post<{ monetization: InitiativeRecord['monetization'] }>(
        `/initiatives/${id}/monetize`,
      );
      patch((r) => {
        r.monetization = res.monetization;
      });
      showToast({ title: 'Monetization computed', intent: 'success' });
    } catch (e) {
      showToast({ title: 'Monetize failed', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  if (isLoading || !draft || !tab) {
    return <Spinner label="Loading initiative…" />;
  }
  if (isError) {
    return <ErrorCard message={apiErrorMessage(error)} onRetry={() => void refetch()} />;
  }

  const showEuros = eurosPermitted(draft.maturity?.tier);
  const focusAreas = config?.focus_areas ?? [];
  const dimensionLabels = Object.fromEntries((config?.dimensions ?? []).map((d) => [d.id, d.label]));
  const phaseLabels = Object.fromEntries((config?.value_chain?.phases ?? []).map((p) => [p.id, p.label]));
  const unconfirmedCount = (draft.estimates ?? []).filter((e) => e.estimate && !e.estimate.confirmed).length;

  const focusLabel = focusAreas.find((fa) => fa.code === draft.initiative.focus_area_code)?.label;
  const sourceCount = draft.compendium?.sources?.length ?? 0;

  return (
    <div className="page">
      <Link to="/initiatives" className="back-link">
        <ArrowLeft16Regular /> All initiatives
      </Link>
      <PageHeader
        eyebrow={focusLabel || 'Initiative'}
        title={draft.initiative.title || 'Untitled initiative'}
        subtitle={draft.initiative.description}
        meta={
          <>
            {draft.maturity?.tier && <span className="pill pill-accent">Maturity: {draft.maturity.tier}</span>}
            {sourceCount > 0 && <span className="pill">{sourceCount} cited sources</span>}
            {draft.impact_score && (
              <span className="pill">
                Impact score {draft.impact_score.score} · {draft.impact_score.label}
              </span>
            )}
          </>
        }
        actions={
          id && (
            <ExportMenu
              initiativeId={id}
              hasCompendium={!!draft.compendium}
              onReviewDraft={() => setTab('estimate')}
            />
          )
        }
      />

      <TabList selectedValue={tab} onTabSelect={onTabSelect} className="tabs">
        <Tab value="compendium">Compendium</Tab>
        <Tab value="overview">Overview</Tab>
        <Tab value="estimate">Estimate</Tab>
        <Tab value="evidence">Evidence</Tab>
        <Tab value="scorecard">Scorecard</Tab>
        <Tab value="tracking">Tracking</Tab>
        <Tab value="history">History</Tab>
      </TabList>

      <div style={{ marginTop: 16 }}>
        {tab === 'compendium' && (
          <div>
            <div className="row gap-8" style={{ marginBottom: 16 }}>
              <Button
                appearance="secondary"
                icon={<ArrowSync20Regular />}
                disabled={regenerating}
                onClick={() => void regenerate()}
              >
                {regenerating ? 'Searching and synthesising…' : draft.compendium ? 'Regenerate compendium' : 'Generate compendium'}
              </Button>
              {unconfirmedCount > 0 && (
                <Button appearance="subtle" onClick={() => setTab('estimate')}>
                  Review {unconfirmedCount} unconfirmed estimate{unconfirmedCount > 1 ? 's' : ''}
                </Button>
              )}
            </div>
            {regenerating ? (
              <SkeletonCards count={2} label="Searching literature and synthesising the brief…" />
            ) : draft.compendium ? (
              <CompendiumView compendium={draft.compendium} dimensionLabels={dimensionLabels} phaseLabels={phaseLabels} />
            ) : (
              <EmptyState
                icon={<BookOpen24Regular />}
                title="No evidence compendium yet"
                description="Generate one from the title and description to pull cited literature into this initiative."
                action={
                  <PrimaryButton size="medium" onClick={() => void regenerate()}>
                    Generate compendium
                  </PrimaryButton>
                }
              />
            )}
          </div>
        )}

        {tab === 'overview' && (
          <div className="card">
            <Field label="Title">
              <Input
                value={draft.initiative.title ?? ''}
                onChange={(_, d) => patch((r) => { r.initiative.title = d.value; })}
              />
            </Field>
            <Field label="Description">
              <Textarea
                value={draft.initiative.description ?? ''}
                onChange={(_, d) => patch((r) => { r.initiative.description = d.value; })}
                rows={4}
              />
            </Field>
            <Field label="Focus area">
              <Dropdown
                selectedOptions={draft.initiative.focus_area_code ? [draft.initiative.focus_area_code] : []}
                onOptionSelect={(_, d) => patch((r) => { r.initiative.focus_area_code = d.optionValue ?? 'UN'; })}
              >
                {focusAreas.map((fa) => (
                  <Option key={fa.code} value={fa.code}>
                    {fa.label || fa.code}
                  </Option>
                ))}
              </Dropdown>
            </Field>
            <Field label="Impact statement">
              <Textarea value={draft.impact_statement ?? ''} readOnly rows={5} />
              <Button appearance="secondary" size="small" style={{ marginTop: 8 }} onClick={() => void runStatement()}>
                Generate statement
              </Button>
            </Field>
            {(draft.quality_warnings ?? []).length > 0 ? (
              <div style={{ marginTop: 12 }}>
                <Text weight="semibold">Quality warnings</Text>
                <ul>
                  {draft.quality_warnings!.map((w, i) => (
                    <li key={i}>{w.message ?? JSON.stringify(w)}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <Field label="Business owner sign-off">
              <Dropdown
                selectedOptions={[draft.initiative.roles?.business_owner_signoff_status ?? 'pending']}
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
          </div>
        )}

        {tab === 'estimate' && (
          <div className="card">
            <div className="surface-head">
              <div>
                <h2 className="surface-title">Estimates</h2>
                <p className="muted">
                  LLM-suggested ranges stay marked DRAFT in every export until you confirm or edit them.
                </p>
              </div>
              {unconfirmedCount > 0 && (
                <PrimaryButton size="medium" onClick={() => void confirmAll()}>
                  Confirm all {unconfirmedCount}
                </PrimaryButton>
              )}
            </div>
            {(draft.estimates ?? []).map((est, idx) => (
              <div key={est.dimension_id} style={{ marginBottom: 16, borderBottom: '1px solid var(--line)', paddingBottom: 16 }}>
                <Text weight="semibold">{dimensionLabels[est.dimension_id] ?? est.dimension_id}</Text>
                <Field label="Direction" style={{ maxWidth: 220, marginTop: 8 }}>
                  <Dropdown
                    selectedOptions={[est.direction ?? 'flat']}
                    value={{ up: 'Up', down: 'Down', flat: 'Flat' }[est.direction ?? 'flat']}
                    onOptionSelect={(_, d) =>
                      patch((r) => {
                        r.estimates![idx].direction = d.optionValue as typeof est.direction;
                      })
                    }
                  >
                    <Option value="up">Up</Option>
                    <Option value="down">Down</Option>
                    <Option value="flat">Flat</Option>
                  </Dropdown>
                </Field>
                {est.estimate ? (
                  <EstimateRangeEditor
                    range={est.estimate}
                    onConfirm={(values) => void confirmEstimate(est.dimension_id, values)}
                  />
                ) : null}
              </div>
            ))}
            {(draft.estimates ?? []).length === 0 ? (
              <Text>Add estimates in the intake wizard or via LLM inference.</Text>
            ) : null}
            {showEuros ? (
              <Button appearance="secondary" onClick={() => void runMonetize()}>
                Compute € monetization
              </Button>
            ) : (
              <Text size={200} block style={{ marginTop: 8 }}>
                € monetization is hidden for exploratory maturity.
              </Text>
            )}
            {(draft.monetization ?? []).length > 0 && showEuros ? (
              <Table style={{ marginTop: 16 }}>
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>Dimension</TableHeaderCell>
                    <TableHeaderCell>Amount (EUR)</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {draft.monetization!.map((m) => (
                    <TableRow key={m.dimension_id}>
                      <TableCell>{m.dimension_id}</TableCell>
                      <TableCell>
                        {m.amount_eur.base} ({m.label})
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : null}
          </div>
        )}

        {tab === 'evidence' && (
          <div className="card">
            {(draft.evidence ?? []).length === 0 ? (
              <Text>No evidence items yet.</Text>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>Kind</TableHeaderCell>
                    <TableHeaderCell>Title</TableHeaderCell>
                    <TableHeaderCell>Source</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {draft.evidence!.map((ev) => (
                    <TableRow key={ev.id}>
                      <TableCell>{ev.kind}</TableCell>
                      <TableCell>{ev.title}</TableCell>
                      <TableCell>{ev.source_or_link}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        )}

        {tab === 'scorecard' && (
          <div className="card">
            <Button appearance="secondary" onClick={() => void runScorecard()}>
              Build scorecard
            </Button>
            {draft.impact_score ? (
              <Text block style={{ marginTop: 12 }}>
                Impact score: {draft.impact_score.score} — {draft.impact_score.label}
              </Text>
            ) : null}
            <Table style={{ marginTop: 16 }}>
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Dimension</TableHeaderCell>
                  <TableHeaderCell>Direction</TableHeaderCell>
                  <TableHeaderCell>Confidence</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(draft.scorecard ?? []).map((s) => (
                  <TableRow key={s.dimension_id}>
                    <TableCell>{s.dimension_id}</TableCell>
                    <TableCell>{s.direction}</TableCell>
                    <TableCell>{s.confidence}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {draft.maturity?.tier === 'mature' ? (
              <div style={{ marginTop: 24 }}>
                <Text weight="semibold" block>
                  Sensitivity (mature only)
                </Text>
                <Button
                  appearance="secondary"
                  style={{ marginTop: 8, marginBottom: 12 }}
                  onClick={() => {
                    void (async () => {
                      if (!id || !draft) return;
                      const ranges: Record<string, unknown> = {};
                      const coefficients: Record<string, number> = {};
                      for (const est of draft.estimates ?? []) {
                        if (!est.estimate) continue;
                        ranges[est.dimension_id] = est.estimate;
                        coefficients[est.dimension_id] = 1;
                      }
                      try {
                        const { data: res } = await api.post<{
                          tornado: TornadoBar[];
                          scenarios: { low: number; base: number; high: number };
                        }>(`/initiatives/${id}/sensitivity`, { ranges, coefficients });
                        setTornado(res.tornado ?? []);
                        setScenarios(res.scenarios);
                      } catch (e) {
                        showToast({
                          title: 'Sensitivity failed',
                          body: apiErrorMessage(e),
                          intent: 'error',
                        });
                      }
                    })();
                  }}
                >
                  Run sensitivity
                </Button>
                <SensitivityTornado bars={tornado} scenarios={scenarios} />
              </div>
            ) : (
              <Text size={200} block style={{ marginTop: 12 }}>
                Sensitivity charts are available for mature initiatives only.
              </Text>
            )}
          </div>
        )}

        {tab === 'tracking' && (
          <div className="card">
            <Text weight="semibold" block>
              KPI plan
            </Text>
            {(draft.measurement_plan ?? []).map((kpi) => (
              <Text key={kpi.id ?? kpi.name} block>
                {kpi.name} — {kpi.cadence}
              </Text>
            ))}
            <Text weight="semibold" block style={{ marginTop: 16 }}>
              Predicted vs realized
            </Text>
            <TrackingChart rows={trackingRows} />
            <Table style={{ marginTop: 16 }}>
              <TableHeader>
                <TableRow>
                  <TableHeaderCell>Period</TableHeaderCell>
                  <TableHeaderCell>KPI</TableHeaderCell>
                  <TableHeaderCell>Predicted</TableHeaderCell>
                  <TableHeaderCell>Actual</TableHeaderCell>
                  <TableHeaderCell>Variance</TableHeaderCell>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trackingRows.map((r, i) => (
                  <TableRow key={`${r.period}-${i}`}>
                    <TableCell>{r.period}</TableCell>
                    <TableCell>{r.kpi_name}</TableCell>
                    <TableCell>{r.predicted?.base ?? '—'}</TableCell>
                    <TableCell>{r.actual?.base ?? '—'}</TableCell>
                    <TableCell>{r.variance?.base ?? '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {tab === 'history' && (
          <div className="card">
            <Text weight="semibold">Versions</Text>
            <pre style={{ fontSize: 12, overflow: 'auto' }}>{JSON.stringify(versions, null, 2)}</pre>
            <Text weight="semibold" style={{ marginTop: 16 }}>
              Audit
            </Text>
            <pre style={{ fontSize: 12, overflow: 'auto' }}>{JSON.stringify(audit, null, 2)}</pre>
          </div>
        )}
      </div>

      {dirty && (
        <div className="action-bar" role="region" aria-label="Unsaved changes">
          <span className="muted" style={{ fontWeight: 500 }}>
            You have unsaved changes. Exports use the last saved version.
          </span>
          <div className="row gap-8">
            <Button appearance="subtle" onClick={() => data && applyServerRecord(data)}>
              Discard
            </Button>
            <PrimaryButton size="medium" disabled={updateMutation.isPending} onClick={() => void save()}>
              {updateMutation.isPending ? 'Saving…' : 'Save changes'}
            </PrimaryButton>
          </div>
        </div>
      )}
    </div>
  );
}
