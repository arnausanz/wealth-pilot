"""modules/networth/router.py — Endpoints REST per al net worth."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.networth import service
from modules.networth.models import NetWorthSnapshot
from modules.networth.schemas import (
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
    """Historial de snapshots de net worth per al període indicat."""
    if period not in _VALID_PERIODS:
        raise HTTPException(422, f"Període invàlid. Opcions: {', '.join(sorted(_VALID_PERIODS))}")

    snapshots = await service.get_history(db, period=period)

    current = snapshots[-1].total_net_worth if snapshots else None
    first   = snapshots[0].total_net_worth  if snapshots else None
    change_eur = (current - first).quantize(__import__("decimal").Decimal("0.01")) if (current and first) else None
    change_pct = (change_eur / first * 100).quantize(__import__("decimal").Decimal("0.01")) if (first and change_eur) else None

    return NetWorthHistoryResponse(
        period=period,
        snapshots=[
            NetWorthSnapshotOut.model_validate({
                "id": s.id,
                "snapshot_date": s.snapshot_date,
                "total_net_worth": s.total_net_worth,
                "investment_portfolio_value": s.investment_portfolio_value,
                "cash_and_bank_value": s.cash_and_bank_value,
                "real_estate_value": s.real_estate_value,
                "pension_value": s.pension_value,
                "other_assets_value": s.other_assets_value,
                "total_liabilities": s.total_liabilities,
                "change_eur": s.change_eur,
                "change_pct": s.change_pct,
                "trigger_source": s.trigger_source,
                "created_at": s.created_at,
                "asset_snapshots": [],
            })
            for s in snapshots
        ],
        current_net_worth=current,
        change_eur_period=change_eur,
        change_pct_period=change_pct,
    )
