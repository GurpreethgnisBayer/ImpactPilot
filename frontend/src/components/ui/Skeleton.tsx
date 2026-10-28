import type { CSSProperties } from 'react';

export function Skeleton({ width = '100%', height = 14, style }: { width?: number | string; height?: number; style?: CSSProperties }) {
  return <div className="skeleton" aria-hidden style={{ width, height, ...style }} />;
}

/** Placeholder card list shown while papers or a brief are loading. */
export function SkeletonCards({ count = 3, label }: { count?: number; label: string }) {
  return (
    <div role="status" aria-live="polite" className="stack">
      <span className="muted" style={{ fontWeight: 500 }}>{label}</span>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="surface" style={{ marginBottom: 0 }}>
          <Skeleton width="62%" height={16} />
          <Skeleton width="30%" height={12} style={{ marginTop: 10 }} />
          <Skeleton height={12} style={{ marginTop: 16 }} />
          <Skeleton width="88%" height={12} style={{ marginTop: 8 }} />
        </div>
      ))}
    </div>
  );
}
