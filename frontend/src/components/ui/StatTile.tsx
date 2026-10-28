import type { ReactNode } from 'react';

interface StatTileProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  tone?: 'default' | 'accent' | 'success' | 'warning';
}

const toneBg: Record<NonNullable<StatTileProps['tone']>, string> = {
  default: '#f1f5f9',
  accent: 'var(--accent-soft)',
  success: 'var(--success-soft)',
  warning: 'var(--warning-soft)',
};

const toneFg: Record<NonNullable<StatTileProps['tone']>, string> = {
  default: 'var(--text-2)',
  accent: 'var(--accent)',
  success: 'var(--success)',
  warning: 'var(--warning)',
};

export function StatTile({ label, value, hint, icon, tone = 'default' }: StatTileProps) {
  return (
    <div className="surface" style={{ marginBottom: 0, padding: 20, display: 'flex', gap: 14, alignItems: 'flex-start' }}>
      {icon && (
        <span
          aria-hidden
          style={{
            width: 40,
            height: 40,
            flexShrink: 0,
            borderRadius: 12,
            display: 'grid',
            placeItems: 'center',
            background: toneBg[tone],
            color: toneFg[tone],
          }}
        >
          {icon}
        </span>
      )}
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {label}
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em', marginTop: 4, color: 'var(--text)' }}>{value}</div>
        {hint && <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>{hint}</div>}
      </div>
    </div>
  );
}
