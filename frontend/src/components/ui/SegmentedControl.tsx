import { useRef, type KeyboardEvent } from 'react';

export interface SegmentOption<T extends string | number> {
  value: T;
  label: string;
  /** Dot colour shown when the option is selected. */
  color?: string;
}

interface SegmentedControlProps<T extends string | number> {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
  size?: 'small' | 'medium';
}

/** Radio-group semantics: arrow keys move the selection, one tab stop for the whole control. */
export function SegmentedControl<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
  size = 'medium',
}: SegmentedControlProps<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const index = Math.max(0, options.findIndex((o) => o.value === value));

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const delta = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
    if (!delta) return;
    e.preventDefault();
    const next = (index + delta + options.length) % options.length;
    onChange(options[next].value);
    refs.current[next]?.focus();
  };

  const pad = size === 'small' ? '5px 12px' : '7px 14px';

  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      onKeyDown={onKey}
      style={{
        display: 'inline-flex',
        padding: 3,
        gap: 2,
        borderRadius: 10,
        background: '#eef1f6',
        border: '1px solid var(--line)',
      }}
    >
      {options.map((opt, i) => {
        const selected = opt.value === value;
        return (
          <button
            key={String(opt.value)}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="radio"
            aria-checked={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(opt.value)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: pad,
              border: 'none',
              borderRadius: 8,
              font: 'inherit',
              fontSize: 13,
              fontWeight: selected ? 650 : 500,
              cursor: 'pointer',
              color: selected ? 'var(--text)' : 'var(--text-3)',
              background: selected ? '#fff' : 'transparent',
              boxShadow: selected ? 'var(--shadow-sm), 0 0 0 1px var(--line)' : 'none',
              transition: 'background 120ms ease, color 120ms ease',
            }}
          >
            {opt.color && (
              <span
                aria-hidden
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 999,
                  background: selected ? opt.color : 'var(--rank-off)',
                }}
              />
            )}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
