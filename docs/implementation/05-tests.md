# Tests — Suite d'Integració

> Última actualització: Març 2026 | 36 tests | 0 errors

---

## Estructura

```
tests/
└── run_tests.sh         Entry point: comprova que Docker corre i llança pytest

backend/tests/
├── conftest.py          Fixtures: db_conn (asyncpg sync wrapper), http_client (ASGI)
├── test_api.py          10 tests — endpoints FastAPI (health, 404, CORS, docs)
├── test_database.py     10 tests — estructura BD (taules, índexs, constraints, columnes)
└── test_seed.py         16 tests — dades inicials (assets, escenaris, paràmetres, etc.)
```

---

## Executar els Tests

```bash
make test          # Comprova que Docker estigui corrent i executa pytest
```

El `run_tests.sh` arranca el Docker stack si no està actiu i executa `pytest` dins del contenidor `backend`.

---

## Disseny dels Fixtures (`conftest.py`)

### `db_conn` — Connexió a BD (sync wrapper)
Tests de BD **no** usen async per evitar problemes d'event loop amb pytest-asyncio. En comptes, s'usa un wrapper síncrón sobre asyncpg:

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

Avantatge: lifecycle net, zero teardown errors, màxima simplicitat.

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

---

## Filosofia: Tests d'Integració, No Unitaris

Tots els tests corren contra la BD real (PostgreSQL al Docker). **No hi ha mocking.**

**Per què?** El projecte va tenir un bug crític on el mock passava però la BD real fallava (CORS_ORIGINS crash). Tests d'integració contra infraestructura real detecten problemes que els mocks amaguen: esquema incorrecte, migracions no aplicades, seed no executat, configuració de connexió incorrecta.

---

## Afegir Nous Tests

Quan s'implementi un nou mòdul (ex: Fase 1 — Yahoo Finance):
1. Crear `backend/tests/test_market.py`
2. Usar `db_conn` per verificar que les taules del mòdul existeixin i el seed s'hagi aplicat
3. Usar `http_client` per verificar que els nous endpoints responguin
4. `make test` hauria de continuar passant al 100%
