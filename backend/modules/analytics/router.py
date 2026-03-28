"""modules/analytics/router.py — Endpoints REST per al mòdul d'analítica."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.analytics import service
from modules.analytics.schemas import (
    AlertsResponse,
    CashflowResponse,
    ExpenseBreakdownResponse,
    NetWorthEvolutionResponse,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/expenses", response_model=ExpenseBreakdownResponse)
async def get_expenses(
    year: int = Query(..., description="Any (ex: 2025)"),
    month: Optional[int] = Query(default=None, ge=1, le=12, description="Mes (1–12), opcional"),
    db: AsyncSession = Depends(get_db),
):
    """Top categories de despesa per a un any (i opcionalment mes)."""
    return await service.get_expense_breakdown(db, year=year, month=month)


@router.get("/cashflow", response_model=CashflowResponse)
async def get_cashflow(
    months: int = Query(default=12, ge=1, le=60, description="Nombre de mesos"),
    db: AsyncSession = Depends(get_db),
):
    """Flux de caixa mensual: ingressos vs despeses vs inversions."""
    return await service.get_cashflow(db, months=months)


@router.get("/evolution", response_model=NetWorthEvolutionResponse)
async def get_evolution(
    months: int = Query(default=24, ge=1, le=120, description="Nombre de mesos"),
    db: AsyncSession = Depends(get_db),
):
    """Evolució del net worth mensual."""
    return await service.get_networth_evolution(db, months=months)


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(db: AsyncSession = Depends(get_db)):
    """Alertes automàtiques generades des de les dades."""
    return await service.get_alerts(db)
