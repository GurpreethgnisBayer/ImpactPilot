import { Button, type ButtonProps } from '@fluentui/react-components';

/** Gradient call-to-action. Use once per view for the main next step. */
export function PrimaryButton({ className, size = 'large', ...props }: ButtonProps) {
  return <Button {...props} size={size} appearance="primary" className={`btn-primary ${className ?? ''}`} />;
}
