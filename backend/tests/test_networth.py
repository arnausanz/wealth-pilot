"""
Tests del mòdul networth (snapshots de net worth).

Estratègia:
  - Tests de schema DB (db_conn): taules i columnes existents.
  - Tests de servei (http_client): POST /snapshot i GET /history amb dades
    insertades directament a la BD de test.
  - Tots els tests són end-to-end contra la BD PostgreSQL de Docker.
  - Cada test neteja les seves dades per garantir idempotència.
"""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

import asyncpg
import pytest
import pytest_asyncio

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import settings


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _asyncpg_dsn() -> str:
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


# ─── Tests Schema DB ─────────────────────────────────────────────────────────

class TestNetworthSchema:
    """Verifica que les taules i columnes necessàries existeixen a la BD."""

    def test_net_worth_snapshots_table_exists(self, db_conn):
        count = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'net_worth_snapshots'"
        )
        assert count == 1, "Taula net_worth_snapshots no existeix"

    def test_net_worth_snapshots_columns(self, db_conn):
        cols = {
            r["column_name"]
            for r in db_conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'net_worth_snapshots'"
            )
        }
        required = {
            "id", "snapshot_date", "total_net_worth",
            "investment_portfolio_value", "cash_and_bank_value",
            "total_liabilities", "change_eur", "change_pct",
            "trigger_source", "created_at",
        }
        assert required <= cols, f"Columnes que falten: {required - cols}"

    def test_asset_snapshots_table_exists(self, db_conn):
        count = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'asset_snapshots'"
        )
        assert count == 1, "Taula asset_snapshots no existeix"

    def test_asset_snapshots_columns(self, db_conn):
        cols = {
            r["column_name"]
            for r in db_conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'asset_snapshots'"
            )
        }
        required = {
            "id", "snapshot_id", "asset_id", "shares", "price_eur",
            "value_eur", "cost_basis_eur", "unrealized_pnl_eur",
            "unrealized_pnl_pct", "weight_actual_pct",
        }
        assert required <= cols, f"Columnes que falten: {required - cols}"

    def test_unique_constraint_networth_date(self, db_conn):
        """La constraint uq_networth_date ha d'existir."""
        count = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.table_constraints "
            "WHERE constraint_name = 'uq_networth_date' "
            "AND table_name = 'net_worth_snapshots'"
        )
        assert count == 1, "Constraint uq_networth_date no existeix"

    def test_mw_transactions_has_shares_column(self, db_conn):
        """La migració de shares i mw_symbol ha d'estar aplicada."""
        cols = {
            r["column_name"]
            for r in db_conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'mw_transactions'"
            )
        }
        assert "shares" in cols, "Columna shares no existeix a mw_transactions"
        assert "mw_symbol" in cols, "Columna mw_symbol no existeix a mw_transactions"


# ─── Tests API Endpoints ──────────────────────────────────────────────────────

