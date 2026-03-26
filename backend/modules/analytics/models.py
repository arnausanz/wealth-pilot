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


class Budget(Base):
    """Monthly budget definition per category."""
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("category_id", "year", "month", name="uq_budget_category_month"),
        Index("idx_budgets_period", "year", "month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=True)
    # null category_id = global monthly budget
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_planned: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_actual: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MonthlySummary(Base):
    """Pre-computed monthly income/expense/savings summary for analytics performance."""
    __tablename__ = "monthly_summaries"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_monthly_summary"),
        Index("idx_monthly_summaries_period", "year", "month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    total_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_investments: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    net_savings: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    savings_rate_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    # top category breakdown stored as JSON for performance
    category_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IncomeSource(Base):
    """Defined income source (salary, freelance, rental, dividends, etc.)."""
    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # salary, freelance, rental, dividends, pension, government, other
    income_type: Mapped[str] = mapped_column(String(30), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # expected monthly net amount
    expected_monthly_net: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    # monthly, biweekly, annual, irregular
    frequency: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    income_records: Mapped[List["IncomeRecord"]] = relationship("IncomeRecord", back_populates="income_source")


class IncomeRecord(Base):
    """Actual income received for a specific period from an income source."""
    __tablename__ = "income_records"
    __table_args__ = (
        Index("idx_income_records_date", "received_date"),
        Index("idx_income_records_source", "income_source_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    income_source_id: Mapped[int] = mapped_column(Integer, ForeignKey("income_sources.id"), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    # gross and net for tax tracking
    amount_gross: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    amount_net: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_withheld: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    social_security_withheld: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    # link to MoneyWiz transaction if available
    mw_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_transactions.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    income_source: Mapped["IncomeSource"] = relationship("IncomeSource", back_populates="income_records")


class SpendingPattern(Base):
    """Auto-detected spending pattern for anomaly detection (e.g. category baseline)."""
    __tablename__ = "spending_patterns"
    __table_args__ = (
        UniqueConstraint("category_id", "pattern_type", name="uq_spending_pattern"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=False)
    # monthly_average, rolling_3m, rolling_12m
    pattern_type: Mapped[str] = mapped_column(String(30), nullable=False)
    average_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    std_deviation: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    # months of data used to compute this pattern
    sample_months: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
