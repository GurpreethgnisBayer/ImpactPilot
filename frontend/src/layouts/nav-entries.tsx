import {
  Book24Regular,
  Folder24Regular,
  Grid24Regular,
  Settings24Regular,
  Sparkle24Regular,
} from '@fluentui/react-icons';
import type { ReactElement } from 'react';

export interface NavEntry {
  to: string;
  label: string;
  icon: ReactElement;
}

export const navEntries: NavEntry[] = [
  { to: '/', label: 'Quick brief', icon: <Sparkle24Regular /> },
  { to: '/initiatives', label: 'Initiatives', icon: <Folder24Regular /> },
  { to: '/portfolio', label: 'Portfolio', icon: <Grid24Regular /> },
  { to: '/settings', label: 'Settings', icon: <Settings24Regular /> },
  { to: '/help', label: 'Help', icon: <Book24Regular /> },
];
