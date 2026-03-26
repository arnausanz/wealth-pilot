from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class PensionPlan(Base):
    """Private pension plan or retirement savings vehicle."""
    __tablename__ = "pension_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # individual, employment, mutual (PPA, PIAS, EPSV, etc.)
    plan_type: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_contributions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # planned retirement age or date
    target_retirement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # conservative, moderate, aggressive, guaranteed
    risk_profile: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    annual_return_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 3), nullable=True)
    include_in_networth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_statement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    contributions: Mapped[List["PensionContribution"]] = relationship("PensionContribution", back_populates="pension_plan")
    valuations: Mapped[List["PensionValuation"]] = relationship("PensionValuation", back_populates="pension_plan")


class PensionContribution(Base):
    """Individual contribution to a pension plan."""
    __tablename__ = "pension_contributions"
    __table_args__ = (
        Index("idx_pension_contributions_plan", "pension_plan_id"),
        Index("idx_pension_contributions_date", "contribution_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pension_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("pension_plans.id"), nullable=False)
    contribution_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # employee, employer, voluntary
    contribution_type: Mapped[str] = mapped_column(String(20), default="voluntary", nullable=False)
    # is this deductible from IRPF (true for most individual plans in Spain)
    is_tax_deductible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mw_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_transactions.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pension_plan: Mapped["PensionPlan"] = relationship("PensionPlan", back_populates="contributions")


class PensionValuation(Base):
    """Historical valuation snapshots for a pension plan."""
    __tablename__ = "pension_valuations"
    __table_args__ = (
        UniqueConstraint("pension_plan_id", "valuation_date", name="uq_pension_valuation"),
        Index("idx_pension_valuations_plan_date", "pension_plan_id", "valuation_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pension_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("pension_plans.id", ondelete="CASCADE"), nullable=False)
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    units: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 8), nullable=True)
    unit_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    # manual, statement, api
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pension_plan: Mapped["PensionPlan"] = relationship("PensionPlan", back_populates="valuations")


class SocialSecurityEstimate(Base):
    """Estimated public pension from Social Security (Seguridad Social)."""
    __tablename__ = "social_security_estimates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estimate_date: Mapped[date] = mapped_column(Date, nullable=False)
    # estimated monthly pension at different retirement ages
    monthly_at_65: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_at_67: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_at_70: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    # total contribution years to date
    contribution_years: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    # contribution base average last 25 years
    regulatory_base: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    # source: tu seguridad social, manual
    source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
