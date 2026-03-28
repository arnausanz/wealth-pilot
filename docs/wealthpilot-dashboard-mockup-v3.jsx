import { useState, useEffect, useRef, useMemo, useCallback } from "react";

// ─── Font constants ─────────────────────────────────────────────────────
const FONT_BODY = "'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif";
const FONT_DISPLAY = "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif";
const FONT_NUM = "'SF Pro Rounded', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif";

// ─── SVG Icon components (minimal, geometric, no emoji) ─────────────────
const Icons = {
  sun: (color) => (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
      <circle cx="9" cy="9" r="3.5" />
      <line x1="9" y1="1.5" x2="9" y2="3" /><line x1="9" y1="15" x2="9" y2="16.5" />
      <line x1="2.64" y1="2.64" x2="3.7" y2="3.7" /><line x1="14.3" y1="14.3" x2="15.36" y2="15.36" />
      <line x1="1.5" y1="9" x2="3" y2="9" /><line x1="15" y1="9" x2="16.5" y2="9" />
      <line x1="2.64" y1="15.36" x2="3.7" y2="14.3" /><line x1="14.3" y1="3.7" x2="15.36" y2="2.64" />
    </svg>
  ),
  moon: (color) => (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15.5 9.7A6.5 6.5 0 1 1 8.3 2.5a5 5 0 0 0 7.2 7.2Z" />
    </svg>
  ),
  home: (color) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7.5 10 2l7 5.5V16a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 16V7.5Z" />
      <path d="M7.5 17.5V11h5v6.5" />
    </svg>
  ),
  portfolio: (color) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="16" height="12" rx="2" />
      <path d="M2 9h16" /><circle cx="10" cy="12.5" r="1.5" />
    </svg>
  ),
  chart: (color) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3,14 7,9 11,11 17,4" />
      <polyline points="13,4 17,4 17,8" />
    </svg>
  ),
  list: (color) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round">
      <line x1="3" y1="5" x2="17" y2="5" /><line x1="3" y1="10" x2="17" y2="10" /><line x1="3" y1="15" x2="12" y2="15" />
    </svg>
  ),
  gear: (color) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="10" r="2.5" />
      <path d="M16.2 12.5a1.2 1.2 0 0 0 .2 1.3l.04.04a1.45 1.45 0 1 1-2.05 2.05l-.04-.04a1.2 1.2 0 0 0-1.3-.2 1.2 1.2 0 0 0-.73 1.1v.12a1.45 1.45 0 0 1-2.9 0v-.06a1.2 1.2 0 0 0-.79-1.1 1.2 1.2 0 0 0-1.3.2l-.04.04a1.45 1.45 0 1 1-2.05-2.05l.04-.04a1.2 1.2 0 0 0 .2-1.3 1.2 1.2 0 0 0-1.1-.73H4.15a1.45 1.45 0 0 1 0-2.9h.06a1.2 1.2 0 0 0 1.1-.79 1.2 1.2 0 0 0-.2-1.3l-.04-.04A1.45 1.45 0 1 1 7.12 5.1l.04.04a1.2 1.2 0 0 0 1.3.2h.06a1.2 1.2 0 0 0 .73-1.1V4.15a1.45 1.45 0 0 1 2.9 0v.06a1.2 1.2 0 0 0 .73 1.1 1.2 1.2 0 0 0 1.3-.2l.04-.04a1.45 1.45 0 1 1 2.05 2.05l-.04.04a1.2 1.2 0 0 0-.2 1.3v.06a1.2 1.2 0 0 0 1.1.73h.12a1.45 1.45 0 0 1 0 2.9h-.06a1.2 1.2 0 0 0-1.1.73Z" />
    </svg>
  ),
  analytics: (color) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="10" width="3.5" height="7" rx="0.5" />
      <rect x="8.25" y="6" width="3.5" height="11" rx="0.5" />
      <rect x="13.5" y="3" width="3.5" height="14" rx="0.5" />
    </svg>
  ),
  warning: (color) => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6.86 2.57 1.21 12a1.33 1.33 0 0 0 1.14 2h11.3a1.33 1.33 0 0 0 1.14-2L9.14 2.57a1.33 1.33 0 0 0-2.28 0Z" />
      <line x1="8" y1="6" x2="8" y2="9" /><circle cx="8" cy="11.5" r="0.5" fill={color} />
    </svg>
  ),
};

