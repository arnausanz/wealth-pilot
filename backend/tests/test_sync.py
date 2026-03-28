"""
Tests del mòdul sync (parser MoneyWiz).

Estratègia:
  - Cap test utilitza el ZIP real de MoneyWiz (dades personals, gitignored).
  - Els tests creen un SQLite sintètic en memòria amb el schema mínim de MoneyWiz
    i el comprimeixen en un ZIP temporal.
  - Tests síncrons (db_conn) per a taules i schema.
  - Tests asíncrons (http_client) per a endpoints, usant el ZIP sintètic.
"""

import io
import sqlite3
import zipfile
from datetime import datetime, timedelta, date, timezone

import pytest


# ─── Fixtures de dades sintètiques ───────────────────────────────────────────

def _apple_ts(d: date) -> float:
    """Converteix una data Python al timestamp de Core Data de MoneyWiz."""
    epoch = datetime(2001, 1, 1, tzinfo=timezone.utc)
    dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return (dt - epoch).total_seconds()


def _build_moneywiz_sqlite() -> bytes:
    """
    Crea un SQLite de MoneyWiz mínim en memòria amb:
    - 2 comptes bancaris (BankChequeAccount + InvestmentAccount)
    - 3 categories (2 arrel + 1 filla)
    - 4 transaccions (1 despesa, 1 ingrés, 1 transferència, 1 inversió)
    Retorna els bytes del fitxer SQLite.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE ZSYNCOBJECT (
            Z_PK INTEGER PRIMARY KEY,
            Z_ENT INTEGER,
            Z_OPT INTEGER,
            ZNAME TEXT, ZNAME2 TEXT, ZNAME3 TEXT, ZNAME4 TEXT,
            ZCURRENCYNAME TEXT, ZCURRENCYNAME2 TEXT,
            ZBALLANCE REAL, ZOPENINGBALANCE REAL,
            ZARCHIVED INTEGER, ZINCLUDEINNETWORTH INTEGER,
            ZTYPE2 INTEGER, ZPARENTCATEGORY INTEGER,
            ZDATE1 REAL, ZAMOUNT1 REAL,
            ZNOTES1 TEXT, ZACCOUNT2 INTEGER,
            ZSTATUS1 INTEGER,
            ZNUMBEROFSHARES REAL, ZSYMBOL1 TEXT
        );
        CREATE TABLE ZCATEGORYASSIGMENT (
            Z_PK INTEGER PRIMARY KEY,
            Z_ENT INTEGER,
            Z_OPT INTEGER,
            ZASSIGMENTNUMBER INTEGER,
            ZCATEGORY INTEGER,
            ZTRANSACTION INTEGER,
            ZAMOUNT REAL
        );
        CREATE TABLE Z_PRIMARYKEY (
            Z_ENT INTEGER PRIMARY KEY,
            Z_NAME TEXT,
            Z_SUPER INTEGER,
            Z_MAX INTEGER
        );
    """)

    # Entitats de referència
    conn.executemany("INSERT INTO Z_PRIMARYKEY VALUES (?,?,?,?)", [
        (10, "BankChequeAccount", 9, 2),
        (15, "InvestmentAccount", 9, 1),
        (19, "Category", 0, 3),
        (37, "DepositTransaction", 36, 1),
        (40, "InvestmentBuyTransaction", 36, 1),
        (45, "TransferDepositTransaction", 36, 1),
        (46, "TransferWithdrawTransaction", 36, 1),
        (47, "WithdrawTransaction", 36, 4),
    ])

    # Comptes: Z_ENT 10 = BankChequeAccount, Z_ENT 15 = InvestmentAccount
    conn.executemany(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZNAME, ZCURRENCYNAME, ZBALLANCE, ZARCHIVED, ZINCLUDEINNETWORTH) VALUES (?,?,?,?,?,?,?)",
        [
            (1, 10, "Compte Corrent", "EUR", 1500.00, 0, 1),
            (2, 15, "Trade Republic", "EUR", 8000.00, 0, 1),
        ],
    )

    # Categories: Z_ENT 19
    # 100 = Casa (arrel, expense)
    # 101 = Roba (arrel, expense)
    # 102 = Súper (filla de Casa, expense)
    conn.executemany(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZNAME2, ZTYPE2, ZPARENTCATEGORY) VALUES (?,?,?,?,?)",
        [
            (100, 19, "Casa",  1, None),
            (101, 19, "Roba",  1, None),
            (102, 19, "Súper", 1, 100),
        ],
    )

    # Transaccions
    d1 = _apple_ts(date(2025, 1, 15))
    d2 = _apple_ts(date(2025, 2, 10))
    d3 = _apple_ts(date(2025, 3, 5))
    d4 = _apple_ts(date(2025, 4, 1))
    conn.execute(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZDATE1, ZAMOUNT1, ZCURRENCYNAME2, ZNOTES1, ZACCOUNT2, ZSTATUS1) VALUES (?,?,?,?,?,?,?,?)",
        (200, 47, d1, -45.50, "EUR", "Mercadona", 1, 0),  # expense
    )
    conn.execute(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZDATE1, ZAMOUNT1, ZCURRENCYNAME2, ZNOTES1, ZACCOUNT2, ZSTATUS1) VALUES (?,?,?,?,?,?,?,?)",
        (201, 37, d2, 2500.0, "EUR", "Nòmina", 1, 1),   # income
    )
    conn.execute(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZDATE1, ZAMOUNT1, ZCURRENCYNAME2, ZNOTES1, ZACCOUNT2, ZSTATUS1) VALUES (?,?,?,?,?,?,?,?)",
        (202, 45, d3, 300.0, "EUR", None, 1, 0),          # transfer_in
    )
    conn.execute(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZDATE1, ZAMOUNT1, ZCURRENCYNAME2, ZNOTES1, ZACCOUNT2, ZSTATUS1, ZNUMBEROFSHARES, ZSYMBOL1) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (203, 40, d4, -500.0, "EUR", "EUNL buy", 2, 0, 4.5, "EUNL"),  # investment_buy
    )

    # Assignació de categories per a la despesa (Z_PK 200 → categoria 102)
    conn.execute(
        "INSERT INTO ZCATEGORYASSIGMENT (Z_PK, Z_ENT, ZASSIGMENTNUMBER, ZCATEGORY, ZTRANSACTION, ZAMOUNT) VALUES (?,?,?,?,?,?)",
        (300, 2, 0, 102, 200, -45.50),
    )
    conn.commit()

    # Exportar a bytes
    buf = io.BytesIO()
    for line in conn.iterdump():
        pass  # iterdump no és el que volem; usem backup API
    conn.close()

    # Escriure el SQLite a un fitxer temporal per llegir-ne els bytes
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        tmp_path = f.name

    conn2 = sqlite3.connect(":memory:")
    conn2.executescript("""
        CREATE TABLE ZSYNCOBJECT (
            Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER,
            ZNAME TEXT, ZNAME2 TEXT, ZNAME3 TEXT, ZNAME4 TEXT,
            ZCURRENCYNAME TEXT, ZCURRENCYNAME2 TEXT,
            ZBALLANCE REAL, ZOPENINGBALANCE REAL,
            ZARCHIVED INTEGER, ZINCLUDEINNETWORTH INTEGER,
            ZTYPE2 INTEGER, ZPARENTCATEGORY INTEGER,
            ZDATE1 REAL, ZAMOUNT1 REAL,
            ZNOTES1 TEXT, ZACCOUNT2 INTEGER, ZSTATUS1 INTEGER,
            ZNUMBEROFSHARES REAL, ZSYMBOL1 TEXT
        );
        CREATE TABLE ZCATEGORYASSIGMENT (
            Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER,
            ZASSIGMENTNUMBER INTEGER, ZCATEGORY INTEGER,
            ZTRANSACTION INTEGER, ZAMOUNT REAL
        );
        CREATE TABLE Z_PRIMARYKEY (
            Z_ENT INTEGER PRIMARY KEY, Z_NAME TEXT, Z_SUPER INTEGER, Z_MAX INTEGER
        );
    """)
    conn2.executemany("INSERT INTO Z_PRIMARYKEY VALUES (?,?,?,?)", [
        (10, "BankChequeAccount", 9, 2),
        (15, "InvestmentAccount", 9, 1),
        (19, "Category", 0, 3),
        (37, "DepositTransaction", 36, 1),
        (40, "InvestmentBuyTransaction", 36, 1),
        (45, "TransferDepositTransaction", 36, 1),
        (46, "TransferWithdrawTransaction", 36, 1),
        (47, "WithdrawTransaction", 36, 4),
    ])
    conn2.executemany(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZNAME, ZCURRENCYNAME, ZBALLANCE, ZARCHIVED, ZINCLUDEINNETWORTH) VALUES (?,?,?,?,?,?,?)",
        [(1, 10, "Compte Corrent", "EUR", 1500.00, 0, 1), (2, 15, "Trade Republic", "EUR", 8000.00, 0, 1)],
    )
    conn2.executemany(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZNAME2, ZTYPE2, ZPARENTCATEGORY) VALUES (?,?,?,?,?)",
        [(100, 19, "Casa", 1, None), (101, 19, "Roba", 1, None), (102, 19, "Súper", 1, 100)],
    )
    d1 = _apple_ts(date(2025, 1, 15))
    d2 = _apple_ts(date(2025, 2, 10))
    d3 = _apple_ts(date(2025, 3, 5))
    d4 = _apple_ts(date(2025, 4, 1))
    conn2.executemany(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZDATE1, ZAMOUNT1, ZCURRENCYNAME2, ZNOTES1, ZACCOUNT2, ZSTATUS1) VALUES (?,?,?,?,?,?,?,?)",
        [
            (200, 47, d1, -45.50, "EUR", "Mercadona", 1, 0),
            (201, 37, d2, 2500.0, "EUR", "Nòmina",    1, 1),
            (202, 45, d3,  300.0, "EUR", None,         1, 0),
        ],
    )
    conn2.execute(
        "INSERT INTO ZSYNCOBJECT (Z_PK, Z_ENT, ZDATE1, ZAMOUNT1, ZCURRENCYNAME2, ZNOTES1, ZACCOUNT2, ZSTATUS1, ZNUMBEROFSHARES, ZSYMBOL1) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (203, 40, d4, -500.0, "EUR", "EUNL buy", 2, 0, 4.5, "EUNL"),
    )
    conn2.execute(
        "INSERT INTO ZCATEGORYASSIGMENT (Z_PK, Z_ENT, ZASSIGMENTNUMBER, ZCATEGORY, ZTRANSACTION, ZAMOUNT) VALUES (?,?,?,?,?,?)",
        (300, 2, 0, 102, 200, -45.50),
    )
    conn2.commit()

    dest_conn = sqlite3.connect(tmp_path)
    conn2.backup(dest_conn)
    dest_conn.close()
    conn2.close()

    with open(tmp_path, "rb") as f:
        sqlite_bytes = f.read()
    os.unlink(tmp_path)
    return sqlite_bytes


