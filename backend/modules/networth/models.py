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


class NetWorthSnapshot(Base):
    """Daily net worth snapshot — the single source of truth for historical net worth."""
    __tablename__ = "net_worth_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_date", name="uq_networth_date"),
        Index("idx_networth_date", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    # total net worth = investment portfolio + cash + real estate + pensions - liabilities
    total_net_worth: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    # breakdown by asset class
    investment_portfolio_value: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    cash_and_bank_value: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    real_estate_value: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    pension_value: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    other_assets_value: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    # change vs previous snapshot
    change_eur: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 2), nullable=True)
    change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    # api, scheduled, manual
    trigger_source: Mapped[str] = mapped_column(String(20), default="api", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset_snapshots: Mapped[List["AssetSnapshot"]] = relationship("AssetSnapshot", back_populates="net_worth_snapshot")


class AssetSnapshot(Base):
    """Per-asset detail within a net worth snapshot."""
    __tablename__ = "asset_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "asset_id", name="uq_asset_snapshot"),
        Index("idx_asset_snapshot_date", "snapshot_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("net_worth_snapshots.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False)
    shares: Mapped[Decimal] = mapped_column(Numeric(16, 8), nullable=False)
    price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    value_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost_basis_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unrealized_pnl_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unrealized_pnl_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    # actual weight in the portfolio at this snapshot
    weight_actual_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    net_worth_snapshot: Mapped["NetWorthSnapshot"] = relationship("NetWorthSnapshot", back_populates="asset_snapshots")


class NetWorthMilestone(Base):
    """User-defined or auto-detected net worth milestones (100k, 200k, etc.)."""
    __tablename__ = "net_worth_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    reached_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_reached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # auto: triggered automatically when threshold crossed; manual: user-defined
    milestone_type: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
