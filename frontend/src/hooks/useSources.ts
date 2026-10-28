import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { SourceInfo } from '../lib/sources';

export function useSources() {
  return useQuery({
    queryKey: ['compendium-sources'],
    queryFn: async () => {
      const { data } = await api.get<SourceInfo[]>('/compendium/sources');
      return data;
    },
    staleTime: 5 * 60_000,
  });
}
