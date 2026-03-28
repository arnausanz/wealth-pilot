import { useState, useEffect } from 'react';
import { Card } from '../../components/ui/Card';
import { ProjectionChart } from '../../components/charts/ProjectionChart';
import { useProjection, useScenariosInfo } from '../../hooks/useSimulation';
import { n } from '../../types';
import { OpenSimulator } from './OpenSimulator';

// Retarda les peticions a l'API mentre l'slider es mou
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const SCENARIO_COLORS: Record<string, string> = {
  adverse:    '#EF4444',
  base:       '#3B82F6',
  optimistic: '#10B981',
};

// ─── Sub-components ──────────────────────────────────────────────────────────

const HORIZON_MARKS = [1, 5, 10, 15, 20, 25, 30] as const;

function HorizonSlider({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  const trackPct = ((value - 1) / 29) * 100;

  return (
    <div style={{ padding: '0 24px 4px' }}>
      {/* Track + thumb */}
      <div style={{ position: 'relative', paddingTop: 4, paddingBottom: 4 }}>
        <input
          type="range"
          min={1}
          max={30}
          step={1}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{
            width: '100%',
            background: `linear-gradient(to right, var(--color-accent) ${trackPct}%, var(--color-glass-border) ${trackPct}%)`,
          }}
        />
      </div>

      {/* Marks */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 6,
        }}
      >
        {HORIZON_MARKS.map((yr) => {
          const isActive = value === yr;
          return (
            <button
              key={yr}
              onClick={() => onChange(yr)}
              style={{
                fontSize: 9,
                fontFamily: 'var(--font-num)',
                color: isActive ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
                background: 'none',
                border: 'none',
                padding: '2px 0',
                cursor: 'pointer',
                fontWeight: isActive ? 700 : 400,
                transition: 'color 0.15s',
                minWidth: 24,
                textAlign: 'center',
              }}
            >
              {yr}a
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ScenarioResultCard({
  type,
  label,
  returnPct,
  endValue,
  cagr,
  isMain,
}: {
  type: string;
  label: string;
  returnPct: number;
  endValue: number;
  cagr: number | null;
  isMain: boolean;
}) {
  const color = SCENARIO_COLORS[type] || 'var(--color-accent)';

  return (
    <div
      style={{
        flex: 1,
        padding: isMain ? '14px 12px' : '12px 10px',
        background: isMain
          ? `linear-gradient(135deg, ${color}22 0%, rgba(255,255,255,0.03) 100%)`
          : 'var(--color-glass-bg)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        border: `1px solid ${isMain ? color + '44' : 'var(--color-glass-border)'}`,
        borderRadius: 14,
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}
    >
      {/* Dot + label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: color,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontSize: 10,
            fontFamily: 'var(--font-num)',
            letterSpacing: '0.06em',
            color: 'var(--color-text-tertiary)',
            textTransform: 'uppercase',
          }}
        >
          {label}
        </span>
      </div>

      {/* End value */}
      <div
        style={{
          fontSize: isMain ? 18 : 14,
          fontWeight: 700,
          fontFamily: 'var(--font-num)',
          letterSpacing: '-0.02em',
          color: 'var(--color-text)',
        }}
      >
        €{endValue.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
      </div>

      {/* Return pct + CAGR */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span
          style={{
            fontSize: 11,
            fontFamily: 'var(--font-num)',
            color,
            fontWeight: 600,
          }}
        >
          +{returnPct.toFixed(1)}% retorn
        </span>
        {cagr != null && (
          <span
            style={{
              fontSize: 9,
              fontFamily: 'var(--font-num)',
              color: 'var(--color-text-tertiary)',
            }}
          >
            CAGR {cagr.toFixed(1)}%/a
          </span>
        )}
      </div>
    </div>
  );
}

function ContributionInfo({
  monthly,
  horizonYears,
}: {
  monthly: number;
  horizonYears: number;
}) {
  const totalContribs = monthly * horizonYears * 12;
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 14px',
        background: 'rgba(255,255,255,0.03)',
        borderRadius: 10,
        border: '1px solid var(--color-glass-border)',
        marginTop: 8,
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
            marginBottom: 2,
          }}
        >
          Aportació mensual
        </div>
        <div
          style={{
            fontSize: 15,
            fontWeight: 600,
            fontFamily: 'var(--font-num)',
            color: 'var(--color-text)',
          }}
        >
          €{monthly.toLocaleString('ca-ES')}
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
            marginBottom: 2,
          }}
        >
          Total aportat ({horizonYears}a)
        </div>
        <div
          style={{
            fontSize: 15,
            fontWeight: 600,
            fontFamily: 'var(--font-num)',
            color: 'var(--color-text-secondary)',
          }}
        >
          €{totalContribs.toLocaleString('ca-ES')}
        </div>
      </div>
    </div>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────────────────

type SimTab = 'projection' | 'custom';

export function SimulationScreen() {
  // Tab 'custom' desactivat temporalment — pendent redisseny (veure Roadmap § 8.2)
  const [simTab] = useState<SimTab>('projection');
  const [horizonYears, setHorizonYears] = useState(10);
  // Debounce per evitar peticions a l'API en cada tick del slider
  const debouncedHorizon = useDebounce(horizonYears, 350);

  const { data: scenariosInfo } = useScenariosInfo();
  const { data: projection, isLoading } = useProjection(debouncedHorizon);

  const startValue   = n(projection?.start_value);
  const monthly      = n(projection?.monthly_contribution ?? scenariosInfo?.monthly_contributions);
  const goalTarget   = projection?.home_purchase_target != null ? n(projection.home_purchase_target) : null;
  const scenarios    = projection?.scenarios;

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
      <div style={{ padding: '56px 24px 12px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
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
              Simulació
            </div>
            {/* Tab bar — 'Personalitzat' ocult fins al redisseny */}
            {startValue > 0 && (
              <div
                style={{
                  fontSize: 12,
                  color: 'var(--color-text-tertiary)',
                  fontFamily: 'var(--font-num)',
                  marginTop: 2,
                }}
              >
                Des de{' '}
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  €{startValue.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
                </span>
              </div>
            )}
          </div>
          {/* Horitzó prominent */}
          <div style={{ textAlign: 'right' }}>
            <div
              style={{
                fontSize: 28,
                fontWeight: 700,
                fontFamily: 'var(--font-num)',
                letterSpacing: '-0.03em',
                color: 'var(--color-text)',
                lineHeight: 1,
              }}
            >
              {horizonYears}
              <span
                style={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: 'var(--color-text-tertiary)',
                  marginLeft: 3,
                }}
              >
                {horizonYears === 1 ? 'any' : 'anys'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {simTab === 'custom' && (
        <div style={{ marginTop: 16 }}>
          <OpenSimulator />
        </div>
      )}

      {/* Projection tab content */}
      {simTab === 'projection' && <>

      {/* Slider */}
      <HorizonSlider value={horizonYears} onChange={setHorizonYears} />

      {/* Chart */}
      <div style={{ padding: '12px 0 0', overflow: 'hidden' }}>
        {isLoading ? (
          <div
            style={{
              height: 240,
              margin: '0 24px',
              background: 'var(--color-glass-bg)',
              borderRadius: 16,
              animation: 'pulse 1.5s ease infinite',
            }}
          />
        ) : scenarios ? (
          <ProjectionChart
            adverse={scenarios.adverse.data_points}
            base={scenarios.base.data_points}
            optimistic={scenarios.optimistic.data_points}
            horizonYears={debouncedHorizon}
            goalValue={goalTarget}
            width={390}
            height={240}
          />
        ) : null}
      </div>

      {/* Legend */}
      {scenarios && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 16,
            padding: '6px 24px 4px',
          }}
        >
          {(['adverse', 'base', 'optimistic'] as const).map((type) => (
            <div
              key={type}
              style={{ display: 'flex', alignItems: 'center', gap: 5 }}
            >
              <div
                style={{
                  width: type === 'base' ? 16 : 12,
                  height: type === 'base' ? 2.5 : 1.5,
                  borderRadius: 2,
                  background: SCENARIO_COLORS[type],
                  opacity: type === 'base' ? 1 : 0.7,
                }}
              />
              <span
                style={{
                  fontSize: 9,
                  fontFamily: 'var(--font-num)',
                  color: 'var(--color-text-tertiary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                {scenarios[type].label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Scenario cards */}
      {scenarios && (
        <div style={{ padding: '12px 24px 0' }}>
          <div style={{ display: 'flex', gap: 8 }}>
            {(['adverse', 'base', 'optimistic'] as const).map((type) => {
              const s = scenarios[type];
              return (
                <ScenarioResultCard
                  key={type}
                  type={type}
                  label={s.label}
                  returnPct={n(s.total_return_pct)}
                  endValue={n(s.end_value)}
                  cagr={s.cagr_pct != null ? n(s.cagr_pct) : null}
                  isMain={type === 'base'}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Contribution info */}
      {monthly > 0 && (
        <div style={{ padding: '0 24px' }}>
          <ContributionInfo monthly={monthly} horizonYears={horizonYears} />
        </div>
      )}

      {/* Scenario returns info */}
      {scenariosInfo && (
        <div style={{ padding: '12px 24px 0' }}>
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
              Retorns anuals ponderats
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {scenariosInfo.scenarios.map((s) => (
                <div
                  key={s.scenario_type}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: SCENARIO_COLORS[s.scenario_type],
                        flexShrink: 0,
                      }}
                    />
                    <span
                      style={{
                        fontSize: 12,
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      {s.label}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: 12,
                      fontFamily: 'var(--font-num)',
                      fontWeight: 600,
                      color: SCENARIO_COLORS[s.scenario_type],
                    }}
                  >
                    {n(s.blended_return_pct).toFixed(2)}% / any
                  </span>
                </div>
              ))}
            </div>
            {goalTarget != null && (
              <div
                style={{
                  marginTop: 12,
                  paddingTop: 10,
                  borderTop: '1px solid var(--color-glass-border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    fontSize: 11,
                    color: 'var(--color-text-tertiary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span style={{ color: '#F59E0B', fontSize: 13 }}>–––</span>
                  Objectiu habitatge
                </span>
                <span
                  style={{
                    fontSize: 13,
                    fontFamily: 'var(--font-num)',
                    fontWeight: 600,
                    color: '#F59E0B',
                  }}
                >
                  €{goalTarget.toLocaleString('ca-ES')}
                </span>
              </div>
            )}
          </Card>
        </div>
      )}

      </>}
    </div>
  );
}