// ─── Fake data generation ───────────────────────────────────────────────
const ASSETS = [
  { name: "MSCI World", ticker: "EUNL", color: "#3B82F6", weight: 22, realWeight: 24.1, value: 5420, change: +1.2, shares: 67.3, avgPrice: 76.42 },
  { name: "Or físic", ticker: "PPFB", color: "#F59E0B", weight: 12, realWeight: 11.8, value: 2654, change: +0.4, shares: 12.1, avgPrice: 208.50 },
  { name: "MSCI Europe", ticker: "EUNK", color: "#8B5CF6", weight: 10, realWeight: 10.3, value: 2315, change: -0.3, shares: 325.6, avgPrice: 6.85 },
  { name: "MSCI EM IMI", ticker: "IS3N", color: "#06B6D4", weight: 5, realWeight: 4.7, value: 1058, change: +0.8, shares: 36.2, avgPrice: 28.10 },
  { name: "Japó", ticker: "CSJP", color: "#10B981", weight: 6, realWeight: 5.9, value: 1326, change: +1.5, shares: 78.4, avgPrice: 16.22 },
  { name: "Defensa Europa", ticker: "WDEF", color: "#F97316", weight: 5, realWeight: 5.4, value: 1214, change: +2.1, shares: 42.8, avgPrice: 26.88 },
  { name: "Bitcoin", ticker: "BTC", color: "#E11D48", weight: 2, realWeight: 2.3, value: 517, change: -1.8, shares: 0.0062, avgPrice: 72150 },
];

const CASH = { value: 6600, weight: 38, target: 28 };
const TOTAL_PORTFOLIO = ASSETS.reduce((s, a) => s + a.value, 0) + CASH.value;
const DAILY_CHANGE_EUR = +142.30;
const DAILY_CHANGE_PCT = +(DAILY_CHANGE_EUR / TOTAL_PORTFOLIO * 100).toFixed(2);

// Generate SEEDED time series (deterministic per range, so morphing is consistent)
const SEED_DATA = {};
function seededRandom(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
}
function generateTimeSeries(months, startValue, endValue, seed) {
  const key = `${months}-${seed}`;
  if (SEED_DATA[key]) return SEED_DATA[key];
  const N = 60; // always same number of points for morphing
  const rng = seededRandom(seed);
  const data = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const noise = (rng() - 0.45) * (endValue - startValue) * 0.08;
    const trend = startValue + (endValue - startValue) * (t * t * (3 - 2 * t));
    data.push(Math.round((trend + noise) * 100) / 100);
  }
  data[data.length - 1] = endValue;
  SEED_DATA[key] = data;
  return data;
}

const TIME_RANGES = {
  "1M": { label: "1M", months: 1, start: 20200, end: TOTAL_PORTFOLIO, seed: 111 },
  "3M": { label: "3M", months: 3, start: 19100, end: TOTAL_PORTFOLIO, seed: 222 },
  "6M": { label: "6M", months: 6, start: 17800, end: TOTAL_PORTFOLIO, seed: 333 },
  "1A": { label: "1A", months: 12, start: 14868, end: TOTAL_PORTFOLIO, seed: 444 },
  "Tot": { label: "Tot", months: 12, start: 14868, end: TOTAL_PORTFOLIO, seed: 555 },
};

// Pre-generate all series
Object.values(TIME_RANGES).forEach(r => generateTimeSeries(r.months, r.start, r.end, r.seed));

