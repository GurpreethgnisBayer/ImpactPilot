import helpText from '../content/help/overview.md?raw';
import { PageHeader } from '../components/ui/PageHeader';

export function HelpPage() {
  const lines = helpText.split('\n');
  return (
    <div className="page page-narrow">
      <PageHeader eyebrow="Guide" title="Help" subtitle="How ImpactPilot turns an idea into a cited, range-based impact brief." />
      <article className="surface" style={{ fontSize: 15, lineHeight: 1.65 }}>
        {lines.map((line, i) => {
          if (line.startsWith('# ')) {
            return (
              <h2 key={i} className="surface-title" style={{ fontSize: 20, marginTop: i ? 24 : 0 }}>
                {line.slice(2)}
              </h2>
            );
          }
          if (line.startsWith('## ')) {
            return (
              <h3 key={i} style={{ fontSize: 16, fontWeight: 650, margin: '18px 0 6px' }}>
                {line.slice(3)}
              </h3>
            );
          }
          if (line.startsWith('- ')) {
            return (
              <div key={i} style={{ display: 'flex', gap: 10, marginLeft: 4 }}>
                <span aria-hidden style={{ color: 'var(--accent)', fontWeight: 700 }}>•</span>
                <span style={{ color: 'var(--text-2)' }}>{line.slice(2)}</span>
              </div>
            );
          }
          if (!line.trim()) return <div key={i} style={{ height: 8 }} />;
          return (
            <p key={i} style={{ margin: 0, color: 'var(--text-2)' }}>
              {line}
            </p>
          );
        })}
      </article>
    </div>
  );
}
