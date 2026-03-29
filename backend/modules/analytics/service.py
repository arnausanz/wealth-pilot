"""modules/analytics/service.py — Lògica de negoci del mòdul d'analítica."""

import logging
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from modules.analytics.schemas import (
    AlertsResponse,
    AnalyticsAlert,
    CashflowMonth,
    CashflowResponse,
    ExpenseBreakdownResponse,
    ExpenseCategory,
    NetWorthEvolutionResponse,
    NetWorthMonth,
)

logger = logging.getLogger(__name__)


async def get_expense_breakdown(
    db: AsyncSession,
    year: int,
    month: int | None = None,
) -> ExpenseBreakdownResponse:
    """Top expense categories for a given year/month."""
    # shares IS NULL: exclou compres d'ETF registrades com expense per MoneyWiz
    if month is not None:
        sql = text("""
            SELECT
                COALESCE(c.name, 'Sense categoria') AS category,
                COALESCE(c.color_hex, NULL)          AS color_hex,
                SUM(ABS(t.amount_eur))               AS total_eur,
                COUNT(*)                             AS tx_count
            FROM mw_transactions t
            LEFT JOIN mw_categories c ON c.id = t.category_id
            WHERE t.tx_type = 'expense'
              AND t.shares IS NULL
              AND t.is_excluded_from_reports = FALSE
              AND EXTRACT(YEAR  FROM t.tx_date) = :year
              AND EXTRACT(MONTH FROM t.tx_date) = :month
            GROUP BY c.name, c.color_hex
            ORDER BY total_eur DESC
            LIMIT 12
        """)
        rows = (await db.execute(sql, {"year": year, "month": month})).fetchall()
    else:
        sql = text("""
            SELECT
                COALESCE(c.name, 'Sense categoria') AS category,
                COALESCE(c.color_hex, NULL)          AS color_hex,
                SUM(ABS(t.amount_eur))               AS total_eur,
                COUNT(*)                             AS tx_count
            FROM mw_transactions t
            LEFT JOIN mw_categories c ON c.id = t.category_id
            WHERE t.tx_type = 'expense'
              AND t.shares IS NULL
              AND t.is_excluded_from_reports = FALSE
              AND EXTRACT(YEAR FROM t.tx_date) = :year
            GROUP BY c.name, c.color_hex
            ORDER BY total_eur DESC
            LIMIT 12
        """)
        rows = (await db.execute(sql, {"year": year})).fetchall()

    total_eur = sum(Decimal(str(r.total_eur)) for r in rows) or Decimal("0")

    categories = []
    for r in rows:
        cat_total = Decimal(str(r.total_eur))
        pct = (cat_total / total_eur * 100).quantize(Decimal("0.1")) if total_eur > 0 else Decimal("0")
        categories.append(
            ExpenseCategory(
                category=r.category,
                total_eur=cat_total.quantize(Decimal("0.01")),
                pct_of_total=pct,
                tx_count=r.tx_count,
                color_hex=r.color_hex,
            )
        )

    return ExpenseBreakdownResponse(
        year=year,
        month=month,
        categories=categories,
        total_eur=total_eur.quantize(Decimal("0.01")),
    )


