from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class Simulation(Base):
    """A named simulation scenario saved by the user."""
    __tablename__ = "simulations"
    __table_args__ = (
        Index("idx_simulations_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # projection, what_if, comparison, monte_carlo
    simulation_type: Mapped[str] = mapped_column(String(30), default="projection", nullable=False)
    # base scenario used: adverse, base, optimistic (from scenarios table)
    base_scenario_type: Mapped[str] = mapped_column(String(20), default="base", nullable=False)
    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False)
    # initial portfolio value override (null = use current real value)
    initial_value_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    params: Mapped[List["SimulationParam"]] = relationship("SimulationParam", back_populates="simulation", cascade="all, delete-orphan")
    events: Mapped[List["SimulationEvent"]] = relationship("SimulationEvent", back_populates="simulation", cascade="all, delete-orphan")
    results: Mapped[List["SimulationResult"]] = relationship("SimulationResult", back_populates="simulation", cascade="all, delete-orphan")


class SimulationParam(Base):
    """Key-value overrides for a simulation (e.g., monthly_contribution=600)."""
    __tablename__ = "simulation_params"
    __table_args__ = (
        UniqueConstraint("simulation_id", "param_key", name="uq_sim_param"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    param_key: Mapped[str] = mapped_column(String(100), nullable=False)
    param_value: Mapped[str] = mapped_column(Text, nullable=False)
    # decimal, integer, string, boolean, json
    value_type: Mapped[str] = mapped_column(String(20), default="decimal", nullable=False)

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="params")


class SimulationEvent(Base):
    """A one-time life event modeled in a simulation (job change, house purchase, etc.)."""
    __tablename__ = "simulation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # lump_sum_in, lump_sum_out, monthly_change, expense_change
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # for monthly_change events, whether this persists after the event date
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # if asset-specific (null = affects total portfolio cash)
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="events")


class SimulationResult(Base):
    """Pre-computed monthly projection data point for a simulation."""
    __tablename__ = "simulation_results"
    __table_args__ = (
        UniqueConstraint("simulation_id", "projection_date", name="uq_sim_result"),
        Index("idx_sim_results_sim_date", "simulation_id", "projection_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    projection_date: Mapped[date] = mapped_column(Date, nullable=False)
    # projected portfolio value at this date
    portfolio_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # cumulative contributions up to this date
    total_contributed: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # cumulative returns (value - contributed)
    total_returns: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # per-asset breakdown (optional, stored as JSON for performance)
    asset_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="results")


class MonteCarloRun(Base):
    """A Monte Carlo simulation run (N random paths to build a distribution)."""
    __tablename__ = "monte_carlo_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    num_iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False)
    # summary statistics (full paths stored as JSONB for size)
    p10_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    p25_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    p50_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    p75_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    p90_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    probability_of_reaching_goal: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    # compressed path data for chart rendering
    paths_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
