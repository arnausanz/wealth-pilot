interface HeroValueProps {
  total: number;
  changeEur: number;
  changePct: number;
  period: string;
}

function periodLabel(period: string): string {
  switch (period) {
    case '1M': return 'últim mes';
    case '3M': return 'últims 3 mesos';
    case '6M': return 'últims 6 mesos';
    case '1A': return 'últim any';
    case 'Tot': return 'total';
    default: return 'període';
  }
}

export function HeroValue({ total, changeEur, changePct, period }: HeroValueProps) {
  const isPositive = changeEur >= 0;
  const changeColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
  const arrow = isPositive ? '▲' : '▼';

  return (
    <div style={{ padding: '24px 24px 0' }}>
      <div
        style={{
          fontSize: 11,
          fontFamily: 'var(--font-num)',
          letterSpacing: '0.06em',
          color: 'var(--color-text-tertiary)',
          textTransform: 'uppercase',
          marginBottom: 6,
        }}
      >
        Patrimoni total
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span
          style={{
            fontSize: 38,
            fontWeight: 300,
            letterSpacing: '-0.03em',
            fontFamily: 'var(--font-num)',
            color: 'var(--color-text)',
          }}
        >
          €{total.toLocaleString('ca-ES')}
        </span>
      </div>
      <div
        style={{
          display: 'flex',
          gap: 12,
          marginTop: 6,
          alignItems: 'center',
        }}
      >
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 13,
            fontWeight: 500,
            color: changeColor,
            fontFamily: 'var(--font-num)',
          }}
        >
          {arrow} €{Math.abs(changeEur).toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          <span style={{ opacity: 0.7 }}>
            ({isPositive ? '+' : ''}{changePct.toFixed(2)}%)
          </span>
        </span>
        <span
          style={{
            fontSize: 11,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-body)',
          }}
        >
          {periodLabel(period)}
        </span>
      </div>
    </div>
  );
}
