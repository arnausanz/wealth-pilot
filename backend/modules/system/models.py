from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class AuditLog(Base):
    """Immutable audit trail of all write operations through the API."""
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_log_entity", "entity_type", "entity_id"),
        Index("idx_audit_log_date", "created_at"),
        Index("idx_audit_log_action", "action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # table/resource name (e.g., "assets", "contributions", "parameters")
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # create, update, delete, import, sync
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    # JSON snapshot of the record before the change (null for create)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # JSON snapshot of the record after the change (null for delete)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # api, seed, migration, import, system
    source: Mapped[str] = mapped_column(String(30), default="api", nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class APIKey(Base):
    """API keys for machine-to-machine authentication (iOS Shortcut, external integrations)."""
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # stored as a hash (SHA-256), never the raw key
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # key prefix shown in the UI for identification (first 8 chars)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    # ios_shortcut, script, dashboard, api
    client_type: Mapped[str] = mapped_column(String(30), default="api", nullable=False)
    # JSON array of allowed endpoints/scopes
    scopes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AppVersion(Base):
    """Record of deployed app versions — useful for tracking when schema/features were added."""
    __tablename__ = "app_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    # description of what changed in this version
    release_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # development, staging, production
    environment: Mapped[str] = mapped_column(String(20), default="development", nullable=False)


class ScheduledTask(Base):
    """Tracking of background scheduled tasks (daily price fetch, snapshot generation, etc.)."""
    __tablename__ = "scheduled_tasks"
    __table_args__ = (
        Index("idx_scheduled_tasks_status", "status"),
        Index("idx_scheduled_tasks_type", "task_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # pending, running, completed, failed, skipped
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # triggered_by: cron, api, startup
    triggered_by: Mapped[str] = mapped_column(String(30), default="cron", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
