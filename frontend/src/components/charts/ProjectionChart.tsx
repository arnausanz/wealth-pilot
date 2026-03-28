/**
 * ProjectionChart — SVG de 3 línies de projecció financera.
 *
 * Mostra 3 escenaris (advers/base/optimista) en un gràfic de línies SVG.
 * Inclou: àrea sombreada entre advers i optimista, línia d'objectiu,
 * etiquetes d'eix, i animació d'entrada.
 *
 * Props:
 *   adverse / base / optimistic: arrays de Decimal (mensuals)
 *   horizonYears: nombre d'anys
 *   goalValue: línia horitzontal d'objectiu (opcional)
 *   width / height: dimensions del SVG
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { n } from '../../types';

interface ProjectionChartProps {
  adverse: (string | number)[];
  base: (string | number)[];
  optimistic: (string | number)[];
  horizonYears: number;
  goalValue?: number | null;
  width?: number;
  height?: number;
}

const COLORS = {
  adverse:    '#EF4444',
  base:       '#3B82F6',
  optimistic: '#10B981',
};

const PAD = { top: 20, right: 16, bottom: 32, left: 56 };

function formatK(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000)     return `${Math.round(v / 1_000)}k`;
  return `${Math.round(v)}`;
}

function buildPath(
  points: number[],
  minVal: number,
  maxVal: number,
  chartW: number,
  chartH: number,
): string {
  if (points.length < 2) return '';
  const total = points.length - 1;
  const range = maxVal - minVal || 1;
  return points
    .map((v, i) => {
      const x = PAD.left + (i / total) * chartW;
      const y = PAD.top + (1 - (v - minVal) / range) * chartH;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

function buildAreaPath(
  lower: number[],
  upper: number[],
  minVal: number,
  maxVal: number,
  chartW: number,
  chartH: number,
): string {
  if (!lower.length || !upper.length) return '';
  const total = lower.length - 1;
  const range = maxVal - minVal || 1;

  const toX = (i: number) => PAD.left + (i / total) * chartW;
  const toY = (v: number) => PAD.top + (1 - (v - minVal) / range) * chartH;

  const top = upper.map((v, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ');
  const bot = [...lower].reverse().map((v, i) => `L${toX(lower.length - 1 - i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ');
  return `${top} ${bot} Z`;
}

export function ProjectionChart({
  adverse,
  base,
  optimistic,
  horizonYears,
  goalValue,
  width = 390,
  height = 240,
}: ProjectionChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [animPct, setAnimPct] = useState(0);
  // Controla si ja s'ha executat l'animació inicial
  const hasAnimatedRef = useRef(false);
  const rafRef = useRef<number>(0);

  const runAnimation = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    let start: number | null = null;
    const duration = 700;

    function frame(ts: number) {
      if (!start) start = ts;
      const elapsed = ts - start;
      const pct = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - pct, 3);
      setAnimPct(eased);
      if (pct < 1) rafRef.current = requestAnimationFrame(frame);
    }
    rafRef.current = requestAnimationFrame(frame);
  }, []);

  // Anima únicament quan arriben dades per primera vegada
  // En canvis d'horitzó (slider) simplement actualitza les dades sense re-animar
  useEffect(() => {
    const hasData = adverse.length > 1 && base.length > 1;
    if (!hasData) return;

    if (!hasAnimatedRef.current) {
      hasAnimatedRef.current = true;
      setAnimPct(0);
      runAnimation();
    } else {
      // Dades actualitzades (nou horitzó): mostra directament sense reiniciar
      setAnimPct(1);
    }

    return () => cancelAnimationFrame(rafRef.current);
  }, [adverse, base, optimistic, runAnimation]);

  if (!adverse.length || !base.length || !optimistic.length) return null;

  const advNums  = adverse.map(n);
  const baseNums = base.map(n);
  const optNums  = optimistic.map(n);

  const allVals  = [...advNums, ...baseNums, ...optNums];
  const rawMin   = Math.min(...allVals);
  const rawMax   = Math.max(...allVals);
  const padding  = (rawMax - rawMin) * 0.08;
  const minVal   = Math.max(0, rawMin - padding);
  const maxVal   = rawMax + padding;

  const chartW   = width - PAD.left - PAD.right;
  const chartH   = height - PAD.top - PAD.bottom;

  // Si animem, agafem un slice proporcional dels punts
  const sliceLen = Math.max(2, Math.round(animPct * advNums.length));
  const sliceAdv  = advNums.slice(0, sliceLen);
  const sliceBase = baseNums.slice(0, sliceLen);
  const sliceOpt  = optNums.slice(0, sliceLen);

  const pathAdv  = buildPath(sliceAdv,  minVal, maxVal, chartW, chartH);
  const pathBase = buildPath(sliceBase, minVal, maxVal, chartW, chartH);
  const pathOpt  = buildPath(sliceOpt,  minVal, maxVal, chartW, chartH);
  const areaPath = buildAreaPath(sliceAdv, sliceOpt, minVal, maxVal, chartW, chartH);

  // Y-axis labels (5 nivells)
  const yLevels = 5;
  const yLabels = Array.from({ length: yLevels }, (_, i) => {
    const frac = i / (yLevels - 1);
    const val  = minVal + (maxVal - minVal) * (1 - frac);
    const y    = PAD.top + frac * chartH;
    return { val, y };
  });

  // X-axis labels (each 2 years or adaptive)
  const step = horizonYears <= 5 ? 1 : horizonYears <= 15 ? 2 : horizonYears <= 25 ? 5 : 10;
  const xLabels: { year: number; x: number }[] = [];
  for (let yr = 0; yr <= horizonYears; yr += step) {
    if (yr === 0) continue; // skip year 0
    const x = PAD.left + (yr / horizonYears) * chartW;
    xLabels.push({ year: yr, x });
  }

  // Goal line Y position
  const goalY = goalValue != null && goalValue >= minVal && goalValue <= maxVal
    ? PAD.top + (1 - (goalValue - minVal) / (maxVal - minVal)) * chartH
    : null;

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      style={{ display: 'block', overflow: 'visible' }}
      aria-label="Gràfic de projecció financera"
    >
      {/* Grid lines */}
      {yLabels.map(({ y }, i) => (
        <line
          key={i}
          x1={PAD.left}
          y1={y}
          x2={width - PAD.right}
          y2={y}
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={1}
        />
      ))}

      {/* Y-axis labels */}
      {yLabels.map(({ val, y }, i) => (
        <text
          key={i}
          x={PAD.left - 6}
          y={y + 4}
          textAnchor="end"
          fontSize={9}
          fontFamily="var(--font-num)"
          fill="rgba(255,255,255,0.3)"
        >
          {formatK(val)}€
        </text>
      ))}

      {/* X-axis labels */}
      {xLabels.map(({ year, x }) => (
        <text
          key={year}
          x={x}
          y={height - PAD.bottom + 14}
          textAnchor="middle"
          fontSize={9}
          fontFamily="var(--font-num)"
          fill="rgba(255,255,255,0.3)"
        >
          {year}a
        </text>
      ))}

      {/* Band area (adverse → optimistic) */}
      <path
        d={areaPath}
        fill={COLORS.base}
        fillOpacity={0.06}
      />

      {/* Goal line */}
      {goalY != null && (
        <>
          <line
            x1={PAD.left}
            y1={goalY}
            x2={width - PAD.right}
            y2={goalY}
            stroke="#F59E0B"
            strokeWidth={1}
            strokeDasharray="4 3"
            opacity={0.7}
          />
          <text
            x={width - PAD.right + 4}
            y={goalY + 4}
            fontSize={8}
            fontFamily="var(--font-num)"
            fill="#F59E0B"
            opacity={0.8}
          >
            Obj.
          </text>
        </>
      )}

      {/* Adverse line */}
      <path
        d={pathAdv}
        fill="none"
        stroke={COLORS.adverse}
        strokeWidth={1.5}
        strokeOpacity={0.7}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Optimistic line */}
      <path
        d={pathOpt}
        fill="none"
        stroke={COLORS.optimistic}
        strokeWidth={1.5}
        strokeOpacity={0.7}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Base line (on top, thicker) */}
      <path
        d={pathBase}
        fill="none"
        stroke={COLORS.base}
        strokeWidth={2.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* End point dots */}
      {animPct >= 0.99 && (
        <>
          {[
            { pts: sliceBase, color: COLORS.base, r: 4 },
            { pts: sliceAdv,  color: COLORS.adverse, r: 3 },
            { pts: sliceOpt,  color: COLORS.optimistic, r: 3 },
          ].map(({ pts, color, r }, i) => {
            const lastVal = pts[pts.length - 1];
            const x = PAD.left + chartW;
            const y = PAD.top + (1 - (lastVal - minVal) / (maxVal - minVal)) * chartH;
            return (
              <circle key={i} cx={x} cy={y} r={r} fill={color} fillOpacity={0.9} />
            );
          })}
        </>
      )}
    </svg>
  );
}