// ─── SVG Chart with MORPHING transition ─────────────────────────────────
function PortfolioChart({ targetData, isDark }) {
  const [displayData, setDisplayData] = useState(targetData);
  const animRef = useRef(null);
  const prevDataRef = useRef(targetData);

  // Morph from previous data to new data
  useEffect(() => {
    const fromData = prevDataRef.current;
    const toData = targetData;
    if (animRef.current) cancelAnimationFrame(animRef.current);

    const duration = 600;
    const start = performance.now();

    function tick(now) {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      // Cubic ease-in-out
      const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

      const interpolated = toData.map((target, i) => {
        const from = i < fromData.length ? fromData[i] : fromData[fromData.length - 1];
        return from + (target - from) * ease;
      });
      setDisplayData(interpolated);

      if (t < 1) {
        animRef.current = requestAnimationFrame(tick);
      } else {
        prevDataRef.current = toData;
      }
    }
    animRef.current = requestAnimationFrame(tick);
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [targetData]);

  const data = displayData;
  const min = Math.min(...data) * 0.98;
  const max = Math.max(...data) * 1.02;
  const W = 343;
  const H = 160;
  const padTop = 12;
  const padBot = 24;
  const chartH = H - padTop - padBot;

  const points = data.map((v, i) => ({
    x: (i / (data.length - 1)) * W,
    y: padTop + chartH - ((v - min) / (max - min)) * chartH,
  }));

  const pathD = useMemo(() => {
    if (points.length < 2) return "";
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const cp = (points[i + 1].x - points[i].x) / 3;
      d += ` C ${points[i].x + cp} ${points[i].y}, ${points[i + 1].x - cp} ${points[i + 1].y}, ${points[i + 1].x} ${points[i + 1].y}`;
    }
    return d;
  }, [points]);

  const areaD = pathD + ` L ${W} ${H - padBot} L 0 ${H - padBot} Z`;

  const gridLines = [0.25, 0.5, 0.75].map(pct => ({
    y: padTop + chartH * (1 - pct),
    label: `€${((min + (max - min) * pct) / 1000).toFixed(1)}k`,
  }));

  const lastPt = points[points.length - 1];
  const isPositive = data[data.length - 1] >= data[0];
  const accentColor = isPositive ? "#10B981" : "#EF4444";

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height={H}
      style={{ overflow: "visible", display: "block" }}
    >
      <defs>
        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={accentColor} stopOpacity="0.2" />
          <stop offset="100%" stopColor={accentColor} stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {gridLines.map((g, i) => (
        <g key={i}>
          <line
            x1="0" y1={g.y} x2={W} y2={g.y}
            stroke={isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)"}
            strokeDasharray="2 4"
          />
          <text
            x={W + 4} y={g.y + 3}
            fill={isDark ? "rgba(255,255,255,0.2)" : "rgba(0,0,0,0.2)"}
            fontSize="7" fontFamily={FONT_NUM}
          >
            {g.label}
          </text>
        </g>
      ))}

      <path d={areaD} fill="url(#chartGrad)" />
      <path
        d={pathD}
        fill="none"
        stroke={accentColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {lastPt && (
        <g>
          <circle cx={lastPt.x} cy={lastPt.y} r="3.5" fill={accentColor} />
          <circle cx={lastPt.x} cy={lastPt.y} r="8" fill={accentColor} opacity="0.15">
            <animate attributeName="r" values="6;11;6" dur="2.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.2;0.04;0.2" dur="2.5s" repeatCount="indefinite" />
          </circle>
        </g>
      )}
    </svg>
  );
}

