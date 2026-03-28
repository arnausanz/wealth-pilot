import { useState } from 'react';
import { n } from '../../types';
import {
  useAnalyticsAlerts,
  useCashflow,
  useExpenseBreakdown,
  useNetworthEvolution,
} from '../../hooks/useAnalytics';
import { WarningIcon } from '../../components/icons/Icons';

// ─── Color palette for categories without a color ─────────────────────────────

const PALETTE = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#06B6D4', '#F97316', '#84CC16', '#14B8A6',
  '#A855F7', '#FB923C',
];

// ─── Shared helpers ───────────────────────────────────────────────────────────

const MONTH_ABBR = ['Gen', 'Feb', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Des'];

function TabPills({
  options,
  value,
  onChange,
}: {
  options: { label: string; value: string | number }[];
  value: string | number;
  onChange: (v: string | number) => void;
}) {
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={String(o.value)}
            onClick={() => onChange(o.value)}
            style={{
              padding: '5px 12px',
              borderRadius: 20,
              border: `1px solid ${active ? 'var(--color-accent)' : 'var(--color-glass-border)'}`,
              background: active ? 'var(--color-accent)' : 'var(--color-glass-bg)',
              color: active ? '#fff' : 'var(--color-text-secondary)',
              fontSize: 12,
              fontFamily: 'var(--font-num)',
              cursor: 'pointer',
              fontWeight: active ? 600 : 400,
              transition: 'all 0.15s',
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

function SkeletonBar() {
  return (
    <div
      style={{
        height: 18,
        borderRadius: 4,
        background: 'var(--color-glass-bg)',
        animation: 'pulse 1.5s ease infinite',
        marginBottom: 8,
      }}
    />
  );
}

// ─── Tab 1: Despeses ──────────────────────────────────────────────────────────

const YEAR_OPTIONS = [2024, 2025, 2026].map((y) => ({ label: String(y), value: y }));
const MONTH_OPTIONS = [
  { label: "Tot l'any", value: 0 },
  ...MONTH_ABBR.map((m, i) => ({ label: m, value: i + 1 })),
];

function ExpensesTab() {
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [month, setMonth] = useState<number>(0); // 0 = full year

  const { data, isLoading } = useExpenseBreakdown(year, month === 0 ? undefined : month);

  const categories = data?.categories ?? [];
  const total = n(data?.total_eur);
  const maxVal = categories.length ? n(categories[0].total_eur) : 1;

  return (
    <div style={{ padding: '0 24px' }}>
      {/* Year selector */}
      <div style={{ marginBottom: 12 }}>
        <TabPills
          options={YEAR_OPTIONS}
          value={year}
          onChange={(v) => setYear(v as number)}
        />
      </div>
      {/* Month selector */}
      <div style={{ marginBottom: 16, overflowX: 'auto', paddingBottom: 4 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {MONTH_OPTIONS.map((o) => {
            const active = o.value === month;
            return (
              <button
                key={o.value}
                onClick={() => setMonth(o.value)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 16,
                  border: `1px solid ${active ? 'var(--color-accent)' : 'var(--color-glass-border)'}`,
                  background: active ? 'var(--color-accent)' : 'transparent',
                  color: active ? '#fff' : 'var(--color-text-tertiary)',
                  fontSize: 11,
                  fontFamily: 'var(--font-num)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s',
                }}
              >
                {o.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bar chart */}
      {isLoading ? (
        <>
          {Array.from({ length: 8 }).map((_, i) => <SkeletonBar key={i} />)}
        </>
      ) : categories.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '40px 0',
            color: 'var(--color-text-tertiary)',
            fontSize: 13,
          }}
        >
          No hi ha dades de despeses per aquest període.
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {categories.map((cat, i) => {
              const val = n(cat.total_eur);
              const pct = n(cat.pct_of_total);
              const barPct = (val / maxVal) * 100;
              const color = cat.color_hex || PALETTE[i % PALETTE.length];

              return (
                <div key={cat.category}>
                  {/* Label row */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: 4,
                      alignItems: 'baseline',
                    }}
                  >
                    <span
                      style={{
                        fontSize: 12,
                        color: 'var(--color-text-secondary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: '55%',
                      }}
                    >
                      {cat.category}
                    </span>
                    <span
                      style={{
                        fontSize: 11,
                        fontFamily: 'var(--font-num)',
                        color: 'var(--color-text)',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      €{val.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
                      <span
                        style={{
                          marginLeft: 6,
                          color: 'var(--color-text-tertiary)',
                          fontSize: 10,
                        }}
                      >
                        {pct.toFixed(1)}%
                      </span>
                    </span>
                  </div>
                  {/* Bar */}
                  <div
                    style={{
                      height: 8,
                      borderRadius: 4,
                      background: 'var(--color-glass-border)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${barPct}%`,
                        background: color,
                        borderRadius: 4,
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Total */}
          <div
            style={{
              marginTop: 16,
              paddingTop: 12,
              borderTop: '1px solid var(--color-glass-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span
              style={{
                fontSize: 12,
                color: 'var(--color-text-tertiary)',
                fontFamily: 'var(--font-num)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              Total despeses
            </span>
            <span
              style={{
                fontSize: 16,
                fontWeight: 700,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-negative, #EF4444)',
              }}
            >
              €{total.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Tab 2: Flux de Caixa ─────────────────────────────────────────────────────

const CASHFLOW_PERIODS = [
  { label: '3M', value: 3 },
  { label: '6M', value: 6 },
  { label: '12M', value: 12 },
];

const CF_INCOME_COLOR   = '#10B981';
const CF_EXPENSE_COLOR  = '#EF4444';
const CF_INVEST_COLOR   = '#3B82F6';

function CashflowTab() {
  const [months, setMonths] = useState<number>(12);
  const { data, isLoading } = useCashflow(months);

  const cfMonths = data?.months ?? [];
  const allVals = cfMonths.flatMap((m) => [
    n(m.income_eur), n(m.expenses_eur), n(m.investments_eur),
  ]);
  const maxVal = allVals.length ? Math.max(...allVals) : 1;

  const PAD = { top: 16, right: 8, bottom: 28, left: 44 };
  const SVG_W = 382;
  const SVG_H = 180;
  const chartW = SVG_W - PAD.left - PAD.right;
  const chartH = SVG_H - PAD.top - PAD.bottom;

  const barGroupW = cfMonths.length > 0 ? chartW / cfMonths.length : 1;
  const barW = Math.max(3, Math.min(10, barGroupW / 4));

  function formatK(v: number) {
    if (v >= 1000) return `${Math.round(v / 1000)}k`;
    return `${Math.round(v)}`;
  }

  const yLevels = 4;
  const yLabels = Array.from({ length: yLevels }, (_, i) => {
    const frac = i / (yLevels - 1);
    const val = maxVal * (1 - frac);
    return { val, y: PAD.top + frac * chartH };
  });

  return (
    <div style={{ padding: '0 24px' }}>
      <div style={{ marginBottom: 16 }}>
        <TabPills
          options={CASHFLOW_PERIODS}
          value={months}
          onChange={(v) => setMonths(v as number)}
        />
      </div>

      {isLoading ? (
        <div
          style={{
            height: 180,
            background: 'var(--color-glass-bg)',
            borderRadius: 12,
            animation: 'pulse 1.5s ease infinite',
          }}
        />
      ) : cfMonths.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '40px 0',
            color: 'var(--color-text-tertiary)',
            fontSize: 13,
          }}
        >
          No hi ha dades per a aquest període.
        </div>
      ) : (
        <>
          {/* SVG chart */}
          <svg
            viewBox={`0 0 ${SVG_W} ${SVG_H}`}
            width="100%"
            style={{ display: 'block', overflow: 'visible' }}
          >
            {/* Grid */}
            {yLabels.map(({ y, val }, i) => (
              <g key={i}>
                <line
                  x1={PAD.left}
                  y1={y}
                  x2={SVG_W - PAD.right}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={1}
                />
                <text
                  x={PAD.left - 4}
                  y={y + 3}
                  textAnchor="end"
                  fontSize={8}
                  fontFamily="var(--font-num)"
                  fill="rgba(255,255,255,0.3)"
                >
                  {formatK(val)}
                </text>
              </g>
            ))}

            {/* Bars */}
            {cfMonths.map((m, gi) => {
              const cx = PAD.left + gi * barGroupW + barGroupW / 2;
              const bars = [
                { v: n(m.income_eur),      color: CF_INCOME_COLOR,  offset: -barW },
                { v: n(m.expenses_eur),    color: CF_EXPENSE_COLOR, offset: 0 },
                { v: n(m.investments_eur), color: CF_INVEST_COLOR,  offset: barW },
              ];
              const monthStr = m.month.slice(5, 7);
              const monthNum = parseInt(monthStr, 10) - 1;
              const label = MONTH_ABBR[monthNum] ?? monthStr;
              const baseY = PAD.top + chartH;

              return (
                <g key={m.month}>
                  {bars.map(({ v, color, offset }, bi) => {
                    const barH = Math.max(2, ((v / (maxVal || 1)) * chartH));
                    const x = cx + offset - barW / 2;
                    return (
                      <rect
                        key={bi}
                        x={x}
                        y={baseY - barH}
                        width={barW}
                        height={barH}
                        fill={color}
                        fillOpacity={0.8}
                        rx={1}
                      />
                    );
                  })}
                  <text
                    x={cx}
                    y={SVG_H - PAD.bottom + 12}
                    textAnchor="middle"
                    fontSize={8}
                    fontFamily="var(--font-num)"
                    fill="rgba(255,255,255,0.35)"
                  >
                    {label}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div
            style={{
              display: 'flex',
              gap: 14,
              justifyContent: 'center',
              marginTop: 6,
              marginBottom: 16,
            }}
          >
            {[
              { color: CF_INCOME_COLOR,  label: 'Ingressos' },
              { color: CF_EXPENSE_COLOR, label: 'Despeses' },
              { color: CF_INVEST_COLOR,  label: 'Inversions' },
            ].map(({ color, label }) => (
              <div
                key={label}
                style={{ display: 'flex', alignItems: 'center', gap: 5 }}
              >
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: 2,
                    background: color,
                  }}
                />
                <span
                  style={{
                    fontSize: 10,
                    color: 'var(--color-text-tertiary)',
                    fontFamily: 'var(--font-num)',
                  }}
                >
                  {label}
                </span>
              </div>
            ))}
          </div>

          {/* Summary cards */}
          {data && (
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                {
                  label: 'Ingressos mitjans',
                  val: n(data.avg_income),
                  color: CF_INCOME_COLOR,
                },
                {
                  label: 'Despeses mitjanes',
                  val: n(data.avg_expenses),
                  color: CF_EXPENSE_COLOR,
                },
                {
                  label: "Taxa estalvi mitjana",
                  val: data.avg_savings_rate_pct != null ? n(data.avg_savings_rate_pct) : null,
                  color: '#F59E0B',
                  isPct: true,
                },
              ].map(({ label, val, color, isPct }) => (
                <div
                  key={label}
                  style={{
                    flex: 1,
                    padding: '10px 10px',
                    background: 'var(--color-glass-bg)',
                    border: '1px solid var(--color-glass-border)',
                    borderRadius: 12,
                  }}
                >
                  <div
                    style={{
                      fontSize: 9,
                      fontFamily: 'var(--font-num)',
                      color: 'var(--color-text-tertiary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      marginBottom: 4,
                    }}
                  >
                    {label}
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      fontFamily: 'var(--font-num)',
                      color,
                    }}
                  >
                    {val != null
                      ? isPct
                        ? `${(val as number).toFixed(1)}%`
                        : `€${(val as number).toLocaleString('ca-ES', { maximumFractionDigits: 0 })}`
                      : '—'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Tab 3: Evolució ──────────────────────────────────────────────────────────

const EVOLUTION_PERIODS = [
  { label: '12M', value: 12 },
  { label: '24M', value: 24 },
];

function EvolutionTab() {
  const [months, setMonths] = useState<number>(24);
  const { data, isLoading } = useNetworthEvolution(months);

  const nwMonths = data?.months ?? [];

  const PAD = { top: 16, right: 12, bottom: 28, left: 52 };
  const SVG_W = 382;
  const SVG_H = 200;
  const chartW = SVG_W - PAD.left - PAD.right;
  const chartH = SVG_H - PAD.top - PAD.bottom;

  const allTotal = nwMonths.map((m) => n(m.total_net_worth));
  const allInv   = nwMonths.map((m) => n(m.investment_value));
  const allVals  = [...allTotal, ...allInv];
  const rawMin   = allVals.length ? Math.min(...allVals) : 0;
  const rawMax   = allVals.length ? Math.max(...allVals) : 1;
  const padding  = (rawMax - rawMin) * 0.08;
  const minVal   = Math.max(0, rawMin - padding);
  const maxVal   = rawMax + padding || 1;

  function formatK(v: number) {
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `${Math.round(v / 1_000)}k`;
    return `${Math.round(v)}`;
  }

  function toX(i: number) {
    return PAD.left + (i / Math.max(nwMonths.length - 1, 1)) * chartW;
  }
  function toY(v: number) {
    return PAD.top + (1 - (v - minVal) / (maxVal - minVal)) * chartH;
  }

  function buildPath(vals: number[]) {
    if (vals.length < 2) return '';
    return vals
      .map((v, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(v).toFixed(1)}`)
      .join(' ');
  }

  const pathTotal = buildPath(allTotal);
  const pathInv   = buildPath(allInv);

  const yLevels = 5;
  const yLabels = Array.from({ length: yLevels }, (_, i) => {
    const frac = i / (yLevels - 1);
    return { val: minVal + (maxVal - minVal) * (1 - frac), y: PAD.top + frac * chartH };
  });

  // X labels: show every 3rd or 6th month
  const step = nwMonths.length <= 12 ? 2 : 4;
  const xLabels = nwMonths
    .map((m, i) => ({ m, i }))
    .filter(({ i }) => i % step === 0 || i === nwMonths.length - 1);

  return (
    <div style={{ padding: '0 24px' }}>
      <div style={{ marginBottom: 16 }}>
        <TabPills
          options={EVOLUTION_PERIODS}
          value={months}
          onChange={(v) => setMonths(v as number)}
        />
      </div>

      {isLoading ? (
        <div
          style={{
            height: 200,
            background: 'var(--color-glass-bg)',
            borderRadius: 12,
            animation: 'pulse 1.5s ease infinite',
          }}
        />
      ) : nwMonths.length < 2 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '40px 0',
            color: 'var(--color-text-tertiary)',
            fontSize: 13,
          }}
        >
          No hi ha prou dades d'evolució per mostrar.
        </div>
      ) : (
        <>
          <svg
            viewBox={`0 0 ${SVG_W} ${SVG_H}`}
            width="100%"
            style={{ display: 'block', overflow: 'visible' }}
          >
            {/* Grid */}
            {yLabels.map(({ val, y }, i) => (
              <g key={i}>
                <line
                  x1={PAD.left}
                  y1={y}
                  x2={SVG_W - PAD.right}
                  y2={y}
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={1}
                />
                <text
                  x={PAD.left - 4}
                  y={y + 3}
                  textAnchor="end"
                  fontSize={8}
                  fontFamily="var(--font-num)"
                  fill="rgba(255,255,255,0.3)"
                >
                  {formatK(val)}€
                </text>
              </g>
            ))}

            {/* X labels */}
            {xLabels.map(({ m, i }) => {
              const parts = m.month.split('-');
              const monthNum = parseInt(parts[1], 10) - 1;
              const label = MONTH_ABBR[monthNum] ?? parts[1];
              const yr = parts[0].slice(2);
              return (
                <text
                  key={m.month}
                  x={toX(i)}
                  y={SVG_H - PAD.bottom + 12}
                  textAnchor="middle"
                  fontSize={8}
                  fontFamily="var(--font-num)"
                  fill="rgba(255,255,255,0.3)"
                >
                  {label} '{yr}
                </text>
              );
            })}

            {/* Investment line (lighter, behind) */}
            <path
              d={pathInv}
              fill="none"
              stroke="#3B82F6"
              strokeWidth={1.5}
              strokeOpacity={0.45}
              strokeLinejoin="round"
              strokeLinecap="round"
              strokeDasharray="3 2"
            />

            {/* Total net worth line */}
            <path
              d={pathTotal}
              fill="none"
              stroke="#10B981"
              strokeWidth={2.5}
              strokeLinejoin="round"
              strokeLinecap="round"
            />

            {/* End dots */}
            {nwMonths.length > 0 && (() => {
              const lastIdx = nwMonths.length - 1;
              return (
                <>
                  <circle
                    cx={toX(lastIdx)}
                    cy={toY(allTotal[lastIdx])}
                    r={4}
                    fill="#10B981"
                  />
                  <circle
                    cx={toX(lastIdx)}
                    cy={toY(allInv[lastIdx])}
                    r={3}
                    fill="#3B82F6"
                    fillOpacity={0.6}
                  />
                </>
              );
            })()}
          </svg>

          {/* Legend */}
          <div
            style={{
              display: 'flex',
              gap: 16,
              justifyContent: 'center',
              marginTop: 6,
              marginBottom: 12,
            }}
          >
            {[
              { color: '#10B981', label: 'Net Worth total', dash: false },
              { color: '#3B82F6', label: 'Cartera inversió', dash: true },
            ].map(({ color, label, dash }) => (
              <div
                key={label}
                style={{ display: 'flex', alignItems: 'center', gap: 5 }}
              >
                <svg width={18} height={6}>
                  <line
                    x1={0}
                    y1={3}
                    x2={18}
                    y2={3}
                    stroke={color}
                    strokeWidth={dash ? 1.5 : 2.5}
                    strokeDasharray={dash ? '3 2' : undefined}
                    strokeOpacity={dash ? 0.6 : 1}
                  />
                </svg>
                <span
                  style={{
                    fontSize: 10,
                    color: 'var(--color-text-tertiary)',
                    fontFamily: 'var(--font-num)',
                  }}
                >
                  {label}
                </span>
              </div>
            ))}
          </div>

          {/* Last value */}
          {nwMonths.length > 0 && (
            <div
              style={{
                textAlign: 'center',
                padding: '12px 0 0',
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  color: 'var(--color-text-tertiary)',
                  fontFamily: 'var(--font-num)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: 4,
                }}
              >
                Últim registre — {nwMonths[nwMonths.length - 1].month}
              </div>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 700,
                  fontFamily: 'var(--font-num)',
                  color: '#10B981',
                  letterSpacing: '-0.02em',
                }}
              >
                €{n(nwMonths[nwMonths.length - 1].total_net_worth).toLocaleString('ca-ES', {
                  maximumFractionDigits: 0,
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Alerts banner ───────────────────────────────────────────────────────────

function AlertsBanner() {
  const { data } = useAnalyticsAlerts();
  const alerts = data?.alerts ?? [];
  if (!alerts.length) return null;

  const severityColor: Record<string, string> = {
    info:     '#3B82F6',
    warning:  '#F59E0B',
    critical: '#EF4444',
  };

  return (
    <div style={{ padding: '0 24px 16px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {alerts.map((a) => {
          const color = severityColor[a.severity] ?? '#3B82F6';
          return (
            <div
              key={a.id}
              style={{
                padding: '10px 12px',
                borderRadius: 12,
                border: `1px solid ${color}44`,
                background: `${color}11`,
                display: 'flex',
                gap: 10,
                alignItems: 'flex-start',
              }}
            >
              <div style={{ flexShrink: 0, paddingTop: 1 }}>
                <WarningIcon color={color} size={14} />
              </div>
              <div>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color,
                    marginBottom: 2,
                  }}
                >
                  {a.title}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--color-text-secondary)',
                    lineHeight: 1.4,
                  }}
                >
                  {a.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Main screen ─────────────────────────────────────────────────────────────

const TABS = [
  { id: 'expenses', label: 'Despeses' },
  { id: 'cashflow', label: 'Flux de Caixa' },
  { id: 'evolution', label: 'Evolució' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export function AnalyticsScreen() {
  const [activeTab, setActiveTab] = useState<TabId>('expenses');

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
      <div style={{ padding: '56px 24px 16px' }}>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            fontFamily: 'var(--font-display)',
          }}
        >
          Analítica
        </div>
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-text-tertiary)',
            marginTop: 2,
          }}
        >
          Patrons de despesa, flux de caixa i evolució
        </div>
      </div>

      {/* Alerts */}
      <AlertsBanner />

      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--color-glass-border)',
          marginBottom: 20,
          padding: '0 24px',
          gap: 0,
        }}
      >
        {TABS.map((tab) => {
          const active = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                padding: '10px 0',
                background: 'none',
                border: 'none',
                borderBottom: `2px solid ${active ? 'var(--color-accent)' : 'transparent'}`,
                color: active ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
                fontSize: 12,
                fontFamily: 'var(--font-num)',
                fontWeight: active ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s',
                letterSpacing: '0.04em',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {activeTab === 'expenses'  && <ExpensesTab />}
      {activeTab === 'cashflow'  && <CashflowTab />}
      {activeTab === 'evolution' && <EvolutionTab />}
    </div>
  );
}
