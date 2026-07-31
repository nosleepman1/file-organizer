import * as React from 'react';

export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export function Switch({ checked, onChange, ...props }: SwitchProps) {
  return (
    <label className="switch">
      <input type="checkbox" checked={checked} onChange={onChange} {...props} />
      <span className="slider round"></span>
    </label>
  );
}
