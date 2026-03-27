"""
modules/sync/router.py — Endpoints de sincronització amb MoneyWiz.

Endpoints:
  POST /sync/upload   — Puja un backup ZIP de MoneyWiz i l'importa.
  GET  /sync/status   — Estat actual (darrera importació + comptadors de BD).
  GET  /sync/batches  — Historial d'importacions (les 20 més recents).
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from modules.sync import service
from modules.sync.schemas import ImportBatchOut, SyncStatusOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])

_MAX_UPLOAD_MB = 100
_MAX_UPLOAD_BYTES = _MAX_UPLOAD_MB * 1024 * 1024


@router.post(
    "/upload",
    response_model=ImportBatchOut,
    status_code=status.HTTP_200_OK,
    summary="Importa un backup de MoneyWiz",
    description=(
        "Accepta un fitxer ZIP exportat des de MoneyWiz. "
        "La importació és idempotent: pujar el mateix backup N vegades no genera duplicats. "
        "Retorna les estadístiques de la importació."
    ),
)
async def upload_backup(
    file: UploadFile = File(..., description="Fitxer .zip exportat des de MoneyWiz"),
    db: AsyncSession = Depends(get_db),
) -> ImportBatchOut:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El fitxer ha de ser un .zip exportat des de MoneyWiz",
        )

    zip_bytes = await file.read()

    if len(zip_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El fitxer supera el límit de {_MAX_UPLOAD_MB} MB",
        )

    if len(zip_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El fitxer està buit",
        )

    logger.info("Rebut backup MoneyWiz: %s (%d bytes)", file.filename, len(zip_bytes))

    try:
        batch = await service.process_upload(
            db=db,
            zip_bytes=zip_bytes,
            filename=file.filename,
            trigger_source="api",
        )
    except ValueError as exc:
        # Error de format (ZIP invàlid, sense SQLite, etc.)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return ImportBatchOut.model_validate(batch)


@router.get(
    "/status",
    response_model=SyncStatusOut,
    summary="Estat de la sincronització",
    description="Retorna la darrera importació completada i els comptadors actuals de la BD.",
)
async def get_status(db: AsyncSession = Depends(get_db)) -> SyncStatusOut:
    data = await service.get_status(db)
    return SyncStatusOut(
        last_import=ImportBatchOut.model_validate(data["last_import"]) if data["last_import"] else None,
        total_accounts=data["total_accounts"],
        total_categories=data["total_categories"],
        total_transactions=data["total_transactions"],
        oldest_transaction=data["oldest_transaction"],
        newest_transaction=data["newest_transaction"],
    )


@router.get(
    "/batches",
    response_model=list[ImportBatchOut],
    summary="Historial d'importacions",
    description="Retorna les darreres 20 importacions, de la més recent a la més antiga.",
)
async def list_batches(db: AsyncSession = Depends(get_db)) -> list[ImportBatchOut]:
    batches = await service.get_batches(db)
    return [ImportBatchOut.model_validate(b) for b in batches]
