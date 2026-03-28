type DotStatus = 'green' | 'yellow' | 'red';

interface StatusDotProps {
  status: DotStatus;
}

const STATUS_COLORS: Record<DotStatus, string> = {
  green: 'var(--color-positive)',
  yellow: 'var(--color-warning)',
  red: 'var(--color-negative)',
};

export function StatusDot({ status }: StatusDotProps) {
  const color = STATUS_COLORS[status];
  return (
    <div
      style={{
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 8px ${color}60`,
        flexShrink: 0,
      }}
    />
  );
}
