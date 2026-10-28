import { Checkmark16Filled } from '@fluentui/react-icons';

export interface StepDef {
  id: string;
  label: string;
  hint?: string;
}

interface StepperProps {
  steps: StepDef[];
  current: string;
  /** Lets users jump back to a completed step. */
  onStepClick?: (id: string) => void;
}

export function Stepper({ steps, current, onStepClick }: StepperProps) {
  const currentIndex = steps.findIndex((s) => s.id === current);
  return (
    <nav aria-label="Progress" style={{ marginBottom: 28 }}>
      <ol
        style={{
          listStyle: 'none',
          margin: 0,
          padding: 6,
          display: 'grid',
          gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))`,
          gap: 6,
          background: 'var(--surface)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        {steps.map((step, i) => {
          const done = i < currentIndex;
          const active = i === currentIndex;
          const clickable = done && !!onStepClick;
          return (
            <li key={step.id}>
              <button
                type="button"
                disabled={!clickable}
                aria-current={active ? 'step' : undefined}
                onClick={() => clickable && onStepClick?.(step.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 14px',
                  border: 'none',
                  borderRadius: 12,
                  textAlign: 'left',
                  font: 'inherit',
                  cursor: clickable ? 'pointer' : 'default',
                  background: active ? 'var(--accent-soft)' : 'transparent',
                  color: 'var(--text)',
                }}
              >
                <span
                  aria-hidden
                  style={{
                    flexShrink: 0,
                    width: 28,
                    height: 28,
                    borderRadius: 999,
                    display: 'grid',
                    placeItems: 'center',
                    fontSize: 13,
                    fontWeight: 700,
                    color: done || active ? '#fff' : 'var(--text-3)',
                    background: done ? 'var(--success)' : active ? 'var(--gradient)' : '#eef1f6',
                  }}
                >
                  {done ? <Checkmark16Filled /> : i + 1}
                </span>
                <span style={{ minWidth: 0 }}>
                  <span style={{ display: 'block', fontWeight: 600, fontSize: 14, color: active ? 'var(--accent)' : undefined }}>
                    {step.label}
                  </span>
                  {step.hint && (
                    <span style={{ display: 'block', fontSize: 12, color: 'var(--text-3)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {step.hint}
                    </span>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
