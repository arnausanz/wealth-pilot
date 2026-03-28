import { useState } from 'react';
import { useNetWorthHistory } from '../../hooks/useNetWorth';
import { useMarketPrices } from '../../hooks/useMarketPrices';
import { useTheme } from '../../hooks/useTheme';
import { SunIcon, MoonIcon } from '../../components/icons/Icons';
import { useConfigObjectives } from '../../hooks/useConfig';
import { n } from '../../types';
import { Card } from '../../components/ui/Card';
import { HeroValue } from './HeroValue';
import { ChartSection } from './ChartSection';
import { StatusCards } from './StatusCards';
import { Allocation } from './Allocation';
import { TopMovers } from './TopMovers';
import { Alerts } from './Alerts';


function SkeletonCard({ height = 100 }: { height?: number }) {
  return (
    <Card
      style={{
        height,
        opacity: 0.5,
        animation: 'pulse 1.5s ease infinite',
      }}
    >
      <div />
    </Card>
  );
}

export function DashboardScreen() {
  const [period, setPeriod] = useState('1A');
  const { isDark, toggle } = useTheme();

  const { data: networthData, isLoading: nwLoading } = useNetWorthHistory(period);
  const { data: pricesData, isLoading: pricesLoading } = useMarketPrices();
  const { data: objectives = [] } = useConfigObjectives();

  // Objectiu d'habitatge des de l'API
  const homePurchaseObj = objectives.find((o) => o.key === 'home_purchase' && o.is_active);
  const GOAL_AMOUNT = homePurchaseObj ? n(homePurchaseObj.target_amount) : 80000;
  const GOAL_YEAR = homePurchaseObj?.target_date
    ? new Date(homePurchaseObj.target_date).getFullYear()
    : 2029;
  const GOAL_LABEL = homePurchaseObj?.name ?? 'Habitatge';

  const snapshots = networthData?.snapshots ?? [];
  const prices = pricesData?.prices ?? [];

  const lastSnapshot = snapshots[snapshots.length - 1];
  const total = n(lastSnapshot?.total_net_worth);
  const changeEur = n(lastSnapshot?.change_eur);
  const changePct = n(lastSnapshot?.change_pct);

  return (
    <div
      style={{
        background: 'var(--color-bg)',
        minHeight: '100vh',
        fontFamily: 'var(--font-body)',
        color: 'var(--color-text)',
        maxWidth: 430,
        margin: '0 auto',
        position: 'relative',
        paddingBottom: 88,
        transition: 'background 0.4s ease, color 0.4s ease',
      }}
    >
      {/* Header */}
      <div style={{ padding: '56px 24px 0' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div
              style={{
                fontSize: 24,
                fontWeight: 700,
                letterSpacing: '-0.02em',
                fontFamily: 'var(--font-display)',
              }}
            >
              Dashboard
            </div>
          </div>
          <button
            onClick={toggle}
            style={{
              width: 36,
              height: 36,
              borderRadius: 12,
              background: 'var(--color-glass-bg)',
              backdropFilter: 'var(--glass-blur)',
              WebkitBackdropFilter: 'var(--glass-blur)',
              border: '1px solid var(--color-glass-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
            }}
            title="Canviar tema"
          >
            {isDark ? (
              <SunIcon color="var(--color-text-secondary)" />
            ) : (
              <MoonIcon color="var(--color-text-secondary)" />
            )}
          </button>
        </div>
      </div>

      {/* Hero value */}
      {nwLoading ? (
        <div style={{ padding: '24px 24px 0' }}>
          <SkeletonCard height={80} />
        </div>
      ) : (
        <HeroValue
          total={total}
          changeEur={changeEur}
          changePct={changePct}
          period={period}
        />
      )}

      {/* Chart section */}
      {nwLoading ? (
        <div style={{ padding: '20px 24px 0' }}>
          <SkeletonCard height={240} />
        </div>
      ) : (
        <ChartSection
          snapshots={snapshots}
          period={period}
          onPeriodChange={setPeriod}
        />
      )}

      {/* Status cards */}
      {nwLoading ? (
        <div style={{ padding: '20px 24px 0' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <SkeletonCard height={100} />
            <SkeletonCard height={100} />
          </div>
        </div>
      ) : (
        <StatusCards
          netWorth={total}
          goalAmount={GOAL_AMOUNT}
          goalYear={GOAL_YEAR}
          goalLabel={GOAL_LABEL}
          lastSnapshot={lastSnapshot}
        />
      )}

      {/* Asset allocation */}
      {nwLoading ? (
        <div style={{ padding: '20px 24px 0' }}>
          <SkeletonCard height={160} />
        </div>
      ) : (
        <Allocation snapshots={snapshots} />
      )}

      {/* Top movers */}
      {pricesLoading ? (
        <div style={{ padding: '20px 24px 0' }}>
          <SkeletonCard height={180} />
        </div>
      ) : (
        <TopMovers prices={prices} />
      )}

      {/* Alerts */}
      {!nwLoading && snapshots.length > 0 && (
        <Alerts snapshots={snapshots} prices={prices} />
      )}

      {/* Bottom padding */}
      <div style={{ height: 32 }} />
    </div>
  );
}