// ─── Mini donut chart ───────────────────────────────────────────────────
function DonutChart({ isDark }) {
  const [hovered, setHovered] = useState(null);
  const allItems = [...ASSETS, { name: "Efectiu", color: isDark ? "#475569" : "#94A3B8", realWeight: CASH.target, value: CASH.value }];
  const total = allItems.reduce((s, a) => s + a.value, 0);

  const size = 120;
  const cx = size / 2;
  const cy = size / 2;
  const r = 42;
  const stroke = 14;

  let cumAngle = -90;
  const segments = allItems.map((a) => {
    const pct = a.value / total;
    const angle = pct * 360;
    const startAngle = cumAngle;
    cumAngle += angle;
    return { ...a, pct, startAngle, angle };
  });

  function arcPath(startDeg, sweepDeg, radius) {
    const s = (startDeg * Math.PI) / 180;
    const e = ((startDeg + sweepDeg) * Math.PI) / 180;
    const x1 = cx + radius * Math.cos(s);
    const y1 = cy + radius * Math.sin(s);
    const x2 = cx + radius * Math.cos(e);
    const y2 = cy + radius * Math.sin(e);
    const large = sweepDeg > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2}`;
  }

  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
        {segments.map((seg, i) => (
          <path
            key={i}
            d={arcPath(seg.startAngle, seg.angle - 1, r)}
            fill="none"
            stroke={seg.color}
            strokeWidth={hovered === i ? stroke + 4 : stroke}
            strokeLinecap="round"
            style={{ transition: "stroke-width 0.3s ease", cursor: "pointer", opacity: hovered !== null && hovered !== i ? 0.4 : 1 }}
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}
          />
        ))}
      </svg>
      <div style={{
        position: "absolute", inset: 0, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", pointerEvents: "none"
      }}>
        {hovered !== null ? (
          <>
            <span style={{ fontSize: 11, fontWeight: 600, color: segments[hovered].color }}>
              {segments[hovered].name}
            </span>
            <span style={{
              fontSize: 10, fontFamily: FONT_NUM,
              color: isDark ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.5)"
            }}>
              {(segments[hovered].pct * 100).toFixed(1)}%
            </span>
          </>
        ) : (
          <>
            <span style={{
              fontSize: 9, fontFamily: FONT_NUM, letterSpacing: "0.04em",
              color: isDark ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.35)"
            }}>
              TOTAL
            </span>
            <span style={{
              fontSize: 14, fontWeight: 600,
              color: isDark ? "rgba(255,255,255,0.85)" : "rgba(0,0,0,0.85)"
            }}>
              €{(total / 1000).toFixed(1)}k
            </span>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Progress ring for housing goal ─────────────────────────────────────
function GoalRing({ current, target, isDark }) {
  const pct = Math.min(current / target, 1);
  const r = 28;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);

  return (
    <svg width="72" height="72" viewBox="0 0 72 72">
      <circle cx="36" cy="36" r={r} fill="none"
        stroke={isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"} strokeWidth="5" />
      <circle cx="36" cy="36" r={r} fill="none"
        stroke="#3B82F6" strokeWidth="5" strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={offset}
        transform="rotate(-90 36 36)"
        style={{ transition: "stroke-dashoffset 1s ease" }}
      />
      <text x="36" y="34" textAnchor="middle" fontSize="13" fontWeight="600"
        fill={isDark ? "#E2E8F0" : "#1E293B"} fontFamily={FONT_NUM}>
        {Math.round(pct * 100)}%
      </text>
      <text x="36" y="46" textAnchor="middle" fontSize="7"
        fill={isDark ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.35)"}
        fontFamily={FONT_NUM} letterSpacing="0.03em">
        de €{(target/1000)}k
      </text>
    </svg>
  );
}

// ─── Main Dashboard ─────────────────────────────────────────────────────
export default function WealthPilotDashboard() {
  const [isDark, setIsDark] = useState(() =>
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  const [timeRange, setTimeRange] = useState("1A");
  const [showCustom, setShowCustom] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e) => setIsDark(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const chartData = useMemo(() => {
    const r = TIME_RANGES[timeRange];
    return generateTimeSeries(r.months, r.start, r.end, r.seed);
  }, [timeRange]);

  const handleTimeChange = useCallback((range) => {
    setShowCustom(false);
    setTimeRange(range);
  }, []);

  // ─── Liquid Glass Theme tokens ──────────────────────────────
  const t = isDark ? {
    bg: "#0B0F19",
    surface: "rgba(255,255,255,0.04)",
    surfaceElevated: "rgba(255,255,255,0.06)",
    glassBg: "rgba(255,255,255,0.05)",
    glassBorder: "rgba(255,255,255,0.08)",
    glassBlur: "blur(40px) saturate(1.8)",
    border: "rgba(255,255,255,0.06)",
    text: "#F1F5F9",
    textSecondary: "rgba(255,255,255,0.55)",
    textTertiary: "rgba(255,255,255,0.25)",
    accent: "#3B82F6",
    positive: "#34D399",
    negative: "#FB7185",
    warning: "#FBBF24",
    cardShadow: "0 2px 8px rgba(0,0,0,0.2), 0 0 1px rgba(255,255,255,0.05) inset",
    navBg: "rgba(11,15,25,0.75)",
  } : {
    bg: "#F2F4F8",
    surface: "rgba(255,255,255,0.65)",
    surfaceElevated: "rgba(255,255,255,0.75)",
    glassBg: "rgba(255,255,255,0.5)",
    glassBorder: "rgba(255,255,255,0.7)",
    glassBlur: "blur(40px) saturate(1.8)",
    border: "rgba(0,0,0,0.05)",
    text: "#0F172A",
    textSecondary: "rgba(0,0,0,0.5)",
    textTertiary: "rgba(0,0,0,0.25)",
    accent: "#2563EB",
    positive: "#059669",
    negative: "#DC2626",
    warning: "#D97706",
    cardShadow: "0 2px 12px rgba(0,0,0,0.04), 0 0 1px rgba(255,255,255,0.8) inset",
    navBg: "rgba(242,244,248,0.75)",
  };

  const changeInRange = TIME_RANGES[timeRange].end - TIME_RANGES[timeRange].start;
  const changePct = ((changeInRange / TIME_RANGES[timeRange].start) * 100).toFixed(1);

  const onTrackPct = 102.3;
  const onTrackStatus = onTrackPct >= 95 ? "green" : onTrackPct >= 85 ? "yellow" : "red";
  const statusColors = { green: t.positive, yellow: t.warning, red: t.negative };
  const statusLabels = { green: "On Track", yellow: "Atenció", red: "Per sota" };

  return (
    <div style={{
      background: t.bg,
      minHeight: "100vh",
      fontFamily: FONT_BODY,
      color: t.text,
      maxWidth: 430,
      margin: "0 auto",
      position: "relative",
      paddingBottom: 88,
      transition: "background 0.4s ease, color 0.4s ease",
    }}>
      {/* ─── Status bar ─── */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "14px 24px 0", fontSize: 12, fontWeight: 600,
        color: t.textSecondary,
      }}>
        <span>9:41</span>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <svg width="16" height="12" viewBox="0 0 16 12" fill={t.textSecondary}>
            <rect x="0" y="6" width="3" height="6" rx="0.5" />
            <rect x="4.5" y="4" width="3" height="8" rx="0.5" />
            <rect x="9" y="1.5" width="3" height="10.5" rx="0.5" />
            <rect x="13.5" y="0" width="2.5" height="12" rx="0.5" opacity="0.3" />
          </svg>
          <svg width="18" height="12" viewBox="0 0 18 12" fill="none" stroke={t.textSecondary} strokeWidth="1.2">
            <rect x="0.5" y="1" width="14" height="10" rx="2" />
            <rect x="15" y="4" width="2" height="4" rx="0.5" fill={t.textSecondary} />
            <rect x="2" y="3" width="8" height="6" rx="1" fill={t.positive} />
          </svg>
        </div>
      </div>

      {/* ─── Header ─── */}
      <div style={{ padding: "20px 24px 0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{
              fontSize: 10, fontFamily: FONT_NUM,
              letterSpacing: "0.14em", color: t.accent, fontWeight: 600,
              marginBottom: 2,
            }}>
              WEALTHPILOT
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em", fontFamily: FONT_DISPLAY }}>
              Dashboard
            </div>
          </div>
          <button
            onClick={() => setIsDark(!isDark)}
            style={{
              width: 36, height: 36, borderRadius: 12,
              background: t.glassBg,
              backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
              border: `1px solid ${t.glassBorder}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer", transition: "all 0.3s ease",
            }}
            title="Canviar tema"
          >
            {isDark ? Icons.sun(t.textSecondary) : Icons.moon(t.textSecondary)}
          </button>
        </div>
      </div>

      {/* ─── Portfolio Value Hero ─── */}
      <div style={{ padding: "24px 24px 0" }}>
        <div style={{
          fontSize: 11, fontFamily: FONT_NUM, letterSpacing: "0.06em",
          color: t.textTertiary, textTransform: "uppercase", marginBottom: 6,
        }}>
          Patrimoni total
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{
            fontSize: 38, fontWeight: 300, letterSpacing: "-0.03em",
            fontFamily: FONT_NUM,
          }}>
            €{TOTAL_PORTFOLIO.toLocaleString("ca-ES")}
          </span>
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 6, alignItems: "center" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            fontSize: 13, fontWeight: 500,
            color: DAILY_CHANGE_EUR >= 0 ? t.positive : t.negative,
            fontFamily: FONT_NUM,
          }}>
            {DAILY_CHANGE_EUR >= 0 ? "▲" : "▼"} €{Math.abs(DAILY_CHANGE_EUR).toFixed(2)}
            <span style={{ opacity: 0.7 }}>({DAILY_CHANGE_PCT >= 0 ? "+" : ""}{DAILY_CHANGE_PCT}%)</span>
          </span>
          <span style={{
            fontSize: 11, color: t.textTertiary,
            fontFamily: FONT_BODY,
          }}>
            avui
          </span>
        </div>
      </div>

      {/* ─── Chart Section ─── */}
      <div style={{ padding: "20px 24px 0" }}>
        {/* Time range selector */}
        <div style={{
          display: "flex", gap: 2, marginBottom: 16,
          background: t.glassBg,
          backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
          borderRadius: 12, padding: 3,
          border: `1px solid ${t.glassBorder}`,
        }}>
          {Object.keys(TIME_RANGES).map(key => (
            <button
              key={key}
              onClick={() => handleTimeChange(key)}
              style={{
                flex: 1, padding: "8px 0", borderRadius: 10, border: "none",
                background: timeRange === key
                  ? (isDark ? "rgba(59,130,246,0.2)" : "rgba(37,99,235,0.12)")
                  : "transparent",
                color: timeRange === key ? t.accent : t.textTertiary,
                fontSize: 12, fontWeight: 600,
                fontFamily: FONT_NUM, letterSpacing: "0.02em",
                cursor: "pointer",
                transition: "all 0.25s ease",
              }}
            >
              {key}
            </button>
          ))}
          <button
            onClick={() => { setShowCustom(!showCustom); }}
            style={{
              flex: 1.2, padding: "7px 0", borderRadius: 8, border: "none",
              background: showCustom
                ? (isDark ? "rgba(59,130,246,0.2)" : "rgba(37,99,235,0.1)")
                : "transparent",
              color: showCustom ? t.accent : t.textTertiary,
              fontSize: 10, fontWeight: 600,
              fontFamily: FONT_NUM,
              cursor: "pointer", transition: "all 0.25s ease",
            }}
          >
            Custom
          </button>
        </div>

        {/* Custom date picker (collapsed by default) */}
        {showCustom && (
          <div style={{
            display: "flex", gap: 8, marginBottom: 14,
            animation: "slideDown 0.3s ease",
          }}>
            <div style={{ flex: 1 }}>
              <label style={{
                fontSize: 9, fontFamily: FONT_NUM,
                color: t.textTertiary, letterSpacing: "0.1em", display: "block", marginBottom: 4,
              }}>DES DE</label>
              <input type="date" defaultValue="2025-04-01" style={{
                width: "100%", padding: "8px 10px",
                background: t.glassBg, border: `1px solid ${t.glassBorder}`,
                backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
                color: t.text, fontSize: 12, fontFamily: FONT_NUM,
                outline: "none", borderRadius: 10,
              }} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{
                fontSize: 9, fontFamily: FONT_NUM,
                color: t.textTertiary, letterSpacing: "0.1em", display: "block", marginBottom: 4,
              }}>FINS A</label>
              <input type="date" defaultValue="2026-03-28" style={{
                width: "100%", padding: "8px 10px",
                background: t.glassBg, border: `1px solid ${t.glassBorder}`,
                backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
                color: t.text, fontSize: 12, fontFamily: FONT_NUM,
                outline: "none", borderRadius: 10,
              }} />
            </div>
          </div>
        )}

        {/* Period change summary */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 8,
        }}>
          <span style={{
            fontSize: 11, color: t.textSecondary, fontFamily: FONT_NUM,
          }}>
            {timeRange === "Tot" ? "Abr 2025 – Ara" :
             timeRange === "1M" ? "Últim mes" :
             timeRange === "3M" ? "Últims 3 mesos" :
             timeRange === "6M" ? "Últims 6 mesos" : "Últim any"}
          </span>
          <span style={{
            fontSize: 12, fontWeight: 600,
            color: changeInRange >= 0 ? t.positive : t.negative,
            fontFamily: FONT_NUM,
          }}>
            {changeInRange >= 0 ? "+" : ""}€{changeInRange.toLocaleString("ca-ES")} ({changePct}%)
          </span>
        </div>

        {/* Chart */}
        <div style={{
          background: t.glassBg,
          backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
          borderRadius: 16, padding: "16px 12px 8px",
          border: `1px solid ${t.glassBorder}`,
          boxShadow: t.cardShadow,
        }}>
          <PortfolioChart targetData={chartData} isDark={isDark} />
        </div>
      </div>

      {/* ─── Status Cards ─── */}
      <div style={{ padding: "20px 24px 0" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {/* On Track */}
          <div style={{
            background: t.glassBg,
            backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
            borderRadius: 16, padding: 14,
            border: `1px solid ${t.glassBorder}`, boxShadow: t.cardShadow,
          }}>
            <div style={{
              display: "flex", alignItems: "center", gap: 6, marginBottom: 8,
            }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: statusColors[onTrackStatus],
                boxShadow: `0 0 8px ${statusColors[onTrackStatus]}60`,
              }} />
              <span style={{
                fontSize: 9, fontFamily: FONT_NUM,
                letterSpacing: "0.06em", color: t.textTertiary,
                textTransform: "uppercase",
              }}>
                PROJECCIÓ
              </span>
            </div>
            <div style={{
              fontSize: 22, fontWeight: 600, color: statusColors[onTrackStatus],
              fontFamily: FONT_NUM,
            }}>
              {onTrackPct}%
            </div>
            <div style={{
              fontSize: 10, color: t.textTertiary, marginTop: 2,
              fontFamily: FONT_NUM,
            }}>
              {statusLabels[onTrackStatus]}
            </div>
          </div>

          {/* Housing Goal */}
          <div style={{
            background: t.glassBg,
            backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
            borderRadius: 16, padding: 14,
            border: `1px solid ${t.glassBorder}`, boxShadow: t.cardShadow,
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <div>
              <div style={{
                fontSize: 9, fontFamily: FONT_NUM,
                letterSpacing: "0.06em", color: t.textTertiary,
                textTransform: "uppercase", marginBottom: 6,
              }}>
                HABITATGE
              </div>
              <div style={{
                fontSize: 16, fontWeight: 600,
                fontFamily: FONT_NUM,
                color: t.text,
              }}>
                €{(CASH.value / 1000).toFixed(1)}k
              </div>
              <div style={{
                fontSize: 9, color: t.textTertiary, marginTop: 2,
                fontFamily: FONT_NUM,
              }}>
                de €40k · 2029
              </div>
            </div>
            <GoalRing current={CASH.value} target={40000} isDark={isDark} />
          </div>
        </div>
      </div>

      {/* ─── Asset Allocation ─── */}
      <div style={{ padding: "20px 24px 0" }}>
        <div style={{
          background: t.glassBg,
          backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
          borderRadius: 16, padding: "18px 16px",
          border: `1px solid ${t.glassBorder}`, boxShadow: t.cardShadow,
        }}>
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            marginBottom: 16,
          }}>
            <span style={{
              fontSize: 10, fontFamily: FONT_NUM,
              letterSpacing: "0.06em", color: t.textTertiary,
              textTransform: "uppercase",
            }}>
              Distribució
            </span>
            <span style={{
              fontSize: 10, fontFamily: FONT_NUM,
              color: t.accent, cursor: "pointer",
            }}>
              Veure detall →
            </span>
          </div>

          <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
            <DonutChart isDark={isDark} />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 5 }}>
              {ASSETS.slice(0, 5).map((a, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 6, height: 6, borderRadius: 2, background: a.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 10, color: t.textSecondary, flex: 1 }}>{a.name}</span>
                  <span style={{
                    fontSize: 10, fontFamily: FONT_NUM,
                    color: t.text, fontWeight: 500,
                  }}>
                    {a.realWeight}%
                  </span>
                  <span style={{
                    fontSize: 8, fontFamily: FONT_NUM,
                    color: Math.abs(a.realWeight - a.weight) > 3 ? t.warning : t.textTertiary,
                  }}>
                    ({a.weight}%)
                  </span>
                </div>
              ))}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ width: 6, height: 6, borderRadius: 2, background: isDark ? "#475569" : "#94A3B8", flexShrink: 0 }} />
                <span style={{ fontSize: 10, color: t.textSecondary, flex: 1 }}>+3 més</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Top Movers ─── */}
      <div style={{ padding: "20px 24px 0" }}>
        <div style={{
          fontSize: 10, fontFamily: FONT_NUM,
          letterSpacing: "0.06em", color: t.textTertiary,
          textTransform: "uppercase", marginBottom: 10,
        }}>
          Moviments del dia
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {[...ASSETS].sort((a, b) => Math.abs(b.change) - Math.abs(a.change)).slice(0, 4).map((a, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "12px 14px",
              background: t.glassBg,
              backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
              border: `1px solid ${t.glassBorder}`,
              borderRadius: i === 0 ? "14px 14px 2px 2px" :
                           i === 3 ? "2px 2px 14px 14px" : "2px",
              boxShadow: i === 0 ? t.cardShadow : "none",
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: 10,
                background: `${a.color}15`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 11, fontWeight: 700, color: a.color,
                fontFamily: FONT_NUM,
              }}>
                {a.ticker.slice(0, 2)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{a.name}</div>
                <div style={{
                  fontSize: 10, color: t.textTertiary,
                  fontFamily: FONT_NUM,
                }}>
                  €{a.value.toLocaleString("ca-ES")}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{
                  fontSize: 13, fontWeight: 600,
                  fontFamily: FONT_NUM,
                  color: a.change >= 0 ? t.positive : t.negative,
                }}>
                  {a.change >= 0 ? "+" : ""}{a.change}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ─── Alerts ─── */}
      <div style={{ padding: "20px 24px 0" }}>
        <div style={{
          background: `${t.warning}10`,
          backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
          border: `1px solid ${t.warning}25`,
          borderRadius: 16, padding: 14,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            {Icons.warning(t.warning)}
            <span style={{
              fontSize: 10, fontFamily: FONT_NUM,
              letterSpacing: "0.06em", color: t.warning,
              textTransform: "uppercase", fontWeight: 600,
            }}>
              Alerta d'assignació
            </span>
          </div>
          <div style={{ fontSize: 12, color: t.textSecondary, lineHeight: 1.5 }}>
            <strong style={{ color: t.text }}>Efectiu</strong> al {CASH.target}% — per sobre de l'objectiu del {CASH.weight}%.
            Considera redistribuir cap a renda variable.
          </div>
        </div>
      </div>

      {/* ─── Quick Actions ─── */}
      <div style={{ padding: "24px 24px 32px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
          {[
            { icon: "portfolio", label: "Cartera" },
            { icon: "chart", label: "Simular" },
            { icon: "analytics", label: "Analítica" },
          ].map((item, i) => (
            <button key={i} style={{
              background: t.glassBg,
              backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
              border: `1px solid ${t.glassBorder}`,
              borderRadius: 16, padding: "14px 8px",
              display: "flex", flexDirection: "column",
              alignItems: "center", gap: 6, cursor: "pointer",
              transition: "all 0.2s ease",
            }}>
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>{Icons[item.icon] ? Icons[item.icon](t.accent) : item.icon}</span>
              <span style={{
                fontSize: 10, fontFamily: FONT_NUM,
                color: t.textSecondary, letterSpacing: "0.06em",
              }}>
                {item.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ─── Bottom Nav Bar ─── */}
      <div style={{
        position: "fixed", bottom: 0, left: "50%", transform: "translateX(-50%)",
        width: "100%", maxWidth: 430,
        background: t.navBg,
        backdropFilter: t.glassBlur, WebkitBackdropFilter: t.glassBlur,
        borderTop: `1px solid ${t.glassBorder}`,
        display: "flex", justifyContent: "space-around", alignItems: "center",
        padding: "8px 0 20px", zIndex: 100,
      }}>
        {[
          { icon: "home", label: "Inici", active: true },
          { icon: "portfolio", label: "Cartera", active: false },
          { icon: "chart", label: "Sim", active: false },
          { icon: "list", label: "Historial", active: false },
          { icon: "gear", label: "Config", active: false },
        ].map((item, i) => (
          <button key={i} style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            background: "none", border: "none", cursor: "pointer",
            padding: "4px 12px",
          }}>
            <span style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.2s ease",
            }}>
              {Icons[item.icon] ? Icons[item.icon](item.active ? t.accent : t.textTertiary) : item.icon}
            </span>
            <span style={{
              fontSize: 9, fontFamily: FONT_NUM,
              letterSpacing: "0.08em",
              color: item.active ? t.accent : t.textTertiary,
              fontWeight: item.active ? 600 : 400,
              transition: "color 0.2s ease",
            }}>
              {item.label}
            </span>
          </button>
        ))}
      </div>

      <style>{`
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        input[type="date"]::-webkit-calendar-picker-indicator {
          filter: ${isDark ? "invert(1)" : "none"};
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        button:hover { opacity: 0.85; }
        button:active { transform: scale(0.97); }
      `}</style>
    </div>
  );
}
