from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class UserPreference(Base):
    """User interface and application preferences (single-user app — one row per key)."""
    __tablename__ = "user_preferences"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    # string, boolean, integer, json
    value_type: Mapped[str] = mapped_column(String(20), default="string", nullable=False)
    # ui, notifications, display, privacy, sync
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DashboardWidget(Base):
    """Configuration of dashboard widgets — position, size, visibility."""
    __tablename__ = "dashboard_widgets"
    __table_args__ = (
        UniqueConstraint("widget_type", name="uq_dashboard_widget_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # net_worth, portfolio_donut, on_track, rebalance, recent_transactions, goals, alerts, simulation_preview
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # widget-specific config (chart colors, period, etc.)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ReportTemplate(Base):
    """Saved report templates (custom views for analytics or tax exports)."""
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # tax_annual, portfolio_summary, expense_breakdown, custom
    template_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # full report configuration as JSON (filters, columns, date ranges, etc.)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
