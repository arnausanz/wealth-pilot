import { useState, useEffect, useRef, useMemo } from 'react';

interface PortfolioChartProps {
  data: number[];
  width?: number;
  height?: number;
}

const W = 343;
const H = 160;
const PAD_TOP = 12;
const PAD_BOT = 24;
const CHART_H = H - PAD_TOP - PAD_BOT;

function cubicEaseInOut(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// Normalize data to exactly N points
function normalizeToN(data: number[], n: number): number[] {
  if (data.length === 0) return Array(n).fill(0);
  if (data.length === n) return data;
  const result: number[] = [];
  for (let i = 0; i < n; i++) {
    const t = (i / (n - 1)) * (data.length - 1);
    const lo = Math.floor(t);
    const hi = Math.min(lo + 1, data.length - 1);
    const frac = t - lo;
    result.push(data[lo] + (data[hi] - data[lo]) * frac);
  }
  return result;
}

export function PortfolioChart({ data }: PortfolioChartProps) {
  const N = 60;
  const targetData = useMemo(() => normalizeToN(data, N), [data]);
  const [displayData, setDisplayData] = useState<number[]>(targetData);
  const animRef = useRef<number | null>(null);
  const prevDataRef = useRef<number[]>(targetData);

  useEffect(() => {
    const fromData = prevDataRef.current;
    const toData = targetData;
    if (animRef.current !== null) cancelAnimationFrame(animRef.current);

    const duration = 600;
    const startTime = performance.now();

    function tick(now: number) {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);
      const ease = cubicEaseInOut(t);

      const interpolated = toData.map((target, i) => {
        const from = i < fromData.length ? fromData[i] : fromData[fromData.length - 1];
        return from + (target - from) * ease;
      });
      setDisplayData(interpolated);

      if (t < 1) {
        animRef.current = requestAnimationFrame(tick);
      } else {
        prevDataRef.current = toData;
        animRef.current = null;
      }
    }

    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current !== null) cancelAnimationFrame(animRef.current);
    };
  }, [targetData]);

  if (displayData.length === 0) return null;

  const min = Math.min(...displayData) * 0.98;
  const max = Math.max(...displayData) * 1.02;
  const range = max - min || 1;

  const points = displayData.map((v, i) => ({
    x: (i / (displayData.length - 1)) * W,
    y: PAD_TOP + CHART_H - ((v - min) / range) * CHART_H,
  }));

  const pathD = (() => {
    if (points.length < 2) return '';
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const cp = (points[i + 1].x - points[i].x) / 3;
      d += ` C ${points[i].x + cp} ${points[i].y}, ${points[i + 1].x - cp} ${points[i + 1].y}, ${points[i + 1].x} ${points[i + 1].y}`;
    }
    return d;
  })();

  const areaD = pathD + ` L ${W} ${H - PAD_BOT} L 0 ${H - PAD_BOT} Z`;

  const gridLines = [0.25, 0.5, 0.75].map((pct) => ({
    y: PAD_TOP + CHART_H * (1 - pct),
    label: `€${((min + range * pct) / 1000).toFixed(1)}k`,
  }));

  const lastPt = points[points.length - 1];
  const isPositive = displayData[displayData.length - 1] >= displayData[0];
  const accentColor = isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
  const gradientId = `chartGrad-${isPositive ? 'pos' : 'neg'}`;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height={H}
      style={{ overflow: 'visible', display: 'block' }}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={accentColor} stopOpacity="0.2" />
          <stop offset="100%" stopColor={accentColor} stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {gridLines.map((g, i) => (
        <g key={i}>
          <line
            x1="0"
            y1={g.y}
            x2={W}
            y2={g.y}
            stroke="var(--color-border)"
            strokeDasharray="2 4"
          />
          <text
            x={W + 4}
            y={g.y + 3}
            fill="var(--color-text-tertiary)"
            fontSize="7"
            fontFamily="var(--font-num)"
          >
            {g.label}
          </text>
        </g>
      ))}

      <path d={areaD} fill={`url(#${gradientId})`} />
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
            <animate
              attributeName="r"
              values="6;11;6"
              dur="2.5s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="0.2;0.04;0.2"
              dur="2.5s"
              repeatCount="indefinite"
            />
          </circle>
        </g>
      )}
    </svg>
  );
}
