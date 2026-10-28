import { makeStyles, mergeClasses } from '@fluentui/react-components';
import { Add20Regular, BrainCircuit20Regular } from '@fluentui/react-icons';
import { NavLink, useNavigate } from 'react-router-dom';
import { useActiveLlm } from '../hooks/useLlm';
import { tokensX } from '../theme';
import { navEntries } from './nav-entries';

const useStyles = makeStyles({
  root: {
    width: '248px',
    height: '100vh',
    position: 'sticky',
    top: 0,
    background: `linear-gradient(180deg, ${tokensX.ink} 0%, ${tokensX.ink2} 100%)`,
    color: tokensX.inkText,
    display: 'flex',
    flexDirection: 'column',
    flexShrink: 0,
    borderRight: '1px solid rgba(255,255,255,0.04)',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '22px 20px 18px',
  },
  mark: {
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    background: tokensX.gradient,
    display: 'grid',
    placeItems: 'center',
    color: '#fff',
    fontWeight: 800,
    fontSize: '15px',
    letterSpacing: '-0.02em',
    boxShadow: '0 6px 18px rgba(124, 58, 237, 0.45)',
  },
  brandTitle: {
    fontSize: '16px',
    fontWeight: 700,
    letterSpacing: '-0.01em',
    color: '#fff',
  },
  brandSub: {
    fontSize: '12px',
    color: tokensX.inkMuted,
    marginTop: '1px',
  },
  cta: {
    margin: '6px 16px 18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    height: '40px',
    borderRadius: '10px',
    border: 'none',
    cursor: 'pointer',
    font: 'inherit',
    fontSize: '14px',
    fontWeight: 600,
    color: '#fff',
    background: tokensX.gradient,
    boxShadow: '0 6px 18px rgba(124, 58, 237, 0.35)',
    transitionProperty: 'filter, transform',
    transitionDuration: '120ms',
    ':hover': { filter: 'brightness(1.08)', transform: 'translateY(-1px)' },
    ':focus-visible': { outline: '2px solid #a5b4fc', outlineOffset: '2px' },
  },
  section: {
    padding: '0 20px 8px',
    fontSize: '11px',
    fontWeight: 600,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: tokensX.inkMuted,
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
    padding: '0 12px',
    gap: '2px',
  },
  link: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '9px 12px',
    borderRadius: '8px',
    color: '#cbd5e1',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: 500,
    transitionProperty: 'background-color, color',
    transitionDuration: '120ms',
    ':hover': { backgroundColor: 'rgba(255,255,255,0.06)', color: '#fff' },
    ':focus-visible': { outline: '2px solid #a5b4fc', outlineOffset: '-2px' },
    '& svg': { width: '20px', height: '20px', flexShrink: 0 },
  },
  linkActive: {
    backgroundColor: 'rgba(129, 140, 248, 0.16)',
    color: '#fff',
    fontWeight: 600,
    '::before': {
      content: '""',
      position: 'absolute',
      left: '-12px',
      top: '8px',
      bottom: '8px',
      width: '3px',
      borderRadius: '0 3px 3px 0',
      background: tokensX.gradient,
    },
    '& svg': { color: '#a5b4fc' },
  },
  footer: {
    marginTop: 'auto',
    padding: '14px 16px 18px',
  },
  modelCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 12px',
    borderRadius: '10px',
    backgroundColor: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.06)',
    color: tokensX.inkText,
    textDecoration: 'none',
    ':hover': { backgroundColor: 'rgba(255,255,255,0.07)' },
  },
  modelLabel: { fontSize: '11px', color: tokensX.inkMuted },
  modelName: {
    fontSize: '13px',
    fontWeight: 600,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: '150px',
  },
  dot: { width: '8px', height: '8px', borderRadius: '999px', flexShrink: 0, marginLeft: 'auto' },
});

export function Sidebar() {
  const styles = useStyles();
  const navigate = useNavigate();
  const llm = useActiveLlm();

  return (
    <aside className={styles.root} aria-label="Main navigation">
      <div className={styles.brand}>
        <div className={styles.mark} aria-hidden>
          IP
        </div>
        <div>
          <div className={styles.brandTitle}>ImpactPilot</div>
          <div className={styles.brandSub}>Evidence-backed impact briefs</div>
        </div>
      </div>

      <button type="button" className={styles.cta} onClick={() => navigate('/', { state: { reset: Date.now() } })}>
        <Add20Regular /> New brief
      </button>

      <div className={styles.section}>Workspace</div>
      <nav className={styles.nav}>
        {navEntries.map((entry) => (
          <NavLink
            key={entry.to}
            to={entry.to}
            end={entry.to === '/'}
            className={({ isActive }) => mergeClasses(styles.link, isActive && styles.linkActive)}
          >
            {entry.icon}
            {entry.label}
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <NavLink to="/settings" className={styles.modelCard} title="Change model in Settings">
          <BrainCircuit20Regular style={{ color: '#a5b4fc', flexShrink: 0 }} />
          <div style={{ minWidth: 0 }}>
            <div className={styles.modelLabel}>Model</div>
            <div className={styles.modelName}>{llm.label}</div>
          </div>
          <span
            className={styles.dot}
            style={{ background: llm.ready ? '#34d399' : '#f59e0b' }}
            aria-label={llm.ready ? 'Connected' : 'Not configured'}
          />
        </NavLink>
      </div>
    </aside>
  );
}
