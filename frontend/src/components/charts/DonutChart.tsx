import { useState } from 'react';

interface Segment {
  name: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  segments: Segment[];
}

const SIZE = 120;
const CX = SIZE / 2;
const CY = SIZE / 2;
const R = 42;
const STROKE = 14;

function arcPath(
  startDeg: number,
  sweepDeg: number,
  radius: number,
  cx: number,
  cy: number
): string {
  const s = (startDeg * Math.PI) / 180;
  const e = ((startDeg + sweepDeg) * Math.PI) / 180;
  const x1 = cx + radius * Math.cos(s);
  const y1 = cy + radius * Math.sin(s);
  const x2 = cx + radius * Math.cos(e);
  const y2 = cy + radius * Math.sin(e);
  const large = sweepDeg > 180 ? 1 : 0;
  return `M ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2}`;
}

export function DonutChart({ segments }: DonutChartProps) {
  const [hovered, setHovered] = useState<number | null>(null);

  const total = segments.reduce((s, a) => s + a.value, 0);
  if (total === 0) return null;

  let cumAngle = -90;
  const segs = segments.map((seg) => {
    const pct = seg.value / total;
    const angle = pct * 360;
    const startAngle = cumAngle;
    cumAngle += angle;
    return { ...seg, pct, startAngle, angle };
  });

  return (
    <div style={{ position: 'relative', width: SIZE, height: SIZE, flexShrink: 0 }}>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width={SIZE} height={SIZE}>
        {segs.map((seg, i) => (
          <path
            key={i}
            d={arcPath(seg.startAngle, seg.angle - 1, R, CX, CY)}
            fill="none"
            stroke={seg.color}
            strokeWidth={hovered === i ? STROKE + 4 : STROKE}
            strokeLinecap="round"
            style={{
              transition: 'stroke-width 0.3s ease',
              cursor: 'pointer',
              opacity: hovered !== null && hovered !== i ? 0.4 : 1,
            }}
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}
            onTouchStart={() => setHovered(i)}
            onTouchEnd={() => setHovered(null)}
          />
        ))}
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        {hovered !== null ? (
          <>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: segs[hovered].color,
                fontFamily: 'var(--font-num)',
                textAlign: 'center',
                maxWidth: 60,
                lineHeight: 1.2,
              }}
            >
              {segs[hovered].name}
            </span>
            <span
              style={{
                fontSize: 10,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text-secondary)',
              }}
            >
              {(segs[hovered].pct * 100).toFixed(1)}%
            </span>
          </>
        ) : (
          <>
            <span
              style={{
                fontSize: 9,
                fontFamily: 'var(--font-num)',
                letterSpacing: '0.04em',
                color: 'var(--color-text-tertiary)',
              }}
            >
              TOTAL
            </span>
            <span
              style={{
                fontSize: 14,
                fontWeight: 600,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text)',
              }}
            >
              €{(total / 1000).toFixed(1)}k
            </span>
          </>
        )}
      </div>
    </div>
  );
}
