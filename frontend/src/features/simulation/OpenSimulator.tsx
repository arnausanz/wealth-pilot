import { useState } from 'react';
import { n } from '../../types';
import type { CompareResponse, SimulationOut } from '../../types';
import {
  useAddEvent,
  useCompareSimulations,
  useCreateSimulation,
  useDeleteEvent,
  useDeleteSimulation,
  useSavedSimulations,
  useSimulationDetail,
} from '../../hooks/useSimulationSaved';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const SCENARIO_LABELS: Record<string, string> = {
  adverse:    'Advers',
  base:       'Base',
  optimistic: 'Optimista',
};

const SCENARIO_COLORS: Record<string, string> = {
  adverse:    '#EF4444',
  base:       '#3B82F6',
  optimistic: '#10B981',
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  one_time_out:        'Despesa única',
  one_time_in:         'Ingrés únic',
  contribution_change: 'Canvi aportació',
  return_override:     'Override retorn',
};

// ─── Mini multi-line projection chart ─────────────────────────────────────────

function CompareChart({ result }: { result: CompareResponse }) {
  const allPts = result.series.flatMap((s) => s.data_points.map(n));
  const rawMin = Math.min(...allPts);
  const rawMax = Math.max(...allPts);
  const pad    = (rawMax - rawMin) * 0.08;
  const minVal = Math.max(0, rawMin - pad);
  const maxVal = rawMax + pad || 1;

  const W = 382;
  const H = 180;
  const PAD = { top: 16, right: 12, bottom: 28, left: 52 };
  const cW = W - PAD.left - PAD.right;
  const cH = H - PAD.top - PAD.bottom;

  function buildPath(pts: (string | number)[]) {
    const nums = pts.map(n);
    if (nums.length < 2) return '';
    const total = nums.length - 1;
    return nums
      .map((v, i) => {
        const x = PAD.left + (i / total) * cW;
        const y = PAD.top + (1 - (v - minVal) / (maxVal - minVal)) * cH;
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  }

  function formatK(v: number) {
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `${Math.round(v / 1_000)}k`;
    return `${Math.round(v)}`;
  }

  const yLevels = 4;
  const yLabels = Array.from({ length: yLevels }, (_, i) => ({
    val: minVal + (maxVal - minVal) * (1 - i / (yLevels - 1)),
    y: PAD.top + (i / (yLevels - 1)) * cH,
  }));

  const years = result.horizon_years;
  const step = years <= 5 ? 1 : years <= 15 ? 3 : 5;
  const xLabels: { yr: number; x: number }[] = [];
  for (let yr = step; yr <= years; yr += step) {
    xLabels.push({ yr, x: PAD.left + (yr / years) * cW });
  }

  return (
    <div style={{ marginTop: 8 }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        style={{ display: 'block', overflow: 'visible' }}
      >
        {yLabels.map(({ val, y }, i) => (
          <g key={i}>
            <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y}
              stroke="rgba(255,255,255,0.06)" strokeWidth={1} />
            <text x={PAD.left - 4} y={y + 3} textAnchor="end"
              fontSize={8} fontFamily="var(--font-num)" fill="rgba(255,255,255,0.3)">
              {formatK(val)}€
            </text>
          </g>
        ))}
        {xLabels.map(({ yr, x }) => (
          <text key={yr} x={x} y={H - PAD.bottom + 12} textAnchor="middle"
            fontSize={8} fontFamily="var(--font-num)" fill="rgba(255,255,255,0.3)">
            {yr}a
          </text>
        ))}
        {result.series.map((s) => (
          <path
            key={s.sim_id ?? 'baseline'}
            d={buildPath(s.data_points)}
            fill="none"
            stroke={s.color}
            strokeWidth={s.sim_id === null ? 2.5 : 2}
            strokeOpacity={s.sim_id === null ? 0.8 : 0.9}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}
      </svg>
      {/* Series legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginTop: 4 }}>
        {result.series.map((s) => (
          <div key={s.sim_id ?? 'baseline'} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 14, height: 2.5, borderRadius: 2, background: s.color }} />
            <span style={{ fontSize: 10, fontFamily: 'var(--font-num)', color: 'var(--color-text-tertiary)' }}>
              {s.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Simulation card ──────────────────────────────────────────────────────────

function SimCard({
  sim,
  onSelect,
  onDelete,
  isSelected,
}: {
  sim: SimulationOut;
  onSelect: () => void;
  onDelete: () => void;
  isSelected: boolean;
}) {
  const scColor = SCENARIO_COLORS[sim.base_scenario_type] ?? '#3B82F6';
  return (
    <div
      style={{
        padding: '12px 14px',
        borderRadius: 14,
        border: `1px solid ${isSelected ? scColor + '55' : 'var(--color-glass-border)'}`,
        background: isSelected ? `${scColor}11` : 'var(--color-glass-bg)',
        marginBottom: 8,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
            {sim.name}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <span
              style={{
                fontSize: 9,
                padding: '2px 7px',
                borderRadius: 10,
                background: `${scColor}22`,
                color: scColor,
                fontFamily: 'var(--font-num)',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              {SCENARIO_LABELS[sim.base_scenario_type] ?? sim.base_scenario_type}
            </span>
            <span
              style={{
                fontSize: 9,
                color: 'var(--color-text-tertiary)',
                fontFamily: 'var(--font-num)',
              }}
            >
              {sim.horizon_months / 12}a
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, marginLeft: 8 }}>
          <button
            onClick={onSelect}
            style={{
              padding: '4px 10px',
              borderRadius: 8,
              border: `1px solid ${isSelected ? scColor : 'var(--color-glass-border)'}`,
              background: isSelected ? scColor : 'transparent',
              color: isSelected ? '#fff' : 'var(--color-text-secondary)',
              fontSize: 11,
              cursor: 'pointer',
              fontFamily: 'var(--font-num)',
            }}
          >
            {isSelected ? 'Actiu' : 'Comparar'}
          </button>
          <button
            onClick={onDelete}
            style={{
              padding: '4px 8px',
              borderRadius: 8,
              border: '1px solid var(--color-glass-border)',
              background: 'transparent',
              color: 'var(--color-text-tertiary)',
              fontSize: 11,
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Expanded simulation with events ─────────────────────────────────────────

function SimDetail({ simId }: { simId: number }) {
  const { data: detail } = useSimulationDetail(simId);
  const addEvent = useAddEvent();
  const deleteEvent = useDeleteEvent();

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '',
    event_type: 'one_time_out',
    event_date: new Date().toISOString().slice(0, 10),
    amount: '',
    notes: '',
  });

  if (!detail) return null;

  function handleSubmit() {
    const amount = parseFloat(form.amount);
    if (!form.name || isNaN(amount) || amount <= 0) return;
    addEvent.mutate({
      simId,
      name: form.name,
      event_type: form.event_type,
      event_date: form.event_date,
      amount,
      notes: form.notes || undefined,
    }, {
      onSuccess: () => {
        setShowForm(false);
        setForm({ name: '', event_type: 'one_time_out', event_date: new Date().toISOString().slice(0, 10), amount: '', notes: '' });
      },
    });
  }

  return (
    <div
      style={{
        marginBottom: 8,
        padding: '12px 14px',
        borderRadius: 14,
        border: '1px solid var(--color-glass-border)',
        background: 'rgba(255,255,255,0.02)',
      }}
    >
      {/* Events list */}
      {detail.events.length === 0 ? (
        <div style={{ fontSize: 12, color: 'var(--color-text-tertiary)', marginBottom: 10 }}>
          Sense events. Afegeix-ne per personalitzar la projecció.
        </div>
      ) : (
        <div style={{ marginBottom: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {detail.events.map((ev) => (
            <div
              key={ev.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 10px',
                borderRadius: 8,
                background: 'var(--color-glass-bg)',
                border: '1px solid var(--color-glass-border)',
              }}
            >
              <div>
                <div style={{ fontSize: 12, color: 'var(--color-text)' }}>{ev.name}</div>
                <div style={{ fontSize: 10, color: 'var(--color-text-tertiary)', fontFamily: 'var(--font-num)' }}>
                  {EVENT_TYPE_LABELS[ev.event_type] ?? ev.event_type} · {ev.event_date}
                  {' · '}
                  <span style={{ color: 'var(--color-text-secondary)' }}>
                    €{n(ev.amount).toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>
              <button
                onClick={() => deleteEvent.mutate({ eventId: ev.id, simId })}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-text-tertiary)',
                  cursor: 'pointer',
                  fontSize: 12,
                  padding: '2px 6px',
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add event form */}
      {showForm ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input
            placeholder="Nom de l'event"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            style={inputStyle}
          />
          <select
            value={form.event_type}
            onChange={(e) => setForm((f) => ({ ...f, event_type: e.target.value }))}
            style={inputStyle}
          >
            {Object.entries(EVENT_TYPE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <input
            type="date"
            value={form.event_date}
            onChange={(e) => setForm((f) => ({ ...f, event_date: e.target.value }))}
            style={inputStyle}
          />
          <input
            type="number"
            placeholder="Import (€ o %)"
            value={form.amount}
            onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
            style={inputStyle}
          />
          <div style={{ display: 'flex', gap: 6 }}>
            <button
              onClick={handleSubmit}
              disabled={addEvent.isPending}
              style={primaryBtnStyle}
            >
              {addEvent.isPending ? 'Guardant…' : 'Guardar event'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              style={secondaryBtnStyle}
            >
              Cancel·lar
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowForm(true)}
          style={secondaryBtnStyle}
        >
          + Afegir event
        </button>
      )}
    </div>
  );
}

// ─── Style helpers ────────────────────────────────────────────────────────────

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  borderRadius: 8,
  border: '1px solid var(--color-glass-border)',
  background: 'var(--color-glass-bg)',
  color: 'var(--color-text)',
  fontSize: 13,
  fontFamily: 'var(--font-body)',
  boxSizing: 'border-box',
};

const primaryBtnStyle: React.CSSProperties = {
  flex: 1,
  padding: '9px 14px',
  borderRadius: 10,
  border: 'none',
  background: 'var(--color-accent)',
  color: '#fff',
  fontSize: 13,
  fontWeight: 600,
  cursor: 'pointer',
  fontFamily: 'var(--font-body)',
};

const secondaryBtnStyle: React.CSSProperties = {
  padding: '8px 14px',
  borderRadius: 10,
  border: '1px solid var(--color-glass-border)',
  background: 'transparent',
  color: 'var(--color-text-secondary)',
  fontSize: 12,
  cursor: 'pointer',
  fontFamily: 'var(--font-body)',
};

// ─── Main OpenSimulator ───────────────────────────────────────────────────────

export function OpenSimulator() {
  const { data: sims = [], isLoading } = useSavedSimulations();
  const createSim = useCreateSimulation();
  const deleteSim = useDeleteSimulation();
  const compareMutation = useCompareSimulations();

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [newForm, setNewForm] = useState({
    name: '',
    base_scenario_type: 'base',
    horizon_months: 120,
  });
  const [horizonYears, setHorizonYears] = useState(10);

  function toggleSelect(id: number) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setExpandedId((prev) => (prev === id ? null : id));
    setCompareResult(null);
  }

  function handleCreate() {
    if (!newForm.name.trim()) return;
    createSim.mutate(
      {
        name: newForm.name,
        base_scenario_type: newForm.base_scenario_type,
        horizon_months: newForm.horizon_months,
      },
      {
        onSuccess: () => {
          setShowNewForm(false);
          setNewForm({ name: '', base_scenario_type: 'base', horizon_months: 120 });
        },
      }
    );
  }

  function handleCompare() {
    compareMutation.mutate(
      { sim_ids: selectedIds, horizon_years: horizonYears },
      { onSuccess: (data) => setCompareResult(data) }
    );
  }

  return (
    <div style={{ padding: '0 24px' }}>
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
          {sims.length} simulació{sims.length !== 1 ? 'ns' : ''} guardada{sims.length !== 1 ? 'des' : ''}
        </div>
        <button
          onClick={() => setShowNewForm((v) => !v)}
          style={{
            padding: '7px 14px',
            borderRadius: 10,
            border: '1px solid var(--color-accent)',
            background: showNewForm ? 'var(--color-accent)' : 'transparent',
            color: showNewForm ? '#fff' : 'var(--color-accent)',
            fontSize: 12,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {showNewForm ? 'Cancel·lar' : '+ Nova Simulació'}
        </button>
      </div>

      {/* New simulation form */}
      {showNewForm && (
        <div
          style={{
            marginBottom: 16,
            padding: '14px',
            borderRadius: 14,
            border: '1px solid var(--color-glass-border)',
            background: 'var(--color-glass-bg)',
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <input
            placeholder="Nom de la simulació"
            value={newForm.name}
            onChange={(e) => setNewForm((f) => ({ ...f, name: e.target.value }))}
            style={inputStyle}
          />
          {/* Scenario pills */}
          <div style={{ display: 'flex', gap: 6 }}>
            {(['adverse', 'base', 'optimistic'] as const).map((sc) => {
              const active = newForm.base_scenario_type === sc;
              const color = SCENARIO_COLORS[sc];
              return (
                <button
                  key={sc}
                  onClick={() => setNewForm((f) => ({ ...f, base_scenario_type: sc }))}
                  style={{
                    flex: 1,
                    padding: '6px 0',
                    borderRadius: 8,
                    border: `1px solid ${active ? color : 'var(--color-glass-border)'}`,
                    background: active ? `${color}22` : 'transparent',
                    color: active ? color : 'var(--color-text-tertiary)',
                    fontSize: 11,
                    cursor: 'pointer',
                    fontFamily: 'var(--font-num)',
                  }}
                >
                  {SCENARIO_LABELS[sc]}
                </button>
              );
            })}
          </div>
          {/* Horizon */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap' }}>
              Horitzó (mesos):
            </span>
            <input
              type="number"
              min={12}
              max={600}
              value={newForm.horizon_months}
              onChange={(e) => setNewForm((f) => ({ ...f, horizon_months: parseInt(e.target.value) || 120 }))}
              style={{ ...inputStyle, width: 80 }}
            />
          </div>
          <button
            onClick={handleCreate}
            disabled={createSim.isPending}
            style={primaryBtnStyle}
          >
            {createSim.isPending ? 'Guardant…' : 'Crear simulació'}
          </button>
        </div>
      )}

      {/* Simulations list */}
      {isLoading ? (
        <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: 13 }}>
          Carregant…
        </div>
      ) : sims.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '32px 0',
            color: 'var(--color-text-tertiary)',
            fontSize: 13,
          }}
        >
          Encara no hi ha simulacions guardades.
          <br />
          Crea'n una per personalitzar la teva projecció.
        </div>
      ) : (
        <>
          {sims.map((sim) => (
            <div key={sim.id}>
              <SimCard
                sim={sim}
                onSelect={() => toggleSelect(sim.id)}
                onDelete={() => {
                  deleteSim.mutate(sim.id);
                  setSelectedIds((p) => p.filter((x) => x !== sim.id));
                  if (expandedId === sim.id) setExpandedId(null);
                }}
                isSelected={selectedIds.includes(sim.id)}
              />
              {expandedId === sim.id && <SimDetail simId={sim.id} />}
            </div>
          ))}

          {/* Compare controls */}
          {selectedIds.length > 0 && (
            <div
              style={{
                marginTop: 16,
                padding: '14px',
                borderRadius: 14,
                border: '1px solid var(--color-glass-border)',
                background: 'var(--color-glass-bg)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                  Horitzó comparació:
                </span>
                {[5, 10, 20, 30].map((yr) => (
                  <button
                    key={yr}
                    onClick={() => setHorizonYears(yr)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 8,
                      border: `1px solid ${horizonYears === yr ? 'var(--color-accent)' : 'var(--color-glass-border)'}`,
                      background: horizonYears === yr ? 'var(--color-accent)' : 'transparent',
                      color: horizonYears === yr ? '#fff' : 'var(--color-text-tertiary)',
                      fontSize: 11,
                      cursor: 'pointer',
                      fontFamily: 'var(--font-num)',
                    }}
                  >
                    {yr}a
                  </button>
                ))}
              </div>
              <button
                onClick={handleCompare}
                disabled={compareMutation.isPending}
                style={primaryBtnStyle}
              >
                {compareMutation.isPending ? 'Calculant…' : `Comparar (${selectedIds.length} seleccionada${selectedIds.length !== 1 ? 'des' : ''} + baseline)`}
              </button>
            </div>
          )}

          {/* Compare results */}
          {compareResult && (
            <div
              style={{
                marginTop: 16,
                padding: '14px',
                borderRadius: 14,
                border: '1px solid var(--color-glass-border)',
                background: 'var(--color-glass-bg)',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-tertiary)',
                  fontFamily: 'var(--font-num)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: 8,
                }}
              >
                Comparació {compareResult.horizon_years}a
              </div>
              <CompareChart result={compareResult} />

              {/* End values */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 12 }}>
                {compareResult.series.map((s) => (
                  <div
                    key={s.sim_id ?? 'baseline'}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 10px',
                      borderRadius: 8,
                      border: `1px solid ${s.color}33`,
                      background: `${s.color}0a`,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: s.color,
                        }}
                      />
                      <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                        {s.name}
                      </span>
                    </div>
                    <span
                      style={{
                        fontSize: 14,
                        fontWeight: 700,
                        fontFamily: 'var(--font-num)',
                        color: s.color,
                      }}
                    >
                      €{n(s.end_value).toLocaleString('ca-ES', { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
