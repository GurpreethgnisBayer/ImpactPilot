import { Button, Dropdown, Field, Option, Spinner, Text } from '@fluentui/react-components';
import {
  ArrowCounterclockwise20Regular,
  CheckmarkCircle20Filled,
  PlugConnected20Regular,
  ShieldLock20Regular,
} from '@fluentui/react-icons';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { PageHeader } from '../components/ui/PageHeader';
import { useToast } from '../components/ToastProvider';
import api from '../lib/api';
import { apiErrorMessage } from '../lib/apiError';
import { clearLlmSettings, type PlatformLlm, saveModelOverride, savedLlmSettings } from '../lib/llmSettings';
import type { LlmSettings } from '../types/initiative';

interface ModelRow {
  id: string;
  model?: string;
}

export function SettingsPage() {
  const { showToast } = useToast();
  const platform = useQuery({
    queryKey: ['llm-platform'],
    queryFn: async () => (await api.get<PlatformLlm>('/llm/settings')).data,
  });
  const models = useQuery({
    queryKey: ['llm-models'],
    queryFn: async () =>
      (await api.post<{ ok: boolean; message: string; models?: ModelRow[] }>('/llm/models', {})).data,
    staleTime: 5 * 60_000,
  });
  const [override, setOverride] = useState<LlmSettings | null>(() => savedLlmSettings());
  const [testing, setTesting] = useState(false);

  const server = platform.data;
  const activeModel = override?.openai_model || server?.openai_model || '';
  const rows = models.data?.models ?? [];
  const options = activeModel && !rows.some((m) => m.id === activeModel) ? [{ id: activeModel }, ...rows] : rows;

  const choose = (model: string) => {
    if (!model || model === server?.openai_model) {
      clearLlmSettings();
      setOverride(null);
      showToast({ title: 'Using the platform default model', intent: 'success' });
      return;
    }
    setOverride(saveModelOverride(model));
    showToast({ title: 'Model updated', body: `Briefs will use ${model}`, intent: 'success' });
  };

  const test = async () => {
    setTesting(true);
    try {
      const { data } = await api.post<{ ok: boolean; message: string }>('/llm/test', override ?? {});
      showToast({
        title: data.ok ? 'Connection OK' : 'Connection failed',
        body: data.message,
        intent: data.ok ? 'success' : 'warning',
      });
    } catch (e) {
      showToast({ title: 'Test failed', body: apiErrorMessage(e), intent: 'error' });
    } finally {
      setTesting(false);
    }
  };

  const modelLabel = (row: ModelRow) => (row.model && row.model !== row.id ? `${row.id} · ${row.model}` : row.id);

  return (
    <div className="page page-narrow">
      <PageHeader
        eyebrow="Workspace"
        title="Settings"
        subtitle="ImpactPilot uses the platform's OpenAI endpoint. You can choose which deployed model writes your briefs."
      />

      <section className="surface">
        <div className="surface-head">
          <div>
            <h2 className="surface-title">Language model</h2>
            <p className="muted">Configured on the server. The API key never reaches the browser.</p>
          </div>
          {server?.has_api_key ? (
            <span className="pill pill-success">
              <CheckmarkCircle20Filled /> Connected
            </span>
          ) : (
            <span className="pill pill-warning">Not configured</span>
          )}
        </div>

        {platform.isLoading ? (
          <Spinner size="small" label="Loading platform settings…" />
        ) : (
          <dl className="kv-grid">
            <dt>Endpoint</dt>
            <dd className="mono">{server?.openai_base_url || 'Not configured'}</dd>
            <dt>Platform model</dt>
            <dd>{server?.openai_model || 'Not configured'}</dd>
            <dt>API key</dt>
            <dd>
              <ShieldLock20Regular style={{ verticalAlign: 'middle', marginRight: 4 }} />
              {server?.has_api_key ? 'Stored on the server' : 'Missing'}
            </dd>
          </dl>
        )}

        <div className="divider" />

        <Field
          label="Model used for briefs"
          hint={override ? 'You picked this model in this browser.' : 'Using the platform default.'}
        >
          <Dropdown
            placeholder={models.isLoading ? 'Loading deployed models…' : 'Select a model'}
            selectedOptions={activeModel ? [activeModel] : []}
            value={activeModel}
            onOptionSelect={(_, d) => choose(d.optionValue ?? '')}
          >
            {options.map((m) => (
              <Option key={m.id} value={m.id} text={modelLabel(m)}>
                {modelLabel(m)}
                {m.id === server?.openai_model ? ' (platform default)' : ''}
              </Option>
            ))}
          </Dropdown>
        </Field>
        {models.data && !models.data.ok && (
          <Text size={200} className="muted">
            Could not list models: {models.data.message}
          </Text>
        )}

        <div className="row gap-8" style={{ marginTop: 16 }}>
          <Button appearance="secondary" icon={<PlugConnected20Regular />} onClick={() => void test()} disabled={testing}>
            {testing ? 'Testing…' : 'Test connection'}
          </Button>
          {override && (
            <Button appearance="subtle" icon={<ArrowCounterclockwise20Regular />} onClick={() => choose('')}>
              Reset to platform default
            </Button>
          )}
        </div>
      </section>
    </div>
  );
}
