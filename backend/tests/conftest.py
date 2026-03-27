"""
Shared pytest fixtures for WealthPilot backend tests.
All tests run against the real Docker PostgreSQL instance — no mocking.

DB fixtures are synchronous (use asyncio.run internally) to avoid pytest-asyncio
event loop teardown complications. API tests use the async ASGI client normally.
"""
import asyncio
import os
import sys

import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import settings  # noqa: E402
from main import app  # noqa: E402
import core.db as _core_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _use_null_pool():
    """
    Replace the SQLAlchemy engine with a NullPool engine for the test session.

    Why: pytest-asyncio creates a NEW event loop for each async test function.
    SQLAlchemy's default connection pool caches asyncpg connections tied to a
    specific event loop. When test N+1 (loop B) tries to reuse a connection from
    test N (loop A), asyncpg raises "Future attached to different loop".

    NullPool disables connection reuse — every request opens a fresh connection
    and closes it immediately. Slightly slower, but correct and safe for tests.

    How: monkey-patch core.db module-level variables. Because get_db() looks up
    AsyncSessionLocal via its __globals__ (the core.db namespace), this works
    without touching any app code.
    """
    test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    _core_db.engine = test_engine
    _core_db.AsyncSessionLocal = test_session_factory

    yield

    # Restore originals (good practice even if session ends)
    _core_db.engine = _core_db.engine
    _core_db.AsyncSessionLocal = _core_db.AsyncSessionLocal


def _asyncpg_dsn() -> str:
    """Convert SQLAlchemy URL (postgresql+asyncpg://...) to plain asyncpg DSN."""
    return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture(scope="module")
def db_conn():
    """
    Synchronous-wrapper DB connection fixture (module-scoped for performance).
    Provides a synchronous interface: use db_conn.run(coroutine) inside tests.
    """
    loop = asyncio.new_event_loop()
    conn = loop.run_until_complete(asyncpg.connect(_asyncpg_dsn()))

    class SyncConn:
        def fetchval(self, query, *args):
            return loop.run_until_complete(conn.fetchval(query, *args))

        def fetch(self, query, *args):
            return loop.run_until_complete(conn.fetch(query, *args))

        def fetchrow(self, query, *args):
            return loop.run_until_complete(conn.fetchrow(query, *args))

    yield SyncConn()

    loop.run_until_complete(conn.close())
    loop.close()


@pytest_asyncio.fixture
async def http_client():
    """ASGI test client that calls the FastAPI app directly (no network)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
