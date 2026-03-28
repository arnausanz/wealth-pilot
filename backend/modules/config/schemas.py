"""modules/config/schemas.py — Schemas Pydantic per al mòdul de configuració."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator


# ─── Assets ──────────────────────────────────────────────────────────────────

class AssetConfigOut(BaseModel):
    id: int
    name: str
    display_name: str
    ticker_yf: Optional[str]
    ticker_mw: Optional[str]
    isin: Optional[str]
    asset_type: str
    currency: str
    color_hex: Optional[str]
    target_weight: Optional[Decimal]
    is_active: bool
    sort_order: int


class AssetConfigPatch(BaseModel):
    display_name: Optional[str] = None
    ticker_yf: Optional[str] = None
    ticker_mw: Optional[str] = None
    isin: Optional[str] = None
    color_hex: Optional[str] = None
    target_weight: Optional[Decimal] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class AssetConfigCreate(BaseModel):
    name: str
    display_name: str
    ticker_yf: Optional[str] = None
    ticker_mw: Optional[str] = None
    isin: Optional[str] = None
    asset_type: str = "etf"
    currency: str = "EUR"
    color_hex: Optional[str] = None
    target_weight: Optional[Decimal] = None
    sort_order: int = 99


# ─── Contributions ────────────────────────────────────────────────────────────

class ContributionOut(BaseModel):
    id: int
    asset_id: int
    asset_display_name: str
    asset_ticker_yf: Optional[str]
    asset_color_hex: Optional[str]
    amount: Decimal
    day_of_month: int
    is_active: bool
    notes: Optional[str]


class ContributionPatch(BaseModel):
    amount: Optional[Decimal] = None
    day_of_month: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ContributionCreate(BaseModel):
    asset_id: int
    amount: Decimal
    day_of_month: int = 2
    notes: Optional[str] = None


# ─── Scenarios ────────────────────────────────────────────────────────────────

class ScenarioRow(BaseModel):
    asset_id: int
    display_name: str
    ticker_yf: Optional[str]
    adverse: Optional[Decimal]
    base: Optional[Decimal]
    optimistic: Optional[Decimal]


class ScenarioPatch(BaseModel):
    annual_return: Decimal

    @field_validator('annual_return')
    @classmethod
    def validate_return(cls, v: Decimal) -> Decimal:
        if v < Decimal("-50") or v > Decimal("100"):
            raise ValueError("annual_return must be between -50 and 100")
        return v


# ─── Objectives ──────────────────────────────────────────────────────────────

class ObjectiveOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    objective_type: str
    target_amount: Decimal
    target_date: Optional[date]
    current_amount: Decimal
    is_active: bool


class ObjectivePatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[Decimal] = None
    target_date: Optional[date] = None
    current_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None


# ─── Parameters ──────────────────────────────────────────────────────────────

class ParameterOut(BaseModel):
    key: str
    value: str
    value_type: str
    description: Optional[str]
    category: Optional[str]
    is_editable: bool


class ParameterPatch(BaseModel):
    value: str


# ─── Generic responses ────────────────────────────────────────────────────────

class WeightValidationWarning(BaseModel):
    message: str
    total_weight: Decimal
