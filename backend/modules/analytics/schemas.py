"""modules/analytics/schemas.py — Schemas Pydantic per al mòdul d'analítica."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ExpenseCategory(BaseModel):
    category: str
    total_eur: Decimal
    pct_of_total: Decimal
    tx_count: int
    color_hex: Optional[str] = None


class ExpenseBreakdownResponse(BaseModel):
    year: int
    month: Optional[int]
    categories: list[ExpenseCategory]
    total_eur: Decimal


class CashflowMonth(BaseModel):
    month: str  # "YYYY-MM"
    income_eur: Decimal
    expenses_eur: Decimal
    investments_eur: Decimal
    savings_eur: Decimal
    savings_rate_pct: Optional[Decimal]


class CashflowResponse(BaseModel):
    months: list[CashflowMonth]
    avg_income: Decimal
    avg_expenses: Decimal
    avg_savings_rate_pct: Optional[Decimal]


class NetWorthMonth(BaseModel):
    month: str  # "YYYY-MM"
    total_net_worth: Decimal
    investment_value: Decimal
    cash_value: Decimal


class NetWorthEvolutionResponse(BaseModel):
    months: list[NetWorthMonth]


class AnalyticsAlert(BaseModel):
    id: str
    severity: str  # "info" | "warning" | "critical"
    title: str
    detail: str
    category: Optional[str] = None


class AlertsResponse(BaseModel):
    alerts: list[AnalyticsAlert]
