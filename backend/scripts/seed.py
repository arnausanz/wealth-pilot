"""
Seed script: popula la BD amb dades inicials (assets, contribucions, escenaris, paràmetres).
Executa amb: make seed  (o: docker compose exec backend python scripts/seed.py)
Idempotent: es pot executar múltiples vegades sense duplicar dades.
"""
import asyncio
import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select, text  # noqa: E402
from core.db import AsyncSessionLocal  # noqa: E402
from modules.portfolio.models import Asset, Contribution  # noqa: E402
from modules.config.models import Scenario, Parameter, Objective  # noqa: E402
from modules.market.models import MarketIndex  # noqa: E402
from modules.preferences.models import DashboardWidget  # noqa: E402


# ── Assets ──────────────────────────────────────────────────────────────────
ASSETS = [
    {
        "name": "iShares Core MSCI World UCITS ETF",
        "display_name": "MSCI World",
        "ticker_mw": "EUNL",
        "ticker_yf": "IWDA.AS",
        "isin": "IE00B4L5Y983",
        "asset_type": "etf",
        "asset_class": "equity",
        "currency": "USD",
        "currency_exposure": "USD",
        "exchange": "AMS",
        "domicile_country": "Ireland",
        "sector": "global_equity",
        "color_hex": "#4F8EF7",
        "target_weight": Decimal("22.0"),
        "sort_order": 1,
    },
    {
        "name": "Invesco Physical Gold ETC",
        "display_name": "Physical Gold",
        "ticker_mw": "PPFB",
        "ticker_yf": "PHAU.L",
        "isin": "IE00B579F325",
        "asset_type": "etf",
        "asset_class": "alternative",
        "currency": "USD",
        "currency_exposure": "USD",
        "exchange": "LSE",
        "domicile_country": "Ireland",
        "sector": "commodity",
        "color_hex": "#F5A623",
        "target_weight": Decimal("12.0"),
        "sort_order": 2,
    },
    {
        "name": "iShares Core MSCI Europe UCITS ETF",
        "display_name": "MSCI Europe",
        "ticker_mw": "EUNK",
        "ticker_yf": "IMAE.MI",
        "isin": "IE00B4K48X80",
        "asset_type": "etf",
        "asset_class": "equity",
        "currency": "EUR",
        "currency_exposure": "EUR",
        "exchange": "MIL",
        "domicile_country": "Ireland",
        "sector": "european_equity",
        "color_hex": "#7ED321",
        "target_weight": Decimal("10.0"),
        "sort_order": 3,
    },
    {
        "name": "iShares MSCI EM IMI UCITS ETF",
        "display_name": "MSCI EM IMI",
        "ticker_mw": "IS3N",
        "ticker_yf": "IS3N.AS",
        "isin": "IE00BKM4GZ66",
        "asset_type": "etf",
        "asset_class": "equity",
        "currency": "USD",
        "currency_exposure": "USD",
        "exchange": "AMS",
        "domicile_country": "Ireland",
        "sector": "emerging_markets",
        "color_hex": "#9B59B6",
        "target_weight": Decimal("5.0"),
        "sort_order": 4,
    },
    {
        "name": "iShares Core MSCI Japan IMI UCITS ETF",
        "display_name": "Japan",
        "ticker_mw": "CSJP",
        "ticker_yf": "CSJP.AS",
        "isin": "IE00B4L5YX21",
        "asset_type": "etf",
        "asset_class": "equity",
        "currency": "JPY",
        "currency_exposure": "JPY",
        "exchange": "AMS",
        "domicile_country": "Ireland",
        "sector": "japan_equity",
        "color_hex": "#E74C3C",
        "target_weight": Decimal("6.0"),
        "sort_order": 5,
    },
    {
        "name": "VanEck Defense UCITS ETF",
        "display_name": "Europe Defence",
        "ticker_mw": "WDEF",
        "ticker_yf": "WDEF.MI",
        "isin": "IE000YYE6WK9",
        "asset_type": "etf",
        "asset_class": "equity",
        "currency": "EUR",
        "currency_exposure": "EUR",
        "exchange": "MIL",
        "domicile_country": "Ireland",
        "sector": "defence",
        "color_hex": "#2ECC71",
        "target_weight": Decimal("5.0"),
        "sort_order": 6,
    },
    {
        "name": "Bitcoin",
        "display_name": "Bitcoin",
        "ticker_mw": "BTC",
        "ticker_yf": "BTC-EUR",
        "isin": None,
        "asset_type": "crypto",
        "asset_class": "alternative",
        "currency": "EUR",
        "currency_exposure": "USD",
        "exchange": None,
        "domicile_country": None,
        "sector": "crypto",
        "color_hex": "#F7931A",
        "target_weight": Decimal("2.0"),
        "sort_order": 7,
    },
    {
        "name": "Cash & Money Market",
        "display_name": "Cash",
        "ticker_mw": None,
        "ticker_yf": None,
        "isin": None,
        "asset_type": "cash",
        "asset_class": "cash",
        "currency": "EUR",
        "currency_exposure": "EUR",
        "exchange": None,
        "domicile_country": None,
        "sector": None,
        "color_hex": "#95A5A6",
        "target_weight": Decimal("25.0"),
        "sort_order": 8,
    },
]

