"""
Tests de dades inicials (seed).
Comproven que el seed s'ha executat correctament i les dades clau existeixin.
"""

from core.constants import IndexTicker, ObjectiveKey, ParameterCategory, ParameterKey, ScenarioType


def test_assets_count(db_conn):
    """Han d'existir exactament 8 assets actius sembrats."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM assets WHERE is_active = true")
    assert count == 8, f"Nombre d'assets incorrecte: {count} (esperat 8)"


def test_all_assets_present(db_conn):
    """Tots els assets del portfolio han d'existir per nom."""
    rows = db_conn.fetch("SELECT display_name FROM assets ORDER BY sort_order")
    names = [r["display_name"] for r in rows]
    expected = ["MSCI World", "Physical Gold", "MSCI Europe", "MSCI EM IMI",
                "Japan", "Europe Defence", "Bitcoin", "Cash"]
    assert names == expected, f"Assets incorrectes: {names}"


def test_assets_target_weights_in_range(db_conn):
    """Els target weights dels assets actius han d'estar entre 80 i 100%."""
    total = db_conn.fetchval(
        "SELECT SUM(target_weight) FROM assets WHERE is_active = true AND target_weight IS NOT NULL"
    )
    assert 80 <= float(total) <= 100, f"Target weights fora de rang: {total}"


def test_assets_have_tickers(db_conn):
    """Els assets ETF i crypto han de tenir ticker_yf."""
    rows = db_conn.fetch(
        "SELECT display_name FROM assets WHERE asset_type IN ('etf', 'crypto') AND ticker_yf IS NULL"
    )
    missing = [r["display_name"] for r in rows]
    assert not missing, f"Assets sense ticker_yf: {missing}"


def test_scenarios_count(db_conn):
    """Han d'existir 3 escenaris × 8 assets = 24 escenaris."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM scenarios")
    assert count == 24, f"Nombre d'escenaris incorrecte: {count} (esperat 24)"


def test_scenarios_types(db_conn):
    """Els tres tipus d'escenari han d'existir."""
    rows = db_conn.fetch("SELECT DISTINCT scenario_type FROM scenarios ORDER BY scenario_type")
    types = [r["scenario_type"] for r in rows]
    expected_types = sorted([ScenarioType.ADVERSE, ScenarioType.BASE, ScenarioType.OPTIMISTIC])
    assert types == expected_types, f"Tipus d'escenari incorrectes: {types}"


def test_scenarios_annual_return_range(db_conn):
    """Tots els escenaris han de tenir annual_return entre -100 i 100."""
    count = db_conn.fetchval(
        "SELECT COUNT(*) FROM scenarios WHERE annual_return < -100 OR annual_return > 100"
    )
    assert count == 0, f"{count} escenaris amb annual_return fora de rang"


def test_contributions_exist(db_conn):
    """Han d'existir contribucions mensuals per als assets principals."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM contributions WHERE is_active = true")
    assert count >= 7, f"Contribucions insuficients: {count} (mínim 7)"


def test_contributions_amounts_positive(db_conn):
    """Totes les contribucions han de tenir import positiu."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM contributions WHERE amount <= 0")
    assert count == 0, f"{count} contribucions amb import no positiu"


def test_parameters_exist(db_conn):
    """Els paràmetres globals crítics han d'existir."""
    critical_params = [
        ParameterKey.CASH_BALANCE_EUR,
        ParameterKey.REBALANCE_THRESHOLD_PCT,
        ParameterKey.DEFAULT_HORIZON_MONTHS,
        ParameterKey.INFLATION_RATE_PCT,
        ParameterKey.IRPF_BRACKET_1_RATE,
        ParameterKey.IRPF_BRACKET_2_RATE,
    ]
    rows = db_conn.fetch("SELECT key FROM parameters")
    existing = {r["key"] for r in rows}
    missing = [p for p in critical_params if p not in existing]
    assert not missing, f"Paràmetres que falten: {missing}"


def test_parameters_have_valid_categories(db_conn):
    """Tots els paràmetres han d'estar en una categoria vàlida."""
    valid = {str(c) for c in ParameterCategory}
    rows = db_conn.fetch("SELECT DISTINCT category FROM parameters WHERE category IS NOT NULL")
    db_cats = {r["category"] for r in rows}
    invalid = db_cats - valid
    assert not invalid, f"Categories de paràmetre no vàlides: {invalid}"


def test_objectives_exist(db_conn):
    """Han d'existir almenys els 2 objectius sembrats."""
    rows = db_conn.fetch("SELECT key FROM objectives")
    keys = {r["key"] for r in rows}
    assert ObjectiveKey.EMERGENCY_FUND in keys, f"Objectiu '{ObjectiveKey.EMERGENCY_FUND}' no trobat"
    assert ObjectiveKey.HOME_PURCHASE in keys, f"Objectiu '{ObjectiveKey.HOME_PURCHASE}' no trobat"


def test_objectives_target_amounts_positive(db_conn):
    """Tots els objectius han de tenir target_amount positiu."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM objectives WHERE target_amount <= 0")
    assert count == 0, f"{count} objectius amb target_amount no positiu"


def test_market_indices_exist(db_conn):
    """Han d'existir els índexs de mercat sembrats."""
    rows = db_conn.fetch("SELECT ticker_yf FROM market_indices")
    tickers = {r["ticker_yf"] for r in rows}
    assert IndexTicker.SP500 in tickers, "S&P 500 no trobat"
    assert IndexTicker.MSCI_WORLD_ETF in tickers, "MSCI World ETF no trobat"


def test_dashboard_widgets_exist(db_conn):
    """Han d'existir els widgets de dashboard sembrats."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM dashboard_widgets")
    assert count >= 8, f"Widgets de dashboard insuficients: {count}"


def test_bitcoin_scenario_has_high_volatility(db_conn):
    """Bitcoin ha de tenir volatilitat > 40% en l'escenari base."""
    row = db_conn.fetchrow(
        "SELECT s.volatility FROM scenarios s "
        "JOIN assets a ON a.id = s.asset_id "
        f"WHERE a.display_name = 'Bitcoin' AND s.scenario_type = '{ScenarioType.BASE}'"
    )
    assert row is not None, "No s'ha trobat l'escenari base de Bitcoin"
    assert float(row["volatility"]) > 40, f"Volatilitat de Bitcoin massa baixa: {row['volatility']}"
