"""modules/networth/schemas.py — Schemas Pydantic per al mòdul de net worth."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssetSnapshotOut(BaseModel):
    """Detall per-asset dins d'un snapshot de net worth."""
    model_config = ConfigDict(from_attributes=True)

    asset_id: int
    display_name: str
    ticker_yf: Optional[str]
    shares: Decimal
    price_eur: Decimal
    value_eur: Decimal
    cost_basis_eur: Decimal
    unrealized_pnl_eur: Decimal
    unrealized_pnl_pct: Optional[Decimal]
    weight_actual_pct: Optional[Decimal]


class NetWorthSnapshotOut(BaseModel):
    """Un snapshot diari del net worth total + breakdown per classe d'actiu."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    snapshot_date: date
    total_net_worth: Decimal
    investment_portfolio_value: Decimal
    cash_and_bank_value: Decimal
    real_estate_value: Decimal
    pension_value: Decimal
    other_assets_value: Decimal
    total_liabilities: Decimal
    change_eur: Optional[Decimal]
    change_pct: Optional[Decimal]
    trigger_source: str
    created_at: datetime
    asset_snapshots: list[AssetSnapshotOut] = []


class NetWorthHistoryResponse(BaseModel):
    """Resposta de l'endpoint d'historial de net worth."""
    period: str
    snapshots: list[NetWorthSnapshotOut]
    current_net_worth: Optional[Decimal]
    change_eur_period: Optional[Decimal]
    change_pct_period: Optional[Decimal]


class GenerateSnapshotResponse(BaseModel):
    """Resposta de la generació d'un snapshot."""
    snapshot_date: date
    total_net_worth: Decimal
    investment_portfolio_value: Decimal
    cash_and_bank_value: Decimal
    assets_tracked: int
    created: bool  # True=nou, False=actualitzat
