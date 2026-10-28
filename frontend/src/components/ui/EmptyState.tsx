import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div
      className="surface"
      style={{
        textAlign: 'center',
        padding: '48px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 10,
        borderStyle: 'dashed',
        boxShadow: 'none',
      }}
    >
      {icon && (
        <span
          aria-hidden
          style={{
            width: 52,
            height: 52,
            borderRadius: 16,
            display: 'grid',
            placeItems: 'center',
            background: 'var(--accent-soft)',
            color: 'var(--accent)',
            marginBottom: 6,
          }}
        >
          {icon}
        </span>
      )}
      <div style={{ fontWeight: 650, fontSize: 17 }}>{title}</div>
      {description && <p className="muted" style={{ maxWidth: 460 }}>{description}</p>}
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </div>
  );
}
