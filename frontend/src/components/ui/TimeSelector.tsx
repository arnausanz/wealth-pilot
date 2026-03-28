interface TimeSelectorProps {
  value: string;
  onChange: (v: string) => void;
}

const PRESETS = ['1M', '3M', '6M', '1A', 'Tot'];

export function TimeSelector({ value, onChange }: TimeSelectorProps) {
  const isCustom = !PRESETS.includes(value);

  function handleCustomToggle() {
    if (isCustom) {
      onChange('1A');
    } else {
      onChange('custom');
    }
  }

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
        <button
          onClick={handleCustomToggle}
          style={{
            flex: 1.2,
            padding: '7px 0',
            borderRadius: 8,
            border: 'none',
            background: isCustom
              ? 'color-mix(in srgb, var(--color-accent) 16%, transparent)'
              : 'transparent',
            color: isCustom ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
            fontSize: 10,
            fontWeight: 600,
            fontFamily: 'var(--font-num)',
            cursor: 'pointer',
            transition: 'all 0.25s ease',
          }}
        >
          Custom
        </button>
      </div>

      {isCustom && (
        <div
          style={{
            display: 'flex',
            gap: 8,
            marginTop: 12,
            animation: 'slideDown 0.3s ease',
          }}
        >
          <div style={{ flex: 1 }}>
            <label
              style={{
                fontSize: 9,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text-tertiary)',
                letterSpacing: '0.1em',
                display: 'block',
                marginBottom: 4,
              }}
            >
              DES DE
            </label>
            <input
              type="date"
              style={{
                width: '100%',
                padding: '8px 10px',
                background: 'var(--color-glass-bg)',
                border: '1px solid var(--color-glass-border)',
                backdropFilter: 'var(--glass-blur)',
                WebkitBackdropFilter: 'var(--glass-blur)',
                color: 'var(--color-text)',
                fontSize: 12,
                fontFamily: 'var(--font-num)',
                outline: 'none',
                borderRadius: 10,
              }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label
              style={{
                fontSize: 9,
                fontFamily: 'var(--font-num)',
                color: 'var(--color-text-tertiary)',
                letterSpacing: '0.1em',
                display: 'block',
                marginBottom: 4,
              }}
            >
              FINS A
            </label>
            <input
              type="date"
              style={{
                width: '100%',
                padding: '8px 10px',
                background: 'var(--color-glass-bg)',
                border: '1px solid var(--color-glass-border)',
                backdropFilter: 'var(--glass-blur)',
                WebkitBackdropFilter: 'var(--glass-blur)',
                color: 'var(--color-text)',
                fontSize: 12,
                fontFamily: 'var(--font-num)',
                outline: 'none',
                borderRadius: 10,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
