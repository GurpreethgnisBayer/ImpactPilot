import { Button, Link as FluentLink, MessageBar, MessageBarBody } from '@fluentui/react-components';
import { Lightbulb20Regular, Open16Regular, Sparkle16Filled } from '@fluentui/react-icons';
import { useState } from 'react';
import { sourceLabel } from '../lib/sources';
import type { CandidateSource, RelevanceRank } from '../types/initiative';
import { EmptyState } from './ui/EmptyState';
import { SegmentedControl, type SegmentOption } from './ui/SegmentedControl';

interface EvidencePickerProps {
  sources: CandidateSource[];
  interpretation: string;
  llmUsed: boolean;
  warnings: string[];
  ranks: Record<string, RelevanceRank>;
  onRank: (sourceId: string, rank: RelevanceRank) => void;
  onRankRecommended: () => void;
  onRankAll: (rank: RelevanceRank) => void;
  onClear: () => void;
}

const RANK_OPTIONS: SegmentOption<RelevanceRank>[] = [
  { value: 0, label: 'Off', color: 'var(--rank-off)' },
  { value: 1, label: 'Low', color: 'var(--rank-low)' },
  { value: 2, label: 'Medium', color: 'var(--rank-medium)' },
  { value: 3, label: 'High', color: 'var(--rank-high)' },
];

const RANK_COLOR: Record<RelevanceRank, string> = {
  0: 'var(--line)',
  1: 'var(--rank-low)',
  2: 'var(--rank-medium)',
  3: 'var(--rank-high)',
};

type Filter = 'all' | 'ranked' | 'suggested';

function snippet(text: string | undefined, max = 260): string {
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function CountChip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <span className="pill" style={{ background: '#fff', border: '1px solid var(--line)' }}>
      <span aria-hidden style={{ width: 8, height: 8, borderRadius: 999, background: color }} />
      {value} {label}
    </span>
  );
}