def _build_moneywiz_zip() -> bytes:
    """Crea un ZIP de MoneyWiz sintètic amb el SQLite generat."""
    sqlite_bytes = _build_moneywiz_sqlite()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MoneyWiz_test.sqlite", sqlite_bytes)
    return buf.getvalue()


# ─── Tests de taules (síncrons) ───────────────────────────────────────────────

class TestSyncTables:
    def test_import_batches_table_exists(self, db_conn):
        row = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'import_batches'"
        )
        assert row == 1

    def test_mw_accounts_table_exists(self, db_conn):
        row = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'mw_accounts'"
        )
        assert row == 1

    def test_mw_categories_table_exists(self, db_conn):
        row = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'mw_categories'"
        )
        assert row == 1

    def test_mw_transactions_table_exists(self, db_conn):
        row = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'mw_transactions'"
        )
        assert row == 1

    def test_mw_transactions_unique_constraint(self, db_conn):
        row = db_conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.table_constraints "
            "WHERE constraint_name = 'uq_mw_transactions_mw_id'"
        )
        assert row == 1, "Falta constraint uq_mw_transactions_mw_id"

    def test_mw_transactions_index_on_date(self, db_conn):
        row = db_conn.fetchval(
            "SELECT COUNT(*) FROM pg_indexes "
            "WHERE tablename = 'mw_transactions' AND indexname = 'idx_mw_tx_date'"
        )
        assert row == 1, "Falta índex idx_mw_tx_date"


