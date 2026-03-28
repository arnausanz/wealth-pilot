"""modules/simulation/schemas.py — Schemas Pydantic per al mòdul de simulació."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ScenarioInfo(BaseModel):
    """Informació d'un escenari de simulació."""
    scenario_type: str                    # adverse | base | optimistic
    blended_return_pct: Decimal           # retorn ponderat de la cartera actual
    label: str                            # "Advers" | "Base" | "Optimista"
    description: str                      # text explicatiu


class ScenariosInfoResponse(BaseModel):
    """Informació dels 3 escenaris + context de la cartera actual."""
    scenarios: list[ScenarioInfo]
    monthly_contributions: Decimal        # suma de contribucions actives
    current_investment_eur: Decimal       # valor cartera inversió actual


class ScenarioProjection(BaseModel):
    """Projecció completa d'un escenari."""
    scenario_type: str
    label: str
    annual_return_pct: Decimal
    end_value: Decimal
    total_return_eur: Decimal
    total_return_pct: Decimal
    total_contributions_eur: Decimal
    cagr_pct: Optional[Decimal]
    # Sèrie temporal: cada punt = valor al mes i (0 = ara)
    # Per horitzons llargs es retornen punts mensuals
    data_points: list[Decimal]


class ProjectionResponse(BaseModel):
    """Projecció dels 3 escenaris per al mateix horitzó."""
    horizon_years: int
    horizon_months: int
    start_value: Decimal
    monthly_contribution: Decimal
    # Objectiu d'habitatge per mostrar al gràfic
    home_purchase_target: Optional[Decimal]
    home_purchase_date: Optional[str]
    scenarios: dict[str, ScenarioProjection]   # keys: "adverse", "base", "optimistic"
