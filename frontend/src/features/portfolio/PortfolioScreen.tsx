import { useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNetWorthHistory } from '../../hooks/useNetWorth';
import { useMarketPrices } from '../../hooks/useMarketPrices';
import { Card } from '../../components/ui/Card';
import { n, ASSET_COLORS } from '../../types';
import type { AssetSnapshot, AssetPrice } from '../../types';

type SyncState = 'idle' | 'uploading' | 'success' | 'error';

function AssetRow({
  asset,
  price,
  weight,
  isLast,
}: {
  asset: AssetSnapshot;
  price?: AssetPrice;
  weight: number;
  isLast: boolean;
}) {
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
        padding: '12px 0',
        borderBottom: isLast ? 'none' : '1px solid var(--color-glass-border)',
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
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [syncState, setSyncState] = useState<SyncState>('idle');
  const [syncError, setSyncError] = useState('');

  async function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    // Reset input per permetre tornar a seleccionar el mateix fitxer
    e.target.value = '';

    setSyncState('uploading');
    setSyncError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/sync/upload', {
        method: 'POST',
        credentials: 'same-origin',
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Error ${res.status}`);
      }
      await queryClient.invalidateQueries();
      setSyncState('success');
      setTimeout(() => setSyncState('idle'), 3000);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Error desconegut');
      setSyncState('error');
      setTimeout(() => setSyncState('idle'), 5000);
    }
  }

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
      <div style={{ padding: '68px 24px 20px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
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

        {/* Botó Actualitzar — obre el selector de fitxers de MoneyWiz */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={syncState === 'uploading'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '7px 14px',
            borderRadius: 20,
            border: `1px solid ${
              syncState === 'success' ? 'var(--color-positive)' :
              syncState === 'error'   ? 'var(--color-negative)' :
              'var(--color-glass-border)'
            }`,
            background: 'var(--color-glass-bg)',
            backdropFilter: 'var(--glass-blur)',
            WebkitBackdropFilter: 'var(--glass-blur)',
            color: syncState === 'success' ? 'var(--color-positive)'
                 : syncState === 'error'   ? 'var(--color-negative)'
                 : 'var(--color-text-secondary)',
            fontSize: 12,
            fontFamily: 'var(--font-num)',
            fontWeight: 500,
            cursor: syncState === 'uploading' ? 'default' : 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          <span style={{
            display: 'inline-block',
            animation: syncState === 'uploading' ? 'spin 1s linear infinite' : 'none',
          }}>
            {syncState === 'success' ? '✓' : syncState === 'error' ? '✗' : '↻'}
          </span>
          {syncState === 'uploading' ? 'Pujant…'
         : syncState === 'success'  ? 'Actualitzat'
         : syncState === 'error'    ? 'Error'
         : 'Actualitzar'}
        </button>

        {/* Input de fitxer ocult — s'obre amb el botó de dalt */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.moneywiz"
          onChange={handleFileSelected}
          style={{ display: 'none' }}
        />
      </div>

      {/* Missatge d'error sync */}
      {syncState === 'error' && syncError && (
        <div style={{ padding: '0 24px 8px' }}>
          <div style={{
            fontSize: 11,
            fontFamily: 'var(--font-num)',
            color: 'var(--color-negative)',
            textAlign: 'center',
          }}>
            {syncError}
          </div>
        </div>
      )}

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
            <Card style={{ padding: '0 14px' }}>
              {assets.map((asset, i) => {
                const weight = totalValue > 0 ? (n(asset.value_eur) / totalValue) * 100 : 0;
                return (
                  <AssetRow
                    key={asset.asset_id}
                    asset={asset}
                    price={priceMap.get(asset.asset_id)}
                    weight={weight}
                    isLast={i === assets.length - 1}
                  />
                );
              })}
            </Card>
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
