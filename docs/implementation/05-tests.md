# Tests — Suite d'Integració

> Última actualització: Març 2026 | 53 tests | 0 errors

---

## Estructura

```
tests/
└── run_tests.sh         Entry point: comprova que Docker corre i llança pytest

backend/tests/
├── conftest.py          Fixtures: _use_null_pool, db_conn, http_client
├── test_api.py          10 tests — endpoints FastAPI (health, 404, CORS, docs)
├── test_database.py     10 tests — estructura BD (taules, índexs, constraints, columnes)
├── test_seed.py         16 tests — dades inicials (assets, escenaris, paràmetres, etc.)
└── test_market.py       17 tests — mòdul de mercat (taules, endpoints, gap fill)
```

---

## Executar els Tests

```bash
make test          # Comprova que Docker estigui corrent i executa pytest
```

El `run_tests.sh` arranca el Docker stack si no està actiu i executa `pytest` dins del contenidor `backend`.

---

## Disseny dels Fixtures (`conftest.py`)

### `_use_null_pool` — Patch del motor SQLAlchemy (autouse, session-scoped)

El fixture més important i el menys visible. S'activa automàticament a l'inici de la sessió de tests.

**El problema:** pytest-asyncio crea un **event loop nou per cada test async**. SQLAlchemy amb asyncpg guarda connexions al pool lligades a l'event loop del test que les va crear. Quan el test N+1 (loop B) intenta reutilitzar una connexió del test N (loop A), asyncpg llança `RuntimeError: Future attached to a different loop`.

**La solució:** `NullPool` — desactiva el pooling de connexions. Cada request obre una connexió fresca i la tanca immediatament. Lleugerament més lent, però correcte i segur per a tests.

**Com funciona:** `get_db()` a `core/db.py` accedeix a `AsyncSessionLocal` via els seus globals (el namespace del mòdul `core.db`). Si reemplacem `core.db.AsyncSessionLocal` al fixture, `get_db()` veu automàticament el nou valor — sense tocar cap codi de l'app.

```python
@pytest.fixture(scope="session", autouse=True)
def _use_null_pool():
    test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    _core_db.engine = test_engine
    _core_db.AsyncSessionLocal = test_session_factory
    yield
```

### `db_conn` — Connexió a BD (sync wrapper)

Tests de BD síncrons que necessiten consultar la BD directament. Utilitza el seu **propi event loop** (no el de pytest-asyncio) per evitar conflictes.

```python
@pytest.fixture(scope="module")
def db_conn():
    loop = asyncio.new_event_loop()
    conn = loop.run_until_complete(asyncpg.connect(dsn))

    class SyncConn:
        def fetchval(self, query, *args): return loop.run_until_complete(conn.fetchval(...))
        def fetch(self, query, *args):    return loop.run_until_complete(conn.fetch(...))
        def fetchrow(self, query, *args): return loop.run_until_complete(conn.fetchrow(...))

    yield SyncConn()
    loop.run_until_complete(conn.close())
    loop.close()
```

**Regla important:** No usar `db_conn` dins de tests async (tests que usen `http_client`). Cridar `loop_A.run_until_complete()` des d'un coroutine que ja corre en `loop_B` de pytest-asyncio pot causar comportament imprevisible. En tests async, obtenir l'asset_id o dades necessàries via l'API HTTP.

### `http_client` — Client ASGI (async)

Per als tests de l'API, s'usa `httpx.AsyncClient` amb `ASGITransport`: crida directament a l'app FastAPI **sense obrir cap port de xarxa**. Molt ràpid.

```python
@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
```

---

## Cobertura dels Tests

### `test_api.py` (10 tests)
- `GET /health` → 200, body amb status/version/env, format semver
- `GET /api/v1` → 200, camp version = "v1"
- `GET /api/v1/nonexistent` → 404, format `{"error": "...", "path": "..."}`
- CORS headers presents amb Origin header
- `/api/docs` i `/api/openapi.json` accessibles

### `test_database.py` (10 tests)
- Connexió → `SELECT 1` retorna 1
- PostgreSQL versió ≥ 15.0
- BD connectada = "wealthpilot"
- Totes les 64+ taules existents (llista exhaustiva de 64 noms)
- Nombre de taules ≥ 64
- Alembic version aplicada
- Índexs crítics de performance presents
- Constraints úniques crítiques presents
- Columnes requerides a `assets` i `transactions`

### `test_seed.py` (16 tests)
- 8 assets actius, en l'ordre correcte (sort_order)
- Target weights entre 80% i 100%
- Assets ETF/crypto amb ticker_yf
- 24 escenaris (3 × 8), els 3 tipus presents
- Annual returns en rang [-100, 100]
- ≥ 7 contribucions actives amb import positiu
- 6 paràmetres crítics presents, categories vàlides
- Objectius "emergency_fund" i "home_purchase" presents
- Índexs de mercat S&P 500 i MSCI World presents
- ≥ 8 widgets de dashboard
- Bitcoin volatilitat > 40% en escenari base

### `test_market.py` (17 tests)

**Taules BD (6 tests):**
- `price_history` existeix amb les columnes correctes
- Constraint únic `uq_price_history` (asset_id, price_date) present
- Índex `idx_price_history_asset_date` present
- `price_fetch_logs` existeix
- `market_indices` existeix

**Endpoints API (11 tests):**
- `GET /api/v1/market/prices` → 200 amb schema `MarketPricesResponse`
- Response conté ≥ 8 assets (els seedats)
- Cada asset té `asset_id`, `display_name`, `asset_type`, `currency`, `is_stale`, `stale_days`
- Camp `cached` és boolean
- `GET /api/v1/market/prices/99999` → 404
- `GET /api/v1/market/history/99999` → 404
- `GET /api/v1/market/history/{id}?days=30` → 200 amb `data` (llista) i `total_rows`
- Validació del paràmetre `days`: 0 → 422, 3650 → 200
- `POST /api/v1/market/refresh` → 200 amb schema `GapFillResponse`
- `GapFillResponse` conté `rows_inserted` (int), `assets_updated` (list), `duration_ms` (int ≥ 0)

---

## Filosofia: Tests d'Integració, No Unitaris

Tots els tests corren contra la BD real (PostgreSQL al Docker). **No hi ha mocking.**

**Per què?** El projecte va tenir un bug crític on el mock passava però la BD real fallava (CORS_ORIGINS crash). Tests d'integració contra infraestructura real detecten problemes que els mocks amaguen: esquema incorrecte, migracions no aplicades, seed no executat, configuració de connexió incorrecta.

---

## Afegir Nous Tests

Quan s'implementi un nou mòdul (ex: Fase 2 — Portfolio):
1. Crear `backend/tests/test_portfolio.py`
2. Classe `TestPortfolioTables` (sync, usa `db_conn`): verifica taules, índexs, constraints
3. Classe `TestPortfolioEndpoints` (async, usa `http_client`): verifica que els endpoints responguin
4. **No barrejar `db_conn` i `http_client` en el mateix test** (vegeu la nota sobre event loops)
5. `make test` hauria de continuar passant al 100%
