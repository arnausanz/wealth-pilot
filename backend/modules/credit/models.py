from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class CreditAccount(Base):
    """Credit card or line of credit account."""
    __tablename__ = "credit_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # credit_card, line_of_credit, overdraft
    account_type: Mapped[str] = mapped_column(String(30), default="credit_card", nullable=False)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    available_credit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    interest_rate_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 3), nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    # billing cycle day
    billing_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payment_due_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # linked MoneyWiz account
    mw_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_accounts.id"), nullable=True)
    include_in_networth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    statements: Mapped[List["CreditStatement"]] = relationship("CreditStatement", back_populates="credit_account")
    payments: Mapped[List["CreditPayment"]] = relationship("CreditPayment", back_populates="credit_account")


class CreditStatement(Base):
    """Monthly credit card statement summary."""
    __tablename__ = "credit_statements"
    __table_args__ = (
        UniqueConstraint("credit_account_id", "statement_date", name="uq_credit_statement"),
        Index("idx_credit_statements_account", "credit_account_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credit_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_accounts.id"), nullable=False)
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    opening_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_payment: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    total_purchases: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    total_payments: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    # pending, paid, partial, overdue
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    credit_account: Mapped["CreditAccount"] = relationship("CreditAccount", back_populates="statements")


class CreditPayment(Base):
    """Payment made to a credit account."""
    __tablename__ = "credit_payments"
    __table_args__ = (
        Index("idx_credit_payments_account", "credit_account_id"),
        Index("idx_credit_payments_date", "payment_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credit_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("credit_accounts.id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # full, minimum, partial, auto_debit
    payment_type: Mapped[str] = mapped_column(String(20), default="full", nullable=False)
    statement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("credit_statements.id"), nullable=True)
    mw_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_transactions.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    credit_account: Mapped["CreditAccount"] = relationship("CreditAccount", back_populates="payments")
