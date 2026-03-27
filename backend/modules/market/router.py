"""
Market data endpoints — current prices, historical data, gap fill.

All price data is served from the BD (PostgreSQL), never directly from Yahoo Finance.
Yahoo Finance is only called explicitly via POST /market/refresh (gap fill).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.market import service
from modules.market.schemas import (
    AssetPriceHistoryResponse,
    AssetPriceOut,
    GapFillResponse,
    MarketPricesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/prices",
    response_model=MarketPricesResponse,
    summary="Current prices for all active assets",
    description=(
        "Returns the most recent price for every active asset, served from the BD. "
        "Includes stale detection and 1-day change. Response is cached in memory for 5 minutes."
    ),
)
async def get_prices(db: DbDep) -> MarketPricesResponse:
    return await service.get_current_prices(db)


@router.get(
    "/prices/{asset_id}",
    response_model=AssetPriceOut,
    summary="Current price for a single asset",
)
async def get_price(asset_id: int, db: DbDep) -> AssetPriceOut:
    response = await service.get_current_prices(db)
    match = next((p for p in response.prices if p.asset_id == asset_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found or not active")
    return match


@router.post(
    "/refresh",
    response_model=GapFillResponse,
    summary="Trigger a gap fill from Yahoo Finance",
    description=(
        "Downloads all missing price history from Yahoo Finance for every active asset. "
        "Idempotent — safe to call multiple times. Returns a summary of what was inserted."
    ),
)
async def refresh_prices(db: DbDep) -> GapFillResponse:
    logger.info("Manual gap fill triggered via API")
    return await service.fill_all_gaps(db)


@router.get(
    "/history/{asset_id}",
    response_model=AssetPriceHistoryResponse,
    summary="Price history for a single asset",
    description="Returns OHLCV data from the BD for the requested number of calendar days.",
)
async def get_history(
    asset_id: int,
    db: DbDep,
    days: Annotated[int, Query(ge=1, le=3650, description="Calendar days to look back")] = 30,
) -> AssetPriceHistoryResponse:
    result = await service.get_asset_price_history(db, asset_id, days)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found or not active")
    return result
