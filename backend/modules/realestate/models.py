from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class Property(Base):
    """Real estate property owned or tracked (primary residence, investment, etc.)."""
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(5), default="ES", nullable=False)
    # primary_residence, investment, vacation, land, commercial
    property_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # owned, rented_out, mixed
    usage: Mapped[str] = mapped_column(String(20), default="primary_residence", nullable=False)
    surface_m2: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    purchase_costs: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    # current estimated market value
    current_estimated_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    last_valuation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    include_in_networth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cadaster_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    valuations: Mapped[List["PropertyValuation"]] = relationship("PropertyValuation", back_populates="property")
    mortgages: Mapped[List["Mortgage"]] = relationship("Mortgage", back_populates="property")
    rental_income_records: Mapped[List["RentalIncome"]] = relationship("RentalIncome", back_populates="property")
    expenses: Mapped[List["PropertyExpense"]] = relationship("PropertyExpense", back_populates="property")


class PropertyValuation(Base):
    """Historical valuation of a property (manual appraisal or automated estimate)."""
    __tablename__ = "property_valuations"
    __table_args__ = (
        Index("idx_property_valuations_property", "property_id"),
        Index("idx_property_valuations_date", "valuation_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # manual, idealista, zillow, appraisal, notarial
    source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="valuations")


class Mortgage(Base):
    """Mortgage or loan linked to a property."""
    __tablename__ = "mortgages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    interest_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False)
    # fixed, variable, mixed
    rate_type: Mapped[str] = mapped_column(String(20), default="variable", nullable=False)
    # for variable rates: euribor_12m, euribor_3m, etc.
    reference_rate: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    spread_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 3), nullable=True)
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    remaining_term_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="mortgages")
    payments: Mapped[List["MortgagePayment"]] = relationship("MortgagePayment", back_populates="mortgage")


class MortgagePayment(Base):
    """Individual mortgage payment record."""
    __tablename__ = "mortgage_payments"
    __table_args__ = (
        Index("idx_mortgage_payments_mortgage", "mortgage_id"),
        Index("idx_mortgage_payments_date", "payment_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mortgage_id: Mapped[int] = mapped_column(Integer, ForeignKey("mortgages.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_payment: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    interest_portion: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_after: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    mw_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_transactions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    mortgage: Mapped["Mortgage"] = relationship("Mortgage", back_populates="payments")


class RentalIncome(Base):
    """Rental income received from an investment property."""
    __tablename__ = "rental_income"
    __table_args__ = (
        Index("idx_rental_income_property", "property_id"),
        Index("idx_rental_income_date", "received_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_gross: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_net: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    tenant_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    period_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mw_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_transactions.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="rental_income_records")


class PropertyExpense(Base):
    """Expense related to a property (maintenance, IBI, insurance, community fees, etc.)."""
    __tablename__ = "property_expenses"
    __table_args__ = (
        Index("idx_property_expenses_property", "property_id"),
        Index("idx_property_expenses_date", "expense_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    # ibi, community_fees, insurance, maintenance, repair, legal, management, other
    expense_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deductible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mw_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_transactions.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property: Mapped["Property"] = relationship("Property", back_populates="expenses")
