import {
  Button,
  Dropdown,
  Option,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
} from '@fluentui/react-components';
import { Add20Regular, Folder24Regular, Sparkle20Filled } from '@fluentui/react-icons';
import { useMemo } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ErrorCard } from '../components/ErrorCard';
import { useToast } from '../components/ToastProvider';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { PrimaryButton } from '../components/ui/PrimaryButton';
import { Skeleton } from '../components/ui/Skeleton';
import { useConfig } from '../hooks/useConfig';
import { useCreateInitiative, useInitiatives } from '../hooks/useInitiatives';
import { apiErrorMessage } from '../lib/apiError';

const TIERS = [
  { value: 'exploratory', label: 'Exploratory' },
  { value: 'emerging_local', label: 'Emerging (local)' },
  { value: 'mature', label: 'Mature' },
];

const tierPill: Record<string, string> = {
  exploratory: 'pill',
  emerging_local: 'pill pill-accent',
  mature: 'pill pill-success',
};

export function InitiativesList() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const filters = useMemo(
    () => ({
      focus_area_code: params.get('focus_area_code') || undefined,
      maturity_tier: params.get('maturity_tier') || undefined,
      phase_id: params.get('phase_id') || undefined,
    }),
    [params],
  );
  const activeFilters = Object.values(filters).filter(Boolean).length;

  const { data: config } = useConfig();
  const { data, isLoading, isError, error, refetch } = useInitiatives(filters);
  const createMutation = useCreateInitiative();

  const setFilter = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(params);
    if (!value) next.delete(key);
    else next.set(key, value);
    setParams(next);
  };

  const handleNew = async () => {
    try {
      const record = await createMutation.mutateAsync({});
      showToast({ title: 'Initiative created', intent: 'success' });
      navigate(`/initiatives/${record.id}`);
    } catch (e) {
      showToast({ title: 'Could not create initiative', body: apiErrorMessage(e), intent: 'error' });
    }
  };

  const focusAreas = config?.focus_areas ?? [];
  const phases = config?.value_chain?.phases ?? [];
  const focusLabel = Object.fromEntries(focusAreas.map((f) => [f.code, f.label || f.code]));
  const phaseLabel = Object.fromEntries(phases.map((p) => [p.id, p.label || p.id]));
  const tierLabel = Object.fromEntries(TIERS.map((t) => [t.value, t.label]));
  const rows = data ?? [];

  return (
    <div className="page">
      <PageHeader
        eyebrow="Workspace"
        title="Initiatives"
        subtitle="Every brief you generate is saved here. Open one to confirm estimates, refine and export."
        actions={
          <>
            <Button appearance="secondary" onClick={() => navigate('/initiatives/new/wizard')}>
              Intake wizard
            </Button>
            <Button
              appearance="secondary"
              icon={<Add20Regular />}
              onClick={() => void handleNew()}
              disabled={createMutation.isPending}
            >
              Blank initiative
            </Button>
            <PrimaryButton size="medium" icon={<Sparkle20Filled />} onClick={() => navigate('/')}>
              New quick brief
            </PrimaryButton>
          </>
        }
      />

      <div className="surface row gap-12" style={{ padding: 14 }}>
        <Dropdown
          placeholder="All focus areas"
          style={{ minWidth: 190 }}
          value={filters.focus_area_code ? focusLabel[filters.focus_area_code] : ''}
          selectedOptions={filters.focus_area_code ? [filters.focus_area_code] : []}
          onOptionSelect={(_, d) => setFilter('focus_area_code', d.optionValue)}
        >
          <Option value="">All focus areas</Option>
          {focusAreas.map((fa) => (
            <Option key={fa.code} value={fa.code}>
              {fa.label || fa.code}
            </Option>
          ))}
        </Dropdown>
        <Dropdown
          placeholder="All maturity tiers"
          style={{ minWidth: 190 }}
          value={filters.maturity_tier ? tierLabel[filters.maturity_tier] : ''}
          selectedOptions={filters.maturity_tier ? [filters.maturity_tier] : []}
          onOptionSelect={(_, d) => setFilter('maturity_tier', d.optionValue)}
        >
          <Option value="">All maturity tiers</Option>
          {TIERS.map((t) => (
            <Option key={t.value} value={t.value}>
              {t.label}
            </Option>
          ))}
        </Dropdown>
        <Dropdown
          placeholder="All phases"
          style={{ minWidth: 190 }}
          value={filters.phase_id ? phaseLabel[filters.phase_id] : ''}
          selectedOptions={filters.phase_id ? [filters.phase_id] : []}
          onOptionSelect={(_, d) => setFilter('phase_id', d.optionValue)}
        >
          <Option value="">All phases</Option>
          {phases.map((p) => (
            <Option key={p.id} value={p.id}>
              {p.label || p.id}
            </Option>
          ))}
        </Dropdown>
        {activeFilters > 0 && (
          <Button appearance="subtle" onClick={() => setParams(new URLSearchParams())}>
            Clear filters
          </Button>
        )}
        <span className="muted" style={{ marginLeft: 'auto', fontSize: 13 }}>
          {isLoading ? '' : `${rows.length} initiative${rows.length === 1 ? '' : 's'}`}
        </span>
      </div>

      {isLoading ? (
        <div className="surface stack" aria-busy>
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} height={18} />
          ))}
        </div>
      ) : isError ? (
        <ErrorCard message={apiErrorMessage(error)} onRetry={() => void refetch()} />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={<Folder24Regular />}
          title={activeFilters ? 'No initiatives match these filters' : 'No initiatives yet'}
          description={
            activeFilters
              ? 'Try clearing a filter.'
              : 'Start with a quick brief: describe an idea and ImpactPilot builds a cited impact estimate.'
          }
          action={
            !activeFilters && (
              <PrimaryButton size="medium" icon={<Sparkle20Filled />} onClick={() => navigate('/')}>
                New quick brief
              </PrimaryButton>
            )
          }
        />
      ) : (
        <div className="surface" style={{ padding: 0, overflow: 'auto' }}>
          <Table aria-label="Initiatives">
            <TableHeader>
              <TableRow>
                <TableHeaderCell style={{ paddingLeft: 20 }}>Title</TableHeaderCell>
                <TableHeaderCell>Focus area</TableHeaderCell>
                <TableHeaderCell>Phase</TableHeaderCell>
                <TableHeaderCell>Maturity</TableHeaderCell>
                <TableHeaderCell>Updated</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow
                  key={row.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/initiatives/${row.id}`)}
                >
                  <TableCell style={{ paddingLeft: 20 }}>
                    <Link
                      to={`/initiatives/${row.id}`}
                      onClick={(e) => e.stopPropagation()}
                      style={{ fontWeight: 600, color: 'var(--text)', textDecoration: 'none' }}
                    >
                      {row.title || '(untitled)'}
                    </Link>
                  </TableCell>
                  <TableCell>{focusLabel[row.focus_area_code ?? ''] ?? row.focus_area_code ?? '—'}</TableCell>
                  <TableCell>{row.phase_id ? phaseLabel[row.phase_id] ?? row.phase_id : '—'}</TableCell>
                  <TableCell>
                    {row.maturity_tier ? (
                      <span className={tierPill[row.maturity_tier] ?? 'pill'}>{tierLabel[row.maturity_tier] ?? row.maturity_tier}</span>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="muted" style={{ fontSize: 13 }}>
                      {row.updated_at ? new Date(row.updated_at).toLocaleDateString(undefined, { dateStyle: 'medium' }) : '—'}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
