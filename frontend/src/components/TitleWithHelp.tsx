import { Button, Popover, PopoverSurface, PopoverTrigger, Text } from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import type { ReactNode } from 'react';

interface TitleWithHelpProps {
  title: string;
  help: ReactNode;
}

export function TitleWithHelp({ title, help }: TitleWithHelpProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
      <Text weight="semibold">{title}</Text>
      <Popover withArrow>
        <PopoverTrigger disableButtonEnhancement>
          <Button appearance="subtle" icon={<Info16Regular />} size="small" aria-label={`Help: ${title}`} />
        </PopoverTrigger>
        <PopoverSurface style={{ maxWidth: 360 }}>{help}</PopoverSurface>
      </Popover>
    </div>
  );
}
