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


class AlertRule(Base):
    """Configurable rule that triggers alerts when conditions are met."""
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # portfolio_drift, spending_spike, goal_off_track, price_drop, price_rise,
    # rebalance_needed, contribution_missed, net_worth_milestone, custom
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # asset_id, category_id, objective_id, etc. (context-dependent)
    entity_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # condition config stored as JSON (threshold, operator, comparison_period, etc.)
    condition_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # low, medium, high, critical
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # suppress re-triggering for N days after first alert
    cooldown_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    history: Mapped[List["AlertHistory"]] = relationship("AlertHistory", back_populates="alert_rule")


class AlertHistory(Base):
    """Record of each time an alert was fired."""
    __tablename__ = "alert_history"
    __table_args__ = (
        Index("idx_alert_history_rule", "alert_rule_id"),
        Index("idx_alert_history_date", "triggered_at"),
        Index("idx_alert_history_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # message shown to the user
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # snapshot of the value that triggered the alert (e.g., drift %, current price)
    trigger_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # new, acknowledged, dismissed, resolved
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    alert_rule: Mapped["AlertRule"] = relationship("AlertRule", back_populates="history")
