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

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import settings  # noqa: E402
from main import app  # noqa: E402


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
