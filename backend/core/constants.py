"""
Domain constants — font única de veritat per a valors de string que apareixen
a través de models, serveis, seeds i tests.

Regles d'ús:
- StrEnum per a valors que es guarden a la BD o s'usen en comparacions Python.
- Classes planes per a identificadors externs (tickers, codis de tercers).
- MAI hardcodejar aquests strings en cap altre fitxer — sempre importar d'aquí.
- Quan Yahoo Finance canvia un ticker, actualitzar NOMÉS Ticker / IndexTicker.
"""

from enum import StrEnum


# ─────────────────────────────────────────────────────────────────────────────
#  Assets
# ─────────────────────────────────────────────────────────────────────────────

class AssetType(StrEnum):
    """Tipus d'actiu d'inversió. Guardat a assets.asset_type."""
    ETF       = "etf"
    CRYPTO    = "crypto"
    CASH      = "cash"
    STOCK     = "stock"
    BOND      = "bond"
    COMMODITY = "commodity"


class AssetClass(StrEnum):
    """Classe d'actiu / bucket d'assignació. Guardat a assets.asset_class."""
    EQUITY       = "equity"
    FIXED_INCOME = "fixed_income"
    ALTERNATIVE  = "alternative"
    CASH         = "cash"


# ─────────────────────────────────────────────────────────────────────────────
#  Scenarios
# ─────────────────────────────────────────────────────────────────────────────

class ScenarioType(StrEnum):
    """Tipus d'escenari de simulació. Guardat a scenarios.scenario_type."""
    ADVERSE    = "adverse"
    BASE       = "base"
    OPTIMISTIC = "optimistic"


# ─────────────────────────────────────────────────────────────────────────────
#  Parameters
# ─────────────────────────────────────────────────────────────────────────────

class ParameterCategory(StrEnum):
    """Categoria d'un paràmetre global. Guardat a parameters.category."""
    PORTFOLIO  = "portfolio"
    SIMULATION = "simulation"
    TAX        = "tax"
    PERSONAL   = "personal"
    UI         = "ui"


class ParameterKey:
    """
    Claus de la taula parameters. Usar com: WHERE key = ParameterKey.X
    Definir aquí totes les claus per evitar magic strings als serveis i tests.
    """
    # Portfolio
    CASH_BALANCE_EUR         = "cash_balance_eur"
    REBALANCE_THRESHOLD_PCT  = "rebalance_threshold_pct"
    PORTFOLIO_INCEPTION_DATE = "portfolio_inception_date"
    # Simulation
    DEFAULT_HORIZON_MONTHS   = "default_horizon_months"
    INFLATION_RATE_PCT       = "inflation_rate_pct"
    DEFAULT_SCENARIO_TYPE    = "default_scenario_type"
    # Tax (Spain IRPF 2024)
    IRPF_BRACKET_1_LIMIT     = "irpf_bracket_1_limit"
    IRPF_BRACKET_1_RATE      = "irpf_bracket_1_rate"
    IRPF_BRACKET_2_LIMIT     = "irpf_bracket_2_limit"
    IRPF_BRACKET_2_RATE      = "irpf_bracket_2_rate"
    IRPF_BRACKET_3_LIMIT     = "irpf_bracket_3_limit"
    IRPF_BRACKET_3_RATE      = "irpf_bracket_3_rate"
    IRPF_BRACKET_4_RATE      = "irpf_bracket_4_rate"
    # Personal
    MONTHLY_INCOME_NET       = "monthly_income_net"
    MONTHLY_EXPENSES_TARGET  = "monthly_expenses_target"
    EMERGENCY_FUND_MONTHS    = "emergency_fund_months"
    # UI
    CURRENCY_DISPLAY         = "currency_display"
    DATE_FORMAT              = "date_format"
    CHART_ANIMATION          = "chart_animation"


# ─────────────────────────────────────────────────────────────────────────────
#  Objectives
# ─────────────────────────────────────────────────────────────────────────────

class ObjectiveKey:
    """Claus de la taula objectives. Guardat a objectives.key."""
    HOME_PURCHASE  = "home_purchase"
    EMERGENCY_FUND = "emergency_fund"


# ─────────────────────────────────────────────────────────────────────────────
#  Market / Fetch
# ─────────────────────────────────────────────────────────────────────────────

class FetchStatus(StrEnum):
    """Estat d'una operació de descàrrega de preus. Guardat a price_fetch_logs.status."""
    SUCCESS      = "success"
    FAILED       = "failed"
    RATE_LIMITED = "rate_limited"
    STALE        = "stale"


# ─────────────────────────────────────────────────────────────────────────────
#  Tickers — font única de veritat
#  Si Yahoo Finance canvia un símbol, actualitzar AQUÍ i en cap altre lloc.
# ─────────────────────────────────────────────────────────────────────────────

class Ticker:
    """
    Tickers de Yahoo Finance per als assets del portfolio.
    Qualsevol codi que necessiti un ticker ha de referència aquesta classe.
    """
    MSCI_WORLD     = "IWDA.AS"
    PHYSICAL_GOLD  = "PHAU.L"
    MSCI_EUROPE    = "IMAE.AS"
    MSCI_EM_IMI    = "EMIM.AS"
    JAPAN          = "CSJP.AS"
    EUROPE_DEFENCE = "WDEF.MI"
    BITCOIN        = "BTC-EUR"


class IndexTicker:
    """
    Tickers de Yahoo Finance per als índexs de mercat de referència.
    Referenciats al seed i als tests — un sol canvi aquí actualitza tot.
    """
    SP500          = "^GSPC"
    MSCI_WORLD_ETF = "URTH"
    EURO_STOXX_50  = "^STOXX50E"
    EURIBOR_12M    = "^IRX"
