from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class TaxReport(Base):
    """Annual tax report snapshot — realized gains/losses and IRPF summary."""
    __tablename__ = "tax_reports"
    __table_args__ = (
        UniqueConstraint("tax_year", name="uq_tax_report_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    # Spanish IRPF brackets:
    # up to 6k: 19%, 6k-50k: 21%, 50k-200k: 23%, 200k+: 26%
    total_realized_gains: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_realized_losses: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    net_taxable_base: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    estimated_tax_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    total_dividends_received: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_dividend_tax_withheld: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    # full per-asset breakdown for export
    asset_detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # draft, final
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RealizedGain(Base):
    """Individual realized gain/loss event (from a sale transaction, FIFO)."""
    __tablename__ = "realized_gains"
    __table_args__ = (
        Index("idx_realized_gains_asset", "asset_id"),
        Index("idx_realized_gains_year", "sale_year"),
        Index("idx_realized_gains_sale_tx", "sale_tx_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    sale_tx_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=False)
    acquisition_tx_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=True)
    tax_lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tax_lots.id"), nullable=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    sale_year: Mapped[int] = mapped_column(Integer, nullable=False)
    shares_sold: Mapped[Decimal] = mapped_column(Numeric(16, 8), nullable=False)
    sale_price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    acquisition_price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    gross_proceeds_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost_basis_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    fees_eur: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    gain_loss_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_long_term: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
