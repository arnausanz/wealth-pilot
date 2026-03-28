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
    ProjectionResponse,
    ScenarioInfo,
    ScenarioProjection,
    ScenariosInfoResponse,
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
