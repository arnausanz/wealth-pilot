from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class Scenario(Base):
    """Expected return assumption per asset per scenario type (editable from UI)."""
    __tablename__ = "scenarios"
    __table_args__ = (
        UniqueConstraint("asset_id", "scenario_type", name="uq_scenario"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    # adverse, base, optimistic (extensible: conservative, aggressive, etc.)
    scenario_type: Mapped[str] = mapped_column(String(20), nullable=False)
    annual_return: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    # standard deviation — used for Monte Carlo simulations in the future
    volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    asset = relationship("Asset")


class Objective(Base):
    """Financial goal (home purchase, retirement, emergency fund, etc.)."""
    __tablename__ = "objectives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # savings, purchase, income, retirement, education, travel, emergency
    objective_type: Mapped[str] = mapped_column(String(30), default="savings", nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # auto-calculated and updated by backend on each sync
    current_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    # cash, portfolio, both, property
    funding_source: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Parameter(Base):
    """Global system parameter — editable from UI, no code changes needed."""
    __tablename__ = "parameters"
    __table_args__ = (
        Index("idx_parameters_category", "category"),
    )

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    # decimal, integer, string, boolean, date, json
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # portfolio, personal, simulation, tax, ui
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ParameterHistory(Base):
    """Immutable audit trail of all parameter changes."""
    __tablename__ = "parameter_history"
    __table_args__ = (
        Index("idx_param_history_key", "param_key"),
        Index("idx_param_history_date", "changed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    param_key: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # api, seed, migration, import
    change_source: Mapped[str] = mapped_column(String(30), default="api", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
