import * as React from 'react';
import { cn } from '../../lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'category' | 'warning' | 'success' | 'info' | 'error';
}

export function Badge({ className, variant = 'category', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        variant === 'category' && 'badge-category',
        variant === 'warning' && 'badge-warning',
        variant === 'success' && 'badge-success',
        variant === 'info' && 'badge-info',
        variant === 'error' && 'badge-error',
        className
      )}
      {...props}
    />
  );
}