async def get_cashflow(db: AsyncSession, months: int = 12) -> CashflowResponse:
    """Monthly cashflow: income vs expenses vs investments for last N months."""
    # Regla clau: shares IS NULL → transacció financera real (expense/income sense inversió)
    # shares IS NOT NULL → operació d'inversió (compra/venda ETF, crypto, etc.)
    # MoneyWiz pot registrar compres d'ETF com expense/income/transfer → shares != NULL els identifica
    sql = text("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', tx_date), 'YYYY-MM') AS month,
            SUM(CASE WHEN tx_type = 'income'  AND shares IS NULL
                     THEN amount_eur ELSE 0 END)              AS income_eur,
            SUM(CASE WHEN tx_type = 'expense' AND shares IS NULL
                     THEN ABS(amount_eur) ELSE 0 END)         AS expenses_eur,
            SUM(CASE WHEN shares IS NOT NULL
                     THEN ABS(amount_eur) ELSE 0 END)         AS investments_eur
        FROM mw_transactions
        WHERE is_excluded_from_reports = FALSE
          AND tx_date >= DATE_TRUNC('month', NOW()) - INTERVAL '1 month' * :months
          AND tx_date <  DATE_TRUNC('month', NOW()) + INTERVAL '1 month'
        GROUP BY DATE_TRUNC('month', tx_date)
        ORDER BY DATE_TRUNC('month', tx_date) ASC
    """)
    rows = (await db.execute(sql, {"months": months})).fetchall()

    result_months = []
    savings_rates = []

    for r in rows:
        income = Decimal(str(r.income_eur))
        expenses = Decimal(str(r.expenses_eur))
        investments = Decimal(str(r.investments_eur))
        savings = income - expenses
        savings_rate: Decimal | None = None
        if income > 0:
            savings_rate = (savings / income * 100).quantize(Decimal("0.1"))
            savings_rates.append(savings_rate)

        result_months.append(
            CashflowMonth(
                month=r.month,
                income_eur=income.quantize(Decimal("0.01")),
                expenses_eur=expenses.quantize(Decimal("0.01")),
                investments_eur=investments.quantize(Decimal("0.01")),
                savings_eur=savings.quantize(Decimal("0.01")),
                savings_rate_pct=savings_rate,
            )
        )

    n = len(result_months) or 1
    avg_income = (
        sum(Decimal(str(m.income_eur)) for m in result_months) / n
    ).quantize(Decimal("0.01"))
    avg_expenses = (
        sum(Decimal(str(m.expenses_eur)) for m in result_months) / n
    ).quantize(Decimal("0.01"))
    avg_savings_rate: Decimal | None = None
    if savings_rates:
        avg_savings_rate = (sum(savings_rates) / len(savings_rates)).quantize(Decimal("0.1"))

    return CashflowResponse(
        months=result_months,
        avg_income=avg_income,
        avg_expenses=avg_expenses,
        avg_savings_rate_pct=avg_savings_rate,
    )


async def get_networth_evolution(
    db: AsyncSession,
    months: int = 24,
) -> NetWorthEvolutionResponse:
    """Last net worth snapshot per month for the last N months."""
    sql = text("""
        SELECT DISTINCT ON (DATE_TRUNC('month', snapshot_date))
            TO_CHAR(DATE_TRUNC('month', snapshot_date), 'YYYY-MM') AS month,
            total_net_worth,
            COALESCE(investment_portfolio_value, 0)                AS investment_value,
            COALESCE(cash_and_bank_value, 0)                       AS cash_value
        FROM net_worth_snapshots
        WHERE snapshot_date >= DATE_TRUNC('month', NOW()) - INTERVAL '1 month' * :months
        ORDER BY DATE_TRUNC('month', snapshot_date) DESC, snapshot_date DESC
    """)
    rows = (await db.execute(sql, {"months": months})).fetchall()

    # Rows come DESC (newest first), reverse to get ASC for chart
    result = [
        NetWorthMonth(
            month=r.month,
            total_net_worth=Decimal(str(r.total_net_worth)).quantize(Decimal("0.01")),
            investment_value=Decimal(str(r.investment_value)).quantize(Decimal("0.01")),
            cash_value=Decimal(str(r.cash_value)).quantize(Decimal("0.01")),
        )
        for r in reversed(rows)
    ]

    return NetWorthEvolutionResponse(months=result)


async def get_alerts(db: AsyncSession) -> AlertsResponse:
    """Auto-generate alerts from transaction data."""
    alerts: list[AnalyticsAlert] = []

    # ── Alert 1: Current month expenses vs 3-month avg ─────────────────────
    sql_expenses = text("""
        SELECT
            TO_CHAR(DATE_TRUNC('month', tx_date), 'YYYY-MM') AS month,
            SUM(ABS(amount_eur)) AS expenses_eur
        FROM mw_transactions
        WHERE tx_type = 'expense'
          AND shares IS NULL
          AND is_excluded_from_reports = FALSE
          AND tx_date >= DATE_TRUNC('month', NOW()) - INTERVAL '3 months'
          AND tx_date <  DATE_TRUNC('month', NOW()) + INTERVAL '1 month'
        GROUP BY DATE_TRUNC('month', tx_date)
        ORDER BY DATE_TRUNC('month', tx_date) ASC
    """)
    exp_rows = (await db.execute(sql_expenses)).fetchall()

    if exp_rows:
        current_month_str = None
        from datetime import datetime
        current_month_str = datetime.now().strftime("%Y-%m")

        current_exp = Decimal("0")
        past_expenses = []
        for r in exp_rows:
            v = Decimal(str(r.expenses_eur))
            if r.month == current_month_str:
                current_exp = v
            else:
                past_expenses.append(v)

        if past_expenses and current_exp > 0:
            avg_past = sum(past_expenses) / len(past_expenses)
            if avg_past > 0:
                ratio = (current_exp - avg_past) / avg_past
                if ratio > Decimal("0.5"):
                    alerts.append(AnalyticsAlert(
                        id="expenses_spike_critical",
                        severity="critical",
                        title="Despeses molt elevades",
                        detail=f"Despeses aquest mes {float(ratio*100):.0f}% per sobre de la mitjana dels últims 3 mesos.",
                    ))
                elif ratio > Decimal("0.3"):
                    alerts.append(AnalyticsAlert(
                        id="expenses_spike_warning",
                        severity="warning",
                        title="Despeses elevades",
                        detail=f"Despeses aquest mes {float(ratio*100):.0f}% per sobre de la mitjana dels últims 3 mesos.",
                    ))

    # ── Alert 2: Savings rate this month ───────────────────────────────────
    sql_savings = text("""
        SELECT
            SUM(CASE WHEN tx_type = 'income'  AND shares IS NULL
                     THEN amount_eur ELSE 0 END)        AS income_eur,
            SUM(CASE WHEN tx_type = 'expense' AND shares IS NULL
                     THEN ABS(amount_eur) ELSE 0 END)   AS expenses_eur
        FROM mw_transactions
        WHERE is_excluded_from_reports = FALSE
          AND tx_date >= DATE_TRUNC('month', NOW())
          AND tx_date <  DATE_TRUNC('month', NOW()) + INTERVAL '1 month'
    """)
    srow = (await db.execute(sql_savings)).fetchone()
    if srow and srow.income_eur and Decimal(str(srow.income_eur)) > 0:
        income_m = Decimal(str(srow.income_eur))
        expenses_m = Decimal(str(srow.expenses_eur or 0))
        savings_rate = (income_m - expenses_m) / income_m * 100

        if savings_rate < 0:
            alerts.append(AnalyticsAlert(
                id="savings_rate_negative",
                severity="critical",
                title="Taxa d'estalvi negativa",
                detail=f"Les despeses superen els ingressos aquest mes ({float(savings_rate):.1f}%).",
            ))
        elif savings_rate < Decimal("10"):
            alerts.append(AnalyticsAlert(
                id="savings_rate_low",
                severity="warning",
                title="Taxa d'estalvi baixa",
                detail=f"Taxa d'estalvi aquest mes: {float(savings_rate):.1f}% (recomanat >10%).",
            ))

    # ── Alert 3: Category spike — any category this month > 2x 3-month avg ─
    sql_cat = text("""
        WITH monthly_cat AS (
            SELECT
                COALESCE(c.name, 'Sense categoria')                        AS category,
                TO_CHAR(DATE_TRUNC('month', t.tx_date), 'YYYY-MM')         AS month,
                SUM(ABS(t.amount_eur))                                     AS total_eur
            FROM mw_transactions t
            LEFT JOIN mw_categories c ON c.id = t.category_id
            WHERE t.tx_type = 'expense'
              AND t.shares IS NULL
              AND t.is_excluded_from_reports = FALSE
              AND t.tx_date >= DATE_TRUNC('month', NOW()) - INTERVAL '3 months'
              AND t.tx_date <  DATE_TRUNC('month', NOW()) + INTERVAL '1 month'
            GROUP BY c.name, DATE_TRUNC('month', t.tx_date)
        ),
        current_month AS (
            SELECT category, total_eur
            FROM monthly_cat
            WHERE month = TO_CHAR(DATE_TRUNC('month', NOW()), 'YYYY-MM')
        ),
        past_avg AS (
            SELECT category, AVG(total_eur) AS avg_eur
            FROM monthly_cat
            WHERE month != TO_CHAR(DATE_TRUNC('month', NOW()), 'YYYY-MM')
            GROUP BY category
        )
        SELECT cm.category, cm.total_eur, pa.avg_eur,
               cm.total_eur / NULLIF(pa.avg_eur, 0) AS ratio
        FROM current_month cm
        JOIN past_avg pa ON pa.category = cm.category
        WHERE cm.total_eur / NULLIF(pa.avg_eur, 0) > 2
        ORDER BY ratio DESC
        LIMIT 1
    """)
    cat_row = (await db.execute(sql_cat)).fetchone()
    if cat_row:
        alerts.append(AnalyticsAlert(
            id="category_spike",
            severity="warning",
            title=f"Pic de despesa: {cat_row.category}",
            detail=f'La categoria "{cat_row.category}" és {float(cat_row.ratio):.1f}x la mitjana dels últims 3 mesos.',
            category=cat_row.category,
        ))

    return AlertsResponse(alerts=alerts)
