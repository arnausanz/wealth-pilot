import { useMemo } from 'react';
import { Card } from '../../components/ui/Card';
import { useConfigAssets } from '../../hooks/useConfig';
import { n } from '../../types';
import type { NetWorthSnapshot } from '../../types';

interface StatusCardsProps {
  netWorth: number;
  goalAmount: number;
  goalYear: number;
  goalLabel: string;
  lastSnapshot?: NetWorthSnapshot | null;
}

interface DeviationRow {
  id: number | string;
  name: string;
  color: string;
  actual: number;
  target: number;
  diff: number;
}

function deviationColor(diff: number): string {
  const abs = Math.abs(diff);
  if (abs <= 2) return 'var(--color-positive)';
  if (abs <= 5) return 'var(--color-warning)';
  return 'var(--color-negative)';
}

export function StatusCards({ netWorth, goalAmount, goalYear, goalLabel, lastSnapshot }: StatusCardsProps) {
  const { data: configAssets = [] } = useConfigAssets();

  const goalPct = goalAmount > 0 ? Math.min((netWorth / goalAmount) * 100, 100) : 0;
  const remaining = Math.max(goalAmount - netWorth, 0);

  // Llista de desviacions: pes actual vs pes objectiu per cada asset
  const deviations = useMemo((): DeviationRow[] => {
    if (!lastSnapshot || netWorth <= 0) return [];

    const rows: DeviationRow[] = [];

    for (const snap of lastSnapshot.asset_snapshots ?? []) {
      const config = configAssets.find((a) => a.id === snap.asset_id);
      if (!config || config.target_weight == null) continue;
      const actual = n(snap.weight_actual_pct);
      const target = n(config.target_weight);
      rows.push({
        id: snap.asset_id,
        name: snap.display_name,
        color: snap.color_hex ?? '#94A3B8',
        actual,
        target,
        diff: actual - target,
      });
    }

    // Efectiu: calculat des dels valors del snapshot
    const cashConfig = configAssets.find((a) => !a.ticker_yf);
    if (cashConfig && cashConfig.target_weight != null) {
      const cashActual = (n(lastSnapshot.cash_and_bank_value) / netWorth) * 100;
      const cashTarget = n(cashConfig.target_weight);
      rows.push({
        id: 'cash',
        name: 'Efectiu',
        color: '#95A5A6',
        actual: cashActual,
        target: cashTarget,
        diff: cashActual - cashTarget,
      });
    }

    // Ordenats per desviació absoluta (major desviació primer)
    return rows.sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));
  }, [lastSnapshot, configAssets, netWorth]);

  return (
    <div style={{ padding: '20px 24px 0' }}>

      {/* ── Card d'objectiu — amplada completa ── */}
      <Card style={{ marginBottom: 10 }}>
        {/* Capçalera: label + any */}
        <div
          style={{
            fontSize: 10,
            fontFamily: 'var(--font-num)',
            letterSpacing: '0.06em',
            color: 'var(--color-text-tertiary)',
            textTransform: 'uppercase',
            marginBottom: 10,
          }}
        >
          {goalLabel} · {goalYear}
        </div>

        {/* Import actual vs objectiu */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
          <span
            style={{
              fontSize: 26,
              fontWeight: 700,
              fontFamily: 'var(--font-num)',
              letterSpacing: '-0.02em',
              color: 'var(--color-text)',
              lineHeight: 1,
            }}
          >
            €{(netWorth / 1000).toFixed(1)}k
          </span>
          <span
            style={{
              fontSize: 13,
              color: 'var(--color-text-tertiary)',
              fontFamily: 'var(--font-num)',
            }}
          >
            de €{(goalAmount / 1000).toFixed(0)}k
          </span>
        </div>

        {/* Barra de progrés */}
        <div
          style={{
            height: 6,
            borderRadius: 3,
            background: 'var(--color-border)',
            overflow: 'hidden',
            marginBottom: 8,
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${goalPct}%`,
              background: 'var(--color-accent)',
              borderRadius: 3,
              transition: 'width 1s ease',
            }}
          />
        </div>

        {/* % assolit + Falten */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span
            style={{
              fontSize: 13,
              fontFamily: 'var(--font-num)',
              fontWeight: 600,
              color: 'var(--color-accent)',
            }}
          >
            {goalPct.toFixed(1)}% assolit
          </span>
          {remaining > 0 && (
            <span
              style={{
                fontSize: 11,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text-tertiary)',
              }}
            >
              Falten €{remaining.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
            </span>
          )}
        </div>
      </Card>

      {/* ── Llista de desviació de pesos ── */}
      {deviations.length > 0 && (
        <Card>
          <div
            style={{
              fontSize: 10,
              fontFamily: 'var(--font-num)',
              letterSpacing: '0.06em',
              color: 'var(--color-text-tertiary)',
              textTransform: 'uppercase',
              marginBottom: 10,
            }}
          >
            Pesos objectiu
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {deviations.map((row, i) => {
              const dColor = deviationColor(row.diff);
              const sign = row.diff >= 0 ? '+' : '';
              const isLast = i === deviations.length - 1;
              return (
                <div
                  key={row.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '9px 0',
                    borderBottom: isLast ? 'none' : '1px solid var(--color-glass-border)',
                  }}
                >
                  {/* Dot de color de l'asset */}
                  <div
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: row.color,
                      flexShrink: 0,
                    }}
                  />
                  {/* Nom */}
                  <span
                    style={{
                      flex: 1,
                      fontSize: 13,
                      color: 'var(--color-text-secondary)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {row.name}
                  </span>
                  {/* Actual / Objectiu */}
                  <span
                    style={{
                      fontSize: 12,
                      fontFamily: 'var(--font-num)',
                      color: 'var(--color-text-tertiary)',
                    }}
                  >
                    {row.actual.toFixed(1)}%
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontFamily: 'var(--font-num)',
                      color: 'var(--color-text-tertiary)',
                      margin: '0 2px',
                    }}
                  >
                    / {row.target.toFixed(0)}%
                  </span>
                  {/* Desviació */}
                  <span
                    style={{
                      fontSize: 12,
                      fontFamily: 'var(--font-num)',
                      fontWeight: 600,
                      color: dColor,
                      minWidth: 42,
                      textAlign: 'right',
                    }}
                  >
                    {sign}{row.diff.toFixed(1)}pp
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}
