import type { CSSProperties, ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  padding?: number;
}

export function Card({ children, className, style, padding = 14 }: CardProps) {
  return (
    <div
      className={className}
      style={{
        background: 'var(--color-glass-bg)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid var(--color-glass-border)',
        borderRadius: 16,
        padding,
        boxShadow: 'var(--card-shadow)',
        ...style,
      }}
    >
      {children}
    </div>
  );
}
