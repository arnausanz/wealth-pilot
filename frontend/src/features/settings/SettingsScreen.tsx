import { useState, useEffect, useRef } from 'react';
import { n } from '../../types';
import {
  useConfigAssets,
  useConfigContributions,
  useConfigScenarios,
  useConfigObjectives,
  useConfigParameters,
  usePatchAsset,
  usePatchContribution,
  usePatchScenario,
  usePatchObjective,
  usePatchParameter,
  useWeightCheck,
  useResetDefaults,
} from '../../hooks/useConfig';

// ─── Toast ────────────────────────────────────────────────────────────────────

interface ToastState {
  message: string;
  type: 'success' | 'error';
}

function Toast({ toast, onDone }: { toast: ToastState; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2400);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 100,
        left: '50%',
        transform: 'translateX(-50%)',
        background: toast.type === 'success' ? 'var(--color-positive)' : 'var(--color-negative)',
        color: '#fff',
        fontSize: 13,
        fontFamily: 'var(--font-body)',
        fontWeight: 600,
        padding: '10px 20px',
        borderRadius: 24,
        zIndex: 9999,
        whiteSpace: 'nowrap',
        boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
        animation: 'slideDown 0.2s ease',
      }}
    >
      {toast.message}
    </div>
  );
}

// ─── Section header ───────────────────────────────────────────────────────────

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          fontSize: 16,
          fontWeight: 700,
          letterSpacing: '-0.01em',
          fontFamily: 'var(--font-display)',
          color: 'var(--color-text)',
        }}
      >
        {title}
      </div>
      {subtitle && (
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-num)',
            marginTop: 2,
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
}

// ─── Inline editable field ────────────────────────────────────────────────────

function InlineField({
  label,
  value,
  type = 'text',
  onSave,
  suffix,
  min,
  max,
  step,
}: {
  label: string;
  value: string;
  type?: 'text' | 'number';
  onSave: (v: string) => void;
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  function handleSave() {
    setEditing(false);
    if (draft !== value) onSave(draft);
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 0',
        borderBottom: '1px solid var(--color-glass-border)',
      }}
    >
      <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {editing ? (
          <input
            ref={inputRef}
            type={type}
            value={draft}
            min={min}
            max={max}
            step={step}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={handleSave}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') { setDraft(value); setEditing(false); }
            }}
            style={{
              fontSize: 13,
              fontFamily: 'var(--font-num)',
              fontWeight: 600,
              color: 'var(--color-text)',
              background: 'var(--color-glass-bg)',
              border: '1px solid var(--color-accent)',
              borderRadius: 6,
              padding: '3px 8px',
              width: 90,
              textAlign: 'right',
              outline: 'none',
            }}
          />
        ) : (
          <button
            onClick={() => { setDraft(value); setEditing(true); }}
            style={{
              fontSize: 13,
              fontFamily: 'var(--font-num)',
              fontWeight: 600,
              color: 'var(--color-text)',
              background: 'none',
              border: 'none',
              padding: 0,
              cursor: 'pointer',
            }}
          >
            {value}{suffix}
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Toggle field ─────────────────────────────────────────────────────────────

function ToggleField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 0',
        borderBottom: '1px solid var(--color-glass-border)',
      }}
    >
      <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{label}</span>
      <button
        onClick={() => onChange(!value)}
        style={{
          width: 40,
          height: 22,
          borderRadius: 11,
          background: value ? 'var(--color-accent)' : 'var(--color-glass-border)',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          position: 'relative',
          transition: 'background 0.2s',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 3,
            left: value ? 21 : 3,
            width: 16,
            height: 16,
            borderRadius: '50%',
            background: '#fff',
            transition: 'left 0.2s',
          }}
        />
      </button>
    </div>
  );
}

// ─── Card wrapper ─────────────────────────────────────────────────────────────

function SettingsCard({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="settings-group"
      style={{
        background: 'var(--color-glass-bg)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        border: '1px solid var(--color-glass-border)',
        borderRadius: 16,
        padding: '4px 16px',
        marginBottom: 8,
        boxShadow: 'var(--card-shadow)',
      }}
    >
      {children}
    </div>
  );
}

