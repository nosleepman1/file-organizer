import * as React from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  sizeVariant?: 'sm' | 'md';
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, sizeVariant = 'md', ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(sizeVariant === 'sm' ? 'form-control-sm' : 'form-control', className)}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';
