"""
modules/history/service.py — Lògica de negoci de l'historial de transaccions.

Fonts de dades:
  - mw_transactions: totes les transaccions importades de MoneyWiz
  - assets: metadades dels assets (display_name, ticker_yf, color_hex)
  - price_history: preus actuals per calcular P&L

Les transaccions d'inversió (investment_buy/sell) s'enriqueixen amb info
de l'asset. Les transaccions no-inversió (expense/income/transfer) es mostren
amb les dades bàsiques de MoneyWiz.
"""

import logging
import math
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from modules.history.schemas import (
    AssetInvestmentSummary,
    InvestmentSummaryResponse,
    TransactionOut,
    TransactionsResponse,
)

logger = logging.getLogger(__name__)

# Tipus de transacció que es filtren per defecte (no inversions)
_ALL_TX_TYPES = {"expense", "income", "investment_buy", "investment_sell", "transfer_in", "transfer_out"}


async def get_transactions(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    tx_type: str | None = None,
    ticker_yf: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    only_investments: bool = False,
) -> TransactionsResponse:
    """
    Retorna transaccions paginades amb filtres opcionals.

    Lògica de filtres:
    - tx_type='investment_buy'  → totes les tx amb shares (no venda): expense/income/transfer/buy
    - tx_type='investment_sell' → investment_sell exacte
    - tx_type='expense'/'income' → exclou les que tenen shares (que són inversions disfressades)
    - only_investments=True → totes les tx amb shares (Inversions)
    - ticker_yf sense tx_type → totes les inversions d'aquell asset
    """
    per_page = max(1, min(100, per_page))
    page     = max(1, page)
    offset   = (page - 1) * per_page

    # Construir condicions de filtre
    where_clauses = []
    params: dict = {"limit": per_page, "offset": offset}

    if tx_type:
        if tx_type == 'investment_buy':
            # Compra = qualsevol tx amb shares que no sigui venda
            where_clauses.append("mt.shares IS NOT NULL AND mt.tx_type != 'investment_sell'")
        elif tx_type == 'investment_sell':
            where_clauses.append("mt.tx_type = 'investment_sell'")
        elif tx_type in ('expense', 'income'):
            # Despesa/ingrés real = sense shares (els amb shares son inversions)
            where_clauses.append("mt.tx_type = :tx_type AND mt.shares IS NULL")
            params["tx_type"] = tx_type
        elif tx_type in _ALL_TX_TYPES:
            where_clauses.append("mt.tx_type = :tx_type")
            params["tx_type"] = tx_type
    else:
        if only_investments or ticker_yf:
            # Inversions: qualsevol tx amb shares (inclou expense/income/transfer que son ETF buys)
            where_clauses.append("mt.shares IS NOT NULL")

    if ticker_yf:
        where_clauses.append("a.ticker_yf = :ticker_yf")
        params["ticker_yf"] = ticker_yf
        # Quan filtrem per asset, sempre joinegem assets (el LEFT JOIN ja és allà)

    if date_from:
        where_clauses.append("mt.tx_date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        where_clauses.append("mt.tx_date <= :date_to")
        params["date_to"] = date_to

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM mw_transactions mt
        LEFT JOIN assets a ON a.ticker_mw = mt.mw_symbol
        {where_sql}
    """
    total = (await db.execute(text(count_sql), params)).scalar() or 0

    rows = (await db.execute(text(f"""
        SELECT
            mt.id,
            mt.tx_date,
            mt.tx_type,
            mt.amount_eur,
            mt.description,
            mt.mw_symbol,
            mt.shares,
            a.display_name,
            a.ticker_yf,
            a.color_hex,
            acc.name AS account_name
        FROM mw_transactions mt
        LEFT JOIN assets a ON a.ticker_mw = mt.mw_symbol
        LEFT JOIN mw_accounts acc ON acc.id = mt.account_id
        {where_sql}
        ORDER BY mt.tx_date DESC, mt.id DESC
        LIMIT :limit OFFSET :offset
    """), params)).fetchall()

    transactions = [
        TransactionOut(
            id=r.id,
            tx_date=r.tx_date,
            tx_type=r.tx_type,
            amount_eur=Decimal(str(r.amount_eur)),
            description=r.description,
            mw_symbol=r.mw_symbol,
            display_name=r.display_name,
            ticker_yf=r.ticker_yf,
            color_hex=r.color_hex,
            shares=Decimal(str(r.shares)) if r.shares else None,
            account_name=r.account_name,
        )
        for r in rows
    ]

    return TransactionsResponse(
        transactions=transactions,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


async def get_investment_summary(db: AsyncSession) -> InvestmentSummaryResponse:
    """
    Resum per asset: total invertit, posició actual, P&L.
    Combina transaccions de MoneyWiz amb preus actuals de Yahoo Finance.
    """
    # Mateixa lògica que networth/service.py:
    # - VENDA (-shares): investment_sell  (únic tipus de venda)
    # - COMPRA (+shares): qualsevol altra tx amb shares (expense/income/transfer/investment_buy)
    rows = (await db.execute(text("""
        SELECT
            a.id             AS asset_id,
            a.display_name,
            a.ticker_yf,
            a.color_hex,
            SUM(CASE
                WHEN mt.tx_type = 'investment_sell' THEN -mt.shares
                ELSE mt.shares
            END)             AS total_shares,
            SUM(CASE
                WHEN mt.tx_type = 'investment_sell' THEN 0
                ELSE mt.amount_eur
            END)             AS total_invested,
            COUNT(CASE WHEN mt.tx_type != 'investment_sell' THEN 1 END) AS buy_count,
            COUNT(CASE WHEN mt.tx_type  = 'investment_sell' THEN 1 END) AS sell_count,
            MIN(CASE WHEN mt.tx_type != 'investment_sell' THEN mt.tx_date END) AS first_buy,
            MAX(CASE WHEN mt.tx_type != 'investment_sell' THEN mt.tx_date END) AS last_buy
        FROM mw_transactions mt
        JOIN assets a ON a.ticker_mw = mt.mw_symbol
        WHERE mt.shares IS NOT NULL
          AND a.is_active = TRUE
        GROUP BY a.id, a.display_name, a.ticker_yf, a.color_hex
        HAVING SUM(CASE
            WHEN mt.tx_type = 'investment_sell' THEN -mt.shares
            ELSE mt.shares
        END) > 0
        ORDER BY total_invested DESC
    """))).fetchall()

    # Preus actuals per calcular P&L
    price_rows = (await db.execute(text("""
        SELECT asset_id, price_close
        FROM (
            SELECT asset_id, price_close,
                   ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY price_date DESC) AS rn
            FROM price_history
        ) sub
        WHERE rn = 1
    """))).fetchall()
    prices: dict[int, Decimal] = {r.asset_id: Decimal(str(r.price_close)) for r in price_rows}

    assets: list[AssetInvestmentSummary] = []
    total_invested = Decimal("0")
    total_current  = Decimal("0")

    for row in rows:
        shares    = Decimal(str(row.total_shares))
        invested  = Decimal(str(row.total_invested)).quantize(Decimal("0.01"))
        avg_cost  = (invested / shares).quantize(Decimal("0.0001")) if shares > 0 else None
        cur_price = prices.get(row.asset_id)
        cur_value = (shares * cur_price).quantize(Decimal("0.01")) if cur_price else None
        pnl_eur   = (cur_value - invested).quantize(Decimal("0.01")) if cur_value else None
        pnl_pct   = (pnl_eur / invested * 100).quantize(Decimal("0.01")) if (pnl_eur and invested > 0) else None

        total_invested += invested
        if cur_value:
            total_current += cur_value

        assets.append(AssetInvestmentSummary(
            asset_id=row.asset_id,
            display_name=row.display_name,
            ticker_yf=row.ticker_yf,
            color_hex=row.color_hex,
            shares=shares,
            total_invested_eur=invested,
            avg_cost_eur=avg_cost,
            current_price_eur=cur_price,
            current_value_eur=cur_value,
            pnl_eur=pnl_eur,
            pnl_pct=pnl_pct,
            buy_count=row.buy_count or 0,
            sell_count=row.sell_count or 0,
            first_buy_date=row.first_buy,
            last_buy_date=row.last_buy,
        ))

    total_pnl = (total_current - total_invested).quantize(Decimal("0.01")) if total_current > 0 else None
    total_pnl_pct = (total_pnl / total_invested * 100).quantize(Decimal("0.01")) if (total_pnl and total_invested > 0) else None

    return InvestmentSummaryResponse(
        assets=assets,
        total_invested_eur=total_invested,
        total_current_value_eur=total_current if total_current > 0 else None,
        total_pnl_eur=total_pnl,
        total_pnl_pct=total_pnl_pct,
    )
