from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssetPriceOut(BaseModel):
    """Preu actual d'un asset, servit sempre des de la BD (mai directament de Yahoo)."""
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    display_name: str
    ticker_yf: Optional[str]
    asset_type: str
    price_close: Optional[Decimal]
    price_date: Optional[date]
    currency: str
    # True si el preu és massa antic (mercat tancat, Yahoo caigut, etc.)
    is_stale: bool
    stale_days: int
    # Canvi respecte el dia anterior (None si no hi ha prou historial)
    change_pct_1d: Optional[Decimal]
    change_eur_1d: Optional[Decimal]


class MarketPricesResponse(BaseModel):
    prices: list[AssetPriceOut]
    total_assets: int
    fresh_count: int
    stale_count: int
    no_data_count: int
    # True si la resposta ve de la caché en memòria (no de BD)
    cached: bool
    cache_age_seconds: Optional[int]


class GapFillResponse(BaseModel):
    """Resultat d'un gap fill (fill_all_gaps)."""
    rows_inserted: int
    assets_updated: list[str]
    assets_failed: list[str]
    assets_skipped: list[str]
    duration_ms: int
    errors: list[str]
    triggered_at: datetime


class PriceHistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price_date: date
    price_close: Decimal
    price_open: Optional[Decimal]
    price_high: Optional[Decimal]
    price_low: Optional[Decimal]
    volume: Optional[Decimal]
    change_pct: Optional[Decimal]  # canvi vs dia anterior


class AssetPriceHistoryResponse(BaseModel):
    asset_id: int
    display_name: str
    ticker_yf: Optional[str]
    currency: str
    data: list[PriceHistoryPoint]
    from_date: Optional[date]
    to_date: Optional[date]
    total_rows: int
