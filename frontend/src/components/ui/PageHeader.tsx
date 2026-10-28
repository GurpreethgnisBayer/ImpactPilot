import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: ReactNode;
  subtitle?: ReactNode;
  eyebrow?: string;
  actions?: ReactNode;
  meta?: ReactNode;
}

export function PageHeader({ title, subtitle, eyebrow, actions, meta }: PageHeaderProps) {
  return (
    <header
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        gap: 24,
        flexWrap: 'wrap',
        marginBottom: 28,
      }}
    >
      <div style={{ minWidth: 0, flex: '1 1 420px' }}>
        {eyebrow && <div className="eyebrow" style={{ marginBottom: 8 }}>{eyebrow}</div>}
        <h1 className="page-title">{title}</h1>
        {subtitle && (
          <p className="muted" style={{ marginTop: 8, fontSize: 15, maxWidth: 680 }}>
            {subtitle}
          </p>
        )}
        {meta && <div className="row gap-8" style={{ marginTop: 12 }}>{meta}</div>}
      </div>
      {actions && <div className="row gap-8">{actions}</div>}
    </header>
  );
}
