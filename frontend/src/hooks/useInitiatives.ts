import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { InitiativeRecord, InitiativeSummary } from '../types/initiative';

export interface InitiativeFilters {
  focus_area_code?: string;
  maturity_tier?: string;
  phase_id?: string;
}

export function useInitiatives(filters: InitiativeFilters = {}) {
  return useQuery({
    queryKey: ['initiatives', filters],
    queryFn: async () => {
      const { data } = await api.get<InitiativeSummary[]>('/initiatives', { params: filters });
      return data;
    },
  });
}

export function useInitiative(id: string | undefined) {
  return useQuery({
    queryKey: ['initiative', id],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<InitiativeRecord>(`/initiatives/${id}`);
      return data;
    },
  });
}

export function useCreateInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload?: Partial<InitiativeRecord>) => {
      const { data } = await api.post<InitiativeRecord>('/initiatives', payload ?? {});
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['initiatives'] });
    },
  });
}

export function useUpdateInitiative() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, record, reason }: { id: string; record: InitiativeRecord; reason?: string }) => {
      const { data } = await api.put<InitiativeRecord>(`/initiatives/${id}`, record, {
        params: reason ? { reason } : undefined,
      });
      return data;
    },
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: ['initiatives'] });
      void qc.invalidateQueries({ queryKey: ['initiative', data.id] });
    },
  });
}

export function usePortfolioAggregations() {
  return useQuery({
    queryKey: ['portfolio', 'aggregations'],
    queryFn: async () => {
      const { data } = await api.get('/portfolio/aggregations');
      return data;
    },
  });
}
