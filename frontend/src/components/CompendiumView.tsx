import { Link as FluentLink, MessageBar, MessageBarBody } from '@fluentui/react-components';
import {
  ArrowTrendingDown16Regular,
  Subtract16Regular,
  ArrowTrending16Regular,
  Warning16Filled,
} from '@fluentui/react-icons';
import { QUERY_LABELS, sourceLabel } from '../lib/sources';
import type { Compendium, CompendiumDimension } from '../types/initiative';

interface CompendiumViewProps {
  compendium: Compendium;
  dimensionLabels?: Record<string, string>;
  phaseLabels?: Record<string, string>;
}

const tierLabels: Record<string, string> = {
  exploratory: 'Exploratory',
  emerging_local: 'Emerging (local)',
  mature: 'Mature',
};

const relevanceTone: Record<string, string> = {
  high: 'var(--rank-high)',
  medium: 'var(--rank-medium)',
  low: 'var(--rank-low)',
};

function fmt(v: number | null): string {
  if (v === null || v === undefined) return '?';
  return Number(v.toPrecision(2)).toString();
}

function DirectionIcon({ direction }: { direction: string }) {
  if (direction === 'down') return <ArrowTrendingDown16Regular />;
  if (direction === 'up') return <ArrowTrending16Regular />;
  return <Subtract16Regular />;
}

/** Low–high band with a base marker, scaled per row so zero is always on the axis. */
function RangeBar({ d }: { d: CompendiumDimension }) {
  if (d.low === null || d.high === null) {
    return <span className="muted" style={{ fontSize: 13 }}>No range reported</span>;
  }
  const lo = Math.min(d.low, d.high);
  const hi = Math.max(d.low, d.high);
  const min = Math.min(0, lo);
  const max = Math.max(0, hi);
  const span = max - min || 1;
  const pct = (v: number) => ((v - min) / span) * 100;
  const base = d.base ?? (lo + hi) / 2;
  return (
    <div>
      <div
        role="img"
        aria-label={`Range ${fmt(d.low)} to ${fmt(d.high)} ${d.unit}, base ${fmt(d.base)}`}
        style={{ position: 'relative', height: 10, borderRadius: 999, background: '#eef1f6' }}
      >
        <div
          style={{
            position: 'absolute',
            left: `${pct(0)}%`,
            top: -3,
            bottom: -3,
            width: 1,
            background: 'var(--line-strong)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: `${pct(lo)}%`,
            width: `${Math.max(2, pct(hi) - pct(lo))}%`,
            top: 0,
            bottom: 0,
            borderRadius: 999,
            background: 'var(--gradient)',
            opacity: 0.85,
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: `calc(${pct(base)}% - 7px)`,
            top: -2,
            width: 14,
            height: 14,
            borderRadius: 999,
            background: '#fff',
            border: '3px solid var(--accent)',
            boxShadow: 'var(--shadow-sm)',
          }}
        />
      </div>
      <div className="row" style={{ justifyContent: 'space-between', marginTop: 6, fontSize: 12, color: 'var(--text-3)' }}>
        <span>Low {fmt(d.low)}</span>
        <span style={{ fontWeight: 650, color: 'var(--text)' }}>
          Base {fmt(d.base)} {d.unit}
        </span>
        <span>High {fmt(d.high)}</span>
      </div>
    </div>
  );
}

