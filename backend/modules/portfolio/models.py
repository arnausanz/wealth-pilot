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


class Asset(Base):
    """Investment asset — ETF, crypto, commodity, cash, stock, bond."""
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker_mw: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    ticker_yf: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    isin: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    # etf, crypto, commodity, cash, stock, bond
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # equity, fixed_income, alternative, cash
    asset_class: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    # dominant currency of underlying holdings (e.g., USD for MSCI World)
    currency_exposure: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domicile_country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color_hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    contributions: Mapped[List["Contribution"]] = relationship("Contribution", back_populates="asset")
    extraordinary_contributions: Mapped[List["ExtraordinaryContribution"]] = relationship("ExtraordinaryContribution", back_populates="asset")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="asset")
    tax_lots: Mapped[List["TaxLot"]] = relationship("TaxLot", back_populates="asset")
    price_history_entries: Mapped[List["PriceHistory"]] = relationship("PriceHistory", back_populates="asset")
    dividends: Mapped[List["Dividend"]] = relationship("Dividend", back_populates="asset")
    corporate_actions: Mapped[List["CorporateAction"]] = relationship("CorporateAction", back_populates="asset")


class Contribution(Base):
    """Recurring monthly contribution to an asset (editable from UI)."""
    __tablename__ = "contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    day_of_month: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="contributions")


class ExtraordinaryContribution(Base):
    """One-time planned contribution (editable from UI)."""
    __tablename__ = "extraordinary_contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    executed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="extraordinary_contributions")


class Transaction(Base):
    """Investment transaction imported from MoneyWiz. Treat as immutable."""
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("mw_date", "asset_id", "amount_eur", "shares", name="uq_transaction"),
        Index("idx_transactions_date", "mw_date"),
        Index("idx_transactions_asset_id", "asset_id"),
        Index("idx_transactions_type", "tx_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mw_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    # buy, sell, dividend, interest, fee, transfer, saveback
    tx_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    shares: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 8), nullable=True)
    price_per_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    fees_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    # original currency fields (if transaction wasn't in EUR)
    currency_original: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    amount_original: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mw_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # FK to import_batches (defined in sync module)
    import_batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("import_batches.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="transactions")
    tax_lots: Mapped[List["TaxLot"]] = relationship(
        "TaxLot", back_populates="acquisition_transaction",
        foreign_keys="TaxLot.acquisition_tx_id",
    )


class TaxLot(Base):
    """Individual purchase lot for FIFO cost-basis and Spanish tax calculations."""
    __tablename__ = "tax_lots"
    __table_args__ = (
        Index("idx_tax_lots_asset", "asset_id"),
        Index("idx_tax_lots_open", "asset_id", "is_closed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    acquisition_tx_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=True)
    acquired_date: Mapped[date] = mapped_column(Date, nullable=False)
    shares_acquired: Mapped[Decimal] = mapped_column(Numeric(16, 8), nullable=False)
    shares_remaining: Mapped[Decimal] = mapped_column(Numeric(16, 8), nullable=False)
    price_per_share_eur: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    cost_basis_eur: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="tax_lots")
    acquisition_transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction", back_populates="tax_lots", foreign_keys=[acquisition_tx_id],
    )


class PriceHistory(Base):
    """Daily closing price cached from Yahoo Finance."""
    __tablename__ = "price_history"
    __table_args__ = (
        UniqueConstraint("asset_id", "price_date", name="uq_price_history"),
        Index("idx_price_history_asset_date", "asset_id", "price_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    price_open: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    price_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    price_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 0), nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="EUR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="price_history_entries")


class Dividend(Base):
    """Dividend or interest received from an asset."""
    __tablename__ = "dividends"
    __table_args__ = (
        Index("idx_dividends_asset", "asset_id"),
        Index("idx_dividends_date", "payment_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    shares_held: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 8), nullable=True)
    amount_per_share: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)
    # dividend, interest, capital_return, return_of_capital
    dividend_type: Mapped[str] = mapped_column(String(20), default="dividend", nullable=False)
    tax_withheld_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    import_batch_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("import_batches.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="dividends")


class CorporateAction(Base):
    """Stock splits, reverse splits, mergers, spinoffs."""
    __tablename__ = "corporate_actions"
    __table_args__ = (
        Index("idx_corporate_actions_asset", "asset_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    # split, reverse_split, merger, spinoff, name_change
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    ratio_from: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    ratio_to: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="corporate_actions")
