import { Button, Checkbox, Dropdown, Field, Input, Option, Spinner, Textarea } from '@fluentui/react-components';
import {
  ArrowLeft20Regular,
  ArrowRight20Regular,
  BrainCircuit20Regular,
  DocumentSearch20Regular,
  Lightbulb16Regular,
  Sparkle20Filled,
} from '@fluentui/react-icons';
import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { CompendiumView } from '../components/CompendiumView';
import { EvidencePicker } from '../components/EvidencePicker';
import { ExportMenu } from '../components/ExportMenu';
import { useToast } from '../components/ToastProvider';
import { PageHeader } from '../components/ui/PageHeader';
import { PrimaryButton } from '../components/ui/PrimaryButton';
import { SkeletonCards } from '../components/ui/Skeleton';
import { Stepper } from '../components/ui/Stepper';
import { useConfig } from '../hooks/useConfig';
import { useActiveLlm } from '../hooks/useLlm';
import { useSources } from '../hooks/useSources';
import { groupSources } from '../lib/sources';
import api from '../lib/api';
import { apiErrorMessage } from '../lib/apiError';
import { queryClient } from '../lib/queryClient';
import type { Compendium, LiteratureSearchResult, RelevanceRank } from '../types/initiative';

type Step = 'idea' | 'evidence' | 'result';

const STEPS = [
  { id: 'idea', label: 'Describe the idea', hint: 'What changes, and where' },
  { id: 'evidence', label: 'Rank the evidence', hint: 'Weight what matters' },
  { id: 'result', label: 'Review & export', hint: 'Cited, range-based brief' },
];

const EXAMPLES = [
  {
    label: 'AI protocol-deviation detection',
    title: 'AI-assisted protocol deviation detection',
    description:
      'Use an ML model on EDC and monitoring data to flag likely protocol deviations weekly, so CRAs review high-risk sites first instead of 100% source data verification. Goal: fewer major deviations and less monitoring effort per site.',
  },
  {
    label: 'ML ADMET triage',
    title: 'ML-based ADMET prediction before synthesis',
    description:
      'Score virtual compounds with ADMET prediction models so chemists deprioritise likely failures before synthesis. Goal: fewer compounds synthesised per candidate and shorter lead-optimisation cycles.',
  },
  {
    label: 'Decentralised trial visits',
    title: 'Hybrid decentralised visits in phase III',
    description:
      'Replace a share of on-site visits with home nursing and eConsent in phase III trials, so patients travel less. Goal: faster enrolment, lower dropout and fewer screen failures.',
  },
];

const SEARCH_STAGES = [
  'Reading your idea…',
  'Searching journals and preprints…',
  'Searching repositories and reports…',
  'Checking trial registries…',
  'Checking regulatory guidance, labels and recalls…',
  'Reviewing matches for relevance…',
];

const SYNTH_STAGES = [
  'Reading abstracts of your ranked papers…',
  'Weighting high-relevance evidence…',
  'Extracting reported effect ranges…',
  'Writing the cited brief…',
];

/** Cycles through progress messages while `active`, so long LLM calls feel alive. */
function useStagedMessage(active: boolean, stages: string[], intervalMs = 3500): string {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (!active) {
      setI(0);
      return;
    }
    const t = setInterval(() => setI((n) => Math.min(n + 1, stages.length - 1)), intervalMs);
    return () => clearInterval(t);
  }, [active, stages.length, intervalMs]);
  return stages[i];
}

