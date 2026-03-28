"""modules/portfolio/schemas.py — Schemas Pydantic per al mòdul de portfolio."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RebalanceSuggestion(BaseModel):
    """Suggeriment de rebalanceig per a un asset."""
    asset_id: int
    display_name: str
    ticker_yf: Optional[str]
    color_hex: Optional[str]
    value_eur: Decimal
    weight_actual_pct: Decimal       # pes real sobre la cartera d'inversió
    target_weight_pct: Optional[Decimal]  # pes objectiu (de la taula assets)
    weight_diff_pct: Optional[Decimal]    # actual − target (positiu = sobreponderat)
    direction: str                   # "overweight" | "underweight" | "on_track" | "missing"
    action_eur: Optional[Decimal]    # import a vendre (>0) o comprar (<0)


class RebalanceResponse(BaseModel):
    """Resposta completa de rebalanceig."""
    snapshot_date: date
    total_investment_eur: Decimal
    total_target_pct: Optional[Decimal]  # suma dels target_weight (hauria de ser 100)
    suggestions: list[RebalanceSuggestion]


class PortfolioSummaryResponse(BaseModel):
    """Resum del portfolio — net worth + desglossat per classe d'actiu."""
    snapshot_date: date
    total_net_worth: Decimal
    investment_portfolio_value: Decimal
    cash_and_bank_value: Decimal
    change_eur: Optional[Decimal]
    change_pct: Optional[Decimal]
    on_track: Optional[bool]          # compara vs. projecció base (Fase 3)
    on_track_detail: Optional[str]    # text explicatiu
