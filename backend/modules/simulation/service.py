"""
modules/simulation/service.py — Lògica de negoci de la simulació.

Estratègia de retorn ponderat:
  Per a cada escenari (adverse/base/optimistic), el retorn de la cartera
  és la mitjana ponderada dels retorns individuals dels assets, usant
  els pesos actuals de la cartera (weight_actual_pct de l'últim snapshot).
  Assets sense posició (i.e., pesos 0) no contribueixen al blended return.
"""

import logging
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from modules.simulation import engine
from modules.simulation.schemas import (
    CompareResponse,
    ProjectionResponse,
    ProjectionSeries,
    ScenarioInfo,
    ScenarioProjection,
    ScenariosInfoResponse,
    SimulationCreate,
    SimulationDetailOut,
    SimulationEventCreate,
    SimulationEventOut,
    SimulationOut,
)

logger = logging.getLogger(__name__)

_SCENARIO_LABELS = {
    "adverse":    ("Advers",    "Mercat baix, retorns conservadors."),
    "base":       ("Base",      "Escenari central, retorns historials."),
    "optimistic": ("Optimista", "Mercat alcista, retorns elevats."),
}
_SCENARIO_ORDER = ["adverse", "base", "optimistic"]


async def _get_blended_returns(db: AsyncSession) -> dict[str, Decimal]:
    """
    Calcula el retorn ponderat de la cartera per a cada escenari,
    usant els pesos actuals de l'últim snapshot.
    """
    rows = (await db.execute(text("""
        SELECT
            asnap.asset_id,
            asnap.weight_actual_pct,
            s.scenario_type,
            s.annual_return
        FROM asset_snapshots asnap
        JOIN scenarios s ON s.asset_id = asnap.asset_id
        WHERE asnap.snapshot_id = (
            SELECT id FROM net_worth_snapshots ORDER BY snapshot_date DESC LIMIT 1
        )
        ORDER BY s.scenario_type, asnap.weight_actual_pct DESC
    """))).fetchall()

    # Ponderar per weight_actual_pct
    blended: dict[str, Decimal] = {t: Decimal("0") for t in _SCENARIO_ORDER}
    total_weight: dict[str, Decimal] = {t: Decimal("0") for t in _SCENARIO_ORDER}

    for row in rows:
        stype  = row.scenario_type
        weight = Decimal(str(row.weight_actual_pct or "0"))
        ret    = Decimal(str(row.annual_return))
        blended[stype]      += weight * ret / Decimal("100")
        total_weight[stype] += weight / Decimal("100")

    # Normalitzar (per si els pesos no sumen exactament 100%)
    result: dict[str, Decimal] = {}
    for stype in _SCENARIO_ORDER:
        tw = total_weight[stype]
        result[stype] = (
            (blended[stype] / tw).quantize(Decimal("0.001"))
            if tw > 0 else Decimal("0")
        )
    return result


