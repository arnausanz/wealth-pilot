import { useMemo } from 'react';
import { WarningIcon } from '../../components/icons/Icons';
import { n } from '../../types';
import type { NetWorthSnapshot, AssetPrice } from '../../types';

interface AlertsProps {
  snapshots: NetWorthSnapshot[];
  /** Preus de mercat — reservat per a alertes futures de variació diària */
  prices: AssetPrice[];
}

interface Alert {
  id: string;
  message: string;
  detail: string;
}

const CASH_TARGET_PCT = 28;
const DEVIATION_THRESHOLD = 5;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function Alerts({ snapshots, prices: _prices }: AlertsProps) {
  const alerts = useMemo((): Alert[] => {
    const result: Alert[] = [];
    const lastSnapshot = snapshots[snapshots.length - 1];
    if (!lastSnapshot) return result;

    const total = n(lastSnapshot.total_net_worth);
    if (total <= 0) return result;

    // Check cash allocation
    const cashValue = n(lastSnapshot.cash_and_bank_value);
    const cashPct = (cashValue / total) * 100;
    if (Math.abs(cashPct - CASH_TARGET_PCT) > DEVIATION_THRESHOLD) {
      const direction = cashPct > CASH_TARGET_PCT ? 'per sobre' : 'per sota';
      result.push({
        id: 'cash-weight',
        message: 'Alerta d\'assignació',
        detail: `Efectiu al ${cashPct.toFixed(1)}% — ${direction} de l'objectiu del ${CASH_TARGET_PCT}%. Considera redistribuir cap a renda variable.`,
      });
    }

    // Check individual asset deviations if asset_snapshots available
    if (lastSnapshot.asset_snapshots?.length) {
      for (const asset of lastSnapshot.asset_snapshots) {
        const pnlPct = n(asset.pnl_pct);
        if (pnlPct < -30) {
          const pnlEur = n(asset.pnl_eur);
          result.push({
            id: `pnl-${asset.asset_id}`,
            message: 'Pèrdua significant',
            detail: `${asset.display_name} mostra una pèrdua de ${pnlPct.toFixed(1)}% (${pnlEur.toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€).`,
          });
        }
      }
    }

    return result;
  }, [snapshots]);

  if (alerts.length === 0) return null;

  return (
    <div style={{ padding: '20px 24px 0' }}>
      {alerts.map((alert) => (
        <div
          key={alert.id}
          style={{
            background: 'color-mix(in srgb, var(--color-warning) 8%, transparent)',
            backdropFilter: 'var(--glass-blur)',
            WebkitBackdropFilter: 'var(--glass-blur)',
            border: '1px solid color-mix(in srgb, var(--color-warning) 25%, transparent)',
            borderRadius: 16,
            padding: 14,
            marginBottom: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 6,
            }}
          >
            <WarningIcon color="var(--color-warning)" />
            <span
              style={{
                fontSize: 10,
                fontFamily: 'var(--font-num)',
                letterSpacing: '0.06em',
                color: 'var(--color-warning)',
                textTransform: 'uppercase',
                fontWeight: 600,
              }}
            >
              {alert.message}
            </span>
          </div>
          <div
            style={{
              fontSize: 12,
              color: 'var(--color-text-secondary)',
              lineHeight: 1.5,
            }}
          >
            {alert.detail}
          </div>
        </div>
      ))}
    </div>
  );
}
