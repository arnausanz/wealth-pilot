"""modules/networth/router.py — Endpoints REST per al net worth."""

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.networth import service
from modules.networth.models import NetWorthSnapshot
from modules.networth.schemas import (
    AssetSnapshotOut,
    GenerateSnapshotResponse,
    NetWorthHistoryResponse,
    NetWorthSnapshotOut,
)

router = APIRouter(prefix="/api/v1/networth", tags=["networth"])

_VALID_PERIODS = {"1m", "3m", "6m", "1y", "2y", "5y", "all"}


@router.post("/snapshot", response_model=GenerateSnapshotResponse, status_code=201)
async def create_snapshot(
    snapshot_date: date | None = Query(default=None, description="Data del snapshot (default: avui)"),
    db: AsyncSession = Depends(get_db),
):
    """Genera (o actualitza) el snapshot de net worth per a una data concreta."""
    return await service.generate_snapshot(db, snapshot_date=snapshot_date, trigger_source="api")


@router.get("/history", response_model=NetWorthHistoryResponse)
async def get_history(
    period: str = Query(default="1y", description="1m | 3m | 6m | 1y | 2y | 5y | all"),
    db: AsyncSession = Depends(get_db),
):
    """Historial de snapshots de net worth per al període indicat, amb detall per asset."""
    if period not in _VALID_PERIODS:
        raise HTTPException(422, f"Període invàlid. Opcions: {', '.join(sorted(_VALID_PERIODS))}")

    snapshots = await service.get_history(db, period=period)

    # ── Carregar asset_snapshots per a tots els snapshots del període ─────────
    snap_ids = [s.id for s in snapshots]
    snap_assets: dict[int, list] = defaultdict(list)

    if snap_ids:
        asset_rows = (await db.execute(text("""
            SELECT
                asnap.snapshot_id,
                asnap.asset_id,
                a.display_name,
                a.ticker_yf,
                a.color_hex,
                asnap.shares,
                asnap.price_eur,
                asnap.value_eur,
                asnap.cost_basis_eur,
                asnap.unrealized_pnl_eur AS pnl_eur,
                asnap.unrealized_pnl_pct AS pnl_pct,
                asnap.weight_actual_pct
            FROM asset_snapshots asnap
            JOIN assets a ON a.id = asnap.asset_id
            WHERE asnap.snapshot_id = ANY(:ids)
            ORDER BY asnap.snapshot_id, asnap.value_eur DESC
        """), {"ids": snap_ids})).fetchall()

        for row in asset_rows:
            snap_assets[row.snapshot_id].append(
                AssetSnapshotOut.model_validate({
                    "asset_id":        row.asset_id,
                    "display_name":    row.display_name,
                    "ticker_yf":       row.ticker_yf,
                    "color_hex":       row.color_hex,
                    "shares":          row.shares,
                    "price_eur":       row.price_eur,
                    "value_eur":       row.value_eur,
                    "cost_basis_eur":  row.cost_basis_eur,
                    "pnl_eur":         row.pnl_eur,
                    "pnl_pct":         row.pnl_pct,
                    "weight_actual_pct": row.weight_actual_pct,
                })
            )

    current    = snapshots[-1].total_net_worth if snapshots else None
    first      = snapshots[0].total_net_worth  if snapshots else None
    change_eur = (current - first).quantize(__import__("decimal").Decimal("0.01")) if (current and first) else None
    change_pct = (change_eur / first * 100).quantize(__import__("decimal").Decimal("0.01")) if (first and change_eur) else None

    return NetWorthHistoryResponse(
        period=period,
        snapshots=[
            NetWorthSnapshotOut.model_validate({
                "id":                         s.id,
                "snapshot_date":              s.snapshot_date,
                "total_net_worth":            s.total_net_worth,
                "investment_portfolio_value": s.investment_portfolio_value,
                "cash_and_bank_value":        s.cash_and_bank_value,
                "real_estate_value":          s.real_estate_value,
                "pension_value":              s.pension_value,
                "other_assets_value":         s.other_assets_value,
                "total_liabilities":          s.total_liabilities,
                "change_eur":                 s.change_eur,
                "change_pct":                 s.change_pct,
                "trigger_source":             s.trigger_source,
                "created_at":                 s.created_at,
                "asset_snapshots":            snap_assets[s.id],
            })
            for s in snapshots
        ],
        current_net_worth=current,
        change_eur_period=change_eur,
        change_pct_period=change_pct,
    )


@router.post("/backfill", status_code=200)
async def backfill_history(
    months: int = Query(default=24, ge=1, le=60, description="Mesos a regenerar (default: 24)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera snapshots mensuals retrospectius per omplir el gràfic d'historial.
    Útil després d'una importació inicial de MoneyWiz.
    Idempotent — segur de cridar múltiples vegades.
    """
    result = await service.backfill_snapshots(db, months=months)
    return {
        "ok": True,
        "snapshots_created": result["created"],
        "errors": result["errors"],
        "dates": result["dates"],
    }
