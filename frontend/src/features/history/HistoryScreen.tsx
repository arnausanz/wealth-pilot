import { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { useInvestmentSummary, useTransactions } from '../../hooks/useHistory';
import { n, ASSET_COLORS, ASSET_COLOR_DEFAULT } from '../../types';
import type { AssetInvestmentSummary, TransactionOut } from '../../types';

// ─── TX type labels ───────────────────────────────────────────────────────────

const TX_LABELS: Record<string, string> = {
  expense:         'Despesa',
  income:          'Ingrés',
  investment_buy:  'Compra',
  investment_sell: 'Venda',
  transfer_in:     'Transferència +',
  transfer_out:    'Transferència −',
};

const TX_COLORS: Record<string, string> = {
  expense:         '#EF4444',
  income:          '#10B981',
  investment_buy:  '#3B82F6',
  investment_sell: '#F59E0B',
  transfer_in:     '#8B5CF6',
  transfer_out:    '#6B7280',
};

const FILTER_PILLS = [
  { label: 'Inversions', txType: undefined as string | undefined, onlyInv: true  },
  { label: 'Compres',    txType: 'investment_buy',                onlyInv: false },
  { label: 'Vendes',     txType: 'investment_sell',               onlyInv: false },
  { label: 'Despeses',   txType: 'expense',                       onlyInv: false },
  { label: 'Ingressos',  txType: 'income',                        onlyInv: false },
];

// ─── Investment summary per asset ─────────────────────────────────────────────

function AssetSummaryRow({ asset, isLast }: { asset: AssetInvestmentSummary; isLast: boolean }) {
  const color   = asset.color_hex || ASSET_COLORS[asset.ticker_yf || ''] || ASSET_COLOR_DEFAULT;
  const ticker2 = asset.display_name.slice(0, 2).toUpperCase();
  const pnl     = n(asset.pnl_eur);
  const pnlPct  = n(asset.pnl_pct);
  const pos     = pnl >= 0;

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
      {/* Icon */}
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 10,
          background: `${color}22`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 10,
          fontWeight: 700,
          color,
          fontFamily: 'var(--font-num)',
          flexShrink: 0,
        }}
      >
        {ticker2}
      </div>

      {/* Name + cost info */}
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
          {n(asset.shares).toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} acc
          {asset.avg_cost_eur != null &&
            ` · cost €${n(asset.avg_cost_eur).toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
        </div>
      </div>

      {/* Values */}
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 600,
            fontFamily: 'var(--font-num)',
            color: 'var(--color-text)',
          }}
        >
          €{n(asset.total_invested_eur).toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
        </div>
        <div
          style={{
            fontSize: 10,
            fontFamily: 'var(--font-num)',
            color: pos ? 'var(--color-positive)' : 'var(--color-negative)',
          }}
        >
          {pos ? '+' : ''}€{pnl.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
          {' '}({pos ? '+' : ''}{pnlPct.toFixed(1)}%)
        </div>
      </div>
    </div>
  );
}

// ─── Transaction row ──────────────────────────────────────────────────────────

function TransactionRow({ tx, isLast }: { tx: TransactionOut; isLast: boolean }) {
  // Una transacció és inversió si té shares (independentment del tx_type que MoneyWiz assigni)
  const isInvest  = tx.shares != null || tx.tx_type === 'investment_buy' || tx.tx_type === 'investment_sell';
  const isSell    = tx.tx_type === 'investment_sell';
  const effectiveType = isInvest ? (isSell ? 'investment_sell' : 'investment_buy') : tx.tx_type;

  const color     = tx.color_hex || ASSET_COLORS[tx.ticker_yf || ''] || TX_COLORS[effectiveType] || ASSET_COLOR_DEFAULT;
  const amount    = n(tx.amount_eur);
  const label     = TX_LABELS[effectiveType] || tx.tx_type;
  const txColor   = TX_COLORS[effectiveType] || 'var(--color-text-secondary)';

  // Format date: "28 mar 2026"
  const d = new Date(tx.tx_date + 'T00:00:00');
  const dateStr = d.toLocaleDateString('ca-ES', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 0',
        borderBottom: isLast ? 'none' : '1px solid var(--color-glass-border)',
      }}
    >
      {/* Type badge */}
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 9,
          background: `${txColor}18`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isInvest && tx.ticker_yf ? (
          <span
            style={{
              fontSize: 9,
              fontWeight: 700,
              color,
              fontFamily: 'var(--font-num)',
            }}
          >
            {tx.ticker_yf.slice(0, 2)}
          </span>
        ) : (
          <span style={{ fontSize: 12 }}>
            {effectiveType === 'expense' ? '↓'
              : effectiveType === 'income' ? '↑'
              : effectiveType === 'transfer_in' ? '↓+'
              : '⇄'}
          </span>
        )}
      </div>

      {/* Description */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-text)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {tx.display_name || tx.description || tx.mw_symbol || label}
        </div>
        <div
          style={{
            fontSize: 9,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-num)',
          }}
        >
          {dateStr} · {label}
        </div>
      </div>

      {/* Amount */}
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 600,
            fontFamily: 'var(--font-num)',
            color: txColor,
          }}
        >
          {(effectiveType === 'income' || effectiveType === 'transfer_in') ? '+' : ''}€{amount.toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        {tx.shares != null && (
          <div
            style={{
              fontSize: 9,
              color: 'var(--color-text-tertiary)',
              fontFamily: 'var(--font-num)',
            }}
          >
            {n(tx.shares).toLocaleString('ca-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} acc
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────────────────

export function HistoryScreen() {
  const [filterIdx, setFilterIdx] = useState(0);
  const [page, setPage] = useState(1);

  const activeFilter = FILTER_PILLS[filterIdx];
  const txFilters = {
    page,
    per_page: 25,
    tx_type:          activeFilter.txType,
    only_investments: activeFilter.onlyInv,
  };

  const { data: investments, isLoading: loadingInv }  = useInvestmentSummary();
  const { data: txData,      isLoading: loadingTx }   = useTransactions(txFilters);

  const totalPnl       = n(investments?.total_pnl_eur);
  const totalPnlPct    = n(investments?.total_pnl_pct);
  const totalInvested  = n(investments?.total_invested_eur);
  const pnlPositive    = totalPnl >= 0;

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
      <div style={{ padding: '68px 24px 16px' }}>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            fontFamily: 'var(--font-display)',
          }}
        >
          Historial
        </div>
      </div>

      {/* ── Investment summary ── */}
      <div style={{ padding: '0 24px 4px' }}>
        <Card>
          {loadingInv ? (
            <div style={{ height: 60, opacity: 0.3, animation: 'pulse 1.5s ease infinite' }} />
          ) : investments ? (
            <>
              {/* Totals header */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-end',
                  marginBottom: 14,
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: 9,
                      fontFamily: 'var(--font-num)',
                      letterSpacing: '0.06em',
                      color: 'var(--color-text-tertiary)',
                      textTransform: 'uppercase',
                      marginBottom: 4,
                    }}
                  >
                    Total invertit
                  </div>
                  <div
                    style={{
                      fontSize: 20,
                      fontWeight: 700,
                      fontFamily: 'var(--font-num)',
                      letterSpacing: '-0.02em',
                      color: 'var(--color-text)',
                    }}
                  >
                    €{totalInvested.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div
                    style={{
                      fontSize: 9,
                      fontFamily: 'var(--font-num)',
                      letterSpacing: '0.06em',
                      color: 'var(--color-text-tertiary)',
                      textTransform: 'uppercase',
                      marginBottom: 4,
                    }}
                  >
                    P&amp;L total
                  </div>
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      fontFamily: 'var(--font-num)',
                      letterSpacing: '-0.02em',
                      color: pnlPositive ? 'var(--color-positive)' : 'var(--color-negative)',
                    }}
                  >
                    {pnlPositive ? '+' : ''}€{totalPnl.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
                    <span
                      style={{
                        fontSize: 12,
                        fontWeight: 500,
                        marginLeft: 4,
                      }}
                    >
                      ({pnlPositive ? '+' : ''}{totalPnlPct.toFixed(1)}%)
                    </span>
                  </div>
                </div>
              </div>

              {/* Per-asset rows */}
              {investments.assets.map((asset, i) => (
                <AssetSummaryRow key={asset.asset_id} asset={asset} isLast={i === investments.assets.length - 1} />
              ))}
            </>
          ) : null}
        </Card>
      </div>

      {/* ── Transactions ── */}
      <div style={{ padding: '16px 24px 0' }}>
        {/* Section header */}
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            letterSpacing: '-0.01em',
            fontFamily: 'var(--font-display)',
            marginBottom: 10,
          }}
        >
          Transaccions
        </div>

        {/* Filter pills */}
        <div
          style={{
            display: 'flex',
            gap: 6,
            marginBottom: 12,
            overflowX: 'auto',
            paddingBottom: 2,
          }}
        >
          {FILTER_PILLS.map((pill, idx) => {
            const isActive = filterIdx === idx;
            return (
              <button
                key={idx}
                onClick={() => { setFilterIdx(idx); setPage(1); }}
                style={{
                  padding: '5px 12px',
                  borderRadius: 20,
                  border: `1px solid ${isActive ? 'var(--color-accent)' : 'var(--color-glass-border)'}`,
                  background: isActive ? 'var(--color-accent)' : 'transparent',
                  color: isActive ? '#fff' : 'var(--color-text-tertiary)',
                  fontSize: 11,
                  fontFamily: 'var(--font-num)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s',
                }}
              >
                {pill.label}
              </button>
            );
          })}
        </div>

        {/* Transaction list */}
        <Card style={{ padding: '0 14px' }}>
          {loadingTx ? (
            <div style={{ height: 120, opacity: 0.3, animation: 'pulse 1.5s ease infinite' }} />
          ) : txData?.transactions.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '32px 0',
                color: 'var(--color-text-tertiary)',
                fontSize: 13,
              }}
            >
              Sense transaccions
            </div>
          ) : (
            txData?.transactions.map((tx, i) => (
              <TransactionRow key={tx.id} tx={tx} isLast={i === (txData.transactions.length - 1)} />
            ))
          )}
        </Card>

        {/* Pagination */}
        {txData && txData.pages > 1 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 0',
            }}
          >
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              style={{
                padding: '6px 14px',
                borderRadius: 20,
                border: '1px solid var(--color-glass-border)',
                background: 'transparent',
                color: page === 1 ? 'var(--color-text-tertiary)' : 'var(--color-text)',
                fontSize: 12,
                fontFamily: 'var(--font-num)',
                cursor: page === 1 ? 'default' : 'pointer',
              }}
            >
              ← Anterior
            </button>
            <span
              style={{
                fontSize: 11,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text-tertiary)',
              }}
            >
              {page} / {txData.pages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(txData.pages, p + 1))}
              disabled={page === txData.pages}
              style={{
                padding: '6px 14px',
                borderRadius: 20,
                border: '1px solid var(--color-glass-border)',
                background: 'transparent',
                color: page === txData.pages ? 'var(--color-text-tertiary)' : 'var(--color-text)',
                fontSize: 12,
                fontFamily: 'var(--font-num)',
                cursor: page === txData.pages ? 'default' : 'pointer',
              }}
            >
              Següent →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