async def get_scenarios_info(db: AsyncSession) -> ScenariosInfoResponse:
    """Retorna els 3 escenaris amb el retorn ponderat + context de cartera."""
    blended = await _get_blended_returns(db)

    # Contribucions mensuals actives
    monthly_contrib = (await db.execute(text("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM contributions
        WHERE is_active = TRUE
    """))).scalar()

    # Valor inversió actual
    inv_value = (await db.execute(text("""
        SELECT COALESCE(investment_portfolio_value, 0)
        FROM net_worth_snapshots
        ORDER BY snapshot_date DESC
        LIMIT 1
    """))).scalar()

    scenarios = [
        ScenarioInfo(
            scenario_type=stype,
            blended_return_pct=blended[stype],
            label=_SCENARIO_LABELS[stype][0],
            description=_SCENARIO_LABELS[stype][1],
        )
        for stype in _SCENARIO_ORDER
        if stype in blended
    ]

    return ScenariosInfoResponse(
        scenarios=scenarios,
        monthly_contributions=Decimal(str(monthly_contrib)),
        current_investment_eur=Decimal(str(inv_value or "0")),
    )


async def project_all(
    db: AsyncSession,
    horizon_years: int,
    monthly_contribution_override: Decimal | None = None,
) -> ProjectionResponse:
    """
    Calcula la projecció dels 3 escenaris per a l'horitzó indicat.

    Args:
      horizon_years:                 anys de projecció (1–50)
      monthly_contribution_override: si s'especifica, sobreescriu les contribucions de la BD
    """
    horizon_years = max(1, min(50, horizon_years))
    months = horizon_years * 12

    blended = await _get_blended_returns(db)

    # Contribucions mensuals
    if monthly_contribution_override is not None:
        monthly = monthly_contribution_override
    else:
        raw = (await db.execute(text("""
            SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE is_active = TRUE
        """))).scalar()
        monthly = Decimal(str(raw))

    # Valor inicial (últim snapshot)
    inv_value = (await db.execute(text("""
        SELECT COALESCE(investment_portfolio_value, 0)
        FROM net_worth_snapshots ORDER BY snapshot_date DESC LIMIT 1
    """))).scalar()
    start_value = Decimal(str(inv_value or "0"))

    # Objectiu d'habitatge
    obj_row = (await db.execute(text("""
        SELECT target_amount, target_date FROM objectives
        WHERE key = 'home_purchase' AND is_active = TRUE LIMIT 1
    """))).fetchone()
    home_target  = Decimal(str(obj_row.target_amount)) if obj_row else None
    home_date    = str(obj_row.target_date) if obj_row and obj_row.target_date else None

    # Projecció per a cada escenari
    projections: dict[str, ScenarioProjection] = {}
    for stype in _SCENARIO_ORDER:
        annual_ret = blended[stype]
        data_pts   = engine.project(start_value, monthly, annual_ret, months)
        end_val    = data_pts[-1]
        total_contribs = monthly * months
        total_ret_eur  = (end_val - start_value - total_contribs).quantize(Decimal("0.01"))
        invested_total = start_value + total_contribs
        total_ret_pct  = (
            (total_ret_eur / invested_total * 100).quantize(Decimal("0.01"))
            if invested_total > 0 else Decimal("0")
        )
        cagr_pct = engine.cagr(start_value, end_val, horizon_years)

        projections[stype] = ScenarioProjection(
            scenario_type=stype,
            label=_SCENARIO_LABELS[stype][0],
            annual_return_pct=annual_ret,
            end_value=end_val,
            total_return_eur=total_ret_eur,
            total_return_pct=total_ret_pct,
            total_contributions_eur=total_contribs,
            cagr_pct=cagr_pct,
            data_points=data_pts,
        )

    return ProjectionResponse(
        horizon_years=horizon_years,
        horizon_months=months,
        start_value=start_value,
        monthly_contribution=monthly,
        home_purchase_target=home_target,
        home_purchase_date=home_date,
        scenarios=projections,
    )


# ─── Open Simulator ───────────────────────────────────────────────────────────

_SIM_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]


async def list_saved_simulations(db: AsyncSession) -> list[SimulationOut]:
    """Llista les simulacions guardades, primer les fixades i desprès per data."""
    rows = (await db.execute(text("""
        SELECT id, name, description, base_scenario_type, horizon_months, is_pinned,
               TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS') AS created_at
        FROM simulations
        ORDER BY is_pinned DESC, created_at DESC
    """))).fetchall()

    return [
        SimulationOut(
            id=r.id,
            name=r.name,
            description=r.description,
            base_scenario_type=r.base_scenario_type,
            horizon_months=r.horizon_months,
            is_pinned=bool(r.is_pinned),
            created_at=r.created_at,
        )
        for r in rows
    ]


async def create_simulation(db: AsyncSession, data: SimulationCreate) -> SimulationOut:
    """Crea una nova simulació i retorna la fila creada."""
    row = (await db.execute(text("""
        INSERT INTO simulations (name, description, base_scenario_type, horizon_months,
                                  simulation_type, is_active, is_pinned)
        VALUES (:name, :description, :base_scenario_type, :horizon_months,
                'custom', TRUE, FALSE)
        RETURNING id, name, description, base_scenario_type, horizon_months, is_pinned,
                  TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS') AS created_at
    """), {
        "name": data.name,
        "description": data.description,
        "base_scenario_type": data.base_scenario_type,
        "horizon_months": data.horizon_months,
    })).fetchone()
    await db.commit()

    return SimulationOut(
        id=row.id,
        name=row.name,
        description=row.description,
        base_scenario_type=row.base_scenario_type,
        horizon_months=row.horizon_months,
        is_pinned=bool(row.is_pinned),
        created_at=row.created_at,
    )


async def get_simulation_detail(db: AsyncSession, sim_id: int) -> SimulationDetailOut | None:
    """Retorna una simulació amb els seus events."""
    sim_row = (await db.execute(text("""
        SELECT id, name, description, base_scenario_type, horizon_months, is_pinned
        FROM simulations WHERE id = :id
    """), {"id": sim_id})).fetchone()

    if not sim_row:
        return None

    event_rows = (await db.execute(text("""
        SELECT id, simulation_id, TO_CHAR(event_date, 'YYYY-MM-DD') AS event_date,
               name, event_type, amount, is_permanent, notes
        FROM simulation_events
        WHERE simulation_id = :sim_id
        ORDER BY event_date ASC
    """), {"sim_id": sim_id})).fetchall()

    events = [
        SimulationEventOut(
            id=r.id,
            simulation_id=r.simulation_id,
            event_date=r.event_date,
            name=r.name,
            event_type=r.event_type,
            amount=Decimal(str(r.amount)),
            is_permanent=bool(r.is_permanent),
            notes=r.notes,
        )
        for r in event_rows
    ]

    return SimulationDetailOut(
        id=sim_row.id,
        name=sim_row.name,
        description=sim_row.description,
        base_scenario_type=sim_row.base_scenario_type,
        horizon_months=sim_row.horizon_months,
        is_pinned=bool(sim_row.is_pinned),
        events=events,
    )


async def delete_simulation(db: AsyncSession, sim_id: int) -> bool:
    """Elimina una simulació i els seus events en cascada."""
    result = await db.execute(text("""
        DELETE FROM simulations WHERE id = :id
    """), {"id": sim_id})
    await db.commit()
    return result.rowcount > 0


async def add_event(
    db: AsyncSession,
    sim_id: int,
    data: SimulationEventCreate,
) -> SimulationEventOut:
    """Afegeix un event a una simulació."""
    row = (await db.execute(text("""
        INSERT INTO simulation_events (simulation_id, event_date, name, event_type,
                                       amount, is_permanent, notes)
        VALUES (:sim_id, :event_date, :name, :event_type, :amount, :is_permanent, :notes)
        RETURNING id, simulation_id, TO_CHAR(event_date, 'YYYY-MM-DD') AS event_date,
                  name, event_type, amount, is_permanent, notes
    """), {
        "sim_id": sim_id,
        "event_date": str(data.event_date),
        "name": data.name,
        "event_type": data.event_type,
        "amount": str(data.amount),
        "is_permanent": data.is_permanent,
        "notes": data.notes,
    })).fetchone()
    await db.commit()

    return SimulationEventOut(
        id=row.id,
        simulation_id=row.simulation_id,
        event_date=row.event_date,
        name=row.name,
        event_type=row.event_type,
        amount=Decimal(str(row.amount)),
        is_permanent=bool(row.is_permanent),
        notes=row.notes,
    )


async def delete_event(db: AsyncSession, event_id: int) -> bool:
    """Elimina un event d'una simulació."""
    result = await db.execute(text("""
        DELETE FROM simulation_events WHERE id = :id
    """), {"id": event_id})
    await db.commit()
    return result.rowcount > 0


async def compare_simulations(
    db: AsyncSession,
    sim_ids: list[int],
    horizon_years: int,
) -> CompareResponse:
    """
    Executa la projecció per a cada simulació + el baseline actual.
    Aplica els events de cada simulació per modificar el flux mensual.
    """
    horizon_years = max(1, min(50, horizon_years))
    months = horizon_years * 12

    blended = await _get_blended_returns(db)
    base_return = blended.get("base", Decimal("7"))

    # Contribucions mensuals actives
    raw_monthly = (await db.execute(text("""
        SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE is_active = TRUE
    """))).scalar()
    base_monthly = Decimal(str(raw_monthly))

    # Valor inicial (últim snapshot)
    inv_value = (await db.execute(text("""
        SELECT COALESCE(investment_portfolio_value, 0)
        FROM net_worth_snapshots ORDER BY snapshot_date DESC LIMIT 1
    """))).scalar()
    start_value = Decimal(str(inv_value or "0"))

    series: list[ProjectionSeries] = []

    # ── Baseline (actual) ─────────────────────────────────────────────────
    baseline_pts = engine.project(start_value, base_monthly, base_return, months)
    baseline_end = baseline_pts[-1]
    baseline_contribs = base_monthly * months
    baseline_return_eur = (baseline_end - start_value - baseline_contribs).quantize(Decimal("0.01"))

    series.append(ProjectionSeries(
        sim_id=None,
        name="Actual (base)",
        color="#3B82F6",
        annual_return_pct=base_return,
        data_points=baseline_pts,
        end_value=baseline_end,
        total_contributions_eur=baseline_contribs,
        total_return_eur=baseline_return_eur,
    ))

    # ── Per a cada simulació guardada ─────────────────────────────────────
    from datetime import date as _date
    today = _date.today()

    for idx, sim_id in enumerate(sim_ids):
        detail = await get_simulation_detail(db, sim_id)
        if not detail:
            continue

        # Escenari base de la simulació
        sim_return = blended.get(detail.base_scenario_type, base_return)
        monthly = base_monthly
        color = _SIM_COLORS[(idx + 1) % len(_SIM_COLORS)]

        # Construir projecció mes a mes aplicant events
        from modules.simulation import engine as eng
        r_m = eng.monthly_rate(sim_return)
        current = start_value
        data_pts: list[Decimal] = [current.quantize(Decimal("0.01"))]

        current_monthly = monthly
        current_return = sim_return

        for m_idx in range(months):
            # Data del mes actual de la projecció (aproximació)
            proj_year  = today.year  + (today.month - 1 + m_idx) // 12
            proj_month = (today.month - 1 + m_idx) % 12 + 1
            proj_date  = _date(proj_year, proj_month, 1)

            # Aplicar events d'aquest mes
            one_time_delta = Decimal("0")
            for ev in detail.events:
                ev_date = _date.fromisoformat(ev.event_date)
                if ev_date.year == proj_date.year and ev_date.month == proj_date.month:
                    if ev.event_type == "one_time_out":
                        one_time_delta -= Decimal(str(ev.amount))
                    elif ev.event_type == "one_time_in":
                        one_time_delta += Decimal(str(ev.amount))
                    elif ev.event_type == "contribution_change":
                        current_monthly = Decimal(str(ev.amount))
                    elif ev.event_type == "return_override":
                        current_return = Decimal(str(ev.amount))
                        r_m = eng.monthly_rate(current_return)

            current = current * (1 + r_m) + current_monthly + one_time_delta
            if current < 0:
                current = Decimal("0")
            data_pts.append(current.quantize(Decimal("0.01")))

        end_val = data_pts[-1]
        total_contribs = current_monthly * months  # approximate
        total_ret = (end_val - start_value - total_contribs).quantize(Decimal("0.01"))

        series.append(ProjectionSeries(
            sim_id=sim_id,
            name=detail.name,
            color=color,
            annual_return_pct=sim_return,
            data_points=data_pts,
            end_value=end_val,
            total_contributions_eur=total_contribs,
            total_return_eur=total_ret,
        ))

    return CompareResponse(
        horizon_years=horizon_years,
        start_value=start_value,
        series=series,
    )
