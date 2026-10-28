import { describe, expect, it } from 'vitest';
import { normalizeConfig } from '../hooks/useConfig';

describe('normalizeConfig', () => {
  it('unwraps YAML documents so focus areas are an array', () => {
    const cfg = normalizeConfig({
      focus_areas: {
        focus_areas: [{ code: 'FA1', label: 'Focus Area 1' }],
      } as never,
      dimensions: {
        dimensions: [{ id: 'cycle_time', label: 'Cycle time' }],
      } as never,
      value_chain: { phases: [{ id: 'clinical', label: 'Clinical' }] },
    });
    expect(Array.isArray(cfg.focus_areas)).toBe(true);
    expect(cfg.focus_areas?.[0]?.code).toBe('FA1');
    expect(cfg.dimensions?.[0]?.id).toBe('cycle_time');
  });
});
