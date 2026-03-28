import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { DonutChart } from '../../components/charts/DonutChart';
import { Card } from '../../components/ui/Card';
import { n, ASSET_COLORS, ASSET_COLOR_DEFAULT } from '../../types';
import type { NetWorthSnapshot } from '../../types';

interface AllocationProps {
  snapshots: NetWorthSnapshot[];
}

export function Allocation({ snapshots }: AllocationProps) {
  const navigate = useNavigate();
  const lastSnapshot = snapshots[snapshots.length - 1];

  const { segments, displayedAssets, remainingCount } = useMemo(() => {
    if (!lastSnapshot?.asset_snapshots || lastSnapshot.asset_snapshots.length === 0) {
      return { segments: [], displayedAssets: [], remainingCount: 0 };
    }

    const assets = [...lastSnapshot.asset_snapshots].sort(
      (a, b) => n(b.value_eur) - n(a.value_eur)
    );
    const top5 = assets.slice(0, 5);
    const rest = assets.slice(5);

    const segs = assets.map((a) => ({
      name: a.display_name,
      value: n(a.value_eur),
      color: a.color_hex || ASSET_COLORS[a.ticker_yf] || ASSET_COLOR_DEFAULT,
    }));

    // Add cash if available
    const cashValue = n(lastSnapshot.cash_and_bank_value);
    if (cashValue > 0) {
      segs.push({
        name: 'Efectiu',
        value: cashValue,
        color: ASSET_COLOR_DEFAULT,
      });
    }

    return {
      segments: segs,
      displayedAssets: top5,
      remainingCount: rest.length,
    };
  }, [lastSnapshot]);

  if (segments.length === 0) {
    return (
      <div style={{ padding: '20px 24px 0' }}>
        <Card padding={18} style={{ padding: '18px 16px' }}>
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-tertiary)',
              textAlign: 'center',
              fontFamily: 'var(--font-num)',
            }}
          >
            Sense dades d'actius disponibles
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px 24px 0' }}>
      <Card padding={0} style={{ padding: '18px 16px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
          }}
        >
          <span
            style={{
              fontSize: 10,
              fontFamily: 'var(--font-num)',
              letterSpacing: '0.06em',
              color: 'var(--color-text-tertiary)',
              textTransform: 'uppercase',
            }}
          >
            Distribució
          </span>
          <span
            style={{
              fontSize: 10,
              fontFamily: 'var(--font-num)',
              color: 'var(--color-accent)',
              cursor: 'pointer',
            }}
            onClick={() => navigate('/portfolio')}
          >
            Veure detall →
          </span>
        </div>

        <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <DonutChart segments={segments} />
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: 5,
            }}
          >
            {displayedAssets.map((a, i) => {
              const total = segments.reduce((s, seg) => s + seg.value, 0);
              const realPct = total > 0 ? (n(a.value_eur) / total) * 100 : 0;
              return (
                <div
                  key={i}
                  style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                >
                  <div
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: 2,
                      background: a.color_hex || ASSET_COLORS[a.ticker_yf] || ASSET_COLOR_DEFAULT,
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontSize: 10,
                      color: 'var(--color-text-secondary)',
                      flex: 1,
                    }}
                  >
                    {a.display_name}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontFamily: 'var(--font-num)',
                      color: 'var(--color-text)',
                      fontWeight: 500,
                    }}
                  >
                    {realPct.toFixed(1)}%
                  </span>
                </div>
              );
            })}
            {remainingCount > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: 2,
                    background: 'var(--color-text-tertiary)',
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: 10,
                    color: 'var(--color-text-secondary)',
                    flex: 1,
                  }}
                >
                  +{remainingCount} més
                </span>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
