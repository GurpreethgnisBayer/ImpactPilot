import { FluentProvider } from '@fluentui/react-components';
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './components/ToastProvider';
import { queryClient } from './lib/queryClient';
import { AppLayout } from './layouts/AppLayout';
import { HelpPage } from './pages/HelpPage';
import { InitiativeDetail } from './pages/InitiativeDetail';
import { InitiativesList } from './pages/InitiativesList';
import { IntakeWizard } from './pages/IntakeWizard';
import { PortfolioPage } from './pages/PortfolioPage';
import { QuickBrief } from './pages/QuickBrief';
import { SettingsPage } from './pages/SettingsPage';
import { appTheme } from './theme';

export default function App() {
  return (
    <FluentProvider theme={appTheme}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ErrorBoundary>
            <BrowserRouter>
              <Routes>
                <Route element={<AppLayout />}>
                  <Route index element={<QuickBrief />} />
                  <Route path="initiatives" element={<InitiativesList />} />
                  <Route path="initiatives/new/wizard" element={<IntakeWizard />} />
                  <Route path="initiatives/:id" element={<InitiativeDetail />} />
                  <Route path="portfolio" element={<PortfolioPage />} />
                  <Route path="settings" element={<SettingsPage />} />
                  <Route path="help" element={<HelpPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </ErrorBoundary>
        </ToastProvider>
      </QueryClientProvider>
    </FluentProvider>
  );
}
