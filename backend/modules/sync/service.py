"""
modules/sync/service.py — MoneyWiz backup parser i importador.

Flux principal:
  1. Rep els bytes d'un ZIP de backup de MoneyWiz.
  2. Extreu el fitxer SQLite (+ WAL/SHM) a un directori temporal.
  3. Parseja comptes, categories i transaccions des del SQLite de Core Data.
  4. Fa mirror complet a PostgreSQL: upsert de tot el ZIP + eliminació del que ja no hi és.
  5. Retorna un ImportBatch amb les estadístiques de la importació.

Estratègia de sincronització — MIRROR COMPLET:
  La BD és una còpia fidel de MoneyWiz. Cada import:
  - UPSERT comptes i categories (ON CONFLICT DO UPDATE).
  - UPSERT transaccions (ON CONFLICT DO UPDATE): reflecteix edicions de data, import,
    notes o categoria que l'usuari hagi fet a MoneyWiz.
  - PRUNE: elimina de la BD els registres que ja no existeixen al backup (l'usuari
    els ha esborrat a MoneyWiz). Ordre: tx → categories → comptes (respecta FKs).

  Resultat: pujar el mateix ZIP N vegades sempre produeix el mateix estat a la BD.

Estadístiques del ImportBatch:
  - records_found:    total de registres al ZIP.
  - records_imported: registres upserted (nous o actualitzats).
  - records_skipped:  registres eliminats de la BD (ja no existeixen a MW).

Format intern de MoneyWiz (Core Data):
  - Una sola taula ZSYNCOBJECT conté totes les entitats.
  - Z_ENT identifica el tipus d'entitat (vegeu _ACCOUNT_TYPE_MAP, _TX_TYPE_MAP).
  - Timestamps: segons des de 2001-01-01 00:00:00 UTC (Apple Core Data epoch).
  - Categories: jeràrquiques via ZPARENTCATEGORY (FK a ZSYNCOBJECT.Z_PK).
  - Assignació de categories: taula ZCATEGORYASSIGMENT (suporta splits N:1).
  - Les transaccions split prenen la categoria del primer registre (MIN Z_PK).
"""

import asyncio
import logging
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timedelta, date, timezone
from pathlib import Path

from sqlalchemy import delete as sa_delete, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.networth import service as networth_service
from modules.sync.models import ImportBatch, MWAccount, MWCategory, MWTransaction

logger = logging.getLogger(__name__)

# ─── Constants de format MoneyWiz ─────────────────────────────────────────────

# Apple Core Data timestamp epoch (2001-01-01 00:00:00 UTC)
_APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

# Z_ENT → account_type (de Z_PRIMARYKEY a la BD de MoneyWiz)
_ACCOUNT_TYPE_MAP: dict[int, str] = {
    10: "checking",   # BankChequeAccount
    11: "savings",    # BankSavingAccount
    12: "cash",       # CashAccount
    13: "credit",     # CreditCardAccount
    14: "loan",       # LoanAccount
    15: "investment", # InvestmentAccount
    16: "forex",      # ForexAccount
}

# Z_ENT → tx_type
_TX_TYPE_MAP: dict[int, str] = {
    47: "expense",        # WithdrawTransaction
    37: "income",         # DepositTransaction
    45: "transfer_in",    # TransferDepositTransaction
    46: "transfer_out",   # TransferWithdrawTransaction
    40: "investment_buy", # InvestmentBuyTransaction
    41: "investment_sell",# InvestmentSellTransaction
}

_CHUNK_SIZE = 500  # màxim de files per INSERT (evita statements massa grans)


# ─── Conversió de timestamps ──────────────────────────────────────────────────

def _apple_ts_to_date(ts: float | None) -> date | None:
    """Converteix timestamp de Core Data (segons des de 2001-01-01) a date Python."""
    if ts is None:
        return None
    try:
        return (_APPLE_EPOCH + timedelta(seconds=float(ts))).date()
    except (TypeError, ValueError, OverflowError):
        return None


# ─── Extracció del SQLite (síncron — s'executa via asyncio.to_thread) ─────────

