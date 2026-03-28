import { useMemo } from 'react';
import { useNetWorthHistory } from '../../hooks/useNetWorth';
import { useMarketPrices } from '../../hooks/useMarketPrices';
import { Card } from '../../components/ui/Card';
import { n, ASSET_COLORS } from '../../types';
import type { AssetSnapshot, AssetPrice } from '../../types';

function AssetRow({
  asset,
  price,
  weight,
  isFirst,
  isLast,
}: {
  asset: AssetSnapshot;
  price?: AssetPrice;
  weight: number;
  isFirst: boolean;
  isLast: boolean;
}) {
  const borderRadius = isFirst
    ? '14px 14px 2px 2px'
    : isLast
    ? '2px 2px 14px 14px'
    : '2px';

  const pnlEur = n(asset.pnl_eur);
  const pnlPct = n(asset.pnl_pct);
  const valueEur = n(asset.value_eur);
  const shares = n(asset.shares);
  const isPositive = pnlEur >= 0;
  const pnlColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
  const ticker2 = asset.ticker_yf.slice(0, 2).toUpperCase();
  const color = asset.color_hex || ASSET_COLORS[asset.ticker_yf] || '#94A3B8';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '12px 14px',
        background: 'var(--color-glass-bg)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid var(--color-glass-border)',
        borderRadius,
        boxShadow: isFirst ? 'var(--card-shadow)' : 'none',
      }}
    >
      {/* Asset icon */}
      <div
        style={{
          width: 36,
          height: 36,
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

      {/* Name & shares */}
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
          {asset.display_name}
        </div>
        <div
          style={{
            fontSize: 10,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-num)',
          }}
        >
          {shares.toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} acc · {price?.price_close != null ? `€${n(price.price_close).toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
        </div>
      </div>

      {/* Value & P&L */}
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            fontFamily: 'var(--font-num)',
            color: 'var(--color-text)',
          }}
        >
          €{valueEur.toLocaleString('ca-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
        </div>
        <div
          style={{
            fontSize: 10,
            fontFamily: 'var(--font-num)',
            color: pnlColor,
          }}
        >
          {isPositive ? '+' : ''}€{pnlEur.toLocaleString('ca-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ({isPositive ? '+' : ''}{pnlPct.toFixed(1)}%)
        </div>
        <div
          style={{
            fontSize: 9,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-num)',
          }}
        >
          {weight.toFixed(1)}%
        </div>
      </div>
    </div>
  );
}

export function PortfolioScreen() {
  const { data: networthData, isLoading } = useNetWorthHistory('1y');
  const { data: pricesData } = useMarketPrices();

  const snapshots = networthData?.snapshots ?? [];
  const prices = pricesData?.prices ?? [];
  const lastSnapshot = snapshots[snapshots.length - 1];

  const { assets, totalValue } = useMemo(() => {
    if (!lastSnapshot?.asset_snapshots?.length) {
      return { assets: [], totalValue: n(lastSnapshot?.investment_portfolio_value) };
    }
    const sorted = [...lastSnapshot.asset_snapshots].sort(
      (a, b) => n(b.value_eur) - n(a.value_eur)
    );
    return { assets: sorted, totalValue: n(lastSnapshot.total_net_worth) };
  }, [lastSnapshot]);

  const priceMap = useMemo(() => {
    const map = new Map<number, AssetPrice>();
    for (const p of prices) {
      map.set(p.asset_id, p);
    }
    return map;
  }, [prices]);

  return (
    <div
      style={{
        background: 'var(--color-bg)',
        minHeight: '100vh',
        fontFamily: 'var(--font-body)',
        color: 'var(--color-text)',
        maxWidth: 430,
        margin: '0 auto',
        paddingBottom: 88,
      }}
    >
      {/* Header */}
      <div style={{ padding: '56px 24px 20px' }}>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            fontFamily: 'var(--font-display)',
          }}
        >
          Cartera
        </div>
      </div>

      {isLoading ? (
        <div style={{ padding: '0 24px' }}>
          <Card style={{ height: 300, opacity: 0.5, animation: 'pulse 1.5s ease infinite' }}>
            <div />
          </Card>
        </div>
      ) : assets.length === 0 ? (
        <div style={{ padding: '0 24px' }}>
          <Card>
            <div
              style={{
                textAlign: 'center',
                padding: '40px 0',
                color: 'var(--color-text-tertiary)',
                fontSize: 13,
                fontFamily: 'var(--font-num)',
              }}
            >
              Sense actius disponibles.
              <br />
              Sincronitza les teves dades per veure la cartera.
            </div>
          </Card>
        </div>
      ) : (
        <>
          {/* Asset list */}
          <div style={{ padding: '0 24px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {assets.map((asset, i) => {
                const weight = totalValue > 0 ? (n(asset.value_eur) / totalValue) * 100 : 0;
                return (
                  <AssetRow
                    key={asset.asset_id}
                    asset={asset}
                    price={priceMap.get(asset.asset_id)}
                    weight={weight}
                    isFirst={i === 0}
                    isLast={i === assets.length - 1}
                  />
                );
              })}
            </div>
          </div>

          {/* Footer total */}
          <div style={{ padding: '20px 24px 0' }}>
            <Card>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    fontSize: 11,
                    fontFamily: 'var(--font-num)',
                    letterSpacing: '0.06em',
                    color: 'var(--color-text-tertiary)',
                    textTransform: 'uppercase',
                  }}
                >
                  Total Cartera
                </span>
                <span
                  style={{
                    fontSize: 20,
                    fontWeight: 600,
                    fontFamily: 'var(--font-num)',
                    color: 'var(--color-text)',
                  }}
                >
                  €{n(totalValue).toLocaleString('ca-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </span>
              </div>
              {n(lastSnapshot?.cash_and_bank_value) > 0 && (
                <div
                  style={{
                    marginTop: 8,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span
                    style={{
                      fontSize: 11,
                      color: 'var(--color-text-tertiary)',
                      fontFamily: 'var(--font-num)',
                    }}
                  >
                    Efectiu
                  </span>
                  <span
                    style={{
                      fontSize: 13,
                      fontFamily: 'var(--font-num)',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    €{n(lastSnapshot?.cash_and_bank_value).toLocaleString('ca-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </span>
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
