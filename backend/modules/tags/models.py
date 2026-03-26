from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class Tag(Base):
    """User-defined tag for flexible cross-entity labeling."""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color_hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    # general, asset, transaction, mw_transaction, note, report
    tag_scope: Mapped[str] = mapped_column(String(30), default="general", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TransactionTag(Base):
    """Many-to-many: tags on investment transactions."""
    __tablename__ = "transaction_tags"
    __table_args__ = (
        UniqueConstraint("transaction_id", "tag_id", name="uq_transaction_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MWTransactionTag(Base):
    """Many-to-many: tags on MoneyWiz transactions."""
    __tablename__ = "mw_transaction_tags"
    __table_args__ = (
        UniqueConstraint("mw_transaction_id", "tag_id", name="uq_mw_transaction_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mw_transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("mw_transactions.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Note(Base):
    """Free-form notes attachable to any entity in the system."""
    __tablename__ = "notes"
    __table_args__ = (
        Index("idx_notes_entity", "entity_type", "entity_id"),
        Index("idx_notes_date", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # asset, transaction, mw_transaction, objective, simulation, property, pension_plan, general
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tags: Mapped[List["NoteTag"]] = relationship("NoteTag", back_populates="note")


class NoteTag(Base):
    """Many-to-many: tags on notes."""
    __tablename__ = "note_tags"
    __table_args__ = (
        UniqueConstraint("note_id", "tag_id", name="uq_note_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    note_id: Mapped[int] = mapped_column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    note: Mapped["Note"] = relationship("Note", back_populates="tags")
