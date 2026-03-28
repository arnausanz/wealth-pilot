import { useMemo } from 'react';
import { TimeSelector } from '../../components/ui/TimeSelector';
import { PortfolioChart } from '../../components/charts/PortfolioChart';
import { Card } from '../../components/ui/Card';
import { n } from '../../types';
import type { NetWorthSnapshot } from '../../types';

interface ChartSectionProps {
  snapshots: NetWorthSnapshot[];
  period: string;
  onPeriodChange: (p: string) => void;
}

function getPeriodLabel(period: string): string {
  switch (period) {
    case '1M': return 'Últim mes';
    case '3M': return 'Últims 3 mesos';
    case '6M': return 'Últims 6 mesos';
    case '1A': return 'Últim any';
    case 'Tot': return 'Inici – Ara';
    default: return 'Període personalitzat';
  }
}

export function ChartSection({ snapshots, period, onPeriodChange }: ChartSectionProps) {
  const chartData = useMemo(() => {
    return snapshots.map((s) => n(s.total_net_worth));
  }, [snapshots]);

  const { changeEur, changePct } = useMemo(() => {
    if (snapshots.length < 2) return { changeEur: 0, changePct: 0 };
    const first = n(snapshots[0].total_net_worth);
    const last = n(snapshots[snapshots.length - 1].total_net_worth);
    const eur = last - first;
    const pct = first !== 0 ? (eur / first) * 100 : 0;
    return { changeEur: eur, changePct: pct };
  }, [snapshots]);

  const isPositive = changeEur >= 0;
  const changeColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';

  return (
    <div style={{ padding: '20px 24px 0' }}>
      <TimeSelector value={period} onChange={onPeriodChange} />

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: 12,
          marginBottom: 8,
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: 'var(--color-text-secondary)',
            fontFamily: 'var(--font-num)',
          }}
        >
          {getPeriodLabel(period)}
        </span>
        {snapshots.length >= 2 && (
          <span
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: changeColor,
              fontFamily: 'var(--font-num)',
            }}
          >
            {isPositive ? '+' : ''}€{Math.abs(changeEur).toLocaleString('ca-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ({isPositive ? '+' : ''}{changePct.toFixed(1)}%)
          </span>
        )}
      </div>

      <Card padding={0} style={{ padding: '16px 12px 8px' }}>
        {chartData.length > 0 ? (
          <PortfolioChart data={chartData} />
        ) : (
          <div
            style={{
              height: 160,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-text-tertiary)',
              fontSize: 12,
              fontFamily: 'var(--font-num)',
            }}
          >
            Sense dades per al període seleccionat
          </div>
        )}
      </Card>
    </div>
  );
}
