"""modules/portfolio/router.py — Endpoints REST per al portfolio."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.portfolio import service
from modules.portfolio.schemas import PortfolioSummaryResponse, RebalanceResponse

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Resum del portfolio: net worth, canvi diari, breakdown per classe d'actiu."""
    result = await service.get_portfolio_summary(db)
    if result is None:
        raise HTTPException(404, "No hi ha snapshots disponibles. Sincronitza MoneyWiz primer.")
    return result


@router.get("/rebalance", response_model=RebalanceResponse)
async def get_rebalance(db: AsyncSession = Depends(get_db)):
    """
    Suggerències de rebalanceig basades en el target_weight de cada asset.

    Retorna per a cada asset:
    - weight_actual_pct: pes real a la cartera d'inversió
    - target_weight_pct: pes objectiu configurat
    - weight_diff_pct: diferència (positiu = sobreponderat)
    - direction: overweight | underweight | missing | on_track
    - action_eur: import a comprar (negatiu) o vendre (positiu) per assolir el target
    """
    result = await service.get_rebalancing(db)
    if result is None:
        raise HTTPException(404, "No hi ha snapshots disponibles. Sincronitza MoneyWiz primer.")
    return result
