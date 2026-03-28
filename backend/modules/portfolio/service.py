"""
modules/portfolio/service.py — Lògica de negoci del portfolio.

Funcions:
  - get_latest_snapshot(): retorna l'últim snapshot de net worth + assets
  - get_rebalancing(): calcula sobreponderat/infraponderat vs. target_weight
  - get_portfolio_summary(): resum net worth per al dashboard
"""

import logging
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from modules.portfolio.schemas import (
    PortfolioSummaryResponse,
    RebalanceResponse,
    RebalanceSuggestion,
)

logger = logging.getLogger(__name__)

_THRESHOLD_PCT = Decimal("1.0")  # ±1% → on_track; > = sobre/infraponderat


async def get_portfolio_summary(db: AsyncSession) -> PortfolioSummaryResponse | None:
    """Retorna el resum del portfolio basat en l'últim snapshot disponible."""
    row = (await db.execute(text("""
        SELECT
            snapshot_date,
            total_net_worth,
            investment_portfolio_value,
            cash_and_bank_value,
            change_eur,
            change_pct
        FROM net_worth_snapshots
        ORDER BY snapshot_date DESC
        LIMIT 1
    """))).fetchone()

    if not row:
        return None

    return PortfolioSummaryResponse(
        snapshot_date=row.snapshot_date,
        total_net_worth=row.total_net_worth,
        investment_portfolio_value=row.investment_portfolio_value,
        cash_and_bank_value=row.cash_and_bank_value,
        change_eur=row.change_eur,
        change_pct=row.change_pct,
        on_track=None,        # implementat a Fase 3 amb el motor de simulació
        on_track_detail=None,
    )


async def get_rebalancing(db: AsyncSession) -> RebalanceResponse | None:
    """
    Calcula les suggerències de rebalanceig.

    Metodologia:
      1. Agafa l'últim snapshot + actius.
      2. Compara weight_actual_pct (cartera inversió) vs. target_weight dels assets.
      3. Calcula l'import a comprar/vendre per a cada asset.
      4. Assets sense target_weight s'indiquen com a "on_track" (sense suggeriment).
    """
    # ── Snapshot actual + assets ─────────────────────────────────────────────
    snapshot_row = (await db.execute(text("""
        SELECT id, snapshot_date, investment_portfolio_value
        FROM net_worth_snapshots
        ORDER BY snapshot_date DESC
        LIMIT 1
    """))).fetchone()

    if not snapshot_row:
        return None

    snapshot_id  = snapshot_row.id
    snap_date    = snapshot_row.snapshot_date
    total_inv    = Decimal(str(snapshot_row.investment_portfolio_value))

    # ── Assets del snapshot amb target_weight ────────────────────────────────
    asset_rows = (await db.execute(text("""
        SELECT
            asnap.asset_id,
            a.display_name,
            a.ticker_yf,
            a.color_hex,
            a.target_weight,
            asnap.value_eur,
            asnap.weight_actual_pct
        FROM asset_snapshots asnap
        JOIN assets a ON a.id = asnap.asset_id
        WHERE asnap.snapshot_id = :sid
        ORDER BY asnap.value_eur DESC
    """), {"sid": snapshot_id})).fetchall()

    # ── Assets amb target_weight però sense posició actual (missing) ─────────
    missing_rows = (await db.execute(text("""
        SELECT id AS asset_id, display_name, ticker_yf, color_hex, target_weight
        FROM assets
        WHERE is_active = TRUE
          AND target_weight IS NOT NULL
          AND target_weight > 0
          AND id NOT IN (
              SELECT asset_id FROM asset_snapshots WHERE snapshot_id = :sid
          )
          AND asset_type != 'cash'
        ORDER BY target_weight DESC
    """), {"sid": snapshot_id})).fetchall()

    # ── Suma dels target_weight dels assets invertibles (no cash) ────────────
    total_target = (await db.execute(text("""
        SELECT COALESCE(SUM(target_weight), 0) AS total
        FROM assets
        WHERE is_active = TRUE
          AND target_weight IS NOT NULL
          AND asset_type != 'cash'
    """))).scalar()

    total_target_dec = Decimal(str(total_target)) if total_target else None

    suggestions: list[RebalanceSuggestion] = []

    # Assets amb posició actual
    for row in asset_rows:
        value       = Decimal(str(row.value_eur))
        actual_pct  = Decimal(str(row.weight_actual_pct)) if row.weight_actual_pct else Decimal("0")
        target_pct  = Decimal(str(row.target_weight)) if row.target_weight else None

        if target_pct is not None and total_inv > 0:
            diff        = (actual_pct - target_pct).quantize(Decimal("0.01"))
            action_eur  = -(diff / 100 * total_inv).quantize(Decimal("0.01"))  # negatiu=comprar, positiu=vendre
            if abs(diff) <= _THRESHOLD_PCT:
                direction = "on_track"
            elif diff > 0:
                direction = "overweight"
            else:
                direction = "underweight"
        else:
            diff       = None
            action_eur = None
            direction  = "on_track"

        suggestions.append(RebalanceSuggestion(
            asset_id=row.asset_id,
            display_name=row.display_name,
            ticker_yf=row.ticker_yf,
            color_hex=row.color_hex,
            value_eur=value,
            weight_actual_pct=actual_pct,
            target_weight_pct=target_pct,
            weight_diff_pct=diff,
            direction=direction,
            action_eur=action_eur,
        ))

    # Assets sense posició (missing)
    for row in missing_rows:
        target_pct = Decimal(str(row.target_weight))
        action_eur = -(target_pct / 100 * total_inv).quantize(Decimal("0.01"))
        suggestions.append(RebalanceSuggestion(
            asset_id=row.asset_id,
            display_name=row.display_name,
            ticker_yf=row.ticker_yf,
            color_hex=row.color_hex,
            value_eur=Decimal("0"),
            weight_actual_pct=Decimal("0"),
            target_weight_pct=target_pct,
            weight_diff_pct=-target_pct,
            direction="missing",
            action_eur=action_eur,
        ))

    # Ordena: primer els que necessiten acció (per magnitud absoluta de diff)
    suggestions.sort(
        key=lambda s: abs(s.weight_diff_pct) if s.weight_diff_pct is not None else Decimal("0"),
        reverse=True,
    )

    return RebalanceResponse(
        snapshot_date=snap_date,
        total_investment_eur=total_inv,
        total_target_pct=total_target_dec,
        suggestions=suggestions,
    )
