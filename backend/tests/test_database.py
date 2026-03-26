"""
Tests de connexió i estructura de la base de dades.
Comproven que totes les taules existeixin i que la connexió funcioni correctament.
"""

EXPECTED_TABLES = sorted([
    # portfolio
    "assets", "contributions", "extraordinary_contributions",
    "transactions", "tax_lots", "price_history", "dividends", "corporate_actions",
    # config
    "scenarios", "objectives", "parameters", "parameter_history",
    # sync
    "import_batches", "mw_accounts", "mw_categories", "mw_payees",
    "mw_transactions", "recurring_expenses",
    # simulation
    "simulations", "simulation_params", "simulation_events",
    "simulation_results", "monte_carlo_runs",
    # networth
    "net_worth_snapshots", "asset_snapshots", "net_worth_milestones",
    # analytics
    "budgets", "monthly_summaries", "income_sources",
    "income_records", "spending_patterns",
    # market
    "market_indices", "market_index_data", "exchange_rates", "price_fetch_logs",
    # history
    "tax_reports", "realized_gains",
    # realestate
    "properties", "property_valuations", "mortgages",
    "mortgage_payments", "rental_income", "property_expenses",
    # pensions
    "pension_plans", "pension_contributions",
    "pension_valuations", "social_security_estimates",
    # credit
    "credit_accounts", "credit_statements", "credit_payments",
    # alerts
    "alert_rules", "alert_history",
    # system
    "audit_log", "api_keys", "app_versions", "scheduled_tasks",
    # preferences
    "user_preferences", "dashboard_widgets", "report_templates",
    # tags
    "tags", "transaction_tags", "mw_transaction_tags", "notes", "note_tags",
])


def test_database_connection(db_conn):
    """La BD respon a consultes bàsiques."""
    result = db_conn.fetchval("SELECT 1")
    assert result == 1


def test_postgresql_version(db_conn):
    """Verificar que estem connectats a PostgreSQL 15+."""
    version_num = db_conn.fetchval("SELECT current_setting('server_version_num')::int")
    assert version_num >= 150000, f"PostgreSQL version massa antiga: {version_num}"


def test_database_name(db_conn):
    """Verificar que estem connectats a la BD correcta."""
    db_name = db_conn.fetchval("SELECT current_database()")
    assert db_name == "wealthpilot", f"BD incorrecta: {db_name}"


def test_all_tables_exist(db_conn):
    """Totes les taules de l'esquema han d'existir."""
    rows = db_conn.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    existing = {r["table_name"] for r in rows}
    missing = [t for t in EXPECTED_TABLES if t not in existing]
    assert not missing, f"Taules que falten a la BD: {missing}"


def test_table_count(db_conn):
    """Han d'existir almenys 64 taules (sense comptar alembic_version)."""
    count = db_conn.fetchval(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
        "AND table_name != 'alembic_version'"
    )
    assert count >= 64, f"Nombre de taules insuficient: {count} (mínim 64)"


def test_alembic_migrations_applied(db_conn):
    """Alembic ha d'haver aplicat almenys una migració."""
    count = db_conn.fetchval("SELECT COUNT(*) FROM alembic_version")
    assert count >= 1, "Cap migració d'Alembic aplicada"


def test_indexes_exist(db_conn):
    """Verificar que existeixen els índexs principals per a performance."""
    critical_indexes = [
        "idx_transactions_date",
        "idx_transactions_asset_id",
        "idx_price_history_asset_date",
        "idx_networth_date",
        "idx_audit_log_date",
        "idx_mw_tx_date",
    ]
    rows = db_conn.fetch("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
    existing = {r["indexname"] for r in rows}
    missing = [i for i in critical_indexes if i not in existing]
    assert not missing, f"Índexs que falten: {missing}"


def test_unique_constraints_exist(db_conn):
    """Verificar que existeixen les constraints úniques crítiques."""
    rows = db_conn.fetch(
        "SELECT conname FROM pg_constraint WHERE contype = 'u' "
        "AND conrelid IN (SELECT oid FROM pg_class WHERE relnamespace = 'public'::regnamespace)"
    )
    constraints = {r["conname"] for r in rows}
    critical = ["uq_transaction", "uq_price_history", "uq_scenario", "uq_networth_date"]
    missing = [c for c in critical if c not in constraints]
    assert not missing, f"Constraints úniques que falten: {missing}"


def test_assets_table_columns(db_conn):
    """La taula assets ha de tenir les columnes mínimes requerides."""
    rows = db_conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'assets'"
    )
    columns = {r["column_name"] for r in rows}
    required = {"id", "name", "display_name", "asset_type", "currency", "target_weight", "is_active"}
    missing = required - columns
    assert not missing, f"Columnes que falten a 'assets': {missing}"


def test_transactions_table_structure(db_conn):
    """La taula transactions ha de tenir les columnes per a cost basis FIFO."""
    rows = db_conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'transactions'"
    )
    columns = {r["column_name"] for r in rows}
    required = {"id", "mw_date", "asset_id", "tx_type", "amount_eur", "shares", "price_per_share", "fees_eur"}
    missing = required - columns
    assert not missing, f"Columnes que falten a 'transactions': {missing}"
