import { createLightTheme, type BrandVariants, type Theme } from '@fluentui/react-components';

/** Indigo brand ramp. Brand anchor (80) is #4f46e5. */
export const brand: BrandVariants = {
  10: '#05041a',
  20: '#110e3a',
  30: '#1c1760',
  40: '#261f85',
  50: '#3128a8',
  60: '#3b33c6',
  70: '#453cd8',
  80: '#4f46e5',
  90: '#625aea',
  100: '#766fee',
  110: '#8a84f1',
  120: '#9f9af4',
  130: '#b4b0f7',
  140: '#c9c6fa',
  150: '#dedcfc',
  160: '#f1f0fe',
};

/** Design tokens shared by makeStyles and plain CSS (index.css mirrors these as variables). */
export const tokensX = {
  ink: '#0b1220',
  ink2: '#111a2e',
  ink3: '#1b2640',
  inkText: '#e2e8f0',
  inkMuted: '#8a96ad',
  text: '#0f172a',
  textSecondary: '#475569',
  textMuted: '#64748b',
  surface: '#ffffff',
  canvas: '#f6f7fb',
  line: '#e5e8f0',
  accent: '#4f46e5',
  accent2: '#7c3aed',
  accentSoft: '#eef0ff',
  gradient: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
  success: '#047857',
  successSoft: '#d1fae5',
  warning: '#b45309',
  warningSoft: '#fef3c7',
  danger: '#b91c1c',
  dangerSoft: '#fee2e2',
  shadowSm: '0 1px 2px rgba(15, 23, 42, 0.06)',
  shadowMd: '0 1px 2px rgba(15, 23, 42, 0.04), 0 6px 16px rgba(15, 23, 42, 0.06)',
  shadowLg: '0 2px 4px rgba(15, 23, 42, 0.04), 0 16px 40px rgba(15, 23, 42, 0.10)',
};

const fontFamily = "'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

const base = createLightTheme(brand);

export const appTheme: Theme = {
  ...base,
  fontFamilyBase: fontFamily,
  borderRadiusNone: '0',
  borderRadiusSmall: '6px',
  borderRadiusMedium: '10px',
  borderRadiusLarge: '12px',
  borderRadiusXLarge: '16px',
  borderRadiusCircular: '9999px',
  colorNeutralBackground2: tokensX.canvas,
  colorNeutralForeground1: tokensX.text,
  colorNeutralForeground2: tokensX.textSecondary,
  colorNeutralForeground3: tokensX.textMuted,
  colorNeutralStroke1: '#d7dbe6',
  colorNeutralStroke2: tokensX.line,
  colorStrokeFocus2: tokensX.accent,
};