# ── Scenarios: (asset_name, scenario_type, annual_return, volatility) ────────
SCENARIO_RETURNS = [
    # MSCI World
    ("MSCI World",     "adverse",    Decimal("4.0"),  Decimal("15.0")),
    ("MSCI World",     "base",       Decimal("7.0"),  Decimal("14.0")),
    ("MSCI World",     "optimistic", Decimal("10.0"), Decimal("13.0")),
    # Physical Gold
    ("Physical Gold",  "adverse",    Decimal("1.0"),  Decimal("12.0")),
    ("Physical Gold",  "base",       Decimal("4.0"),  Decimal("11.0")),
    ("Physical Gold",  "optimistic", Decimal("7.0"),  Decimal("10.0")),
    # MSCI Europe
    ("MSCI Europe",    "adverse",    Decimal("3.0"),  Decimal("14.0")),
    ("MSCI Europe",    "base",       Decimal("6.0"),  Decimal("13.0")),
    ("MSCI Europe",    "optimistic", Decimal("9.0"),  Decimal("12.0")),
    # MSCI EM IMI
    ("MSCI EM IMI",    "adverse",    Decimal("2.0"),  Decimal("20.0")),
    ("MSCI EM IMI",    "base",       Decimal("7.0"),  Decimal("18.0")),
    ("MSCI EM IMI",    "optimistic", Decimal("12.0"), Decimal("16.0")),
    # Japan
    ("Japan",          "adverse",    Decimal("2.0"),  Decimal("15.0")),
    ("Japan",          "base",       Decimal("5.0"),  Decimal("14.0")),
    ("Japan",          "optimistic", Decimal("8.0"),  Decimal("13.0")),
    # Europe Defence
    ("Europe Defence", "adverse",    Decimal("3.0"),  Decimal("16.0")),
    ("Europe Defence", "base",       Decimal("8.0"),  Decimal("15.0")),
    ("Europe Defence", "optimistic", Decimal("13.0"), Decimal("14.0")),
    # Bitcoin
    ("Bitcoin",        "adverse",    Decimal("-10.0"), Decimal("60.0")),
    ("Bitcoin",        "base",       Decimal("15.0"),  Decimal("50.0")),
    ("Bitcoin",        "optimistic", Decimal("40.0"),  Decimal("45.0")),
    # Cash
    ("Cash",           "adverse",    Decimal("2.0"),  Decimal("0.5")),
    ("Cash",           "base",       Decimal("3.0"),  Decimal("0.3")),
    ("Cash",           "optimistic", Decimal("4.0"),  Decimal("0.2")),
]

# ── Contributions: (asset_name, amount, day_of_month) ───────────────────────
CONTRIBUTIONS = [
    ("MSCI World",     Decimal("200.00"), 2),
    ("Physical Gold",  Decimal("100.00"), 2),
    ("MSCI Europe",    Decimal("100.00"), 2),
    ("MSCI EM IMI",    Decimal("50.00"),  2),
    ("Japan",          Decimal("50.00"),  2),
    ("Europe Defence", Decimal("50.00"),  2),
    ("Bitcoin",        Decimal("25.00"),  2),
]

