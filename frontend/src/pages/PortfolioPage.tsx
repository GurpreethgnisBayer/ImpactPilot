import { Button, Spinner, Table, TableBody, TableCell, TableHeader, TableHeaderCell, TableRow } from '@fluentui/react-components';
import { ArrowDownload20Regular, Grid24Regular, Layer20Regular } from '@fluentui/react-icons';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { ErrorCard } from '../components/ErrorCard';
import { useToast } from '../components/ToastProvider';
import { EmptyState } from '../components/ui/EmptyState';
import { PageHeader } from '../components/ui/PageHeader';
import { StatTile } from '../components/ui/StatTile';
import { useInitiatives, usePortfolioAggregations } from '../hooks/useInitiatives';
import { apiErrorMessage } from '../lib/apiError';
import { downloadFile } from '../lib/download';
import type { PortfolioAggregations } from '../types/initiative';

const tierLabels: Record<string, string> = {
  exploratory: 'Exploratory',
  emerging_local: 'Emerging (local)',
  mature: 'Mature',
};

export function PortfolioPage() {
  const { showToast } = useToast();
  const { data: initiatives, isLoading, isError, error, refetch } = useInitiatives();
  const { data: aggRaw, isLoading: aggLoading } = usePortfolioAggregations();
  const agg = aggRaw as PortfolioAggregations | undefined;
  const [downloading, setDownloading] = useState(false);

  const scoreChart = useMemo(() => {
    if (!agg?.by_impact_score) return [];
    return Object.entries(agg.by_impact_score).map(([name, value]) => ({ name, value }));
  }, [agg]);

  const downloadCsv = async () => {
    setDownloading(true);
    try {
      const name = await downloadFile('/portfolio/export.csv', 'portfolio.csv');
      showToast({ title: 'Portfolio CSV downloaded', body: name, intent: 'success' });
    } catch (e) {
      showToast({ title: 'CSV export failed', body: e instanceof Error ? e.message : String(e), intent: 'error' });
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="page">
      <PageHeader
        eyebrow="Workspace"
        title="Portfolio"
        subtitle="All initiatives at a glance, grouped by maturity and impact score."
        actions={
          <Button
            appearance="secondary"
            icon={downloading ? <Spinner size="tiny" /> : <ArrowDownload20Regular />}
            disabled={downloading}
            onClick={() => void downloadCsv()}
          >
            Download CSV
          </Button>
        }
      />

      {aggLoading ? (
        <Spinner label="Loading portfolio…" />
      ) : agg ? (
        <div className="grid-3" style={{ marginBottom: 16 }}>
          <StatTile label="Initiatives" value={agg.count} icon={<Layer20Regular />} tone="accent" />
          {Object.entries(agg.by_tier).map(([tier, value]) => (
            <StatTile key={tier} label={tierLabels[tier] ?? tier} value={value} tone={tier === 'mature' ? 'success' : 'default'} />
          ))}
        </div>
      ) : null}
      {agg?.note && <p className="muted" style={{ marginBottom: 16 }}>{agg.note}</p>}

      {scoreChart.length > 0 && (
        <section className="surface" style={{ height: 300 }}>
          <h2 className="surface-title" style={{ marginBottom: 12 }}>By impact score</h2>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={scoreChart}>
              <CartesianGrid vertical={false} stroke="#e5e8f0" />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
              <Tooltip cursor={{ fill: 'rgba(79,70,229,0.06)' }} />
              <Bar dataKey="value" fill="#4f46e5" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>
      )}

      {isLoading ? (
        <Spinner label="Loading list…" />
      ) : isError ? (
        <ErrorCard message={apiErrorMessage(error)} onRetry={() => void refetch()} />
      ) : (initiatives ?? []).length === 0 ? (
        <EmptyState icon={<Grid24Regular />} title="Your portfolio is empty" description="Generate a quick brief to add the first initiative." />
      ) : (
        <div className="surface" style={{ padding: 0, overflow: 'auto' }}>
          <Table aria-label="Portfolio">
            <TableHeader>
              <TableRow>
                <TableHeaderCell style={{ paddingLeft: 20 }}>Title</TableHeaderCell>
                <TableHeaderCell>Focus area</TableHeaderCell>
                <TableHeaderCell>Maturity</TableHeaderCell>
                <TableHeaderCell>Impact score</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(initiatives ?? []).map((row) => (
                <TableRow key={row.id}>
                  <TableCell style={{ paddingLeft: 20 }}>
                    <Link to={`/initiatives/${row.id}`} style={{ fontWeight: 600, color: 'var(--text)', textDecoration: 'none' }}>
                      {row.title || '(untitled)'}
                    </Link>
                  </TableCell>
                  <TableCell>{row.focus_area_code || '—'}</TableCell>
                  <TableCell>{row.maturity_tier ? tierLabels[row.maturity_tier] ?? row.maturity_tier : '—'}</TableCell>
                  <TableCell>{row.impact_score ?? '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