def _open_sqlite(zip_bytes: bytes) -> tuple[sqlite3.Connection, tempfile.TemporaryDirectory]:
    """
    Extreu el ZIP a un directori temporal i obre la connexió SQLite.
    Retorna (conn, tmp_dir). El caller és responsable de tancar conn i cleanup tmp_dir.
    Extreu TOTS els fitxers sqlite-related (inclòs -wal i -shm) perquè SQLite
    apliqui automàticament el WAL en obrir la BD.
    """
    tmp = tempfile.TemporaryDirectory()
    tmp_path = Path(tmp.name)

    zip_path = tmp_path / "backup.zip"
    zip_path.write_bytes(zip_bytes)

    try:
        zf_handle = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        tmp.cleanup()
        raise ValueError(f"Format ZIP invàlid: {exc}") from exc

    with zf_handle as zf:
        sqlite_entries = [n for n in zf.namelist() if ".sqlite" in n]
        if not sqlite_entries:
            tmp.cleanup()
            raise ValueError("El ZIP no conté cap fitxer .sqlite")
        for name in sqlite_entries:
            zf.extract(name, tmp_path)

    main_sqlite = next(n for n in sqlite_entries if n.endswith(".sqlite"))
    conn = sqlite3.connect(str(tmp_path / main_sqlite))
    conn.row_factory = sqlite3.Row
    return conn, tmp


def _read_accounts(conn: sqlite3.Connection) -> list[dict]:
    """
    Extreu tots els comptes (Z_ENT 10-16) amb el balanç calculat des de transaccions.

    MoneyWiz no guarda el balanç actual en cap camp de ZSYNCOBJECT (ZBALLANCE és
    sempre 0 o NULL). El balanç real és:
        ZOPENINGBALANCE + SUM(ZAMOUNT1 de totes les transaccions del compte)
    Els ZAMOUNT1 ja estan signats (negatiu per a sortides, positiu per a entrades).
    """
    ent_ids = ",".join(str(e) for e in _ACCOUNT_TYPE_MAP)
    rows = conn.execute(f"""
        SELECT
            a.Z_PK,
            a.Z_ENT,
            a.ZNAME,
            a.ZCURRENCYNAME,
            a.ZARCHIVED,
            a.ZINCLUDEINNETWORTH,
            COALESCE(a.ZOPENINGBALANCE, 0) +
            COALESCE((
                SELECT SUM(t.ZAMOUNT1)
                FROM ZSYNCOBJECT t
                WHERE t.ZACCOUNT2 = a.Z_PK
                  AND t.ZAMOUNT1 IS NOT NULL
            ), 0) AS current_balance
        FROM ZSYNCOBJECT a
        WHERE a.Z_ENT IN ({ent_ids})
        ORDER BY a.Z_PK
    """).fetchall()
    return [
        {
            "mw_internal_id": str(r["Z_PK"]),
            "name": r["ZNAME"] or "Unknown",
            "account_type": _ACCOUNT_TYPE_MAP[r["Z_ENT"]],
            "currency": r["ZCURRENCYNAME"] or "EUR",
            "current_balance": float(r["current_balance"]),
            "is_active": not bool(r["ZARCHIVED"]),
            "include_in_networth": bool(r["ZINCLUDEINNETWORTH"]) if r["ZINCLUDEINNETWORTH"] is not None else True,
        }
        for r in rows
    ]


def _read_categories(conn: sqlite3.Connection) -> list[dict]:
    """
    Extreu categories (Z_ENT 19), ordenades amb pares primer.
    Retorna mw_parent_id com a string (mw_internal_id del pare) per resoldre
    el FK en el segon pas de l'upsert.
    """
    rows = conn.execute("""
        SELECT Z_PK, ZNAME2, ZTYPE2, ZPARENTCATEGORY
        FROM ZSYNCOBJECT
        WHERE Z_ENT = 19
        ORDER BY ZPARENTCATEGORY NULLS FIRST, Z_PK
    """).fetchall()
    return [
        {
            "mw_internal_id": str(r["Z_PK"]),
            "name": r["ZNAME2"] or "Unknown",
            "category_type": "income" if r["ZTYPE2"] == 2 else "expense",
            "mw_parent_id": str(r["ZPARENTCATEGORY"]) if r["ZPARENTCATEGORY"] else None,
        }
        for r in rows
    ]


