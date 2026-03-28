import { useMemo } from 'react';
import { Card } from '../../components/ui/Card';
import { n, ASSET_COLORS } from '../../types';
import type { AssetPrice } from '../../types';

interface TopMoversProps {
  prices: AssetPrice[];
}

export function TopMovers({ prices }: TopMoversProps) {
  const topMovers = useMemo(() => {
    return [...prices]
      .filter((p) => p.price_close != null)
      .sort((a, b) => Math.abs(n(b.change_pct_1d)) - Math.abs(n(a.change_pct_1d)));
  }, [prices]);

  if (topMovers.length === 0) {
    return (
      <div style={{ padding: '20px 24px 0' }}>
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
          Moviments del dia
        </div>
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-num)',
            textAlign: 'center',
            padding: '20px 0',
          }}
        >
          Sense dades de mercat disponibles
        </div>
      </div>
    );
  }

  // Derive a consistent color from asset type / ticker
  function getAssetColor(price: AssetPrice): string {
    return ASSET_COLORS[price.ticker_yf] ?? '#94A3B8';
  }

  return (
    <div style={{ padding: '20px 24px 0' }}>
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
        Moviments del dia
      </div>
      <Card style={{ padding: '0 14px' }}>
        {topMovers.map((price, i) => {
          const isLast = i === topMovers.length - 1;
          const changePct = n(price.change_pct_1d);
          const priceClose = n(price.price_close);
          const isPositive = changePct >= 0;
          const changeColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
          const color = getAssetColor(price);
          const ticker2 = price.ticker_yf.slice(0, 2).toUpperCase();

          return (
            <div
              key={price.asset_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 0',
                borderBottom: isLast ? 'none' : '1px solid var(--color-glass-border)',
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 10,
                  background: `${color}22`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 11,
                  fontWeight: 700,
                  color,
                  fontFamily: 'var(--font-num)',
                  flexShrink: 0,
                }}
              >
                {ticker2}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    color: 'var(--color-text)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {price.display_name}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: 'var(--color-text-tertiary)',
                    fontFamily: 'var(--font-num)',
                  }}
                >
                  €{priceClose.toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    fontFamily: 'var(--font-num)',
                    color: changeColor,
                  }}
                >
                  {isPositive ? '+' : ''}{changePct.toFixed(2)}%
                </div>
                {price.is_stale && (
                  <div
                    style={{
                      fontSize: 9,
                      color: 'var(--color-warning)',
                      fontFamily: 'var(--font-num)',
                    }}
                  >
                    antic
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </Card>
    </div>
  );
}
