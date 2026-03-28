"""modules/history/router.py — Endpoints REST per a l'historial."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.history import service
from modules.history.schemas import InvestmentSummaryResponse, TransactionsResponse

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("/transactions", response_model=TransactionsResponse)
async def get_transactions(
    page: int = Query(default=1, ge=1, description="Pàgina (1-based)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Resultats per pàgina"),
    tx_type: Optional[str] = Query(default=None, description="expense | income | investment_buy | investment_sell | transfer_in | transfer_out"),
    ticker_yf: Optional[str] = Query(default=None, description="Filtrar per ticker (e.g. IWDA.AS)"),
    date_from: Optional[str] = Query(default=None, description="Data inici (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(default=None, description="Data fi (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna transaccions paginades de MoneyWiz.

    Filtres opcionals:
    - **tx_type**: filtra per tipus de transacció
    - **ticker_yf**: filtra per asset (mostra automàticament solo investment_buy/sell)
    - **date_from / date_to**: rang de dates (YYYY-MM-DD)
    """
    return await service.get_transactions(
        db,
        page=page,
        per_page=per_page,
        tx_type=tx_type,
        ticker_yf=ticker_yf,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/investments", response_model=InvestmentSummaryResponse)
async def get_investment_summary(db: AsyncSession = Depends(get_db)):
    """
    Resum de totes les inversions per asset.

    Per a cada asset: total invertit, shares actuals, cost mitjà, valor actual, P&L €/%.
    Útil per a la pantalla d'historial i per a informes fiscals futurs (FIFO/LIFO).
    """
    return await service.get_investment_summary(db)