export function CompendiumView({ compendium: c, dimensionLabels = {}, phaseLabels = {} }: CompendiumViewProps) {
  const refNum = new Map(c.sources.map((s, i) => [s.source_id, i + 1]));
  const Cite = ({ ids }: { ids: string[] }) => (
    <span style={{ display: 'inline-flex', gap: 4, marginLeft: 6, verticalAlign: 'middle' }}>
      {ids
        .filter((id) => refNum.has(id))
        .map((id) => (
          <a key={id} href={`#ref-${refNum.get(id)}`} className="cite-chip" aria-label={`Reference ${refNum.get(id)}`}>
            {refNum.get(id)}
          </a>
        ))}
    </span>
  );

  const facts = [
    c.value_chain_phase && { label: 'Value-chain phase', value: phaseLabels[c.value_chain_phase] ?? c.value_chain_phase },
    c.process_step && { label: 'Process step', value: c.process_step },
    c.mechanism && { label: 'Mechanism', value: c.mechanism },
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <div className="stack">
      <section
        className="surface"
        style={{
          marginBottom: 0,
          padding: 28,
          background: 'linear-gradient(135deg, #0b1220 0%, #1e1b4b 60%, #312e81 100%)',
          color: '#e2e8f0',
          border: 'none',
          boxShadow: 'var(--shadow-lg)',
        }}
      >
        <div className="row" style={{ justifyContent: 'space-between', gap: 12, marginBottom: 12 }}>
          <span className="eyebrow" style={{ color: '#a5b4fc' }}>Executive summary</span>
          <div className="row gap-8">
            <span className="pill" style={{ background: 'rgba(255,255,255,0.1)', color: '#e0e7ff' }}>
              {c.sources.length} sources
            </span>
            <span className="pill" style={{ background: 'rgba(255,255,255,0.1)', color: '#e0e7ff' }}>
              Maturity: {tierLabels[c.suggested_maturity] ?? c.suggested_maturity}
            </span>
            <span className="pill" style={{ background: 'rgba(251,191,36,0.18)', color: '#fde68a' }}>
              <Warning16Filled /> Draft · needs SME review
            </span>
          </div>
        </div>
        <p style={{ margin: 0, fontSize: 17, lineHeight: 1.6, color: '#f8fafc' }}>{c.executive_summary}</p>
        {facts.length > 0 && (
          <div className="grid-3" style={{ marginTop: 20 }}>
            {facts.map((f) => (
              <div
                key={f.label}
                style={{ padding: 14, borderRadius: 12, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
              >
                <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#a5b4fc', fontWeight: 600 }}>
                  {f.label}
                </div>
                <div style={{ marginTop: 4, fontSize: 14, color: '#f1f5f9' }}>{f.value}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {c.warnings.length > 0 && (
        <MessageBar intent="info">
          <MessageBarBody>
            {c.warnings.map((w, i) => (
              <div key={i}>{w}</div>
            ))}
          </MessageBarBody>
        </MessageBar>
      )}

      {c.dimensions.length > 0 && (
        <section className="surface" style={{ marginBottom: 0 }}>
          <div className="surface-head">
            <div>
              <h2 className="surface-title">Literature-reported effects</h2>
              <p className="muted">Ranges as reported in the cited papers. Dot marks the base case.</p>
            </div>
          </div>
          <div className="grid-2">
            {c.dimensions.map((d) => (
              <div
                key={d.dimension_id}
                style={{ padding: 16, border: '1px solid var(--line)', borderRadius: 12, background: '#fcfcfe' }}
              >
                <div className="row" style={{ justifyContent: 'space-between', gap: 8, marginBottom: 12 }}>
                  <span style={{ fontWeight: 650, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <DirectionIcon direction={d.direction} />
                    {dimensionLabels[d.dimension_id] ?? d.dimension_id}
                  </span>
                  <span className="row gap-8">
                    <span className="pill" style={{ padding: '2px 8px', fontSize: 11 }}>
                      {d.confidence} confidence
                    </span>
                    {!d.evidence_backed && (
                      <span className="pill pill-danger" style={{ padding: '2px 8px', fontSize: 11 }}>
                        unsupported
                      </span>
                    )}
                    {d.evidence_backed && d.grounded === false && (
                      <span
                        className="pill pill-warning"
                        style={{ padding: '2px 8px', fontSize: 11 }}
                        title="Cited, but this range isn't a number reported in the source — it's the model's estimate around it."
                      >
                        model-interpolated
                      </span>
                    )}
                  </span>
                </div>
                <RangeBar d={d} />
                {d.rationale && (
                  <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
                    {d.rationale}
                    {d.evidence_backed && <Cite ids={d.citations} />}
                  </p>
                )}
                {d.quotes.slice(0, 2).map((q, i) => (
                  <blockquote
                    key={i}
                    style={{
                      margin: '10px 0 0',
                      padding: '6px 10px',
                      borderLeft: '3px solid var(--accent-soft)',
                      fontSize: 12,
                      fontStyle: 'italic',
                      color: 'var(--text-2)',
                    }}
                  >
                    “{q}”
                  </blockquote>
                ))}
              </div>
            ))}
          </div>
        </section>
      )}

      {c.key_findings.length > 0 && (
        <section className="surface" style={{ marginBottom: 0 }}>
          <h2 className="surface-title" style={{ marginBottom: 12 }}>Key findings</h2>
          <ol className="finding-list">
            {c.key_findings.map((f, i) => (
              <li key={i}>
                {f.finding}
                <Cite ids={f.citations} />
              </li>
            ))}
          </ol>
        </section>
      )}

      <div className="grid-2">
        <section className="surface" style={{ marginBottom: 0 }}>
          <h2 className="surface-title">Suggested maturity</h2>
          <span className="pill pill-accent" style={{ marginTop: 6 }}>
            {tierLabels[c.suggested_maturity] ?? c.suggested_maturity}
          </span>
          <p className="muted" style={{ marginTop: 10 }}>{c.maturity_rationale}</p>
        </section>
        {c.suggested_kpis.length > 0 && (
          <section className="surface" style={{ marginBottom: 0 }}>
            <h2 className="surface-title" style={{ marginBottom: 10 }}>Suggested KPIs</h2>
            <ul className="plain-list">
              {c.suggested_kpis.map((k, i) => (
                <li key={i}>
                  <b>{k.name}</b>
                  {k.cadence && <span className="pill" style={{ marginLeft: 6, padding: '1px 8px', fontSize: 11 }}>{k.cadence}</span>}
                  {k.definition && <div className="muted" style={{ fontSize: 13 }}>{k.definition}</div>}
                </li>
              ))}
            </ul>
          </section>
        )}
        {c.risks_and_caveats.length > 0 && (
          <section className="surface" style={{ marginBottom: 0 }}>
            <h2 className="surface-title" style={{ marginBottom: 10 }}>Risks and caveats</h2>
            <ul className="plain-list">
              {c.risks_and_caveats.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </section>
        )}
        {c.open_questions.length > 0 && (
          <section className="surface" style={{ marginBottom: 0 }}>
            <h2 className="surface-title" style={{ marginBottom: 10 }}>Open questions for SMEs</h2>
            <ul className="plain-list">
              {c.open_questions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
          </section>
        )}
      </div>

      {!c.llm_used && c.numeric_snippets.length > 0 && (
        <section className="surface" style={{ marginBottom: 0 }}>
          <h2 className="surface-title" style={{ marginBottom: 10 }}>Numbers found in abstracts</h2>
          <ul className="plain-list">
            {c.numeric_snippets.slice(0, 15).map((n, i) => (
              <li key={i}>
                <b>{n.raw}</b> — {n.context} <Cite ids={[n.pmid]} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="surface" style={{ marginBottom: 0 }}>
        <h2 className="surface-title" style={{ marginBottom: 12 }}>References ({c.sources.length})</h2>
        <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {c.sources.map((s, i) => (
            <li key={s.source_id} id={`ref-${i + 1}`} style={{ display: 'flex', gap: 12, scrollMarginTop: 24 }}>
              <span className="cite-chip" aria-hidden style={{ flexShrink: 0, marginTop: 2 }}>
                {i + 1}
              </span>
              <div style={{ minWidth: 0 }}>
                {s.url ? (
                  <FluentLink href={s.url} target="_blank" rel="noreferrer" style={{ fontWeight: 600 }}>
                    {s.title}
                  </FluentLink>
                ) : (
                  <span style={{ fontWeight: 600 }}>{s.title}</span>
                )}
                <div className="row gap-8" style={{ marginTop: 2, fontSize: 12, color: 'var(--text-3)' }}>
                  <span>
                    {[s.venue, s.year, s.type, sourceLabel(s.database)].filter(Boolean).join(' · ')}
                  </span>
                  {s.relevance && (
                    <span className="row" style={{ gap: 4, fontWeight: 600, color: 'var(--text-2)' }}>
                      <span aria-hidden style={{ width: 8, height: 8, borderRadius: 999, background: relevanceTone[s.relevance] }} />
                      {s.relevance} relevance
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ol>
        {Object.entries(c.queries ?? {}).some(([, value]) => value) && (
          <>
            <div className="divider" />
            <p className="muted" style={{ fontSize: 12 }}>
              Queries —{' '}
              {Object.entries(c.queries)
                .filter(([, value]) => value)
                .map(([key, value], i) => (
                  <span key={key}>
                    {i > 0 ? ' · ' : ''}
                    {QUERY_LABELS[key] || key}: <code>{value}</code>
                  </span>
                ))}
            </p>
          </>
        )}
      </section>
    </div>
  );
}
