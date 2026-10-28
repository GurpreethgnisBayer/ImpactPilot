import { FluentProvider } from '@fluentui/react-components';
import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ToastProvider } from '../components/ToastProvider';
import { queryClient } from '../lib/queryClient';
import { InitiativesList } from '../pages/InitiativesList';
import { appTheme } from '../theme';

vi.mock('../hooks/useInitiatives', () => ({
  useInitiatives: () => ({ data: [], isLoading: false, isError: false, refetch: vi.fn() }),
  useCreateInitiative: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock('../hooks/useConfig', () => ({
  useConfig: () => ({ data: { focus_areas: [], value_chain: { phases: [] } } }),
}));

describe('App smoke', () => {
  it('renders initiatives heading', () => {
    render(
      <FluentProvider theme={appTheme}>
        <QueryClientProvider client={queryClient}>
          <ToastProvider>
            <MemoryRouter>
              <InitiativesList />
            </MemoryRouter>
          </ToastProvider>
        </QueryClientProvider>
      </FluentProvider>,
    );
    expect(screen.getByRole('heading', { name: /initiatives/i })).toBeInTheDocument();
  });
});
