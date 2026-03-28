interface GoalRingProps {
  current: number;
  target: number;
  label: string;
}

const R = 28;
const CIRC = 2 * Math.PI * R;

export function GoalRing({ current, target, label }: GoalRingProps) {
  const pct = Math.min(current / target, 1);
  const offset = CIRC * (1 - pct);

  return (
    <svg width="72" height="72" viewBox="0 0 72 72">
      <circle
        cx="36"
        cy="36"
        r={R}
        fill="none"
        stroke="var(--color-border)"
        strokeWidth="5"
      />
      <circle
        cx="36"
        cy="36"
        r={R}
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray={CIRC}
        strokeDashoffset={offset}
        transform="rotate(-90 36 36)"
        style={{ transition: 'stroke-dashoffset 1s ease' }}
      />
      <text
        x="36"
        y="34"
        textAnchor="middle"
        fontSize="13"
        fontWeight="600"
        fill="var(--color-text)"
        fontFamily="var(--font-num)"
      >
        {Math.round(pct * 100)}%
      </text>
      <text
        x="36"
        y="46"
        textAnchor="middle"
        fontSize="7"
        fill="var(--color-text-tertiary)"
        fontFamily="var(--font-num)"
        letterSpacing="0.03em"
      >
        {label}
      </text>
    </svg>
  );
}
