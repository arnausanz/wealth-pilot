"""
modules/config/service.py — CRUD per a la configuració de l'app.

Totes les operacions són simples SELECT/UPDATE/INSERT sense lògica complexa.
Les validacions de negoci (target_weight suma 100%, etc.) es fan aquí.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from modules.config.schemas import (
    AssetConfigCreate,
    AssetConfigOut,
    AssetConfigPatch,
    ContributionCreate,
    ContributionOut,
    ContributionPatch,
    ObjectiveOut,
    ObjectivePatch,
    ParameterOut,
    ParameterPatch,
    ScenarioPatch,
    ScenarioRow,
)

logger = logging.getLogger(__name__)


# ─── Assets ──────────────────────────────────────────────────────────────────

async def list_assets(db: AsyncSession) -> list[AssetConfigOut]:
    rows = (await db.execute(text("""
        SELECT id, name, display_name, ticker_yf, ticker_mw, isin,
               asset_type, currency, color_hex, target_weight, is_active, sort_order
        FROM assets
        ORDER BY sort_order, id
    """))).fetchall()
    return [AssetConfigOut(**dict(row._mapping)) for row in rows]


async def patch_asset(db: AsyncSession, asset_id: int, data: AssetConfigPatch) -> AssetConfigOut | None:
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        return await get_asset(db, asset_id)

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = asset_id
    updates["updated_at"] = datetime.now(timezone.utc)
    set_clauses += ", updated_at = :updated_at"

    await db.execute(text(f"UPDATE assets SET {set_clauses} WHERE id = :id"), updates)
    await db.commit()
    return await get_asset(db, asset_id)


async def get_asset(db: AsyncSession, asset_id: int) -> AssetConfigOut | None:
    row = (await db.execute(text("""
        SELECT id, name, display_name, ticker_yf, ticker_mw, isin,
               asset_type, currency, color_hex, target_weight, is_active, sort_order
        FROM assets WHERE id = :id
    """), {"id": asset_id})).fetchone()
    return AssetConfigOut(**dict(row._mapping)) if row else None


async def create_asset(db: AsyncSession, data: AssetConfigCreate) -> AssetConfigOut:
    row = (await db.execute(text("""
        INSERT INTO assets (name, display_name, ticker_yf, ticker_mw, isin,
                            asset_type, currency, color_hex, target_weight, sort_order,
                            is_active, created_at, updated_at)
        VALUES (:name, :display_name, :ticker_yf, :ticker_mw, :isin,
                :asset_type, :currency, :color_hex, :target_weight, :sort_order,
                TRUE, NOW(), NOW())
        RETURNING id
    """), data.model_dump())).fetchone()
    return await get_asset(db, row.id)


async def get_total_target_weight(db: AsyncSession) -> Decimal:
    result = (await db.execute(text("""
        SELECT COALESCE(SUM(target_weight), 0) FROM assets WHERE is_active = TRUE AND target_weight IS NOT NULL
    """))).scalar()
    return Decimal(str(result))


# ─── Contributions ────────────────────────────────────────────────────────────

async def list_contributions(db: AsyncSession) -> list[ContributionOut]:
    rows = (await db.execute(text("""
        SELECT c.id, c.asset_id, a.display_name AS asset_display_name,
               a.ticker_yf AS asset_ticker_yf, a.color_hex AS asset_color_hex,
               c.amount, c.day_of_month, c.is_active, c.notes
        FROM contributions c
        JOIN assets a ON a.id = c.asset_id
        ORDER BY a.sort_order, c.id
    """))).fetchall()
    return [ContributionOut(**dict(row._mapping)) for row in rows]


async def patch_contribution(db: AsyncSession, contrib_id: int, data: ContributionPatch) -> ContributionOut | None:
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        return await get_contribution(db, contrib_id)

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = contrib_id
    updates["updated_at"] = datetime.now(timezone.utc)
    set_clauses += ", updated_at = :updated_at"

    await db.execute(text(f"UPDATE contributions SET {set_clauses} WHERE id = :id"), updates)
    await db.commit()
    return await get_contribution(db, contrib_id)


async def get_contribution(db: AsyncSession, contrib_id: int) -> ContributionOut | None:
    row = (await db.execute(text("""
        SELECT c.id, c.asset_id, a.display_name AS asset_display_name,
               a.ticker_yf AS asset_ticker_yf, a.color_hex AS asset_color_hex,
               c.amount, c.day_of_month, c.is_active, c.notes
        FROM contributions c
        JOIN assets a ON a.id = c.asset_id
        WHERE c.id = :id
    """), {"id": contrib_id})).fetchone()
    return ContributionOut(**dict(row._mapping)) if row else None


async def create_contribution(db: AsyncSession, data: ContributionCreate) -> ContributionOut:
    row = (await db.execute(text("""
        INSERT INTO contributions (asset_id, amount, day_of_month, start_date, is_active, notes, created_at, updated_at)
        VALUES (:asset_id, :amount, :day_of_month, CURRENT_DATE, TRUE, :notes, NOW(), NOW())
        RETURNING id
    """), data.model_dump())).fetchone()
    return await get_contribution(db, row.id)


async def delete_contribution(db: AsyncSession, contrib_id: int) -> bool:
    result = await db.execute(text("DELETE FROM contributions WHERE id = :id"), {"id": contrib_id})
    await db.commit()
    return result.rowcount > 0


# ─── Scenarios ────────────────────────────────────────────────────────────────

async def list_scenarios(db: AsyncSession) -> list[ScenarioRow]:
    rows = (await db.execute(text("""
        SELECT a.id AS asset_id, a.display_name, a.ticker_yf,
               MAX(CASE s.scenario_type WHEN 'adverse'    THEN s.annual_return END) AS adverse,
               MAX(CASE s.scenario_type WHEN 'base'       THEN s.annual_return END) AS base,
               MAX(CASE s.scenario_type WHEN 'optimistic' THEN s.annual_return END) AS optimistic
        FROM assets a
        LEFT JOIN scenarios s ON s.asset_id = a.id
        WHERE a.is_active = TRUE
        GROUP BY a.id, a.display_name, a.ticker_yf
        ORDER BY a.sort_order
    """))).fetchall()
    return [ScenarioRow(**dict(row._mapping)) for row in rows]


async def patch_scenario(
    db: AsyncSession,
    asset_id: int,
    scenario_type: str,
    data: ScenarioPatch,
) -> ScenarioRow | None:
    await db.execute(text("""
        INSERT INTO scenarios (asset_id, scenario_type, annual_return, updated_at)
        VALUES (:asset_id, :scenario_type, :annual_return, NOW())
        ON CONFLICT (asset_id, scenario_type) DO UPDATE
        SET annual_return = EXCLUDED.annual_return, updated_at = NOW()
    """), {"asset_id": asset_id, "scenario_type": scenario_type, "annual_return": data.annual_return})
    await db.commit()
    rows = await list_scenarios(db)
    return next((r for r in rows if r.asset_id == asset_id), None)


# ─── Objectives ──────────────────────────────────────────────────────────────

async def list_objectives(db: AsyncSession) -> list[ObjectiveOut]:
    rows = (await db.execute(text("""
        SELECT id, key, name, description, objective_type,
               target_amount, target_date, current_amount, is_active
        FROM objectives ORDER BY priority, id
    """))).fetchall()
    return [ObjectiveOut(**dict(row._mapping)) for row in rows]


async def patch_objective(db: AsyncSession, obj_id: int, data: ObjectivePatch) -> ObjectiveOut | None:
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        return await get_objective(db, obj_id)

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = obj_id
    updates["updated_at"] = datetime.now(timezone.utc)
    set_clauses += ", updated_at = :updated_at"

    await db.execute(text(f"UPDATE objectives SET {set_clauses} WHERE id = :id"), updates)
    await db.commit()
    return await get_objective(db, obj_id)


async def get_objective(db: AsyncSession, obj_id: int) -> ObjectiveOut | None:
    row = (await db.execute(text("""
        SELECT id, key, name, description, objective_type,
               target_amount, target_date, current_amount, is_active
        FROM objectives WHERE id = :id
    """), {"id": obj_id})).fetchone()
    return ObjectiveOut(**dict(row._mapping)) if row else None


# ─── Parameters ──────────────────────────────────────────────────────────────

async def list_parameters(db: AsyncSession, category: Optional[str] = None) -> list[ParameterOut]:
    sql = """
        SELECT key, value, value_type, description, category, is_editable
        FROM parameters
        WHERE is_editable = TRUE
    """
    params: dict = {}
    if category:
        sql += " AND category = :category"
        params["category"] = category
    sql += " ORDER BY category, key"
    rows = (await db.execute(text(sql), params)).fetchall()
    return [ParameterOut(**dict(row._mapping)) for row in rows]


async def patch_parameter(db: AsyncSession, key: str, data: ParameterPatch) -> ParameterOut | None:
    result = await db.execute(text("""
        UPDATE parameters SET value = :value, updated_at = NOW()
        WHERE key = :key AND is_editable = TRUE
        RETURNING key
    """), {"key": key, "value": data.value})
    await db.commit()
    if not result.fetchone():
        return None
    row = (await db.execute(text("""
        SELECT key, value, value_type, description, category, is_editable
        FROM parameters WHERE key = :key
    """), {"key": key})).fetchone()
    return ParameterOut(**dict(row._mapping)) if row else None


# ─── Reset a valors per defecte ───────────────────────────────────────────────

# Estructura: (ticker_yf o None, display_name, target_weight)
_DEFAULT_TARGET_WEIGHTS: list[tuple[str | None, str, Decimal]] = [
    ("IWDA.AS",  "MSCI World",       Decimal("22.0")),
    ("PPFB.DE",  "Physical Gold",    Decimal("12.0")),
    ("IMAE.AS",  "MSCI Europe",      Decimal("10.0")),
    ("EMIM.AS",  "MSCI EM IMI",      Decimal("5.0")),
    ("CSJP.AS",  "Japan",            Decimal("6.0")),
    ("WDEF.MI",  "Europe Defence",   Decimal("5.0")),
    ("BTC-EUR",  "Bitcoin",          Decimal("2.0")),
    (None,       "Cash",             Decimal("25.0")),
]

# Estructura: (ticker_yf o None, display_name, scenario_type, annual_return)
_DEFAULT_SCENARIOS: list[tuple[str | None, str, str, Decimal]] = [
    ("IWDA.AS",  "MSCI World",     "adverse",    Decimal("4.0")),
    ("IWDA.AS",  "MSCI World",     "base",       Decimal("7.0")),
    ("IWDA.AS",  "MSCI World",     "optimistic", Decimal("10.0")),
    ("PPFB.DE",  "Physical Gold",  "adverse",    Decimal("1.0")),
    ("PPFB.DE",  "Physical Gold",  "base",       Decimal("4.0")),
    ("PPFB.DE",  "Physical Gold",  "optimistic", Decimal("7.0")),
    ("IMAE.AS",  "MSCI Europe",    "adverse",    Decimal("3.0")),
    ("IMAE.AS",  "MSCI Europe",    "base",       Decimal("6.0")),
    ("IMAE.AS",  "MSCI Europe",    "optimistic", Decimal("9.0")),
    ("EMIM.AS",  "MSCI EM IMI",    "adverse",    Decimal("2.0")),
    ("EMIM.AS",  "MSCI EM IMI",    "base",       Decimal("7.0")),
    ("EMIM.AS",  "MSCI EM IMI",    "optimistic", Decimal("12.0")),
    ("CSJP.AS",  "Japan",          "adverse",    Decimal("2.0")),
    ("CSJP.AS",  "Japan",          "base",       Decimal("5.0")),
    ("CSJP.AS",  "Japan",          "optimistic", Decimal("8.0")),
    ("WDEF.MI",  "Europe Defence", "adverse",    Decimal("3.0")),
    ("WDEF.MI",  "Europe Defence", "base",       Decimal("8.0")),
    ("WDEF.MI",  "Europe Defence", "optimistic", Decimal("13.0")),
    ("BTC-EUR",  "Bitcoin",        "adverse",    Decimal("-10.0")),
    ("BTC-EUR",  "Bitcoin",        "base",       Decimal("15.0")),
    ("BTC-EUR",  "Bitcoin",        "optimistic", Decimal("40.0")),
    (None,       "Cash",           "adverse",    Decimal("2.0")),
    (None,       "Cash",           "base",       Decimal("3.0")),
    (None,       "Cash",           "optimistic", Decimal("4.0")),
]

# Estructura: (ticker_yf o None, display_name, amount)
_DEFAULT_CONTRIBUTIONS: list[tuple[str | None, str, Decimal]] = [
    ("IWDA.AS",  "MSCI World",     Decimal("200.00")),
    ("PPFB.DE",  "Physical Gold",  Decimal("100.00")),
    ("IMAE.AS",  "MSCI Europe",    Decimal("100.00")),
    ("EMIM.AS",  "MSCI EM IMI",    Decimal("50.00")),
    ("CSJP.AS",  "Japan",          Decimal("50.00")),
    ("WDEF.MI",  "Europe Defence", Decimal("50.00")),
    ("BTC-EUR",  "Bitcoin",        Decimal("25.00")),
]

_DEFAULT_OBJECTIVES: dict[str, dict] = {
    "home_purchase": {
        "target_amount": Decimal("80000.00"),
        "target_date": date(2029, 12, 31),
        "is_active": True,
    },
    "emergency_fund": {
        "target_amount": Decimal("15000.00"),
        "target_date": None,
        "is_active": True,
    },
}


def _asset_lookup_clause(ticker: str | None) -> str:
    """Retorna la clàusula WHERE per trobar un asset per ticker_yf o display_name."""
    return "ticker_yf = :ticker" if ticker else "display_name = :name"


async def reset_to_defaults(db: AsyncSession) -> dict:
    """Restaura assets target_weight, escenaris, contribucions i objectius als valors seed."""
    changes: dict[str, int] = {
        "assets_updated": 0,
        "scenarios_updated": 0,
        "contributions_updated": 0,
        "objectives_updated": 0,
    }

    # 1. Assets: restaurar target_weight per ticker_yf (o display_name si ticker és None)
    for ticker, name, weight in _DEFAULT_TARGET_WEIGHTS:
        where = _asset_lookup_clause(ticker)
        result = await db.execute(
            text(f"UPDATE assets SET target_weight = :w, updated_at = NOW() WHERE {where}"),
            {"w": weight, "ticker": ticker, "name": name},
        )
        changes["assets_updated"] += result.rowcount

    # 2. Escenaris: upsert per ticker_yf/display_name → asset_id
    for ticker, name, scenario_type, annual_return in _DEFAULT_SCENARIOS:
        where = _asset_lookup_clause(ticker)
        asset_row = (await db.execute(
            text(f"SELECT id FROM assets WHERE {where}"),
            {"ticker": ticker, "name": name},
        )).fetchone()
        if not asset_row:
            continue
        asset_id = asset_row.id
        await db.execute(text("""
            INSERT INTO scenarios (asset_id, scenario_type, annual_return, updated_at)
            VALUES (:asset_id, :scenario_type, :annual_return, NOW())
            ON CONFLICT (asset_id, scenario_type) DO UPDATE
            SET annual_return = EXCLUDED.annual_return, updated_at = NOW()
        """), {"asset_id": asset_id, "scenario_type": scenario_type, "annual_return": annual_return})
        changes["scenarios_updated"] += 1

    # 3. Contribucions: restaurar amount per ticker_yf/display_name
    for ticker, name, amount in _DEFAULT_CONTRIBUTIONS:
        where = _asset_lookup_clause(ticker)
        result = await db.execute(
            text(f"""
                UPDATE contributions SET amount = :amount, updated_at = NOW()
                WHERE asset_id = (SELECT id FROM assets WHERE {where} LIMIT 1)
            """),
            {"amount": amount, "ticker": ticker, "name": name},
        )
        changes["contributions_updated"] += result.rowcount

    # 4. Objectius: restaurar per key
    for key, vals in _DEFAULT_OBJECTIVES.items():
        result = await db.execute(
            text("""
                UPDATE objectives
                SET target_amount = :target_amount,
                    target_date = :target_date,
                    is_active = :is_active,
                    updated_at = NOW()
                WHERE key = :key
            """),
            {
                "key": key,
                "target_amount": vals["target_amount"],
                "target_date": vals["target_date"],
                "is_active": vals["is_active"],
            },
        )
        changes["objectives_updated"] += result.rowcount

    await db.commit()
    logger.info("Config reset to defaults: %s", changes)
    return changes
