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


class ImportBatch(Base):
    """Tracks each MoneyWiz backup upload for traceability and deduplication."""
    __tablename__ = "import_batches"
    __table_args__ = (
        Index("idx_import_batches_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # pending, processing, completed, failed, partial
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # counts
    records_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # MoneyWiz backup date range
    mw_date_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mw_date_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # api, script, scheduled
    trigger_source: Mapped[str] = mapped_column(String(30), default="api", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MWAccount(Base):
    """MoneyWiz account — bank accounts, investment accounts, credit cards, etc."""
    __tablename__ = "mw_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mw_internal_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # checking, savings, investment, credit, loan, cash
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    institution: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    current_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_in_networth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    mw_transactions: Mapped[List["MWTransaction"]] = relationship("MWTransaction", back_populates="account")


class MWCategory(Base):
    """MoneyWiz expense/income category (hierarchical)."""
    __tablename__ = "mw_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mw_internal_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=True)
    # expense, income, transfer, investment
    category_type: Mapped[str] = mapped_column(String(20), default="expense", nullable=False)
    color_hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent: Mapped[Optional["MWCategory"]] = relationship("MWCategory", remote_side="MWCategory.id")
    children: Mapped[List["MWCategory"]] = relationship("MWCategory", back_populates="parent")
    mw_transactions: Mapped[List["MWTransaction"]] = relationship("MWTransaction", back_populates="category")


class MWPayee(Base):
    """MoneyWiz payee — merchant or counterpart of a transaction."""
    __tablename__ = "mw_payees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mw_internal_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    # normalized name for grouping (e.g., "MERCADONA" for various Mercadona branches)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    default_category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    mw_transactions: Mapped[List["MWTransaction"]] = relationship("MWTransaction", back_populates="payee")


class MWTransaction(Base):
    """Raw financial transaction from MoneyWiz (non-investment: expenses, income, transfers)."""
    __tablename__ = "mw_transactions"
    __table_args__ = (
        UniqueConstraint("mw_internal_id", name="uq_mw_transactions_mw_id"),
        Index("idx_mw_tx_date", "tx_date"),
        Index("idx_mw_tx_account", "account_id"),
        Index("idx_mw_tx_category", "category_id"),
        Index("idx_mw_tx_type", "tx_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mw_internal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_accounts.id"), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=True)
    payee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_payees.id"), nullable=True)
    # expense, income, transfer, refund, investment_buy, investment_sell
    tx_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tx_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_excluded_from_reports: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Investment fields — NULL per a transaccions no-inversió
    shares: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 8), nullable=True)
    mw_symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # FK to the batch that imported this transaction
    import_batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("import_batches.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    account: Mapped[Optional["MWAccount"]] = relationship("MWAccount", back_populates="mw_transactions")
    category: Mapped[Optional["MWCategory"]] = relationship("MWCategory", back_populates="mw_transactions")
    payee: Mapped[Optional["MWPayee"]] = relationship("MWPayee", back_populates="mw_transactions")


class RecurringExpense(Base):
    """Detected or manually added recurring expense pattern (subscription, rent, etc.)."""
    __tablename__ = "recurring_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_categories.id"), nullable=True)
    payee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mw_payees.id"), nullable=True)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # monthly, quarterly, annual, weekly, biweekly
    frequency: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    expected_day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # auto-detected, manual
    detection_source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    last_seen_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
