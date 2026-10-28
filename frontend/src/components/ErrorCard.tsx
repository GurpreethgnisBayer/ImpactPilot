import { Button, Text } from '@fluentui/react-components';
import { DismissCircle24Regular } from '@fluentui/react-icons';

interface ErrorCardProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorCard({ title = 'Error', message, onRetry }: ErrorCardProps) {
  return (
    <div className="card" role="alert">
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <DismissCircle24Regular color="#c50f1f" />
        <div style={{ flex: 1 }}>
          <Text weight="semibold" block>
            {title}
          </Text>
          <Text block style={{ marginTop: 4 }}>
            {message}
          </Text>
          {onRetry ? (
            <Button appearance="secondary" size="small" style={{ marginTop: 12 }} onClick={onRetry}>
              Try again
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