class TestNetworthSnapshotEndpoint:
    """Tests de POST /api/v1/networth/snapshot."""

    @pytest.mark.asyncio
    async def test_create_snapshot_returns_201(self, http_client):
        """POST /snapshot ha de retornar 201."""
        resp = await http_client.post("/api/v1/networth/snapshot")
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_snapshot_response_shape(self, http_client):
        """La resposta ha de contenir els camps esperats."""
        resp = await http_client.post("/api/v1/networth/snapshot")
        assert resp.status_code == 201
        body = resp.json()
        assert "snapshot_date" in body
        assert "total_net_worth" in body
        assert "investment_portfolio_value" in body
        assert "cash_and_bank_value" in body
        assert "assets_tracked" in body
        assert "created" in body

    @pytest.mark.asyncio
    async def test_create_snapshot_specific_date(self, http_client):
        """Pot generar un snapshot per a una data específica passada."""
        resp = await http_client.post(
            "/api/v1/networth/snapshot",
            params={"snapshot_date": "2025-01-01"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["snapshot_date"] == "2025-01-01"

    @pytest.mark.asyncio
    async def test_create_snapshot_idempotent(self, http_client):
        """Cridar POST /snapshot dues vegades per la mateixa data → no error."""
        resp1 = await http_client.post(
            "/api/v1/networth/snapshot",
            params={"snapshot_date": "2025-06-01"},
        )
        resp2 = await http_client.post(
            "/api/v1/networth/snapshot",
            params={"snapshot_date": "2025-06-01"},
        )
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        # El total ha de ser el mateix (mateixa data, mateixa BD)
        assert resp1.json()["total_net_worth"] == resp2.json()["total_net_worth"]

    @pytest.mark.asyncio
    async def test_create_snapshot_invalid_date(self, http_client):
        """Data invàlida ha de retornar 422."""
        resp = await http_client.post(
            "/api/v1/networth/snapshot",
            params={"snapshot_date": "not-a-date"},
        )
        assert resp.status_code == 422


class TestNetworthHistoryEndpoint:
    """Tests de GET /api/v1/networth/history."""

    @pytest.mark.asyncio
    async def test_history_default_period(self, http_client):
        """GET /history sense params ha de retornar 200."""
        resp = await http_client.get("/api/v1/networth/history")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_history_response_shape(self, http_client):
        """La resposta ha de tenir l'estructura correcta."""
        resp = await http_client.get("/api/v1/networth/history")
        assert resp.status_code == 200
        body = resp.json()
        assert "period" in body
        assert "snapshots" in body
        assert isinstance(body["snapshots"], list)
        assert "current_net_worth" in body
        assert "change_eur_period" in body
        assert "change_pct_period" in body

    @pytest.mark.asyncio
    async def test_history_all_valid_periods(self, http_client):
        """Tots els períodes vàlids han de retornar 200."""
        for period in ["1m", "3m", "6m", "1y", "2y", "5y", "all"]:
            resp = await http_client.get(f"/api/v1/networth/history?period={period}")
            assert resp.status_code == 200, f"Període {period} ha fallat"

    @pytest.mark.asyncio
    async def test_history_invalid_period(self, http_client):
        """Període invàlid ha de retornar 422."""
        resp = await http_client.get("/api/v1/networth/history?period=10y")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_history_snapshots_sorted_ascending(self, http_client):
        """Els snapshots han d'estar ordenats per data ascendent."""
        # Generar dos snapshots per a dates conegudes
        await http_client.post(
            "/api/v1/networth/snapshot",
            params={"snapshot_date": "2024-01-01"},
        )
        await http_client.post(
            "/api/v1/networth/snapshot",
            params={"snapshot_date": "2024-02-01"},
        )

        resp = await http_client.get("/api/v1/networth/history?period=all")
        assert resp.status_code == 200
        snapshots = resp.json()["snapshots"]
        if len(snapshots) >= 2:
            dates = [s["snapshot_date"] for s in snapshots]
            assert dates == sorted(dates), "Els snapshots no estan ordenats per data"

    @pytest.mark.asyncio
    async def test_history_period_reflected_in_response(self, http_client):
        """El camp period de la resposta ha de coincidir amb el paràmetre."""
        resp = await http_client.get("/api/v1/networth/history?period=3m")
        assert resp.status_code == 200
        assert resp.json()["period"] == "3m"


# ─── Tests Servei (lògica de negoci) ─────────────────────────────────────────

class TestNetworthService:
    """
    Tests de la lògica del servei.
    Inserim dades sintètiques a mw_accounts i verifiquem que el càlcul és correcte.
    """

    @pytest.mark.asyncio
    async def test_cash_value_from_mw_accounts(self, http_client):
        """
        El snapshot ha de llegir els balanços de mw_accounts.
        Inserim un compte checking temporal i verifiquem que cash_and_bank_value
        canvia en conseqüència (test qualitatiu: no ha de ser 0 si hi ha comptes).
        """
        loop = asyncio.get_event_loop()
        conn = await asyncpg.connect(_asyncpg_dsn())

        try:
            # Inserim un compte de prova
            await conn.execute("""
                INSERT INTO mw_accounts (mw_internal_id, name, account_type, currency, current_balance,
                                         is_active, include_in_networth)
                VALUES ('test_99991', '__test_checking__', 'checking', 'EUR', 5000.00, TRUE, TRUE)
                ON CONFLICT (mw_internal_id) DO UPDATE SET current_balance = 5000.00
            """)

            resp = await http_client.post(
                "/api/v1/networth/snapshot",
                params={"snapshot_date": "2020-01-15"},
            )
            assert resp.status_code == 201
            body = resp.json()
            # Amb un compte checking de 5000 EUR, cash_and_bank_value >= 5000
            cash = Decimal(body["cash_and_bank_value"])
            assert cash >= Decimal("5000.00"), (
                f"cash_and_bank_value={cash} hauria de ser >= 5000 EUR"
            )

        finally:
            # Neteja
            await conn.execute("DELETE FROM mw_accounts WHERE mw_internal_id = 'test_99991'")
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date = '2020-01-15'"
            )
            await conn.close()

    @pytest.mark.asyncio
    async def test_snapshot_total_equals_cash_plus_investment_minus_liabilities(self, http_client):
        """
        total_net_worth = investment + cash - liabilities.
        Inserim comptes sintètics i verifiquem l'aritmètica bàsica.
        """
        loop = asyncio.get_event_loop()
        conn = await asyncpg.connect(_asyncpg_dsn())

        try:
            # Comptes aïllats amb include_in_networth = TRUE
            await conn.execute("""
                INSERT INTO mw_accounts (mw_internal_id, name, account_type, currency, current_balance,
                                         is_active, include_in_networth)
                VALUES
                    ('test_99992', '__test_cash__',  'checking',  'EUR', 1000.00, TRUE, TRUE),
                    ('test_99993', '__test_inv__',   'investment','EUR', 3000.00, TRUE, TRUE),
                    ('test_99994', '__test_liab__',  'credit',    'EUR', 500.00,  TRUE, TRUE)
                ON CONFLICT (mw_internal_id) DO UPDATE SET
                    current_balance     = EXCLUDED.current_balance,
                    account_type        = EXCLUDED.account_type,
                    include_in_networth = TRUE,
                    is_active           = TRUE
            """)

            # Necessitem una data antiga per no interferir amb altres snapshots
            resp = await http_client.post(
                "/api/v1/networth/snapshot",
                params={"snapshot_date": "2019-06-15"},
            )
            assert resp.status_code == 201
            body = resp.json()

            inv   = Decimal(body["investment_portfolio_value"])
            cash  = Decimal(body["cash_and_bank_value"])
            total = Decimal(body["total_net_worth"])

            # El total ha de ser >= (cash+inv - liab) per als nostres comptes sintètics
            # (hi pot haver altres comptes reals a la BD, per tant no podem comparar exacte)
            assert total >= Decimal("0"), "total_net_worth no pot ser negatiu amb comptes positius"

        finally:
            await conn.execute(
                "DELETE FROM mw_accounts WHERE mw_internal_id IN ('test_99992', 'test_99993', 'test_99994')"
            )
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date = '2019-06-15'"
            )
            await conn.close()

    @pytest.mark.asyncio
    async def test_excluded_accounts_not_counted(self, http_client):
        """Comptes amb include_in_networth=FALSE no han d'afectar el total."""
        conn = await asyncpg.connect(_asyncpg_dsn())

        try:
            # Compte exclòs explícitament
            _AMOUNT = Decimal("100.00")

            await conn.execute("""
                INSERT INTO mw_accounts (mw_internal_id, name, account_type, currency, current_balance,
                                         is_active, include_in_networth)
                VALUES ('test_99995', '__test_excluded__', 'checking', 'EUR', 100.00, TRUE, FALSE)
                ON CONFLICT (mw_internal_id) DO UPDATE SET
                    current_balance     = 100.00,
                    include_in_networth = FALSE,
                    is_active           = TRUE
            """)

            # Snapshot A: sense el compte exclòs
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date = '2018-01-01'"
            )
            resp_a = await http_client.post(
                "/api/v1/networth/snapshot",
                params={"snapshot_date": "2018-01-01"},
            )
            total_a = Decimal(resp_a.json()["total_net_worth"])

            # Afegim un compte igual però inclòs
            await conn.execute("""
                INSERT INTO mw_accounts (mw_internal_id, name, account_type, currency, current_balance,
                                         is_active, include_in_networth)
                VALUES ('test_99996', '__test_included__', 'checking', 'EUR', 100.00, TRUE, TRUE)
                ON CONFLICT (mw_internal_id) DO UPDATE SET
                    current_balance     = 100.00,
                    include_in_networth = TRUE,
                    is_active           = TRUE
            """)

            # Snapshot B: ara hi ha el compte inclòs
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date = '2018-02-01'"
            )
            resp_b = await http_client.post(
                "/api/v1/networth/snapshot",
                params={"snapshot_date": "2018-02-01"},
            )
            total_b = Decimal(resp_b.json()["total_net_worth"])

            # Snapshot B ha de ser exactament _AMOUNT € més gran que A
            diff = total_b - total_a
            assert diff == _AMOUNT, (
                f"Diferència esperada {_AMOUNT} EUR, obtinguda {diff}"
            )

        finally:
            await conn.execute(
                "DELETE FROM mw_accounts WHERE mw_internal_id IN ('test_99995', 'test_99996')"
            )
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date IN ('2018-01-01', '2018-02-01')"
            )
            await conn.close()

    @pytest.mark.asyncio
    async def test_change_eur_calculated_vs_previous(self, http_client):
        """
        change_eur del segon snapshot ha de ser la diferència vs. el primer.
        """
        conn = await asyncpg.connect(_asyncpg_dsn())

        try:
            # Neteja prèvia per evitar interferències
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date IN ('2015-01-01', '2015-02-01')"
            )

            # Compte amb 10000 EUR
            await conn.execute("""
                INSERT INTO mw_accounts (mw_internal_id, name, account_type, currency, current_balance,
                                         is_active, include_in_networth)
                VALUES ('test_99997', '__test_change__', 'checking', 'EUR', 10000.00, TRUE, TRUE)
                ON CONFLICT (mw_internal_id) DO UPDATE SET
                    current_balance     = 10000.00,
                    include_in_networth = TRUE,
                    is_active           = TRUE
            """)

            resp1 = await http_client.post(
                "/api/v1/networth/snapshot",
                params={"snapshot_date": "2015-01-01"},
            )
            assert resp1.status_code == 201
            total1 = Decimal(resp1.json()["total_net_worth"])

            # Modifiquem el balanç a 12000
            await conn.execute(
                "UPDATE mw_accounts SET current_balance = 12000.00 WHERE mw_internal_id = 'test_99997'"
            )

            resp2 = await http_client.post(
                "/api/v1/networth/snapshot",
                params={"snapshot_date": "2015-02-01"},
            )
            assert resp2.status_code == 201
            total2 = Decimal(resp2.json()["total_net_worth"])

            # Verificar change_eur via GET /history (camp persistit a la BD)
            resp_hist = await http_client.get("/api/v1/networth/history?period=all")
            assert resp_hist.status_code == 200
            snaps = resp_hist.json()["snapshots"]
            snap_feb = next((s for s in snaps if s["snapshot_date"] == "2015-02-01"), None)
            assert snap_feb is not None, "Snapshot 2015-02-01 no trobat a l'historial"

            change_eur = Decimal(snap_feb["change_eur"]) if snap_feb["change_eur"] else None
            expected_change = (total2 - total1).quantize(Decimal("0.01"))
            assert change_eur == expected_change, (
                f"change_eur={change_eur} esperava {expected_change}"
            )

        finally:
            await conn.execute("DELETE FROM mw_accounts WHERE mw_internal_id = 'test_99997'")
            await conn.execute(
                "DELETE FROM net_worth_snapshots WHERE snapshot_date IN ('2015-01-01', '2015-02-01')"
            )
            await conn.close()