// ─── Tab pill ─────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'assets',        label: 'Assets' },
  { id: 'contributions', label: 'Aportacions' },
  { id: 'scenarios',     label: 'Escenaris' },
  { id: 'objectives',    label: 'Objectius' },
  { id: 'parameters',    label: 'Paràmetres' },
] as const;

type TabId = typeof TABS[number]['id'];

// ─── Assets Tab ───────────────────────────────────────────────────────────────

function AssetsTab({ showToast }: { showToast: (msg: string, type?: 'success' | 'error') => void }) {
  const { data: assets = [] } = useConfigAssets();
  const { data: weightCheck } = useWeightCheck();
  const patchAsset = usePatchAsset();

  function save(id: number, field: string, value: unknown) {
    patchAsset.mutate(
      { id, data: { [field]: value } as never },
      {
        onSuccess: () => showToast('Guardat', 'success'),
        onError: () => showToast('Error en guardar', 'error'),
      },
    );
  }

  return (
    <div>
      {weightCheck && (
        <div
          style={{
            padding: '8px 12px',
            borderRadius: 10,
            background: weightCheck.is_valid
              ? 'rgba(16,185,129,0.1)'
              : 'rgba(239,68,68,0.1)',
            border: `1px solid ${weightCheck.is_valid ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
            fontSize: 11,
            fontFamily: 'var(--font-num)',
            color: weightCheck.is_valid ? 'var(--color-positive)' : 'var(--color-negative)',
            marginBottom: 12,
          }}
        >
          {weightCheck.message}
        </div>
      )}

      {assets.map((asset) => (
        <div key={asset.id} style={{ marginBottom: 12 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 4,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: asset.color_hex ?? '#64748B',
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: 'var(--color-text)',
                fontFamily: 'var(--font-display)',
              }}
            >
              {asset.display_name}
            </span>
            <span
              style={{
                fontSize: 10,
                color: 'var(--color-text-tertiary)',
                fontFamily: 'var(--font-num)',
              }}
            >
              {asset.ticker_yf ?? '—'}
            </span>
          </div>
          <SettingsCard>
            <InlineField
              label="Pes objectiu (%)"
              value={asset.target_weight != null ? n(asset.target_weight).toFixed(1) : '0.0'}
              type="number"
              min={0}
              max={100}
              step={0.5}
              onSave={(v) => save(asset.id, 'target_weight', parseFloat(v))}
              suffix="%"
            />
            <InlineField
              label="Ticker Yahoo Finance"
              value={asset.ticker_yf ?? ''}
              onSave={(v) => save(asset.id, 'ticker_yf', v)}
            />
            <ToggleField
              label="Actiu"
              value={asset.is_active}
              onChange={(v) => save(asset.id, 'is_active', v)}
            />
          </SettingsCard>
        </div>
      ))}
    </div>
  );
}

// ─── Contributions Tab ────────────────────────────────────────────────────────

function ContributionsTab({ showToast }: { showToast: (msg: string, type?: 'success' | 'error') => void }) {
  const { data: contributions = [] } = useConfigContributions();
  const patchContribution = usePatchContribution();

  function save(id: number, field: string, value: unknown) {
    patchContribution.mutate(
      { id, data: { [field]: value } as never },
      {
        onSuccess: () => showToast('Guardat', 'success'),
        onError: () => showToast('Error en guardar', 'error'),
      },
    );
  }

  const total = contributions
    .filter((c) => c.is_active)
    .reduce((acc, c) => acc + n(c.amount), 0);

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
          padding: '10px 14px',
          background: 'rgba(59,130,246,0.08)',
          borderRadius: 10,
          border: '1px solid rgba(59,130,246,0.2)',
        }}
      >
        <span style={{ fontSize: 11, color: 'var(--color-text-tertiary)', fontFamily: 'var(--font-num)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Total mensual actiu
        </span>
        <span style={{ fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-num)', color: 'var(--color-accent)' }}>
          €{total.toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
        </span>
      </div>

      {contributions.map((c) => (
        <div key={c.id} style={{ marginBottom: 12 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 4,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: c.asset_color_hex ?? '#64748B',
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text)', fontFamily: 'var(--font-display)' }}>
              {c.asset_display_name}
            </span>
          </div>
          <SettingsCard>
            <InlineField
              label="Import mensual (€)"
              value={n(c.amount).toFixed(0)}
              type="number"
              min={0}
              step={50}
              onSave={(v) => save(c.id, 'amount', parseFloat(v))}
              suffix="€"
            />
            <InlineField
              label="Dia del mes"
              value={String(c.day_of_month)}
              type="number"
              min={1}
              max={28}
              onSave={(v) => save(c.id, 'day_of_month', parseInt(v))}
            />
            <ToggleField
              label="Activa"
              value={c.is_active}
              onChange={(v) => save(c.id, 'is_active', v)}
            />
          </SettingsCard>
        </div>
      ))}
    </div>
  );
}

// ─── Scenarios Tab ────────────────────────────────────────────────────────────

const SCENARIO_COLORS: Record<string, string> = {
  adverse: '#EF4444',
  base: '#3B82F6',
  optimistic: '#10B981',
};

const SCENARIO_LABELS: Record<string, string> = {
  adverse: 'Advers',
  base: 'Base',
  optimistic: 'Optimista',
};

function ScenariosTab({ showToast }: { showToast: (msg: string, type?: 'success' | 'error') => void }) {
  const { data: rows = [] } = useConfigScenarios();
  const patchScenario = usePatchScenario();

  function save(assetId: number, scenarioType: 'adverse' | 'base' | 'optimistic', value: string) {
    patchScenario.mutate(
      { assetId, scenarioType, annualReturn: parseFloat(value) },
      {
        onSuccess: () => showToast('Guardat', 'success'),
        onError: () => showToast('Error en guardar', 'error'),
      },
    );
  }

  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr repeat(3, 60px)',
          gap: 4,
          marginBottom: 8,
          padding: '0 4px',
        }}
      >
        <span />
        {(['adverse', 'base', 'optimistic'] as const).map((type) => (
          <span
            key={type}
            style={{
              fontSize: 9,
              fontFamily: 'var(--font-num)',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
              color: SCENARIO_COLORS[type],
              textAlign: 'center',
            }}
          >
            {SCENARIO_LABELS[type]}
          </span>
        ))}
      </div>

      <SettingsCard>
        {rows.map((row, idx) => (
          <div
            key={row.asset_id}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr repeat(3, 60px)',
              gap: 4,
              alignItems: 'center',
              padding: '8px 0',
              borderBottom: idx < rows.length - 1 ? '1px solid var(--color-glass-border)' : 'none',
            }}
          >
            <span
              style={{
                fontSize: 12,
                color: 'var(--color-text-secondary)',
                fontFamily: 'var(--font-body)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {row.display_name}
            </span>
            {(['adverse', 'base', 'optimistic'] as const).map((type) => {
              const val = row[type];
              return (
                <ScenarioCell
                  key={type}
                  value={val != null ? n(val).toFixed(1) : '—'}
                  color={SCENARIO_COLORS[type]}
                  onSave={(v) => save(row.asset_id, type, v)}
                />
              );
            })}
          </div>
        ))}
      </SettingsCard>
    </div>
  );
}

function ScenarioCell({
  value,
  color,
  onSave,
}: {
  value: string;
  color: string;
  onSave: (v: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  function handleSave() {
    setEditing(false);
    if (draft !== value && draft !== '—') onSave(draft);
  }

  return editing ? (
    <input
      ref={inputRef}
      type="number"
      value={draft}
      step={0.5}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={handleSave}
      onKeyDown={(e) => {
        if (e.key === 'Enter') handleSave();
        if (e.key === 'Escape') { setDraft(value); setEditing(false); }
      }}
      style={{
        width: '100%',
        fontSize: 12,
        fontFamily: 'var(--font-num)',
        color,
        background: 'var(--color-glass-bg)',
        border: `1px solid ${color}`,
        borderRadius: 6,
        padding: '2px 4px',
        textAlign: 'center',
        outline: 'none',
      }}
    />
  ) : (
    <button
      onClick={() => { setDraft(value); setEditing(true); }}
      style={{
        width: '100%',
        fontSize: 12,
        fontFamily: 'var(--font-num)',
        fontWeight: 600,
        color,
        background: 'none',
        border: 'none',
        padding: '2px 0',
        cursor: 'pointer',
        textAlign: 'center',
      }}
    >
      {value}%
    </button>
  );
}

// ─── Objectives Tab ───────────────────────────────────────────────────────────

function ObjectivesTab({ showToast }: { showToast: (msg: string, type?: 'success' | 'error') => void }) {
  const { data: objectives = [] } = useConfigObjectives();
  const patchObjective = usePatchObjective();

  function save(id: number, field: string, value: unknown) {
    patchObjective.mutate(
      { id, data: { [field]: value } as never },
      {
        onSuccess: () => showToast('Guardat', 'success'),
        onError: () => showToast('Error en guardar', 'error'),
      },
    );
  }

  if (objectives.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-tertiary)', fontSize: 13 }}>
        Cap objectiu configurat
      </div>
    );
  }

  return (
    <div>
      {objectives.map((obj) => (
        <div key={obj.id} style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text)', fontFamily: 'var(--font-display)', marginBottom: 4 }}>
            {obj.name}
          </div>
          {obj.description && (
            <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', marginBottom: 6 }}>
              {obj.description}
            </div>
          )}
          <SettingsCard>
            <InlineField
              label="Import objectiu (€)"
              value={n(obj.target_amount).toFixed(0)}
              type="number"
              min={0}
              step={1000}
              onSave={(v) => save(obj.id, 'target_amount', parseFloat(v))}
              suffix="€"
            />
            <InlineField
              label="Data objectiu"
              value={obj.target_date ?? ''}
              onSave={(v) => save(obj.id, 'target_date', v || null)}
            />
            <ToggleField
              label="Actiu"
              value={obj.is_active}
              onChange={(v) => save(obj.id, 'is_active', v)}
            />
          </SettingsCard>
        </div>
      ))}
    </div>
  );
}

// ─── Parameters Tab ───────────────────────────────────────────────────────────

function ParametersTab({ showToast }: { showToast: (msg: string, type?: 'success' | 'error') => void }) {
  const { data: params = [] } = useConfigParameters();
  const patchParam = usePatchParameter();

  function save(key: string, value: string) {
    patchParam.mutate(
      { key, value },
      {
        onSuccess: () => showToast('Guardat', 'success'),
        onError: () => showToast('Error en guardar', 'error'),
      },
    );
  }

  const editable = params.filter((p) => p.is_editable);
  const byCategory: Record<string, typeof editable> = {};
  for (const p of editable) {
    const cat = p.category ?? 'general';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(p);
  }

  return (
    <div>
      {Object.entries(byCategory).map(([cat, items]) => (
        <div key={cat} style={{ marginBottom: 16 }}>
          <div
            style={{
              fontSize: 9,
              fontFamily: 'var(--font-num)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--color-text-tertiary)',
              marginBottom: 6,
            }}
          >
            {cat}
          </div>
          <SettingsCard>
            {items.map((p) => (
              <div key={p.key}>
                {p.description && (
                  <div style={{ paddingTop: 8, fontSize: 10, color: 'var(--color-text-tertiary)' }}>
                    {p.description}
                  </div>
                )}
                <InlineField
                  label={p.key.replace(/_/g, ' ')}
                  value={p.value}
                  type={p.value_type === 'decimal' || p.value_type === 'integer' ? 'number' : 'text'}
                  onSave={(v) => save(p.key, v)}
                  step={p.value_type === 'decimal' ? 0.01 : undefined}
                />
              </div>
            ))}
          </SettingsCard>
        </div>
      ))}
      {editable.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--color-text-tertiary)', fontSize: 13 }}>
          Cap paràmetre editable
        </div>
      )}
    </div>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export function SettingsScreen() {
  const [activeTab, setActiveTab] = useState<TabId>('assets');
  const [toast, setToast] = useState<ToastState | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const resetDefaults = useResetDefaults();

  function showToast(message: string, type: 'success' | 'error' = 'success') {
    setToast({ message, type });
  }

  function handleReset() {
    if (!confirmReset) {
      setConfirmReset(true);
      // Auto-cancel confirm after 4s
      setTimeout(() => setConfirmReset(false), 4000);
      return;
    }
    setConfirmReset(false);
    resetDefaults.mutate(undefined, {
      onSuccess: () => showToast('Valors restaurats', 'success'),
      onError: () => showToast('Error en restaurar', 'error'),
    });
  }

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
      <div style={{ padding: '68px 24px 16px' }}>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            fontFamily: 'var(--font-display)',
          }}
        >
          Configuració
        </div>
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-text-tertiary)',
            fontFamily: 'var(--font-num)',
            marginTop: 2,
          }}
        >
          Gestiona els paràmetres de la teva cartera
        </div>
      </div>

      {/* Tabs */}
      <div
        style={{
          overflowX: 'auto',
          paddingBottom: 2,
          WebkitOverflowScrolling: 'touch' as never,
          scrollbarWidth: 'none',
        }}
      >
        <div
          style={{
            display: 'flex',
            gap: 6,
            padding: '0 24px 12px',
            width: 'max-content',
          }}
        >
          {TABS.map((tab) => {
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  fontSize: 12,
                  fontFamily: 'var(--font-num)',
                  fontWeight: active ? 700 : 500,
                  color: active ? '#fff' : 'var(--color-text-secondary)',
                  background: active ? 'var(--color-accent)' : 'var(--color-glass-bg)',
                  border: `1px solid ${active ? 'transparent' : 'var(--color-glass-border)'}`,
                  borderRadius: 20,
                  padding: '6px 14px',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s',
                  backdropFilter: 'var(--glass-blur)',
                  WebkitBackdropFilter: 'var(--glass-blur)',
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '0 24px' }}>
        {activeTab === 'assets' && (
          <>
            <SectionHeader title="Assets" subtitle="Configura els pesos objectiu de cada actiu" />
            <AssetsTab showToast={showToast} />
          </>
        )}
        {activeTab === 'contributions' && (
          <>
            <SectionHeader title="Aportacions mensuals" subtitle="Import i dia d'aportació per asset" />
            <ContributionsTab showToast={showToast} />
          </>
        )}
        {activeTab === 'scenarios' && (
          <>
            <SectionHeader title="Retorns esperats" subtitle="Rendiment anual estimat per escenari i asset (%)" />
            <ScenariosTab showToast={showToast} />
          </>
        )}
        {activeTab === 'objectives' && (
          <>
            <SectionHeader title="Objectius financers" subtitle="Metes d'estalvi i inversió" />
            <ObjectivesTab showToast={showToast} />
          </>
        )}
        {activeTab === 'parameters' && (
          <>
            <SectionHeader title="Paràmetres globals" subtitle="Variables generals del sistema" />
            <ParametersTab showToast={showToast} />
          </>
        )}
      </div>

      {/* Reset a valors per defecte */}
      <div style={{ padding: '24px 24px 0' }}>
        <div
          style={{
            borderTop: '1px solid var(--color-glass-border)',
            paddingTop: 20,
          }}
        >
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-tertiary)',
              fontFamily: 'var(--font-num)',
              marginBottom: 10,
              lineHeight: 1.4,
            }}
          >
            Restaura els pesos dels assets, retorns d'escenaris, aportacions mensuals i objectius als valors originals.
          </div>
          <button
            onClick={handleReset}
            disabled={resetDefaults.isPending}
            style={{
              width: '100%',
              padding: '12px 0',
              borderRadius: 12,
              border: `1px solid ${confirmReset ? 'var(--color-negative)' : 'var(--color-glass-border)'}`,
              background: confirmReset
                ? 'rgba(239,68,68,0.1)'
                : 'var(--color-glass-bg)',
              backdropFilter: 'var(--glass-blur)',
              WebkitBackdropFilter: 'var(--glass-blur)',
              color: confirmReset ? 'var(--color-negative)' : 'var(--color-text-secondary)',
              fontSize: 13,
              fontFamily: 'var(--font-body)',
              fontWeight: 600,
              cursor: resetDefaults.isPending ? 'not-allowed' : 'pointer',
              opacity: resetDefaults.isPending ? 0.5 : 1,
              transition: 'all 0.2s',
            }}
          >
            {resetDefaults.isPending
              ? 'Restaurant…'
              : confirmReset
              ? 'Confirmar reset? (toca de nou)'
              : 'Restaurar valors per defecte'}
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && <Toast toast={toast} onDone={() => setToast(null)} />}
    </div>
  );
}