# ─── Tests del parser (síncron, sense BD) ────────────────────────────────────

class TestMoneyWizParser:
    """Tests de les funcions de parsing pur del SQLite, sense tocar PostgreSQL."""

    def _parse(self) -> dict:
        from modules.sync.service import _parse_zip_sync
        return _parse_zip_sync(_build_moneywiz_zip())

    def test_parser_returns_expected_keys(self):
        data = self._parse()
        assert set(data.keys()) == {"accounts", "categories", "transactions"}

    def test_parser_accounts_count(self):
        data = self._parse()
        assert len(data["accounts"]) == 2

    def test_parser_account_fields(self):
        data = self._parse()
        acc = next(a for a in data["accounts"] if a["name"] == "Compte Corrent")
        assert acc["account_type"] == "checking"
        assert acc["currency"] == "EUR"
        assert acc["is_active"] is True
        assert acc["include_in_networth"] is True
        assert acc["current_balance"] == pytest.approx(1500.0)

    def test_parser_investment_account_type(self):
        data = self._parse()
        acc = next(a for a in data["accounts"] if a["name"] == "Trade Republic")
        assert acc["account_type"] == "investment"

    def test_parser_categories_count(self):
        data = self._parse()
        assert len(data["categories"]) == 3

    def test_parser_categories_root_have_no_parent(self):
        data = self._parse()
        roots = [c for c in data["categories"] if c["mw_parent_id"] is None]
        assert len(roots) == 2

    def test_parser_category_child_has_parent(self):
        data = self._parse()
        child = next(c for c in data["categories"] if c["name"] == "Súper")
        assert child["mw_parent_id"] is not None

    def test_parser_transactions_count(self):
        data = self._parse()
        assert len(data["transactions"]) == 4

    def test_parser_expense_type(self):
        data = self._parse()
        expense = next(t for t in data["transactions"] if t["tx_type"] == "expense")
        assert expense["amount"] == pytest.approx(45.50)
        assert expense["notes"] == "Mercadona"
        assert expense["mw_category_id"] is not None  # categoria assignada

    def test_parser_income_type(self):
        data = self._parse()
        income = next(t for t in data["transactions"] if t["tx_type"] == "income")
        assert income["amount"] == pytest.approx(2500.0)
        assert income["is_reconciled"] is True

    def test_parser_investment_buy_type(self):
        data = self._parse()
        inv = next(t for t in data["transactions"] if t["tx_type"] == "investment_buy")
        assert inv["amount"] == pytest.approx(500.0)

    def test_parser_amounts_always_positive(self):
        """Els imports sempre es guarden positius — tx_type encoda la direcció."""
        data = self._parse()
        for t in data["transactions"]:
            assert t["amount"] >= 0, f"Import negatiu a {t['mw_internal_id']}"

    def test_parser_dates_are_date_objects(self):
        from datetime import date as date_type
        data = self._parse()
        for t in data["transactions"]:
            assert isinstance(t["tx_date"], date_type), f"tx_date no és date: {t['tx_date']}"

    def test_parser_transfer_types(self):
        data = self._parse()
        types = {t["tx_type"] for t in data["transactions"]}
        assert "transfer_in" in types