# ── Global parameters ────────────────────────────────────────────────────────
PARAMETERS = [
    # portfolio
    ("cash_balance_eur",          "0",    "decimal", "portfolio", "Balanç de caixa actual (actualitzat manualment o via sync)"),
    ("rebalance_threshold_pct",   "5",    "decimal", "portfolio", "Desviació màxima del target weight abans de rebalancejar (%)"),
    ("portfolio_inception_date",  "2022-01-01", "date", "portfolio", "Data d'inici del portfolio"),
    # simulation
    ("default_horizon_months",    "36",   "integer", "simulation", "Horitzó de simulació per defecte (mesos)"),
    ("inflation_rate_pct",        "2.5",  "decimal", "simulation", "Taxa d'inflació anual estimada (%)"),
    ("default_scenario_type",     "base", "string",  "simulation", "Escenari per defecte (adverse/base/optimistic)"),
    # tax (Spain IRPF 2024)
    ("irpf_bracket_1_limit",      "6000",  "decimal", "tax", "Primer tram IRPF capital: fins a 6.000€ → 19%"),
    ("irpf_bracket_1_rate",       "19",    "decimal", "tax", "Tipus impositiu primer tram IRPF (%)"),
    ("irpf_bracket_2_limit",      "50000", "decimal", "tax", "Segon tram IRPF capital: 6.000–50.000€ → 21%"),
    ("irpf_bracket_2_rate",       "21",    "decimal", "tax", "Tipus impositiu segon tram IRPF (%)"),
    ("irpf_bracket_3_limit",      "200000","decimal", "tax", "Tercer tram IRPF capital: 50.000–200.000€ → 23%"),
    ("irpf_bracket_3_rate",       "23",    "decimal", "tax", "Tipus impositiu tercer tram IRPF (%)"),
    ("irpf_bracket_4_rate",       "26",    "decimal", "tax", "Tipus impositiu quart tram IRPF: >200.000€ (%)"),
    # personal
    ("monthly_income_net",        "0",    "decimal", "personal", "Ingressos nets mensuals estimats (€)"),
    ("monthly_expenses_target",   "0",    "decimal", "personal", "Despeses mensuals objectiu (€)"),
    ("emergency_fund_months",     "6",    "integer", "personal", "Mesos de despeses que ha de cobrir el fons d'emergència"),
    # ui
    ("currency_display",          "EUR",  "string",  "ui", "Moneda de visualització principal"),
    ("date_format",               "DD/MM/YYYY", "string", "ui", "Format de dates a la UI"),
    ("chart_animation",           "true", "boolean", "ui", "Activar animacions als gràfics"),
]

# ── Objectives ───────────────────────────────────────────────────────────────
OBJECTIVES = [
    {
        "key": "home_purchase",
        "name": "Compra d'habitatge",
        "description": "Capital necessari per a l'entrada d'un pis",
        "objective_type": "purchase",
        "target_amount": Decimal("80000.00"),
        "target_date": date(2029, 12, 31),
        "funding_source": "portfolio",
        "priority": 1,
    },
    {
        "key": "emergency_fund",
        "name": "Fons d'Emergència",
        "description": "6 mesos de despeses en liquiditat",
        "objective_type": "emergency",
        "target_amount": Decimal("15000.00"),
        "target_date": None,
        "funding_source": "cash",
        "priority": 0,
    },
]

# ── Market Indices ────────────────────────────────────────────────────────────
MARKET_INDICES = [
    {"name": "S&P 500", "ticker_yf": "^GSPC", "display_name": "S&P 500", "currency": "USD", "index_type": "equity", "region": "US", "is_default_benchmark": False},
    {"name": "MSCI World", "ticker_yf": "URTH", "display_name": "MSCI World ETF", "currency": "USD", "index_type": "equity", "region": "Global", "is_default_benchmark": True},
    {"name": "Euro Stoxx 50", "ticker_yf": "^STOXX50E", "display_name": "Euro Stoxx 50", "currency": "EUR", "index_type": "equity", "region": "Europe", "is_default_benchmark": False},
    {"name": "EURIBOR 12M", "ticker_yf": "^IRX", "display_name": "EURIBOR 12M", "currency": "EUR", "index_type": "fixed_income", "region": "Europe", "is_default_benchmark": False},
]

