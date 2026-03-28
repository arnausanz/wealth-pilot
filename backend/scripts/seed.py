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
from core.constants import (  # noqa: E402
    AssetClass, AssetType,
    FetchStatus, IndexTicker,
    ObjectiveKey,
    ParameterCategory, ParameterKey,
    ScenarioType, Ticker,
)
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
        "ticker_yf": Ticker.MSCI_WORLD,
        "isin": "IE00B4L5Y983",
        "asset_type": AssetType.ETF,
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
        "currency_exposure": "USD",
        "exchange": "AMS",
        "domicile_country": "Ireland",
        "sector": "global_equity",
        "color_hex": "#4F8EF7",
        "target_weight": Decimal("35.0"),
        "sort_order": 1,
    },
    {
        "name": "iShares Physical Gold ETC",
        "display_name": "Physical Gold",
        "ticker_mw": "PPFB",
        "ticker_yf": Ticker.PHYSICAL_GOLD,
        "isin": "IE00B4ND3602",
        "asset_type": AssetType.ETF,
        "asset_class": AssetClass.ALTERNATIVE,
        "currency": "EUR",
        "currency_exposure": "USD",
        "exchange": "XETRA",
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
        "ticker_yf": Ticker.MSCI_EUROPE,
        "isin": "IE00B4K48X80",
        "asset_type": AssetType.ETF,
        "asset_class": AssetClass.EQUITY,
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
        "ticker_yf": Ticker.MSCI_EM_IMI,
        "isin": "IE00BKM4GZ66",
        "asset_type": AssetType.ETF,
        "asset_class": AssetClass.EQUITY,
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
        "ticker_mw": "XMK9",
        "ticker_yf": Ticker.JAPAN,
        "isin": "IE00B4L5YX21",
        "asset_type": AssetType.ETF,
        "asset_class": AssetClass.EQUITY,
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
        "ticker_mw": "EUDF",
        "ticker_yf": Ticker.EUROPE_DEFENCE,
        "isin": "IE000YYE6WK9",
        "asset_type": AssetType.ETF,
        "asset_class": AssetClass.EQUITY,
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
        "ticker_yf": Ticker.BITCOIN,
        "isin": None,
        "asset_type": AssetType.CRYPTO,
        "asset_class": AssetClass.ALTERNATIVE,
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
        "asset_type": AssetType.CASH,
        "asset_class": AssetClass.CASH,
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
    ("MSCI World",     ScenarioType.ADVERSE,    Decimal("4.0"),   Decimal("15.0")),
    ("MSCI World",     ScenarioType.BASE,        Decimal("7.0"),   Decimal("14.0")),
    ("MSCI World",     ScenarioType.OPTIMISTIC,  Decimal("10.0"),  Decimal("13.0")),
    # Physical Gold
    ("Physical Gold",  ScenarioType.ADVERSE,     Decimal("1.0"),   Decimal("12.0")),
    ("Physical Gold",  ScenarioType.BASE,         Decimal("4.0"),   Decimal("11.0")),
    ("Physical Gold",  ScenarioType.OPTIMISTIC,   Decimal("7.0"),   Decimal("10.0")),
    # MSCI Europe
    ("MSCI Europe",    ScenarioType.ADVERSE,      Decimal("3.0"),   Decimal("14.0")),
    ("MSCI Europe",    ScenarioType.BASE,          Decimal("6.0"),   Decimal("13.0")),
    ("MSCI Europe",    ScenarioType.OPTIMISTIC,    Decimal("9.0"),   Decimal("12.0")),
    # MSCI EM IMI
    ("MSCI EM IMI",    ScenarioType.ADVERSE,       Decimal("2.0"),   Decimal("20.0")),
    ("MSCI EM IMI",    ScenarioType.BASE,           Decimal("7.0"),   Decimal("18.0")),
    ("MSCI EM IMI",    ScenarioType.OPTIMISTIC,     Decimal("12.0"),  Decimal("16.0")),
    # Japan
    ("Japan",          ScenarioType.ADVERSE,        Decimal("2.0"),   Decimal("15.0")),
    ("Japan",          ScenarioType.BASE,            Decimal("5.0"),   Decimal("14.0")),
    ("Japan",          ScenarioType.OPTIMISTIC,      Decimal("8.0"),   Decimal("13.0")),
    # Europe Defence
    ("Europe Defence", ScenarioType.ADVERSE,         Decimal("3.0"),   Decimal("16.0")),
    ("Europe Defence", ScenarioType.BASE,             Decimal("8.0"),   Decimal("15.0")),
    ("Europe Defence", ScenarioType.OPTIMISTIC,       Decimal("13.0"),  Decimal("14.0")),
    # Bitcoin
    ("Bitcoin",        ScenarioType.ADVERSE,          Decimal("-10.0"), Decimal("60.0")),
    ("Bitcoin",        ScenarioType.BASE,              Decimal("15.0"),  Decimal("50.0")),
    ("Bitcoin",        ScenarioType.OPTIMISTIC,        Decimal("40.0"),  Decimal("45.0")),
    # Cash
    ("Cash",           ScenarioType.ADVERSE,           Decimal("2.0"),   Decimal("0.5")),
    ("Cash",           ScenarioType.BASE,               Decimal("3.0"),   Decimal("0.3")),
    ("Cash",           ScenarioType.OPTIMISTIC,         Decimal("4.0"),   Decimal("0.2")),
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

# ── Global parameters: (key, value, value_type, category, description) ───────
PARAMETERS = [
    # portfolio
    (ParameterKey.CASH_BALANCE_EUR,         "0",           "decimal", ParameterCategory.PORTFOLIO,  "Balanç de caixa actual (actualitzat manualment o via sync)"),
    (ParameterKey.REBALANCE_THRESHOLD_PCT,  "5",           "decimal", ParameterCategory.PORTFOLIO,  "Desviació màxima del target weight abans de rebalancejar (%)"),
    (ParameterKey.PORTFOLIO_INCEPTION_DATE, "2022-01-01",  "date",    ParameterCategory.PORTFOLIO,  "Data d'inici del portfolio"),
    # simulation
    (ParameterKey.DEFAULT_HORIZON_MONTHS,   "36",          "integer", ParameterCategory.SIMULATION, "Horitzó de simulació per defecte (mesos)"),
    (ParameterKey.INFLATION_RATE_PCT,       "2.5",         "decimal", ParameterCategory.SIMULATION, "Taxa d'inflació anual estimada (%)"),
    (ParameterKey.DEFAULT_SCENARIO_TYPE,    ScenarioType.BASE, "string", ParameterCategory.SIMULATION, "Escenari per defecte (adverse/base/optimistic)"),
    # tax (Spain IRPF 2024)
    (ParameterKey.IRPF_BRACKET_1_LIMIT,     "6000",        "decimal", ParameterCategory.TAX,        "Primer tram IRPF capital: fins a 6.000€ → 19%"),
    (ParameterKey.IRPF_BRACKET_1_RATE,      "19",          "decimal", ParameterCategory.TAX,        "Tipus impositiu primer tram IRPF (%)"),
    (ParameterKey.IRPF_BRACKET_2_LIMIT,     "50000",       "decimal", ParameterCategory.TAX,        "Segon tram IRPF capital: 6.000–50.000€ → 21%"),
    (ParameterKey.IRPF_BRACKET_2_RATE,      "21",          "decimal", ParameterCategory.TAX,        "Tipus impositiu segon tram IRPF (%)"),
    (ParameterKey.IRPF_BRACKET_3_LIMIT,     "200000",      "decimal", ParameterCategory.TAX,        "Tercer tram IRPF capital: 50.000–200.000€ → 23%"),
    (ParameterKey.IRPF_BRACKET_3_RATE,      "23",          "decimal", ParameterCategory.TAX,        "Tipus impositiu tercer tram IRPF (%)"),
    (ParameterKey.IRPF_BRACKET_4_RATE,      "26",          "decimal", ParameterCategory.TAX,        "Tipus impositiu quart tram IRPF: >200.000€ (%)"),
    # personal
    (ParameterKey.MONTHLY_INCOME_NET,       "0",           "decimal", ParameterCategory.PERSONAL,   "Ingressos nets mensuals estimats (€)"),
    (ParameterKey.MONTHLY_EXPENSES_TARGET,  "0",           "decimal", ParameterCategory.PERSONAL,   "Despeses mensuals objectiu (€)"),
    (ParameterKey.EMERGENCY_FUND_MONTHS,    "6",           "integer", ParameterCategory.PERSONAL,   "Mesos de despeses que ha de cobrir el fons d'emergència"),
    # ui
    (ParameterKey.CURRENCY_DISPLAY,         "EUR",         "string",  ParameterCategory.UI,         "Moneda de visualització principal"),
    (ParameterKey.DATE_FORMAT,              "DD/MM/YYYY",  "string",  ParameterCategory.UI,         "Format de dates a la UI"),
    (ParameterKey.CHART_ANIMATION,          "true",        "boolean", ParameterCategory.UI,         "Activar animacions als gràfics"),
]

# ── Objectives ───────────────────────────────────────────────────────────────
OBJECTIVES = [
    {
        "key": ObjectiveKey.HOME_PURCHASE,
        "name": "Compra d'habitatge",
        "description": "Capital necessari per a l'entrada d'un pis",
        "objective_type": "purchase",
        "target_amount": Decimal("80000.00"),
        "target_date": date(2029, 12, 31),
        "funding_source": "portfolio",
        "priority": 1,
    },
    {
        "key": ObjectiveKey.EMERGENCY_FUND,
        "name": "Fons d'Emergència",
        "description": "6 mesos de despeses en liquiditat",
        "objective_type": "emergency",
        "target_amount": Decimal("15000.00"),
        "target_date": None,
        "funding_source": AssetType.CASH,
        "priority": 0,
    },
]

# ── Market Indices ────────────────────────────────────────────────────────────
MARKET_INDICES = [
    {"name": "S&P 500",       "ticker_yf": IndexTicker.SP500,          "display_name": "S&P 500",       "currency": "USD", "index_type": "equity",       "region": "US",     "is_default_benchmark": False},
    {"name": "MSCI World",    "ticker_yf": IndexTicker.MSCI_WORLD_ETF, "display_name": "MSCI World ETF", "currency": "USD", "index_type": "equity",       "region": "Global", "is_default_benchmark": True},
    {"name": "Euro Stoxx 50", "ticker_yf": IndexTicker.EURO_STOXX_50,  "display_name": "Euro Stoxx 50",  "currency": "EUR", "index_type": "equity",       "region": "Europe", "is_default_benchmark": False},
    {"name": "EURIBOR 12M",   "ticker_yf": IndexTicker.EURIBOR_12M,    "display_name": "EURIBOR 12M",    "currency": "EUR", "index_type": "fixed_income", "region": "Europe", "is_default_benchmark": False},
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
