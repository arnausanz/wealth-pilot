interface TimeSelectorProps {
  value: string;
  onChange: (v: string) => void;
}

const PRESETS = ['1M', '3M', '6M', '1A', 'Tot'];

export function TimeSelector({ value, onChange }: TimeSelectorProps) {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: 2,
          background: 'var(--color-glass-bg)',
          backdropFilter: 'var(--glass-blur)',
          WebkitBackdropFilter: 'var(--glass-blur)',
          borderRadius: 12,
          padding: 3,
          border: '1px solid var(--color-glass-border)',
        }}
      >
        {PRESETS.map((key) => {
          const active = value === key;
          return (
            <button
              key={key}
              onClick={() => onChange(key)}
              style={{
                flex: 1,
                padding: '8px 0',
                borderRadius: 10,
                border: 'none',
                background: active
                  ? 'rgba(var(--accent-rgb, 59,130,246), 0.16)'
                  : 'transparent',
                backgroundColor: active
                  ? 'color-mix(in srgb, var(--color-accent) 16%, transparent)'
                  : 'transparent',
                color: active ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'var(--font-num)',
                letterSpacing: '0.02em',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
              }}
            >
              {key}
            </button>
          );
        })}
      </div>
    </div>
  );
}
