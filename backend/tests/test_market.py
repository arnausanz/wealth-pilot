"""
Integration tests for the market module.

These tests verify:
- DB tables (price_history, price_fetch_logs) exist and have correct structure
- API endpoints respond with correct schemas
- Gap fill endpoint is callable and returns the expected response shape
- Price history endpoint works correctly

NOTE: Gap fill calls Yahoo Finance over the network. In CI without network access
the test marks it as skipped. Locally it runs as a real integration test.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


# ─────────────────────────────────────────────────────────────────────────────
#  DB structure tests (use the sync db_conn fixture from conftest)
# ─────────────────────────────────────────────────────────────────────────────

class TestMarketTables:
    def test_price_history_table_exists(self, db_conn):
        exists = db_conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'price_history'
            )
        """)
        assert exists is True

    def test_price_fetch_logs_table_exists(self, db_conn):
        exists = db_conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'price_fetch_logs'
            )
        """)
        assert exists is True

    def test_price_history_unique_constraint(self, db_conn):
        """Verify the ON CONFLICT (asset_id, price_date) constraint exists."""
        exists = db_conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'price_history'
                  AND constraint_type = 'UNIQUE'
                  AND constraint_name = 'uq_price_history'
            )
        """)
        assert exists is True

    def test_price_history_columns(self, db_conn):
        cols = db_conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'price_history'
        """)
        col_names = {r["column_name"] for r in cols}
        required = {"id", "asset_id", "price_date", "price_close", "price_open",
                    "price_high", "price_low", "volume", "currency", "created_at"}
        assert required.issubset(col_names), f"Missing columns: {required - col_names}"

    def test_price_history_index_exists(self, db_conn):
        exists = db_conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'price_history'
                  AND indexname = 'idx_price_history_asset_date'
            )
        """)
        assert exists is True

    def test_market_indices_table_exists(self, db_conn):
        exists = db_conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'market_indices'
            )
        """)
        assert exists is True


# ─────────────────────────────────────────────────────────────────────────────
#  API endpoint tests (use the async http_client fixture from conftest)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestMarketEndpoints:
    async def test_get_prices_returns_200(self, http_client: AsyncClient):
        """GET /api/v1/market/prices must return 200 even with no price data."""
        response = await http_client.get("/api/v1/market/prices")
        assert response.status_code == 200

    async def test_get_prices_response_schema(self, http_client: AsyncClient):
        """Response must contain the required top-level fields."""
        response = await http_client.get("/api/v1/market/prices")
        body = response.json()
        required_keys = {"prices", "total_assets", "fresh_count", "stale_count",
                         "no_data_count", "cached"}
        assert required_keys.issubset(body.keys()), f"Missing keys: {required_keys - body.keys()}"

    async def test_get_prices_assets_count(self, http_client: AsyncClient):
        """Should return at least 8 active assets (seeded)."""
        response = await http_client.get("/api/v1/market/prices")
        body = response.json()
        assert body["total_assets"] >= 8

    async def test_get_prices_asset_schema(self, http_client: AsyncClient):
        """Each price item must have the expected fields."""
        response = await http_client.get("/api/v1/market/prices")
        prices = response.json()["prices"]
        assert len(prices) > 0
        first = prices[0]
        required = {"asset_id", "display_name", "asset_type", "currency",
                    "is_stale", "stale_days"}
        assert required.issubset(first.keys()), f"Missing fields: {required - first.keys()}"

    async def test_get_prices_is_cached_field_bool(self, http_client: AsyncClient):
        response = await http_client.get("/api/v1/market/prices")
        body = response.json()
        assert isinstance(body["cached"], bool)

    async def test_get_single_asset_price_404_on_invalid(self, http_client: AsyncClient):
        """Non-existent asset_id must return 404."""
        response = await http_client.get("/api/v1/market/prices/99999")
        assert response.status_code == 404

    async def test_get_history_404_on_invalid_asset(self, http_client: AsyncClient):
        """History for a non-existent asset must return 404."""
        response = await http_client.get("/api/v1/market/history/99999")
        assert response.status_code == 404

    async def test_get_history_valid_asset_returns_200(self, http_client: AsyncClient):
        """History for a real asset (with or without data) returns 200 with correct schema."""
        # Get an asset_id from the prices endpoint — avoids mixing db_conn's loop
        # with the async test's event loop (asyncpg "Future attached to different loop").
        prices = await http_client.get("/api/v1/market/prices")
        asset_id = prices.json()["prices"][0]["asset_id"]

        response = await http_client.get(f"/api/v1/market/history/{asset_id}?days=30")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "total_rows" in body
        assert isinstance(body["data"], list)

    async def test_get_history_days_validation(self, http_client: AsyncClient):
        """days parameter must be validated: 0 → 422, 3650 → 200."""
        prices = await http_client.get("/api/v1/market/prices")
        asset_id = prices.json()["prices"][0]["asset_id"]

        r_invalid = await http_client.get(f"/api/v1/market/history/{asset_id}?days=0")
        assert r_invalid.status_code == 422

        r_valid = await http_client.get(f"/api/v1/market/history/{asset_id}?days=3650")
        assert r_valid.status_code == 200

    async def test_refresh_endpoint_returns_200(self, http_client: AsyncClient):
        """POST /api/v1/market/refresh must return 200 with GapFillResponse schema."""
        response = await http_client.post("/api/v1/market/refresh")
        assert response.status_code == 200
        body = response.json()
        required = {"rows_inserted", "assets_updated", "assets_failed",
                    "assets_skipped", "duration_ms", "errors", "triggered_at"}
        assert required.issubset(body.keys()), f"Missing keys: {required - body.keys()}"

    async def test_refresh_response_types(self, http_client: AsyncClient):
        """Gap fill response fields must have correct types."""
        response = await http_client.post("/api/v1/market/refresh")
        body = response.json()
        assert isinstance(body["rows_inserted"], int)
        assert isinstance(body["assets_updated"], list)
        assert isinstance(body["assets_failed"], list)
        assert isinstance(body["assets_skipped"], list)
        assert isinstance(body["duration_ms"], int)
        assert isinstance(body["errors"], list)
        assert body["duration_ms"] >= 0