def _read_transactions(conn: sqlite3.Connection) -> list[dict]:
    """
    Extreu totes les transaccions financeres (despeses, ingressos, transferències,
    inversions). Per a transaccions amb split de categories, pren la categoria
    principal (MIN Z_PK a ZCATEGORYASSIGMENT).
    """
    _INV_TYPES = {40, 41}  # investment_buy, investment_sell
    ent_ids = ",".join(str(e) for e in _TX_TYPE_MAP)
    rows = conn.execute(f"""
        SELECT
            s.Z_PK, s.Z_ENT,
            s.ZDATE1,
            s.ZAMOUNT1,
            s.ZCURRENCYNAME2,
            s.ZNOTES1,
            s.ZACCOUNT2,
            s.ZSTATUS1,
            s.ZNUMBEROFSHARES,
            s.ZSYMBOL1,
            agg.ZCATEGORY AS cat_mw_pk
        FROM ZSYNCOBJECT s
        LEFT JOIN (
            SELECT ZTRANSACTION, MIN(ZCATEGORY) AS ZCATEGORY
            FROM ZCATEGORYASSIGMENT
            GROUP BY ZTRANSACTION
        ) agg ON agg.ZTRANSACTION = s.Z_PK
        WHERE s.Z_ENT IN ({ent_ids})
        ORDER BY s.ZDATE1
    """).fetchall()

    txs = []
    for r in rows:
        tx_date = _apple_ts_to_date(r["ZDATE1"])
        if not tx_date:
            logger.warning("Transacció Z_PK=%s sense data vàlida — ignorada", r["Z_PK"])
            continue
        amount = abs(float(r["ZAMOUNT1"])) if r["ZAMOUNT1"] is not None else 0.0
        is_inv = r["Z_ENT"] in _INV_TYPES
        txs.append({
            "mw_internal_id": str(r["Z_PK"]),
            "tx_type": _TX_TYPE_MAP[r["Z_ENT"]],
            "tx_date": tx_date,
            "amount": amount,
            "currency": r["ZCURRENCYNAME2"] or "EUR",
            # Si moneda == EUR, amount_eur = amount. Gestió FX multi-divisa: tasca futura.
            "amount_eur": amount,
            "notes": r["ZNOTES1"],
            "is_reconciled": bool(r["ZSTATUS1"]) if r["ZSTATUS1"] is not None else False,
            "mw_account_id": str(r["ZACCOUNT2"]) if r["ZACCOUNT2"] else None,
            "mw_category_id": str(r["cat_mw_pk"]) if r["cat_mw_pk"] else None,
            # Camps d'inversió — None per a transaccions no-inversió
            "shares": abs(float(r["ZNUMBEROFSHARES"])) if (is_inv and r["ZNUMBEROFSHARES"]) else None,
            "mw_symbol": str(r["ZSYMBOL1"]).strip() if (is_inv and r["ZSYMBOL1"]) else None,
        })
    return txs


def _parse_zip_sync(zip_bytes: bytes) -> dict:
    """
    Extreu i parseja el ZIP de MoneyWiz de forma síncrona.
    Sempre cridar via asyncio.to_thread per no bloquejar el loop d'asyncio.
    """
    conn, tmp = _open_sqlite(zip_bytes)
    try:
        return {
            "accounts": _read_accounts(conn),
            "categories": _read_categories(conn),
            "transactions": _read_transactions(conn),
        }
    finally:
        conn.close()
        tmp.cleanup()


# ─── Upsert a PostgreSQL ──────────────────────────────────────────────────────