# ── Dashboard Widgets ─────────────────────────────────────────────────────────
DASHBOARD_WIDGETS = [
    ("net_worth",           "Net Worth Total",        True,  0),
    ("on_track",            "On Track",               True,  1),
    ("portfolio_donut",     "Distribució Portfolio",   True,  2),
    ("goals_progress",      "Progrés Objectius",       True,  3),
    ("rebalance",           "Rebalanceig",             True,  4),
    ("recent_transactions", "Últimes Transaccions",    True,  5),
    ("alerts",              "Alertes",                 True,  6),
    ("simulation_preview",  "Simulació Ràpida",        False, 7),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # ── Assets ──────────────────────────────────────────────────────
        asset_map: dict[str, int] = {}
        for a in ASSETS:
            existing = await session.scalar(select(Asset).where(Asset.display_name == a["display_name"]))
            if not existing:
                asset = Asset(**a)
                session.add(asset)
                await session.flush()
                asset_map[a["display_name"]] = asset.id
                print(f"  [+] Asset: {a['display_name']}")
            else:
                asset_map[a["display_name"]] = existing.id
                print(f"  [=] Asset ja existeix: {a['display_name']}")

        # ── Scenarios ────────────────────────────────────────────────────
        for display_name, scenario_type, annual_return, volatility in SCENARIO_RETURNS:
            asset_id = asset_map.get(display_name)
            if not asset_id:
                continue
            existing = await session.scalar(
                select(Scenario).where(Scenario.asset_id == asset_id, Scenario.scenario_type == scenario_type)
            )
            if not existing:
                session.add(Scenario(
                    asset_id=asset_id,
                    scenario_type=scenario_type,
                    annual_return=annual_return,
                    volatility=volatility,
                ))
                print(f"  [+] Scenario: {display_name} / {scenario_type}")
            else:
                print(f"  [=] Scenario ja existeix: {display_name} / {scenario_type}")

        # ── Contributions ─────────────────────────────────────────────────
        for display_name, amount, day_of_month in CONTRIBUTIONS:
            asset_id = asset_map.get(display_name)
            if not asset_id:
                continue
            existing = await session.scalar(
                select(Contribution).where(Contribution.asset_id == asset_id, Contribution.is_active == True)
            )
            if not existing:
                session.add(Contribution(
                    asset_id=asset_id,
                    amount=amount,
                    day_of_month=day_of_month,
                    start_date=date(2025, 1, 1),
                    is_active=True,
                ))
                print(f"  [+] Contribution: {display_name} → {amount}€/mes")
            else:
                print(f"  [=] Contribution ja existeix: {display_name}")

        # ── Parameters ────────────────────────────────────────────────────
        for key, value, value_type, category, description in PARAMETERS:
            existing = await session.scalar(select(Parameter).where(Parameter.key == key))
            if not existing:
                session.add(Parameter(
                    key=key,
                    value=value,
                    value_type=value_type,
                    category=category,
                    description=description,
                ))
                print(f"  [+] Parameter: {key}")
            else:
                print(f"  [=] Parameter ja existeix: {key}")

        # ── Objectives ────────────────────────────────────────────────────
        for obj in OBJECTIVES:
            existing = await session.scalar(select(Objective).where(Objective.key == obj["key"]))
            if not existing:
                session.add(Objective(**obj))
                print(f"  [+] Objective: {obj['name']}")
            else:
                print(f"  [=] Objective ja existeix: {obj['name']}")

        # ── Market Indices ─────────────────────────────────────────────────
        for idx in MARKET_INDICES:
            existing = await session.scalar(select(MarketIndex).where(MarketIndex.ticker_yf == idx["ticker_yf"]))
            if not existing:
                session.add(MarketIndex(**idx))
                print(f"  [+] MarketIndex: {idx['display_name']}")
            else:
                print(f"  [=] MarketIndex ja existeix: {idx['display_name']}")

        # ── Dashboard Widgets ──────────────────────────────────────────────
        for widget_type, display_name, is_visible, sort_order in DASHBOARD_WIDGETS:
            from modules.preferences.models import DashboardWidget
            existing = await session.scalar(select(DashboardWidget).where(DashboardWidget.widget_type == widget_type))
            if not existing:
                session.add(DashboardWidget(
                    widget_type=widget_type,
                    display_name=display_name,
                    is_visible=is_visible,
                    sort_order=sort_order,
                ))
                print(f"  [+] Widget: {widget_type}")
            else:
                print(f"  [=] Widget ja existeix: {widget_type}")

        await session.commit()
        print("\nSeed completat correctament.")


if __name__ == "__main__":
    asyncio.run(seed())