# ─── Tests d'endpoints (asíncrons) ───────────────────────────────────────────

class TestSyncEndpoints:

    @pytest.mark.asyncio
    async def test_status_returns_200(self, http_client):
        resp = await http_client.get("/api/v1/sync/status")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_status_schema(self, http_client):
        resp = await http_client.get("/api/v1/sync/status")
        body = resp.json()
        assert "total_accounts" in body
        assert "total_categories" in body
        assert "total_transactions" in body
        assert "last_import" in body

    @pytest.mark.asyncio
    async def test_batches_returns_200(self, http_client):
        resp = await http_client.get("/api/v1/sync/batches")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_upload_invalid_extension_returns_422(self, http_client):
        resp = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("backup.txt", b"not a zip", "text/plain")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_empty_file_returns_422(self, http_client):
        resp = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("backup.zip", b"", "application/zip")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_invalid_zip_content_returns_422(self, http_client):
        resp = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("backup.zip", b"not a real zip", "application/zip")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_synthetic_backup_returns_200(self, http_client):
        zip_bytes = _build_moneywiz_zip()
        resp = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_upload_creates_batch_record(self, http_client):
        zip_bytes = _build_moneywiz_zip()
        resp = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        body = resp.json()
        assert body["status"] == "completed"
        assert body["id"] > 0
        assert body["records_found"] > 0
        assert body["records_imported"] > 0

    @pytest.mark.asyncio
    async def test_upload_imports_accounts(self, http_client):
        zip_bytes = _build_moneywiz_zip()
        await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        status_resp = await http_client.get("/api/v1/sync/status")
        assert status_resp.json()["total_accounts"] >= 2

    @pytest.mark.asyncio
    async def test_upload_imports_categories(self, http_client):
        zip_bytes = _build_moneywiz_zip()
        await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        status_resp = await http_client.get("/api/v1/sync/status")
        assert status_resp.json()["total_categories"] >= 3

    @pytest.mark.asyncio
    async def test_upload_imports_transactions(self, http_client):
        zip_bytes = _build_moneywiz_zip()
        await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        status_resp = await http_client.get("/api/v1/sync/status")
        assert status_resp.json()["total_transactions"] >= 4

    @pytest.mark.asyncio
    async def test_upload_is_idempotent(self, http_client):
        """Pujar el mateix ZIP dues vegades no ha de duplicar les dades."""
        zip_bytes = _build_moneywiz_zip()

        await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        status_after_first = (await http_client.get("/api/v1/sync/status")).json()
        tx_count_1 = status_after_first["total_transactions"]

        await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        status_after_second = (await http_client.get("/api/v1/sync/status")).json()
        tx_count_2 = status_after_second["total_transactions"]

        assert tx_count_1 == tx_count_2, (
            f"Idempotència fallada: {tx_count_1} → {tx_count_2} transaccions (esperava igual)"
        )

    @pytest.mark.asyncio
    async def test_upload_second_call_no_deletions_for_identical_zip(self, http_client):
        """
        El segon upload del MATEIX ZIP no ha d'eliminar res (mirror idèntic):
        records_skipped == 0 perquè no hi ha registres obsolets.
        """
        zip_bytes = _build_moneywiz_zip()
        await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        resp2 = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        body = resp2.json()
        # Mirror idèntic: res s'elimina, tot s'actualitza (DO UPDATE)
        assert body["records_skipped"] == 0

    @pytest.mark.asyncio
    async def test_batches_list_contains_upload(self, http_client):
        zip_bytes = _build_moneywiz_zip()
        resp = await http_client.post(
            "/api/v1/sync/upload",
            files={"file": ("MoneyWiz_test.zip", zip_bytes, "application/zip")},
        )
        batch_id = resp.json()["id"]
        batches = (await http_client.get("/api/v1/sync/batches")).json()
        ids = [b["id"] for b in batches]
        assert batch_id in ids
