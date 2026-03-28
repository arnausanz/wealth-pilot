"""
scripts/sanity_check.py — Informe de salut de WealthPilot.

Mostra:
  1. Darrera sincronització de MoneyWiz (data, registres, rang de dates).
  2. Estat de les transaccions MW (total, tipus, última data).
  3. Comptes MW actius.
  4. Preus de mercat (última data per asset, dies desfasats).

Ús:
  docker compose exec backend python scripts/sanity_check.py
"""

import asyncio
import sys
from datetime import date, datetime, timezone

from sqlalchemy import text

sys.path.insert(0, "/app")

# Desactivar tots els logs de nivell INFO i inferior (aquest script usa print())
import logging
logging.disable(logging.WARNING)  # bloqueja DEBUG, INFO i WARNING; manté ERROR+

from core.db import AsyncSessionLocal


def _sep(title: str = "", width: int = 56) -> str:
    if title:
        pad = (width - len(title) - 2) // 2
        return f"{'─' * pad} {title} {'─' * (width - pad - len(title) - 2)}"
    return "─" * width


def _days_label(days) -> str:
    if days is None:
        return "—"
    if days == 0:
        return "avui"
    if days == 1:
        return "ahir"
    return f"fa {days}d"


async def run():
    async with AsyncSessionLocal() as db:

        print()
        print("━" * 58)
        print("  WealthPilot — Sanity Check")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print("━" * 58)

        # ── MoneyWiz: darrers imports ─────────────────────────────────────
        print()
        print(_sep("MoneyWiz — Darrers imports"))
        rows = (await db.execute(text("""
            SELECT id, status, filename,
                   records_imported, records_skipped,
                   mw_date_from, mw_date_to,
                   completed_at,
                   (CURRENT_DATE - completed_at::date) AS dies_ago
            FROM import_batches
            ORDER BY created_at DESC
            LIMIT 3
        """))).fetchall()

        if not rows:
            print("  (cap import registrat)")
        else:
            for r in rows:
                status_icon = "✅" if r.status == "completed" else "❌"
                print(f"  {status_icon} #{r.id}  {r.status.upper():<12}"
                      f"  {_days_label(r.dies_ago):<8}"
                      f"  importats={r.records_imported}  eliminats={r.records_skipped}")
                print(f"     fitxer : {r.filename}")
                print(f"     periode: {r.mw_date_from} → {r.mw_date_to}")

        # ── MoneyWiz: resum transaccions ───────────────────────────────────
        print()
        print(_sep("MoneyWiz — Transaccions"))
        total_row = (await db.execute(text("""
            SELECT COUNT(*) AS total,
                   MIN(tx_date) AS first_date,
                   MAX(tx_date) AS last_date,
                   (CURRENT_DATE - MAX(tx_date)) AS dies_des_ultima
            FROM mw_transactions
        """))).fetchone()

        if total_row and total_row.total:
            print(f"  Total        : {total_row.total:,}")
            print(f"  Primera data : {total_row.first_date}")
            print(f"  Última data  : {total_row.last_date}  "
                  f"({_days_label(total_row.dies_des_ultima)})")
        else:
            print("  (cap transacció importada)")

        tx_types = (await db.execute(text("""
            SELECT tx_type, COUNT(*) AS n, MAX(tx_date) AS last_date
            FROM mw_transactions
            GROUP BY tx_type
            ORDER BY n DESC
        """))).fetchall()
        if tx_types:
            print()
            for r in tx_types:
                print(f"  {r.tx_type:<18} {r.n:>6,}  última: {r.last_date}")

        # ── MoneyWiz: comptes actius ───────────────────────────────────────
        print()
        print(_sep("MoneyWiz — Comptes actius"))
        accounts = (await db.execute(text("""
            SELECT name, account_type, currency,
                   ROUND(current_balance::numeric, 2) AS balance,
                   include_in_networth
            FROM mw_accounts
            WHERE is_active = TRUE
            ORDER BY name
        """))).fetchall()

        if not accounts:
            print("  (cap compte)")
        else:
            for a in accounts:
                networth_icon = "💰" if a.include_in_networth else "  "
                print(f"  {networth_icon} {a.name:<28} {a.account_type:<12}"
                      f"  {a.currency}  {a.balance:>12,.2f}")

        # ── Preus de mercat ────────────────────────────────────────────────
        print()
        print(_sep("Preus de mercat"))
        prices = (await db.execute(text("""
            SELECT a.display_name, a.ticker_yf, a.asset_type,
                   ph.price_close, ph.currency, ph.price_date,
                   (CURRENT_DATE - ph.price_date) AS dies_old
            FROM assets a
            LEFT JOIN LATERAL (
                SELECT price_close, currency, price_date
                FROM price_history
                WHERE asset_id = a.id
                ORDER BY price_date DESC
                LIMIT 1
            ) ph ON TRUE
            WHERE a.is_active = TRUE
            ORDER BY a.sort_order
        """))).fetchall()

        if not prices:
            print("  (cap preu importat)")
        else:
            for p in prices:
                if p.price_close is None:
                    status = "⚠️  sense preu"
                elif p.dies_old is None:
                    status = "⚠️  sense data"
                elif p.dies_old > 5:
                    status = f"🔴 {_days_label(p.dies_old)}"
                elif p.dies_old > 2:
                    status = f"🟡 {_days_label(p.dies_old)}"
                else:
                    status = f"🟢 {_days_label(p.dies_old)}"

                price_str = f"{p.price_close:>10.4f} {p.currency}" if p.price_close else "—"
                print(f"  {status:<14} {p.display_name:<28} {price_str}  ({p.ticker_yf})")

        print()
        print("━" * 58)
        print()


if __name__ == "__main__":
    asyncio.run(run())
