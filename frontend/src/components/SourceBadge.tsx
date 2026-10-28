import { Badge } from '@fluentui/react-components';
import type { ValueSource } from '../types/initiative';

const labels: Record<ValueSource, string> = {
  evidence: 'Evidence',
  user: 'User',
  llm_suggested: 'LLM suggested',
  default: 'Default',
  config: 'Config',
};

const colors: Record<ValueSource, 'success' | 'warning' | 'informative' | 'brand' | 'important' | 'subtle'> = {
  evidence: 'success',
  user: 'brand',
  llm_suggested: 'warning',
  default: 'subtle',
  config: 'informative',
};

interface SourceBadgeProps {
  source?: ValueSource | string;
}

export function SourceBadge({ source }: SourceBadgeProps) {
  const key = (source || 'user') as ValueSource;
  const label = labels[key] ?? source ?? 'User';
  const appearance = colors[key] ?? 'subtle';
  return (
    <Badge appearance="filled" color={appearance} size="small">
      {label}
    </Badge>
  );
}