export function EvidencePicker({
  sources,
  interpretation,
  llmUsed,
  warnings,
  ranks,
  onRank,
  onRankRecommended,
  onRankAll,
  onClear,
}: EvidencePickerProps) {
  const [filter, setFilter] = useState<Filter>('all');
  const recommendedCount = sources.filter((s) => s.recommended).length;
  const counts = { high: 0, medium: 0, low: 0, off: 0 };
  for (const s of sources) {
    const rank = ranks[s.source_id] ?? 0;
    if (rank === 3) counts.high += 1;
    else if (rank === 2) counts.medium += 1;
    else if (rank === 1) counts.low += 1;
    else counts.off += 1;
  }
  const rankedCount = sources.length - counts.off;

  const order = new Map(sources.map((s, i) => [s.source_id, i]));
  const shown = [...sources]
    .filter((s) =>
      filter === 'ranked' ? (ranks[s.source_id] ?? 0) > 0 : filter === 'suggested' ? !!s.recommended : true,
    )
    .sort((a, b) => {
      const delta = (ranks[b.source_id] ?? 0) - (ranks[a.source_id] ?? 0);
      if (delta !== 0) return delta;
      return (order.get(a.source_id) ?? 0) - (order.get(b.source_id) ?? 0);
    });

  return (
    <div className="stack">
      {interpretation && (
        <div
          className="surface"
          style={{
            marginBottom: 0,
            display: 'flex',
            gap: 14,
            background: 'linear-gradient(135deg, #f5f3ff 0%, #eef2ff 100%)',
            borderColor: '#e0e7ff',
          }}
        >
          <span
            aria-hidden
            style={{
              width: 36,
              height: 36,
              flexShrink: 0,
              borderRadius: 10,
              display: 'grid',
              placeItems: 'center',
              background: 'var(--gradient)',
              color: '#fff',
            }}
          >
            <Lightbulb20Regular />
          </span>
          <div>
            <div style={{ fontWeight: 650, marginBottom: 4 }}>How ImpactPilot read your idea</div>
            <p className="muted" style={{ color: 'var(--text-2)' }}>
              {interpretation} If that is off, go back and adjust the description.
            </p>
          </div>
        </div>
      )}

      {!llmUsed && (
        <MessageBar intent="warning">
          <MessageBarBody>
            The model was unavailable, so these are plain keyword-search results. Rank them carefully.
          </MessageBarBody>
        </MessageBar>
      )}
      {warnings.length > 0 && (
        <MessageBar intent="warning">
          <MessageBarBody>
            {warnings.map((w, i) => (
              <div key={i}>{w}</div>
            ))}
          </MessageBarBody>
        </MessageBar>
      )}

      {sources.length === 0 ? (
        <EmptyState
          title="No candidate papers found"
          description="Try broadening the description, or go back and adjust the idea."
        />
      ) : (
        <>
          <div className="surface" style={{ marginBottom: 0, padding: 16 }}>
            <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
              <div className="row gap-8">
                <CountChip label="high" value={counts.high} color="var(--rank-high)" />
                <CountChip label="medium" value={counts.medium} color="var(--rank-medium)" />
                <CountChip label="low" value={counts.low} color="var(--rank-low)" />
                <CountChip label="off" value={counts.off} color="var(--rank-off)" />
              </div>
              <div className="row gap-8">
                <Button size="small" appearance="subtle" icon={<Sparkle16Filled />} onClick={onRankRecommended}>
                  Suggested → High ({recommendedCount})
                </Button>
                <Button size="small" appearance="subtle" onClick={() => onRankAll(2)}>
                  All → Medium
                </Button>
                <Button size="small" appearance="subtle" onClick={onClear}>
                  Clear
                </Button>
              </div>
            </div>
            <div className="divider" style={{ margin: '14px 0' }} />
            <div className="row" style={{ justifyContent: 'space-between', gap: 12 }}>
              <SegmentedControl<Filter>
                ariaLabel="Filter papers"
                size="small"
                value={filter}
                onChange={setFilter}
                options={[
                  { value: 'all', label: `All ${sources.length}` },
                  { value: 'ranked', label: `Ranked ${rankedCount}` },
                  { value: 'suggested', label: `Suggested ${recommendedCount}` },
                ]}
              />
              <span className="muted" style={{ fontSize: 13 }}>
                <b>High</b> drives the estimates · <b>Medium</b> supports · <b>Low</b> is context · <b>Off</b> is excluded
              </span>
            </div>
          </div>

          {shown.length === 0 && (
            <p className="muted" style={{ textAlign: 'center', padding: 24 }}>
              No papers match this filter.
            </p>
          )}

          {shown.map((s) => {
            const rank = ranks[s.source_id] ?? 0;
            const meta = [s.venue, s.year, s.type].filter(Boolean).join(' · ');
            return (
              <article
                key={s.source_id}
                className="surface"
                style={{
                  marginBottom: 0,
                  padding: 20,
                  borderLeft: `4px solid ${RANK_COLOR[rank]}`,
                  opacity: rank === 0 ? 0.78 : 1,
                  transition: 'opacity 150ms ease, border-color 150ms ease',
                }}
              >
                <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
                  <div style={{ minWidth: 0, flex: '1 1 380px' }}>
                    <div className="row gap-8" style={{ marginBottom: 6 }}>
                      <span className="pill" style={{ padding: '2px 8px', fontSize: 11 }}>
                        {sourceLabel(s.database)}
                      </span>
                      {s.recommended ? (
                        <span className="pill pill-accent" style={{ padding: '2px 8px', fontSize: 11 }}>
                          <Sparkle16Filled /> Suggested
                        </span>
                      ) : llmUsed ? (
                        <span className="pill" style={{ padding: '2px 8px', fontSize: 11 }}>
                          Possibly off-topic
                        </span>
                      ) : null}
                      {meta && <span className="muted" style={{ fontSize: 12 }}>{meta}</span>}
                    </div>
                    <h3 style={{ margin: 0, fontSize: 15, fontWeight: 650, lineHeight: 1.4 }}>
                      {s.url ? (
                        <FluentLink href={s.url} target="_blank" rel="noreferrer" style={{ color: 'var(--text)' }}>
                          {s.title} <Open16Regular style={{ verticalAlign: 'middle', color: 'var(--text-3)' }} />
                        </FluentLink>
                      ) : (
                        s.title
                      )}
                    </h3>
                  </div>
                  <SegmentedControl<RelevanceRank>
                    ariaLabel={`Relevance for ${s.title}`}
                    size="small"
                    value={rank}
                    onChange={(v) => onRank(s.source_id, v)}
                    options={RANK_OPTIONS}
                  />
                </div>
                {s.note && (
                  <p
                    style={{
                      margin: '10px 0 0',
                      fontSize: 13,
                      fontWeight: 500,
                      color: s.recommended ? 'var(--accent)' : 'var(--text-2)',
                    }}
                  >
                    {s.note}
                  </p>
                )}
                {s.abstract && (
                  <p className="muted" style={{ marginTop: 8, fontSize: 13 }}>
                    {snippet(s.abstract)}
                  </p>
                )}
              </article>
            );
          })}
        </>
      )}
    </div>
  );
}
