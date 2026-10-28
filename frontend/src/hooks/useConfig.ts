import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { AppConfig } from '../types/initiative';

/** YAML files are wrapped objects (`focus_areas: { focus_areas: [...] }`). Flatten them for the UI. */
export function normalizeConfig(raw: AppConfig): AppConfig {
  const unwrap = <T,>(value: unknown, key: string): T[] => {
    if (Array.isArray(value)) return value as T[];
    if (value && typeof value === 'object') {
      const nested = (value as Record<string, unknown>)[key];
      if (Array.isArray(nested)) return nested as T[];
    }
    return [];
  };

  return {
    ...raw,
    focus_areas: unwrap(raw.focus_areas, 'focus_areas'),
    dimensions: unwrap(raw.dimensions, 'dimensions'),
    value_chain: raw.value_chain ?? { phases: [] },
  };
}

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const { data } = await api.get<AppConfig>('/config');
      return normalizeConfig(data);
    },
    staleTime: 60_000,
  });
}
