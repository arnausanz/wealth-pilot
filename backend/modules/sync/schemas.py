"""
modules/sync/schemas.py — Pydantic schemas per al mòdul sync.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ImportBatchOut(BaseModel):
    """Resultat d'una importació de backup de MoneyWiz."""
    id: int
    filename: str
    file_size_bytes: Optional[int]
    # pending, processing, completed, failed, partial
    status: str
    records_found: int
    records_imported: int
    records_skipped: int
    records_failed: int
    mw_date_from: Optional[date]
    mw_date_to: Optional[date]
    error_log: Optional[str]
    trigger_source: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncStatusOut(BaseModel):
    """Estat actual de la sincronització amb MoneyWiz."""
    last_import: Optional[ImportBatchOut]
    total_accounts: int
    total_categories: int
    total_transactions: int
    oldest_transaction: Optional[date]
    newest_transaction: Optional[date]

    model_config = {"from_attributes": True}
