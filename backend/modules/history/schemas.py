"""modules/history/schemas.py — Schemas Pydantic per al mòdul d'historial."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TransactionOut(BaseModel):
    """Una transacció de MoneyWiz (qualsevol tipus)."""
    id: int
    tx_date: date
    tx_type: str                       # expense, income, investment_buy, investment_sell, transfer_in, transfer_out
    amount_eur: Decimal
    description: Optional[str]
    # Camps específics d'inversió (nuls per a altres tipus)
    mw_symbol: Optional[str]
    display_name: Optional[str]        # nom de l'asset (si s'ha identificat)
    ticker_yf: Optional[str]
    color_hex: Optional[str]
    shares: Optional[Decimal]
    account_name: Optional[str]


class TransactionsResponse(BaseModel):
    """Resposta paginada de transaccions."""
    transactions: list[TransactionOut]
    total: int
    page: int
    per_page: int
    pages: int


class AssetInvestmentSummary(BaseModel):
    """Resum d'inversió per a un asset concret."""
    asset_id: int
    display_name: str
    ticker_yf: Optional[str]
    color_hex: Optional[str]
    shares: Decimal                    # posició actual (buys - sells)
    total_invested_eur: Decimal        # suma d'imports de compres
    avg_cost_eur: Optional[Decimal]    # cost mitjà per acció
    current_price_eur: Optional[Decimal]
    current_value_eur: Optional[Decimal]
    pnl_eur: Optional[Decimal]
    pnl_pct: Optional[Decimal]
    buy_count: int
    sell_count: int
    first_buy_date: Optional[date]
    last_buy_date: Optional[date]


class InvestmentSummaryResponse(BaseModel):
    """Resum agregat de totes les inversions."""
    assets: list[AssetInvestmentSummary]
    total_invested_eur: Decimal
    total_current_value_eur: Optional[Decimal]
    total_pnl_eur: Optional[Decimal]
    total_pnl_pct: Optional[Decimal]
