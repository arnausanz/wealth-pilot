"""modules/simulation/schemas.py — Schemas Pydantic per al mòdul de simulació."""

from datetime import date
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


# ─── Open Simulator ───────────────────────────────────────────────────────────

class SimulationOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    base_scenario_type: str
    horizon_months: int
    is_pinned: bool
    created_at: str


class SimulationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_scenario_type: str = "base"
    horizon_months: int = 120


class SimulationEventCreate(BaseModel):
    event_date: date
    name: str
    event_type: str  # one_time_out | one_time_in | contribution_change | return_override
    amount: Decimal
    is_permanent: bool = False
    notes: Optional[str] = None


class SimulationEventOut(BaseModel):
    id: int
    simulation_id: int
    event_date: str
    name: str
    event_type: str
    amount: Decimal
    is_permanent: bool
    notes: Optional[str]


class SimulationDetailOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    base_scenario_type: str
    horizon_months: int
    is_pinned: bool
    events: list[SimulationEventOut]


class ProjectionSeries(BaseModel):
    sim_id: Optional[int]  # None for baseline
    name: str
    color: str
    annual_return_pct: Decimal
    data_points: list[Decimal]
    end_value: Decimal
    total_contributions_eur: Decimal
    total_return_eur: Decimal


class CompareResponse(BaseModel):
    horizon_years: int
    start_value: Decimal
    series: list[ProjectionSeries]