def _chunks(lst: list, size: int):
    """Divideix una llista en trossos de mida màxima `size`."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


async def _upsert_accounts(
    db: AsyncSession, accounts: list[dict]
) -> tuple[int, dict[str, int]]:
    """
    Upsert de comptes.
    ON CONFLICT (mw_internal_id) DO UPDATE: actualitza balanç i flags.
    Retorna (n_upserted, {mw_internal_id: db_id}).
    """
    if not accounts:
        return 0, {}

    now = datetime.now(timezone.utc)
    rows = [
        {
            "mw_internal_id": a["mw_internal_id"],
            "name": a["name"],
            "account_type": a["account_type"],
            "currency": a["currency"],
            "current_balance": a["current_balance"],
            "is_active": a["is_active"],
            "include_in_networth": a["include_in_networth"],
            "last_synced_at": now,
        }
        for a in accounts
    ]

    stmt = pg_insert(MWAccount).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["mw_internal_id"],
        set_={
            "name": stmt.excluded.name,
            "current_balance": stmt.excluded.current_balance,
            "is_active": stmt.excluded.is_active,
            "include_in_networth": stmt.excluded.include_in_networth,
            "last_synced_at": now,
        },
    ).returning(MWAccount.id, MWAccount.mw_internal_id)

    result = await db.execute(stmt)
    rows_returned = result.fetchall()
    id_map = {r.mw_internal_id: r.id for r in rows_returned}
    return len(rows_returned), id_map


async def _upsert_categories(
    db: AsyncSession, categories: list[dict]
) -> tuple[int, dict[str, int]]:
    """
    Upsert de categories en dos passos:
    - Pas 1: insert/update sense parent_id (evita problemes de FK ordering).
    - Pas 2: UPDATE parent_id usant un self-join per mw_internal_id.
    Retorna (n_upserted, {mw_internal_id: db_id}).
    """
    if not categories:
        return 0, {}

    rows = [
        {
            "mw_internal_id": c["mw_internal_id"],
            "name": c["name"],
            "category_type": c["category_type"],
            "parent_id": None,  # s'actualitza al pas 2
        }
        for c in categories
    ]

    stmt = pg_insert(MWCategory).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["mw_internal_id"],
        set_={
            "name": stmt.excluded.name,
            "category_type": stmt.excluded.category_type,
        },
    ).returning(MWCategory.id, MWCategory.mw_internal_id)

    result = await db.execute(stmt)
    rows_returned = result.fetchall()
    id_map = {r.mw_internal_id: r.id for r in rows_returned}

    # Pas 2: resolució de jerarquia
    children = [(c["mw_internal_id"], c["mw_parent_id"]) for c in categories if c["mw_parent_id"]]
    for child_mw_id, parent_mw_id in children:
        await db.execute(
            text("""
                UPDATE mw_categories AS c
                SET parent_id = p.id
                FROM mw_categories AS p
                WHERE c.mw_internal_id = :child_id
                  AND p.mw_internal_id = :parent_id
            """),
            {"child_id": child_mw_id, "parent_id": parent_mw_id},
        )

    return len(rows_returned), id_map


async def _upsert_transactions(
    db: AsyncSession,
    transactions: list[dict],
    batch_id: int,
    acc_map: dict[str, int],
    cat_map: dict[str, int],
) -> int:
    """
    Upsert de transaccions en blocs de _CHUNK_SIZE.
    ON CONFLICT DO UPDATE: reflecteix edicions fetes a MoneyWiz (data, import, notes,
    categoria). El import_batch_id es conserva del primer import (traçabilitat).
    Retorna el nombre de files processades.
    """
    if not transactions:
        return 0

    rows = [
        {
            "mw_internal_id": t["mw_internal_id"],
            "account_id": acc_map.get(t["mw_account_id"]) if t["mw_account_id"] else None,
            "category_id": cat_map.get(t["mw_category_id"]) if t["mw_category_id"] else None,
            "tx_type": t["tx_type"],
            "tx_date": t["tx_date"],
            "amount": t["amount"],
            "currency": t["currency"],
            "amount_eur": t["amount_eur"],
            "notes": t["notes"],
            "is_reconciled": t["is_reconciled"],
            "shares": t.get("shares"),
            "mw_symbol": t.get("mw_symbol"),
            "import_batch_id": batch_id,
        }
        for t in transactions
    ]

    processed = 0
    for chunk in _chunks(rows, _CHUNK_SIZE):
        stmt = pg_insert(MWTransaction).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_mw_transactions_mw_id",
            set_={
                "account_id": stmt.excluded.account_id,
                "category_id": stmt.excluded.category_id,
                "tx_date": stmt.excluded.tx_date,
                "amount": stmt.excluded.amount,
                "currency": stmt.excluded.currency,
                "amount_eur": stmt.excluded.amount_eur,
                "notes": stmt.excluded.notes,
                "is_reconciled": stmt.excluded.is_reconciled,
                "shares": stmt.excluded.shares,
                "mw_symbol": stmt.excluded.mw_symbol,
                # import_batch_id: mantenim el del primer import per traçabilitat
            },
        ).returning(MWTransaction.id)
        result = await db.execute(stmt)
        processed += len(result.fetchall())

    return processed


async def _prune_removed(
    db: AsyncSession,
    acc_ids: list[str],
    cat_ids: list[str],
    tx_ids: list[str],
) -> int:
    """
    Elimina de la BD els registres que ja no existeixen al backup de MoneyWiz.
    Garanteix que la BD és un mirror exacte del darrer ZIP importat.

    Ordre d'eliminació respecta les FK constraints:
      1. Transaccions (referencien comptes i categories)
      2. Categories (jerarquia self-referent; ON DELETE SET NULL per a parent_id)
      3. Comptes

    Guard: si qualsevol llista és buida, no s'elimina res d'aquella taula (evita
    esborrar tot si el ZIP és parcialment corrupte).

    Retorna el total de registres eliminats.
    """
    deleted = 0

    if tx_ids:
        r = await db.execute(
            sa_delete(MWTransaction).where(
                MWTransaction.mw_internal_id.notin_(tx_ids)
            )
        )
        deleted += r.rowcount
        if r.rowcount:
            logger.info("Prune: eliminades %d transaccions obsoletes", r.rowcount)

    if cat_ids:
        # Pas 1: elimina categories filles (parent_id IS NOT NULL) no presents al backup.
        # Pas 2: elimina categories pare restants. Necessari per la FK self-referent.
        r1 = await db.execute(
            sa_delete(MWCategory).where(
                MWCategory.mw_internal_id.notin_(cat_ids),
                MWCategory.parent_id.isnot(None),
            )
        )
        r2 = await db.execute(
            sa_delete(MWCategory).where(
                MWCategory.mw_internal_id.notin_(cat_ids),
            )
        )
        n_cat_deleted = r1.rowcount + r2.rowcount
        deleted += n_cat_deleted
        if n_cat_deleted:
            logger.info("Prune: eliminades %d categories obsoletes", n_cat_deleted)

    if acc_ids:
        r = await db.execute(
            sa_delete(MWAccount).where(
                MWAccount.mw_internal_id.notin_(acc_ids)
            )
        )
        deleted += r.rowcount
        if r.rowcount:
            logger.info("Prune: eliminats %d comptes obsolets", r.rowcount)

    return deleted


# ─── API pública ──────────────────────────────────────────────────────────────

async def process_upload(
    db: AsyncSession,
    zip_bytes: bytes,
    filename: str,
    trigger_source: str = "api",
) -> ImportBatch:
    """
    Processa un backup de MoneyWiz (ZIP) i fa un mirror complet a PostgreSQL.

    Garanties:
    - Mirror exacte: la BD reflecteix el contingut del ZIP (inclòs esborrats a MW).
    - Atòmic per dades: si l'import falla, es fa rollback de tots els canvis.
    - El registre ImportBatch sempre es crea (status='failed' si hi ha error).
    - El ZIP es processa en memòria i es neteja en finalitzar.

    Estadístiques retornades:
    - records_found:    total de registres al ZIP.
    - records_imported: registres upserted (nous o actualitzats).
    - records_skipped:  registres eliminats de la BD (ja no existeixen a MW).
    """
    now = datetime.now(timezone.utc)

    # Transacció 1: crear el registre de batch (commit immediat per audit trail)
    batch = ImportBatch(
        filename=filename,
        file_size_bytes=len(zip_bytes),
        status="processing",
        trigger_source=trigger_source,
        started_at=now,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)  # recarrega id i atributs expirats post-commit
    batch_id = batch.id     # int simple, immune a expiry/rollback

    try:
        # Parsing del SQLite (síncron, fora del loop d'asyncio)
        logger.info("Parsejant ZIP de MoneyWiz: %s (%d bytes)", filename, len(zip_bytes))
        data = await asyncio.to_thread(_parse_zip_sync, zip_bytes)

        n_accounts = len(data["accounts"])
        n_categories = len(data["categories"])
        n_transactions = len(data["transactions"])
        logger.info(
            "ZIP parsesat: %d comptes, %d categories, %d transaccions",
            n_accounts, n_categories, n_transactions,
        )

        # Transacció 2: upsert + prune (mirror complet)
        acc_n, acc_map = await _upsert_accounts(db, data["accounts"])
        cat_n, cat_map = await _upsert_categories(db, data["categories"])
        tx_n = await _upsert_transactions(
            db, data["transactions"], batch.id, acc_map, cat_map
        )

        # Prune: elimina registres que ja no existeixen al backup
        acc_ids = [a["mw_internal_id"] for a in data["accounts"]]
        cat_ids = [c["mw_internal_id"] for c in data["categories"]]
        tx_ids  = [t["mw_internal_id"] for t in data["transactions"]]
        deleted = await _prune_removed(db, acc_ids, cat_ids, tx_ids)

        # Rang de dates de les transaccions
        dates = [t["tx_date"] for t in data["transactions"]]
        date_from = min(dates) if dates else None
        date_to   = max(dates) if dates else None

        records_found    = n_accounts + n_categories + n_transactions
        records_imported = acc_n + cat_n + tx_n

        batch.status           = "completed"
        batch.records_found    = records_found
        batch.records_imported = records_imported
        batch.records_skipped  = deleted  # registres eliminats del mirror
        batch.mw_date_from     = date_from
        batch.mw_date_to       = date_to
        batch.completed_at     = datetime.now(timezone.utc)

        await db.commit()

        logger.info(
            "Sync completat [batch=%d]: %d comptes, %d categories, "
            "%d transaccions upserted, %d registres eliminats (prune)",
            batch_id, acc_n, cat_n, tx_n, deleted,
        )

        # Trigger automàtic: generar snapshot de net worth per avui
        try:
            snap = await networth_service.generate_snapshot(db, trigger_source="sync")
            # Genera snapshots mensuals retrospectius per al gràfic d'historial
            await networth_service.backfill_snapshots(db, months=24)
            logger.info(
                "Snapshot net worth generat post-sync: %.2f EUR",
                snap.total_net_worth,
            )
        except Exception as snap_exc:
            # No fallar el sync si el snapshot falla
            logger.error("Snapshot net worth fallat (non-fatal): %s", snap_exc)

    except Exception as exc:
        await db.rollback()

        # Actualitza el batch a 'failed' (el batch va ser committed a la transacció 1)
        await db.execute(
            text("""
                UPDATE import_batches
                SET status = 'failed',
                    error_log = :log,
                    completed_at = :now
                WHERE id = :id
            """),
            {"log": str(exc)[:5000], "now": datetime.now(timezone.utc), "id": batch_id},
        )
        await db.commit()

        logger.error("MoneyWiz sync fallat [batch=%d]: %s", batch_id, exc, exc_info=True)
        raise

    # Recarrega batch per retornar atributs frescos (segon commit els havia expirat)
    await db.refresh(batch)
    return batch


async def get_status(db: AsyncSession) -> dict:
    """
    Retorna l'estat de sincronització actual:
    última importació + comptadors de la BD.
    """
    # Darrer batch completat
    result = await db.execute(
        select(ImportBatch)
        .where(ImportBatch.status == "completed")
        .order_by(ImportBatch.completed_at.desc())
        .limit(1)
    )
    last_batch = result.scalar_one_or_none()

    # Comptadors
    acc_count = (await db.execute(
        text("SELECT COUNT(*) FROM mw_accounts WHERE is_active = true")
    )).scalar()
    cat_count = (await db.execute(
        text("SELECT COUNT(*) FROM mw_categories WHERE is_active = true")
    )).scalar()
    tx_count = (await db.execute(
        text("SELECT COUNT(*) FROM mw_transactions")
    )).scalar()
    date_range = (await db.execute(
        text("SELECT MIN(tx_date), MAX(tx_date) FROM mw_transactions")
    )).fetchone()

    return {
        "last_import": last_batch,
        "total_accounts": acc_count or 0,
        "total_categories": cat_count or 0,
        "total_transactions": tx_count or 0,
        "oldest_transaction": date_range[0] if date_range else None,
        "newest_transaction": date_range[1] if date_range else None,
    }


async def get_batches(db: AsyncSession, limit: int = 20) -> list[ImportBatch]:
    """Retorna el historial d'importacions, del més recent al més antic."""
    result = await db.execute(
        select(ImportBatch)
        .order_by(ImportBatch.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
