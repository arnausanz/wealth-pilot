"""
scripts/net_worth.py — Resum del net worth actual.

Mostra:
  1. Net worth total i desglossat per compte MW.
  2. Posicions d'inversió: asset, accions, preu, valor, P&L.
  3. Últim snapshot registrat (si existeix).

Ús:
  docker compose exec backend python scripts/net_worth.py
"""

import asyncio
import sys
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text

sys.path.insert(0, "/app")

import logging
logging.disable(logging.WARNING)

from core.db import AsyncSessionLocal


def _sep(title: str = "", width: int = 70) -> str:
    if title:
        pad = (width - len(title) - 2) // 2
        return f"{'─' * pad} {title} {'─' * (width - pad - len(title) - 2)}"
    return "─" * width


def _fmt_eur(amount, width: int = 14) -> str:
    if amount is None:
        return "—".rjust(width)
    return f"{float(amount):>{width},.2f} €"


def _pnl_icon(pnl) -> str:
    if pnl is None:
        return " "
    return "🟢" if float(pnl) >= 0 else "🔴"


async def run():
    async with AsyncSessionLocal() as db:

        print()
        print("━" * 72)
        print("  WealthPilot — Net Worth")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print("━" * 72)

        # ── 1. Comptes MW per tipus ────────────────────────────────────────────
        print()
        print(_sep("Comptes MoneyWiz"))
        accounts = (await db.execute(text("""
            SELECT name, account_type, currency,
                   ROUND(current_balance::numeric, 2) AS balance,
                   include_in_networth
            FROM mw_accounts
            WHERE is_active = TRUE
            ORDER BY
                CASE account_type
                    WHEN 'checking'   THEN 1
                    WHEN 'savings'    THEN 2
                    WHEN 'cash'       THEN 3
                    WHEN 'forex'      THEN 4
                    WHEN 'investment' THEN 5
                    WHEN 'credit'     THEN 6
                    WHEN 'loan'       THEN 7
                    ELSE 8
                END,
                name
        """))).fetchall()

        cash_total = Decimal("0")
        inv_total  = Decimal("0")
        liab_total = Decimal("0")

        _CASH_TYPES = ("checking", "savings", "cash", "forex")
        _INV_TYPES  = ("investment",)
        _LIAB_TYPES = ("credit", "loan")

        if not accounts:
            print("  (cap compte)")
        else:
            for a in accounts:
                bal = Decimal(str(a.balance)) if a.balance is not None else Decimal("0")
                if a.include_in_networth:
                    if a.account_type in _CASH_TYPES:
                        cash_total += bal
                    elif a.account_type in _INV_TYPES:
                        inv_total += bal
                    elif a.account_type in _LIAB_TYPES:
                        liab_total += bal
                    icon = "➕" if a.account_type not in _LIAB_TYPES else "➖"
                    excl = ""
                else:
                    icon = "  "
                    excl = "  (exclòs del net worth)"
                print(f"  {icon} {a.name:<30} {a.account_type:<12}  {a.currency}  {_fmt_eur(a.balance)}{excl}")

        total_net_worth = cash_total + inv_total - liab_total

        lbl_inv  = "Cartera d'inversió"
        lbl_liab = "Passius (crèdit/préstec)"
        print()
        print(f"  {'Efectiu i comptes':<44}  {_fmt_eur(cash_total)}")
        print(f"  {lbl_inv:<44}  {_fmt_eur(inv_total)}")
        if liab_total > 0:
            print(f"  {lbl_liab:<44}  {_fmt_eur(-liab_total)}")

        # ── 2. Posicions d'inversió ────────────────────────────────────────────
        print()
        print(_sep("Posicions d'inversió"))

        positions = (await db.execute(text("""
            SELECT
                a.display_name,
                a.ticker_yf,
                SUM(
                    CASE mt.tx_type
                        WHEN 'investment_buy'  THEN  mt.shares
                        WHEN 'investment_sell' THEN -mt.shares
                        ELSE 0
                    END
                )                          AS total_shares,
                SUM(
                    CASE mt.tx_type
                        WHEN 'investment_buy' THEN mt.amount_eur
                        ELSE 0
                    END
                )                          AS cost_basis,
                ph.price_close             AS last_price,
                ph.price_date              AS price_date,
                ph.currency                AS price_currency
            FROM mw_transactions mt
            JOIN assets a ON a.ticker_mw = mt.mw_symbol
            LEFT JOIN LATERAL (
                SELECT price_close, currency, price_date
                FROM price_history
                WHERE asset_id = a.id
                ORDER BY price_date DESC
                LIMIT 1
            ) ph ON TRUE
            WHERE mt.tx_type IN ('investment_buy', 'investment_sell')
              AND mt.shares IS NOT NULL
              AND a.is_active = TRUE
            GROUP BY a.id, a.display_name, a.ticker_yf, ph.price_close, ph.price_date, ph.currency
            HAVING SUM(
                CASE mt.tx_type
                    WHEN 'investment_buy'  THEN  mt.shares
                    WHEN 'investment_sell' THEN -mt.shares
                    ELSE 0
                END
            ) > 0
            ORDER BY a.display_name
        """))).fetchall()

        total_tracked = Decimal("0")
        total_cost    = Decimal("0")

        if not positions:
            print("  (cap posició amb ticker mapejat)")
        else:
            header = (
                f"  {'Asset':<28} {'Accions':>10}  {'Preu':>10}  "
                f"{'Valor €':>12}  {'P&L €':>10}  {'P&L%':>7}"
            )
            print(header)
            print("  " + "─" * 68)
            for p in positions:
                if p.last_price is None:
                    print(f"  ⚠️  {p.display_name:<26} (sense preu — {p.ticker_yf})")
                    continue

                shares     = Decimal(str(p.total_shares))
                price      = Decimal(str(p.last_price))
                cost       = Decimal(str(p.cost_basis)).quantize(Decimal("0.01"))
                value      = (shares * price).quantize(Decimal("0.01"))
                pnl_eur    = (value - cost).quantize(Decimal("0.01"))
                pnl_pct    = (pnl_eur / cost * 100).quantize(Decimal("0.01")) if cost else None

                total_tracked += value
                total_cost    += cost

                icon = _pnl_icon(pnl_eur)
                pnl_str = f"{float(pnl_eur):>+10,.2f}"
                pct_str = f"{float(pnl_pct):>+6.2f}%" if pnl_pct is not None else "      —"
                print(
                    f"  {icon} {p.display_name:<26} {float(shares):>10.4f}  "
                    f"{float(price):>10.4f}  {float(value):>12,.2f}  {pnl_str}  {pct_str}"
                )
                print(f"     {'':28} {'ticker: ' + (p.ticker_yf or '—'):<18} "
                      f"cost: {float(cost):>10,.2f} €   preu: {p.price_date}")

            print("  " + "─" * 68)
            total_pnl = (total_tracked - total_cost).quantize(Decimal("0.01"))
            total_pct = (total_pnl / total_cost * 100).quantize(Decimal("0.01")) if total_cost else None
            pct_str = f"{float(total_pct):>+6.2f}%" if total_pct is not None else "      —"
            print(
                f"  {'TOTAL CARTERA (rastreada)':<28} {'':>10}  {'':>10}  "
                f"{float(total_tracked):>12,.2f}  {float(total_pnl):>+10,.2f}  {pct_str}"
            )

        # ── 3. Resum final ─────────────────────────────────────────────────────
        print()
        print(_sep("Resum"))
        print(f"  {'NET WORTH TOTAL (comptes MW)':<44}  {_fmt_eur(total_net_worth)}")
        if total_tracked > 0:
            print(f"  {'Cartera rastreada (shares × preu YF)':<44}  {_fmt_eur(total_tracked)}")
            untracked = inv_total - total_tracked
            if abs(untracked) > Decimal("1"):
                print(f"  {'  Diferència no rastreada (NUKL, etc.)':<44}  {_fmt_eur(untracked)}")

        # ── 4. Últim snapshot guardat ──────────────────────────────────────────
        print()
        print(_sep("Últim snapshot guardat"))
        last = (await db.execute(text("""
            SELECT snapshot_date, total_net_worth, investment_portfolio_value,
                   cash_and_bank_value, total_liabilities, trigger_source,
                   change_eur, change_pct, created_at
            FROM net_worth_snapshots
            ORDER BY snapshot_date DESC
            LIMIT 1
        """))).fetchone()

        if last is None:
            print("  (cap snapshot guardat — executa POST /api/v1/networth/snapshot)")
        else:
            change_str = ""
            if last.change_eur is not None:
                sign = "+" if float(last.change_eur) >= 0 else ""
                change_str = f"  ({sign}{float(last.change_eur):,.2f} €  /  {sign}{float(last.change_pct):.2f}%)"
            print(f"  Data:       {last.snapshot_date}")
            print(f"  Net Worth:  {_fmt_eur(last.total_net_worth)}{change_str}")
            print(f"  Inversió:   {_fmt_eur(last.investment_portfolio_value)}")
            print(f"  Efectiu:    {_fmt_eur(last.cash_and_bank_value)}")
            if float(last.total_liabilities or 0) > 0:
                print(f"  Passius:    {_fmt_eur(last.total_liabilities)}")
            print(f"  Font:       {last.trigger_source}  —  {last.created_at.strftime('%Y-%m-%d %H:%M UTC') if last.created_at else '—'}")

        print()
        print("━" * 72)
        print()


if __name__ == "__main__":
    asyncio.run(run())
