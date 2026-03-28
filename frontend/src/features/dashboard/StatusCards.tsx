import { StatusDot } from '../../components/ui/StatusDot';
import { GoalRing } from '../../components/charts/GoalRing';
import { Card } from '../../components/ui/Card';

type TrackStatus = 'green' | 'yellow' | 'red';

interface StatusCardsProps {
  netWorth: number;
  goalAmount: number;
  goalYear: number;
  goalLabel: string;
}

const STATUS_LABELS: Record<TrackStatus, string> = {
  green: 'On Track',
  yellow: 'Atenció',
  red: 'Per sota',
};

const STATUS_COLORS: Record<TrackStatus, string> = {
  green: 'var(--color-positive)',
  yellow: 'var(--color-warning)',
  red: 'var(--color-negative)',
};

function computeOnTrackPct(netWorth: number, goalAmount: number): number {
  if (goalAmount === 0) return 0;
  return (netWorth / goalAmount) * 100;
}

function getTrackStatus(pct: number): TrackStatus {
  if (pct >= 95) return 'green';
  if (pct >= 85) return 'yellow';
  return 'red';
}

export function StatusCards({ netWorth, goalAmount, goalYear, goalLabel }: StatusCardsProps) {
  const onTrackPct = computeOnTrackPct(netWorth, goalAmount);
  const status = getTrackStatus(onTrackPct);
  const statusColor = STATUS_COLORS[status];

  return (
    <div style={{ padding: '20px 24px 0' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 10,
        }}
      >
        {/* Projection card */}
        <Card>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 8,
            }}
          >
            <StatusDot status={status} />
            <span
              style={{
                fontSize: 9,
                fontFamily: 'var(--font-num)',
                letterSpacing: '0.06em',
                color: 'var(--color-text-tertiary)',
                textTransform: 'uppercase',
              }}
            >
              Projecció
            </span>
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 600,
              color: statusColor,
              fontFamily: 'var(--font-num)',
            }}
          >
            {onTrackPct.toFixed(1)}%
          </div>
          <div
            style={{
              fontSize: 10,
              color: 'var(--color-text-tertiary)',
              marginTop: 2,
              fontFamily: 'var(--font-num)',
            }}
          >
            {STATUS_LABELS[status]}
          </div>
        </Card>

        {/* Housing goal card */}
        <Card
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
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
                marginBottom: 6,
              }}
            >
              {goalLabel}
            </div>
            <div
              style={{
                fontSize: 16,
                fontWeight: 600,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text)',
              }}
            >
              €{(netWorth / 1000).toFixed(1)}k
            </div>
            <div
              style={{
                fontSize: 9,
                color: 'var(--color-text-tertiary)',
                marginTop: 2,
                fontFamily: 'var(--font-num)',
              }}
            >
              de €{(goalAmount / 1000).toFixed(0)}k · {goalYear}
            </div>
          </div>
          <GoalRing
            current={netWorth}
            target={goalAmount}
            label={`de €${(goalAmount / 1000).toFixed(0)}k`}
          />
        </Card>
      </div>
    </div>
  );
}