export function QuickBrief() {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const { data: config } = useConfig();
  const llm = useActiveLlm();

  const [step, setStep] = useState<Step>('idea');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [focusArea, setFocusArea] = useState('');
  const [phase, setPhase] = useState('');
  const { data: sourceList = [], isError: sourcesFailed } = useSources();
  const [sourcesOn, setSourcesOn] = useState<Record<string, boolean>>({});
  useEffect(() => {
    if (!sourceList.length) return;
    setSourcesOn((prev) =>
      Object.keys(prev).length
        ? prev
        : Object.fromEntries(sourceList.map((s) => [s.key, s.available && s.default_on])),
    );
  }, [sourceList]);

  const [searching, setSearching] = useState(false);
  const [search, setSearch] = useState<LiteratureSearchResult | null>(null);
  const [ranks, setRanks] = useState<Record<string, RelevanceRank>>({});

  const [synthesizing, setSynthesizing] = useState(false);
  const [result, setResult] = useState<{ id: string; compendium: Compendium } | null>(null);

  const searchStage = useStagedMessage(searching, SEARCH_STAGES);
  const synthStage = useStagedMessage(synthesizing, SYNTH_STAGES, 5000);

  const resetToken = (location.state as { reset?: number } | null)?.reset;
  useEffect(() => {
    if (resetToken) startOver(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetToken]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [step]);

  const phases = config?.value_chain?.phases ?? [];
  const dimensionLabels = Object.fromEntries((config?.dimensions ?? []).map((d) => [d.id, d.label]));
  const phaseLabels = Object.fromEntries(phases.map((p) => [p.id, p.label]));
  const titleOk = title.trim().length >= 3;
  const descriptionOk = description.trim().length >= 10;
  const enabledSources = sourceList.filter((s) => s.available && sourcesOn[s.key]).map((s) => s.key);
  // If the list failed to load, let the server use its defaults rather than blocking the search.
  const sourcesOk = sourcesFailed || enabledSources.length > 0;
  const canSearch = titleOk && descriptionOk && sourcesOk;

  const findPapers = async () => {
    setSearching(true);
    try {
      const { data } = await api.post<LiteratureSearchResult>('/compendium/search', {
        title: title.trim(),
        description: description.trim(),
        phase_id: phase,
        sources: sourcesFailed ? undefined : enabledSources,
        llm_settings: llm.override,
      });
      setSearch(data);
      setRanks(Object.fromEntries(data.sources.map((s) => [s.source_id, s.recommended ? 3 : 0])));
      setStep('evidence');
    } catch (e) {
      showToast({ title: 'Literature search failed', body: apiErrorMessage(e), intent: 'error' });
    } finally {
      setSearching(false);
    }
  };

  const setRank = (id: string, rank: RelevanceRank) => setRanks((prev) => ({ ...prev, [id]: rank }));
  const rankedCount = search ? search.sources.filter((s) => (ranks[s.source_id] ?? 0) > 0).length : 0;

  const generateFromSelection = async () => {
    if (!search) return;
    const chosen = search.sources
      .filter((s) => (ranks[s.source_id] ?? 0) > 0)
      .map((s) => ({ ...s, relevance: ranks[s.source_id] }));
    if (chosen.length === 0) return;
    setSynthesizing(true);
    try {
      const { data } = await api.post<{ initiative_id: string; compendium: Compendium }>('/compendium/synthesize', {
        title: title.trim(),
        description: description.trim(),
        focus_area_code: focusArea,
        phase_id: phase,
        sources: chosen,
        llm_settings: llm.override,
      });
      setResult({ id: data.initiative_id, compendium: data.compendium });
      void queryClient.invalidateQueries({ queryKey: ['initiatives'] });
      setStep('result');
      const high = chosen.filter((s) => s.relevance === 3).length;
      showToast({
        title: 'Brief ready',
        body: `Built from ${chosen.length} ranked sources (${high} high). Saved to Initiatives.`,
        intent: 'success',
      });
    } catch (e) {
      showToast({ title: 'Brief generation failed', body: apiErrorMessage(e), intent: 'error' });
    } finally {
      setSynthesizing(false);
    }
  };

  function startOver(clearIdea = false) {
    setStep('idea');
    setSearch(null);
    setRanks({});
    setResult(null);
    if (clearIdea) {
      setTitle('');
      setDescription('');
      setPhase('');
      setFocusArea('');
    }
  }

  const modelChip = (
    <Link to="/settings" className="pill" style={{ textDecoration: 'none' }} title="Change model in Settings">
      <BrainCircuit20Regular /> {llm.label}
    </Link>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Quick brief"
        title={step === 'result' && result ? title || 'Your impact brief' : 'Turn an idea into an evidence-backed brief'}
        subtitle={
          step === 'idea'
            ? 'Describe the change in a few sentences. ImpactPilot finds the literature, you rank it, and it writes a cited, range-based brief.'
            : step === 'evidence'
              ? 'Rank how much each paper should shape the brief. High-ranked papers drive the estimates.'
              : 'Saved to Initiatives. Export it now, or open the full brief to confirm the suggested ranges.'
        }
        meta={modelChip}
        actions={
          step === 'result' && result ? (
            <ExportMenu initiativeId={result.id} hasCompendium onReviewDraft={() => navigate(`/initiatives/${result.id}`)} />
          ) : undefined
        }
      />

      <Stepper steps={STEPS} current={step} onStepClick={(id) => !searching && !synthesizing && setStep(id as Step)} />

      {step === 'idea' && (
        <>
          <section className="surface">
            <div className="stack">
              <Field
                label="Idea title"
                required
                validationState={title && !titleOk ? 'error' : 'none'}
                validationMessage={title && !titleOk ? 'At least 3 characters' : undefined}
              >
                <Input
                  size="large"
                  value={title}
                  onChange={(_, d) => setTitle(d.value)}
                  placeholder="e.g. ML-based ADMET prediction to deprioritise compounds before synthesis"
                />
              </Field>
              <Field
                label="What changes, and what should improve?"
                required
                hint="Who does what differently, in which process step, and what you expect to improve (time, cost, success rate…)."
                validationState={description && !descriptionOk ? 'error' : 'none'}
                validationMessage={description && !descriptionOk ? 'Add a little more detail' : undefined}
              >
                <Textarea value={description} onChange={(_, d) => setDescription(d.value)} rows={5} resize="vertical" />
              </Field>

              {!title && !description && (
                <div>
                  <div className="muted" style={{ fontSize: 13, marginBottom: 8, fontWeight: 500 }}>
                    <Lightbulb16Regular style={{ verticalAlign: 'middle' }} /> Not sure where to start? Try an example
                  </div>
                  <div className="row gap-8">
                    {EXAMPLES.map((ex) => (
                      <button
                        key={ex.label}
                        type="button"
                        className="chip-button"
                        onClick={() => {
                          setTitle(ex.title);
                          setDescription(ex.description);
                        }}
                      >
                        {ex.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="divider" style={{ margin: '4px 0' }} />

              <div className="grid-2">
                <Field label="Value-chain phase" hint="Optional — leave empty to let the model suggest one.">
                  <Dropdown
                    placeholder="Let the model suggest"
                    selectedOptions={phase ? [phase] : []}
                    value={phaseLabels[phase] ?? ''}
                    onOptionSelect={(_, d) => setPhase(d.optionValue ?? '')}
                  >
                    <Option value="">Let the model suggest</Option>
                    {phases.map((p) => (
                      <Option key={p.id} value={p.id}>
                        {p.label}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
                <Field label="Focus area" hint="Optional — used to group briefs in the portfolio.">
                  <Dropdown
                    placeholder="Unassigned"
                    selectedOptions={focusArea ? [focusArea] : []}
                    value={(config?.focus_areas ?? []).find((f) => f.code === focusArea)?.label ?? ''}
                    onOptionSelect={(_, d) => setFocusArea(d.optionValue ?? '')}
                  >
                    {(config?.focus_areas ?? []).map((fa) => (
                      <Option key={fa.code} value={fa.code}>
                        {fa.label || fa.code}
                      </Option>
                    ))}
                  </Dropdown>
                </Field>
              </div>

              <div role="group" aria-labelledby="search-in-label">
                <div id="search-in-label" style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                  Search in
                </div>
                <div className="stack" style={{ gap: 10 }}>
                  {groupSources(sourceList).map((group) => (
                    <div key={group.label}>
                      <div className="muted" style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                        {group.label}
                      </div>
                      <div className="row" style={{ gap: 16, flexWrap: 'wrap' }}>
                        {group.items.map((src) => (
                          <span key={src.key} title={src.available ? src.note : `Needs ${src.needs} on the server`}>
                            <Checkbox
                              label={src.available ? src.label : `${src.label} (needs key)`}
                              checked={src.available && !!sourcesOn[src.key]}
                              disabled={!src.available}
                              onChange={(_, d) => setSourcesOn((prev) => ({ ...prev, [src.key]: !!d.checked }))}
                            />
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                {sourceList.length > 0 && !sourcesOk && (
                  <div role="alert" style={{ color: 'var(--danger)', fontSize: 12, marginTop: 4 }}>
                    Pick at least one database
                  </div>
                )}
              </div>
            </div>
          </section>

          {searching && <SkeletonCards count={2} label={searchStage} />}

          <div className="action-bar">
            <span className="muted">
              {canSearch ? 'Ready to search the literature.' : 'Add a title and a short description to continue.'}
            </span>
            <PrimaryButton
              icon={searching ? <Spinner size="tiny" /> : <DocumentSearch20Regular />}
              disabled={!canSearch || searching}
              onClick={() => void findPapers()}
            >
              {searching ? 'Searching…' : 'Find relevant papers'}
            </PrimaryButton>
          </div>
        </>
      )}

      {step === 'evidence' && search && (
        <>
          {synthesizing ? (
            <SkeletonCards count={3} label={synthStage} />
          ) : (
            <EvidencePicker
              sources={search.sources}
              interpretation={search.interpretation}
              llmUsed={search.llm_used}
              warnings={search.warnings}
              ranks={ranks}
              onRank={setRank}
              onRankRecommended={() =>
                setRanks(Object.fromEntries(search.sources.map((s) => [s.source_id, s.recommended ? 3 : 0])))
              }
              onRankAll={(rank) => setRanks(Object.fromEntries(search.sources.map((s) => [s.source_id, rank])))}
              onClear={() => setRanks(Object.fromEntries(search.sources.map((s) => [s.source_id, 0])))}
            />
          )}

          <div className="action-bar">
            <Button
              appearance="subtle"
              icon={<ArrowLeft20Regular />}
              disabled={synthesizing}
              onClick={() => setStep('idea')}
            >
              Edit idea
            </Button>
            <div className="row gap-12">
              <span className="muted" aria-live="polite">
                {rankedCount === 0
                  ? 'Rank at least one paper above Off.'
                  : `${rankedCount} of ${search.sources.length} papers will be used`}
              </span>
              <PrimaryButton
                icon={synthesizing ? <Spinner size="tiny" /> : <Sparkle20Filled />}
                disabled={rankedCount === 0 || synthesizing}
                onClick={() => void generateFromSelection()}
              >
                {synthesizing ? 'Writing brief…' : 'Generate brief'}
              </PrimaryButton>
            </div>
          </div>
        </>
      )}

      {step === 'result' && result && (
        <>
          <CompendiumView compendium={result.compendium} dimensionLabels={dimensionLabels} phaseLabels={phaseLabels} />
          <div className="action-bar">
            <div className="row gap-8">
              <Button appearance="subtle" icon={<ArrowLeft20Regular />} onClick={() => setStep('evidence')}>
                Re-rank sources
              </Button>
              <Button appearance="subtle" onClick={() => startOver(true)}>
                Start a new brief
              </Button>
            </div>
            <PrimaryButton
              icon={<ArrowRight20Regular />}
              iconPosition="after"
              onClick={() => navigate(`/initiatives/${result.id}`)}
            >
              Open full brief
            </PrimaryButton>
          </div>
        </>
      )}
    </div>
  );
}
