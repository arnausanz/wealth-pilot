"""
scripts/update_data.py — Actualitza totes les dades de WealthPilot.

Passos:
  1. Gap fill de preus de mercat (Yahoo Finance → price_history).
  2. Sincronització de MoneyWiz: agafa el ZIP més recent de /data/moneywiz/
     i fa un mirror complet a la BD.

Ús:
  docker compose exec backend python scripts/update_data.py

El script és idempotent: es pot executar N vegades sense efectes secundaris.
Útil per a:
  - Actualització manual des del terminal (make update-data).
  - Futur: trigger automàtic quan l'iOS Shortcut deposita un nou ZIP.
"""

import asyncio
import glob
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/app")

# Desactivar logs INFO/WARNING (usem print(); volem veure ERROR si alguna cosa peta)
import logging
logging.disable(logging.WARNING)

from core.db import AsyncSessionLocal
from modules.market import service as market_service
from modules.sync import service as sync_service
from modules.market import service as market_service
from modules.sync import service as sync_service

MW_ZIP_DIR = "/data/moneywiz"


def _fmt_duration(start: datetime) -> str:
    ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    return f"{ms}ms" if ms < 1000 else f"{ms / 1000:.1f}s"


async def update_market_prices(db) -> None:
    print("▶ Actualitzant preus de mercat (Yahoo Finance)...")
    t0 = datetime.now(timezone.utc)
    try:
        result = await market_service.fill_all_gaps(db)
        print(f"  ✅ {result.rows_inserted} files inserides, "
              f"{len(result.assets_updated)} assets actualitzats  [{_fmt_duration(t0)}]")
    except Exception as exc:
        print(f"  ❌ Error actualitzant preus: {exc}")


async def sync_moneywiz(db) -> None:
    print("▶ Sincronitzant MoneyWiz...")

    zips = sorted(
        glob.glob(os.path.join(MW_ZIP_DIR, "*.zip")),
        key=os.path.getmtime,
        reverse=True,
    )

    if not zips:
        print(f"  ⚠️  No s'ha trobat cap ZIP a {MW_ZIP_DIR}/")
        print("     Posa el backup de MoneyWiz a data/moneywiz/ i torna a executar.")
        return

    latest = zips[0]
    size_mb = os.path.getsize(latest) / (1024 * 1024)
    print(f"  ZIP: {Path(latest).name}  ({size_mb:.1f} MB)")

    if len(zips) > 1:
        print(f"  ℹ️  {len(zips)} ZIPs trobats — s'utilitza el més recent (per data de modificació)")

    t0 = datetime.now(timezone.utc)
    try:
        with open(latest, "rb") as f:
            zip_bytes = f.read()

        batch = await sync_service.process_upload(
            db=db,
            zip_bytes=zip_bytes,
            filename=Path(latest).name,
            trigger_source="script",
        )

        print(f"  ✅ Batch #{batch.id}  status={batch.status}  [{_fmt_duration(t0)}]")
        print(f"     Importats : {batch.records_imported:,}")
        print(f"     Eliminats : {batch.records_skipped:,}  (registres esborrats a MoneyWiz)")
        print(f"     Periode   : {batch.mw_date_from} → {batch.mw_date_to}")

    except Exception as exc:
        print(f"  ❌ Error sincronitzant MoneyWiz: {exc}")


async def main() -> None:
    print()
    print("━" * 52)
    print("  WealthPilot — Actualització de dades")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("━" * 52)
    print()

    async with AsyncSessionLocal() as db:
        await update_market_prices(db)
        print()
        await sync_moneywiz(db)

    print()
    print("━" * 52)
    print()


if __name__ == "__main__":
    asyncio.run(main())
