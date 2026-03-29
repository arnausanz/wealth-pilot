"""
modules/networth/service.py — Generació de snapshots de net worth.

Estratègia de càlcul:
  - CASH: sum de mw_accounts (checking/savings/cash/forex) + cash no invertit
    en comptes d'inversió (mw_accounts.current_balance per a investment = EUR líquid
    sense invertir, e.g. els 5.7k€ a Trade Republic que no estan en ETFs).
  - INVESTMENT PORTFOLIO: shares acumulades × preu actual de Yahoo Finance.
    Nota: actius no mapejats (e.g. NUKL sense ticker_mw) no queden inclosos.
  - LIABILITIES: sum de mw_accounts credit/loan.
  - TOTAL NET WORTH = cash + investment_portfolio - liabilities.

Trigger:
  - Cridat automàticament des de sync.service.process_upload() post-import MW.
  - Cridat manualment via POST /api/v1/networth/snapshot.
  - Idempotent: ON CONFLICT snapshot_date → DO UPDATE.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from modules.networth.models import AssetSnapshot, NetWorthSnapshot
from modules.networth.schemas import GenerateSnapshotResponse

logger = logging.getLogger(__name__)

_CASH_ACCOUNT_TYPES = ("checking", "savings", "cash", "forex")
_INV_ACCOUNT_TYPES  = ("investment",)
_LIAB_ACCOUNT_TYPES = ("credit", "loan")


async def generate_snapshot(
    db: AsyncSession,
    snapshot_date: date | None = None,
    trigger_source: str = "api",
) -> GenerateSnapshotResponse:
    """
    Genera (o actualitza) el snapshot de net worth per a snapshot_date (default: avui).

    Passos:
      1. Cash value: suma de mw_accounts checking/savings/cash.
      2. Investment value: suma de mw_accounts investment (font de veritat per al total).
      3. Liabilities: suma de mw_accounts credit/loan.
      4. Per cada asset amb ticker_mw mapejat → calcular posició (shares × preu YF).
      5. Upsert a net_worth_snapshots + asset_snapshots.
      6. Calcular canvi vs. snapshot anterior.
    """
    if snapshot_date is None:
        snapshot_date = date.today()

    # ── 1. Account balances des de MoneyWiz ─────────────────────────────────
    #
    # Nota sobre comptes d'inversió (account_type='investment'):
    #   mw_accounts.current_balance per a un compte d'inversió = únicament el cash
    #   no invertit (EUR líquid dins de TR, etc.). El valor de les accions/ETFs/crypto
    #   NO és inclòs — es calcula al pas 2 via shares × preu YF.
    #
    #   Per tant:
    #     cash_value  = checking + savings + cash + forex + INVESTMENT CASH
    #     inv_value   = shares × preu YF (calculat al pas 2)
    #     liab_value  = credit + loan
    #     total       = cash_value + inv_value - liab_value
    balances = (await db.execute(text("""
        SELECT account_type, SUM(current_balance) AS total
        FROM mw_accounts
        WHERE is_active = TRUE
          AND include_in_networth = TRUE
          AND current_balance IS NOT NULL
        GROUP BY account_type
    """))).fetchall()

    cash_value = Decimal("0")
    liab_value = Decimal("0")

    for row in balances:
        amount = Decimal(str(row.total))
        if row.account_type in _CASH_ACCOUNT_TYPES or row.account_type in _INV_ACCOUNT_TYPES:
            # Investment account balance = cash no invertit → compta com a efectiu
            cash_value += amount
        elif row.account_type in _LIAB_ACCOUNT_TYPES:
            liab_value += amount

    # inv_value s'assigna després del pas 2 (shares × preu YF)
    inv_value = Decimal("0")

    # ── 2. Posicions per asset (shares × preu YF actual) ────────────────────
    # MoneyWiz pot registrar compres d'ETF de tres maneres:
    #   - investment_buy / investment_sell : compra/venda nativa des del compte inversió
    #   - expense / income                : compra/venda registrada des del compte corrent
    #   - transfer_out / transfer_in      : transferència entre comptes (compra/venda)
    # Qualsevol transacció amb shares != NULL és una operació d'inversió.
    # Direcció: diners sortint (expense, transfer_out, investment_buy) = compra (+shares)
    #           diners entrant (income,  transfer_in,  investment_sell) = venda  (-shares)
    positions_rows = (await db.execute(text("""
        SELECT
            a.id          AS asset_id,
            a.display_name,
            a.ticker_yf,
            SUM(
                CASE
                    WHEN mt.tx_type IN ('investment_buy',  'expense', 'transfer_out') THEN  mt.shares
                    WHEN mt.tx_type IN ('investment_sell', 'income',  'transfer_in')  THEN -mt.shares
                    ELSE 0
                END
            )                                             AS total_shares,
            SUM(
                CASE
                    WHEN mt.tx_type IN ('investment_buy', 'expense', 'transfer_out') THEN mt.amount_eur
                    ELSE 0
                END
            )                                             AS cost_basis,
            ph.price_close                                AS last_price,
            ph.currency                                   AS price_currency
        FROM mw_transactions mt
        JOIN assets a ON a.ticker_mw = mt.mw_symbol
        LEFT JOIN LATERAL (
            SELECT price_close, currency
            FROM price_history
            WHERE asset_id = a.id
              AND price_date <= :snap_date
            ORDER BY price_date DESC
            LIMIT 1
        ) ph ON TRUE
        WHERE mt.shares IS NOT NULL
          AND mt.tx_date <= :snap_date
          AND a.is_active = TRUE
        GROUP BY a.id, a.display_name, a.ticker_yf, ph.price_close, ph.currency
        HAVING SUM(
            CASE
                WHEN mt.tx_type IN ('investment_buy',  'expense', 'transfer_out') THEN  mt.shares
                WHEN mt.tx_type IN ('investment_sell', 'income',  'transfer_in')  THEN -mt.shares
                ELSE 0
            END
        ) > 0
    """), {"snap_date": snapshot_date})).fetchall()

    asset_data = []
    for p in positions_rows:
        if p.last_price is None:
            logger.warning("Sense preu per a %s (%s) — omès del snapshot", p.display_name, p.ticker_yf)
            continue
        shares      = Decimal(str(p.total_shares))
        price_eur   = Decimal(str(p.last_price))
        value_eur   = (shares * price_eur).quantize(Decimal("0.01"))
        cost_basis  = Decimal(str(p.cost_basis)).quantize(Decimal("0.01"))
        pnl_eur     = (value_eur - cost_basis).quantize(Decimal("0.01"))
        pnl_pct     = (pnl_eur / cost_basis * 100).quantize(Decimal("0.01")) if cost_basis else None
        asset_data.append({
            "asset_id":           p.asset_id,
            "display_name":       p.display_name,
            "ticker_yf":          p.ticker_yf,
            "shares":             shares,
            "price_eur":          price_eur,
            "value_eur":          value_eur,
            "cost_basis_eur":     cost_basis,
            "unrealized_pnl_eur": pnl_eur,
            "unrealized_pnl_pct": pnl_pct,
        })

    # inv_value = total de shares × preu YF (tots els actius traçats)
    total_tracked_value = sum(a["value_eur"] for a in asset_data)
    inv_value = total_tracked_value

    # Calcular pes de cada asset sobre la cartera d'inversió
    for a in asset_data:
        a["weight_actual_pct"] = (
            (a["value_eur"] / total_tracked_value * 100).quantize(Decimal("0.01"))
            if total_tracked_value else None
        )

    total_net_worth = cash_value + inv_value - liab_value

    # ── 3. Canvi vs. snapshot anterior ──────────────────────────────────────
    prev = (await db.execute(text("""
        SELECT total_net_worth
        FROM net_worth_snapshots
        WHERE snapshot_date < :d
        ORDER BY snapshot_date DESC
        LIMIT 1
    """), {"d": snapshot_date})).fetchone()

    change_eur = (total_net_worth - Decimal(str(prev.total_net_worth))).quantize(Decimal("0.01")) if prev else None
    change_pct = (change_eur / Decimal(str(prev.total_net_worth)) * 100).quantize(Decimal("0.01")) if (prev and prev.total_net_worth) else None

    # ── 4. Upsert snapshot principal ────────────────────────────────────────
    snap_stmt = pg_insert(NetWorthSnapshot).values(
        snapshot_date=snapshot_date,
        total_net_worth=total_net_worth,
        investment_portfolio_value=inv_value,
        cash_and_bank_value=cash_value,
        real_estate_value=Decimal("0"),
        pension_value=Decimal("0"),
        other_assets_value=Decimal("0"),
        total_liabilities=liab_value,
        change_eur=change_eur,
        change_pct=change_pct,
        trigger_source=trigger_source,
        created_at=datetime.now(timezone.utc),
    )
    snap_stmt = snap_stmt.on_conflict_do_update(
        constraint="uq_networth_date",
        set_={
            "total_net_worth":            snap_stmt.excluded.total_net_worth,
            "investment_portfolio_value": snap_stmt.excluded.investment_portfolio_value,
            "cash_and_bank_value":        snap_stmt.excluded.cash_and_bank_value,
            "total_liabilities":          snap_stmt.excluded.total_liabilities,
            "change_eur":                 snap_stmt.excluded.change_eur,
            "change_pct":                 snap_stmt.excluded.change_pct,
            "trigger_source":             snap_stmt.excluded.trigger_source,
            "created_at":                 snap_stmt.excluded.created_at,
        },
    ).returning(NetWorthSnapshot.id, NetWorthSnapshot.created_at)

    result     = await db.execute(snap_stmt)
    snap_row   = result.fetchone()
    snapshot_id = snap_row.id

    # ── 5. Upsert asset_snapshots ────────────────────────────────────────────
    # Primer esborrem els existents per a aquest snapshot (re-insert net)
    await db.execute(
        text("DELETE FROM asset_snapshots WHERE snapshot_id = :sid"),
        {"sid": snapshot_id},
    )
    if asset_data:
        asset_rows = [
            {
                "snapshot_id":         snapshot_id,
                "asset_id":            a["asset_id"],
                "shares":              a["shares"],
                "price_eur":           a["price_eur"],
                "value_eur":           a["value_eur"],
                "cost_basis_eur":      a["cost_basis_eur"],
                "unrealized_pnl_eur":  a["unrealized_pnl_eur"],
                "unrealized_pnl_pct":  a["unrealized_pnl_pct"],
                "weight_actual_pct":   a["weight_actual_pct"],
            }
            for a in asset_data
        ]
        await db.execute(pg_insert(AssetSnapshot).values(asset_rows))

    await db.commit()

    logger.info(
        "Snapshot generat [%s]: net worth=%.2f EUR, "
        "inversió=%.2f EUR, cash=%.2f EUR, %d assets",
        snapshot_date, total_net_worth, inv_value, cash_value, len(asset_data),
    )

    return GenerateSnapshotResponse(
        snapshot_date=snapshot_date,
        total_net_worth=total_net_worth,
        investment_portfolio_value=inv_value,
        cash_and_bank_value=cash_value,
        assets_tracked=len(asset_data),
        created=True,
    )


async def get_history(
    db: AsyncSession,
    period: str = "1y",
) -> list[NetWorthSnapshot]:
    """
    Retorna els snapshots de net worth per al període indicat.
    Períodes suportats: 1m, 3m, 6m, 1y, 2y, 5y, all.
    """
    period_days = {
        "1m": 30, "3m": 91, "6m": 182,
        "1y": 365, "2y": 730, "5y": 1825, "all": 36500,
    }
    days = period_days.get(period, 365)

    result = await db.execute(
        select(NetWorthSnapshot)
        .where(
            NetWorthSnapshot.snapshot_date >= text(f"CURRENT_DATE - INTERVAL '{days} days'")
        )
        .order_by(NetWorthSnapshot.snapshot_date.asc())
    )
    return list(result.scalars().all())


async def backfill_snapshots(
    db: AsyncSession,
    months: int = 24,
) -> dict:
    """
    Genera snapshots mensuals retrospectius des de fa `months` mesos fins a ahir.
    Utilitza el primer dia de cada mes. Idempotent: ON CONFLICT DO UPDATE.

    Retorna un resum amb el nombre de snapshots creats i errors.
    """
    from calendar import monthrange

    today = date.today()
    results = {"created": 0, "errors": 0, "dates": []}

    for i in range(months, 0, -1):
        # Calcular el primer dia del mes d'i mesos enrere
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        # Usar el darrer dia del mes per tenir la posició final del mes
        last_day = monthrange(year, month)[1]
        snap_date = date(year, month, last_day)

        # No generar snapshots futurs
        if snap_date >= today:
            continue

        try:
            await generate_snapshot(db, snapshot_date=snap_date, trigger_source="backfill")
            results["created"] += 1
            results["dates"].append(snap_date.isoformat())
            logger.info("Backfill snapshot creat: %s", snap_date)
        except Exception as exc:
            results["errors"] += 1
            logger.warning("Backfill snapshot fallat per %s: %s", snap_date, exc)

    # Generar també el d'avui
    try:
        await generate_snapshot(db, snapshot_date=today, trigger_source="backfill")
        results["created"] += 1
        results["dates"].append(today.isoformat())
    except Exception as exc:
        results["errors"] += 1
        logger.warning("Backfill snapshot d'avui fallat: %s", exc)

    logger.info(
        "Backfill completat: %d snapshots creats, %d errors",
        results["created"], results["errors"],
    )
    return results
