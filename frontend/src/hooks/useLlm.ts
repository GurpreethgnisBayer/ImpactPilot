import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import api from '../lib/api';
import { describeLlm, LLM_CHANGED_EVENT, type PlatformLlm, savedLlmSettings } from '../lib/llmSettings';
import type { LlmSettings } from '../types/initiative';

export function usePlatformLlm() {
  return useQuery({
    queryKey: ['llm-platform'],
    queryFn: async () => (await api.get<PlatformLlm>('/llm/settings')).data,
    staleTime: 5 * 60_000,
  });
}

/** Browser model override plus platform defaults; re-reads when Settings changes the override. */
export function useActiveLlm() {
  const platform = usePlatformLlm();
  const [override, setOverride] = useState<LlmSettings | null>(() => savedLlmSettings());

  useEffect(() => {
    const sync = () => setOverride(savedLlmSettings());
    window.addEventListener(LLM_CHANGED_EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(LLM_CHANGED_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  return {
    override,
    platform: platform.data,
    label: describeLlm(override, platform.data),
    ready: !!platform.data?.has_api_key,
  };
}
