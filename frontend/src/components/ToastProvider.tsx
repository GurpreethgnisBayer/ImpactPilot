import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  Toast,
  ToastBody,
  ToastTitle,
  Toaster,
  useId,
  useToastController,
  type ToastIntent,
} from '@fluentui/react-components';

interface ToastPayload {
  title: string;
  body?: string;
  intent?: ToastIntent;
}

interface ToastContextValue {
  showToast: (payload: ToastPayload) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const toasterId = useId('impactpilot-toaster');
  const { dispatchToast } = useToastController(toasterId);
  const [, setTick] = useState(0);

  const showToast = useCallback(
    ({ title, body, intent = 'info' }: ToastPayload) => {
      dispatchToast(
        <Toast>
          <ToastTitle>{title}</ToastTitle>
          {body ? <ToastBody>{body}</ToastBody> : null}
        </Toast>,
        { intent, timeout: 5000 },
      );
      setTick((t) => t + 1);
    },
    [dispatchToast],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <Toaster toasterId={toasterId} position="top-end" offset={{ vertical: 16, horizontal: 16 }} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
