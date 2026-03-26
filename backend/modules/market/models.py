from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class MarketIndex(Base):
    """Market benchmark index (S&P 500, MSCI World, Eurostoxx 50, etc.)."""
    __tablename__ = "market_indices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ticker_yf: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), default="USD", nullable=False)
    # equity, fixed_income, commodity, volatility, crypto
    index_type: Mapped[str] = mapped_column(String(20), default="equity", nullable=False)
    # region / geography
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # use this index as the default benchmark for portfolio comparison
    is_default_benchmark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    data_points: Mapped[List["MarketIndexData"]] = relationship("MarketIndexData", back_populates="market_index")


class MarketIndexData(Base):
    """Daily data point for a market index."""
    __tablename__ = "market_index_data"
    __table_args__ = (
        UniqueConstraint("index_id", "data_date", name="uq_market_index_data"),
        Index("idx_market_index_data_date", "index_id", "data_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index_id: Mapped[int] = mapped_column(Integer, ForeignKey("market_indices.id", ondelete="CASCADE"), nullable=False)
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    price_open: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    price_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    price_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 0), nullable=True)
    # daily return percentage
    daily_return_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    market_index: Mapped["MarketIndex"] = relationship("MarketIndex", back_populates="data_points")


class ExchangeRate(Base):
    """Daily foreign exchange rate (base: EUR)."""
    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", "rate_date", name="uq_exchange_rate"),
        Index("idx_exchange_rate_date", "rate_date"),
        Index("idx_exchange_rate_pair", "from_currency", "to_currency"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_currency: Mapped[str] = mapped_column(String(5), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(5), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    # ecb, yahoo, manual
    source: Mapped[str] = mapped_column(String(20), default="yahoo", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PriceFetchLog(Base):
    """Log of price fetch operations from Yahoo Finance (for debugging and rate limit tracking)."""
    __tablename__ = "price_fetch_logs"
    __table_args__ = (
        Index("idx_price_fetch_logs_date", "fetched_at"),
        Index("idx_price_fetch_logs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("assets.id"), nullable=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # success, failed, rate_limited, stale
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    price_returned: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
